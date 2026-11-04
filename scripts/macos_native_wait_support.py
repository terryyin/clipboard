"""Child-wait harness and independent producer for the macOS wait probe.

``start_kind_child`` runs the public ``clipboard.wait_for_kind`` in a child
Python whose default native inspector is wrapped only to record each
observation, and ``start_text_change_child`` runs
``clipboard.wait_for_text_change`` with the default native text reader
wrapped the same way; both return once that child announces its first
observation (for the change wait, its baseline). ``finish_child`` collects
the child's JSON outcome; ``returned_after_copy`` and ``ended_at_timeout``
judge it against the probe's two timing bounds. ``pbcopy_independent`` is
the independent producer and ``session_state`` reads the CGSession
dictionary through JXA (independent of ``clipboard.*``).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from macos_native_clear_support import _jxa

ROOT = Path(__file__).resolve().parents[1]
INTERVAL_S = 0.5  # the children use the waits' default interval
SLACK_S = 0.1  # process slack on every timing bound

# The child records each native observation, then runs the public wait.
_CHILD = """
import json, sys, time
sys.path.insert(0, {root!r})
import clipboard
from clipboard import _offer, _text

observations = []

def recording(read, describe):
    def observe():
        started = time.monotonic()
        value = read()
        observations.append({{
            "started_at": started,
            "duration_s": time.monotonic() - started,
            **describe(value),
        }})
        if len(observations) == 1:
            print("observed", flush=True)
        return value
    return observe

{setup}
started = time.monotonic()
try:
    result = {call}
except clipboard.ClipboardContentError as exc:
    outcome = {{"raised": "ClipboardContentError", "message": str(exc)}}
else:
    outcome = {{"raised": None, {result_key!r}: {result_value}}}
finished = time.monotonic()
outcome.update(
    started_at=started,
    finished_at=finished,
    deadline=started + {timeout!r},
    elapsed_s=finished - started,
    observations=observations,
)
print(json.dumps(outcome), flush=True)
"""

_KIND_SETUP = """clipboard.set_clipboard_inspector(recording(
    _offer._default_clipboard_inspector,
    lambda snapshot: {"kinds": sorted(snapshot.kinds)},
))"""
_KIND_RESULT = (
    "None if result is None else "
    '{"kinds": sorted(result.kinds), "formats": list(result.formats)}'
)
# The probe copies only its own fixed strings, so the observed text is shown.
_TEXT_SETUP = """clipboard.set_text_clipboard_reader(recording(
    _text._default_text_clipboard_reader,
    lambda text: {"text": text},
))"""


# The dictionary keys are spelled ``CGSSession...`` / ``kCGSSession...``.
_JXA_SESSION = """
ObjC.import("CoreGraphics");
var d = ObjC.deepUnwrap(ObjC.castRefToObject($.CGSessionCopyCurrentDictionary()));
JSON.stringify({
  locked: d.CGSSessionScreenIsLocked === true || d.CGSSessionScreenIsLocked === 1,
  on_console: d.kCGSSessionOnConsoleKey === true || d.kCGSSessionOnConsoleKey === 1,
  login_done: d.kCGSessionLoginDoneKey === true || d.kCGSessionLoginDoneKey === 1
});
"""


def start_kind_child(kind: str, timeout: float) -> subprocess.Popen:
    """Start a child ``wait_for_kind``; return after its first observation."""
    return _start(
        setup=_KIND_SETUP,
        call=f"clipboard.wait_for_kind({kind!r}, timeout={timeout!r})",
        result_key="snapshot",
        result_value=_KIND_RESULT,
        timeout=timeout,
    )


def start_text_change_child(timeout: float) -> subprocess.Popen:
    """Start a child ``wait_for_text_change``; return after its baseline read."""
    return _start(
        setup=_TEXT_SETUP,
        call=f"clipboard.wait_for_text_change(timeout={timeout!r})",
        result_key="text",
        result_value="result",
        timeout=timeout,
    )


def _start(*, timeout: float, **parts: str) -> subprocess.Popen:
    code = _CHILD.format(root=str(ROOT), timeout=timeout, **parts)
    child = subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    announced = child.stdout.readline().strip()
    if announced != "observed":
        child.kill()
        out, err = child.communicate()
        raise RuntimeError(f"child made no first observation: {announced!r} {err!r}")
    return child


def finish_child(child: subprocess.Popen, bound: float) -> dict:
    """The child's return code, stderr and parsed JSON outcome."""
    try:
        out, err = child.communicate(timeout=bound)
    except subprocess.TimeoutExpired:
        child.kill()
        out, err = child.communicate()
        return {"error": f"child exceeded {bound} s", "stderr": err.strip()}
    run = {"returncode": child.returncode, "stderr": err.strip()}
    try:
        run["outcome"] = json.loads(out.strip().splitlines()[-1])
    except (IndexError, ValueError):
        run["outcome"] = None
        run["stdout"] = out
    return run


def _observation_timing(outcome: dict) -> tuple[list, float]:
    observations = outcome.get("observations", [])
    return observations, max((o["duration_s"] for o in observations), default=0.0)


def returned_after_copy(run: dict, copied: dict, timeout: float) -> tuple:
    """Judge a child wait that the independent ``copied`` should end.

    Returns ``(ok, observations, evidence)``. ``ok`` holds when the producer
    and the child succeeded, nothing was raised, and the wait returned after
    the copy started, before ``timeout``, and within one interval plus two
    observations (one may have started just before the copy landed) plus
    ``SLACK_S`` of the copy finishing; the step adds its result condition.
    """
    outcome = run.get("outcome") or {}
    observations, longest = _observation_timing(outcome)
    finished = outcome.get("finished_at", float("inf"))
    latency = finished - copied["finished_at"]
    ok = (
        copied["returncode"] == 0
        and run.get("returncode") == 0
        and outcome.get("raised") is None
        and finished > copied["started_at"]
        and outcome.get("elapsed_s", float("inf")) < timeout
        and latency <= INTERVAL_S + 2 * longest + SLACK_S
    )
    evidence = {
        "elapsed_s": outcome.get("elapsed_s"),
        "latency_after_copy_s": latency,
        "observation_count": len(observations),
        "longest_observation_s": longest,
    }
    return ok, observations, evidence


def ended_at_timeout(run: dict, result_key: str, timeout: float) -> tuple:
    """Judge a child wait that nothing should end before ``timeout``.

    Returns ``(ok, observations, evidence)``. ``ok`` holds when the child
    succeeded, nothing was raised, its ``result_key`` is ``None``, it
    observed at least once, no observation started after the deadline, and
    it returned no earlier than ``timeout`` and no later than ``timeout``
    plus one observation plus ``SLACK_S``.
    """
    outcome = run.get("outcome") or {}
    observations, longest = _observation_timing(outcome)
    elapsed = outcome.get("elapsed_s", float("inf"))
    deadline = outcome.get("deadline", float("-inf"))
    ok = (
        run.get("returncode") == 0
        and outcome.get("raised") is None
        and result_key in outcome
        and outcome[result_key] is None
        and bool(observations)
        and all(o["started_at"] <= deadline for o in observations)
        and timeout <= elapsed <= timeout + longest + SLACK_S
    )
    evidence = {
        "result": outcome.get(result_key, "missing"),
        "elapsed_s": elapsed,
        "timeout_s": timeout,
        "observation_count": len(observations),
        "longest_observation_s": longest,
    }
    return ok, observations, evidence


def pbcopy_independent(text: str) -> dict:
    """Independent producer: ``pbcopy`` in its own process, timed."""
    env = {**os.environ, "LANG": "en_US.UTF-8"}
    copy_started = time.monotonic()
    result = subprocess.run(
        ["pbcopy"], input=text, text=True, env=env, capture_output=True, timeout=30
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
        "started_at": copy_started,
        "finished_at": time.monotonic(),
    }


def session_state() -> dict:
    """``locked`` / ``on_console`` / ``login_done`` from CGSession (JXA)."""
    return _jxa(_JXA_SESSION, failure="CGSession state read failed")

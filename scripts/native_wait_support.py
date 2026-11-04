"""Child-wait harness, timing rules and steps shared by every native wait probe.

``start_kind_child`` runs the public ``clipboard.wait_for_kind`` in a child
Python whose default native inspector is wrapped only to record each
observation (kinds and native formats), and ``start_text_change_child`` runs
``clipboard.wait_for_text_change`` with the default native text reader
wrapped the same way (text per observation); both return once that child
announces its first observation (for the change wait, its baseline).
``finish_child`` collects the child's JSON outcome; ``returned_after_copy``
and ``ended_at_timeout`` judge it against the probe's two timing bounds,
which scale with the longest observation the child measured.

A ``WaitDesktop`` names what differs between desktops: the independent text
producer (``pbcopy``, ``xclip``, ``wl-copy``, PowerShell ``Set-Clipboard``)
with its step-name label, and the independent listing with its
empty-clipboard predicate used after each setup ``clipboard.clear()``. The
four steps below are the same on every desktop; each desktop's probe keeps
only its session gate and environment floors.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERVAL_S = 0.5  # the children use the waits' default interval
SLACK_S = 0.1  # process slack on every timing bound
WAIT_TIMEOUT_S = 20
NONE_TIMEOUT_S = 1
COPY_DELAY_S = 1.0
PRODUCED_TEXT = "wait probe text"
CHANGE_TIMEOUT_S = 20
RECOPY_TIMEOUT_S = 3
OLD_TEXT = "wait probe old text"
NEW_TEXT = "wait probe new text"

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
    lambda snapshot: {
        "kinds": sorted(snapshot.kinds),
        "formats": list(snapshot.formats),
    },
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


@dataclass(frozen=True)
class WaitDesktop:
    """One desktop's independent producer and listing, as the steps use them.

    ``produce(text)`` copies ``text`` from an independent process and returns
    a record whose ``returncode`` is 0 on success; ``listing()`` is the
    independent consumer and ``is_empty`` its empty-clipboard predicate.
    """

    producer: str
    produce: Callable[[str], dict]
    listing: Callable[[], dict]
    is_empty: Callable[[dict], bool]

    def copy(self, text: str) -> dict:
        """The independent producer's record, timed around the whole copy."""
        started = time.monotonic()
        produced = self.produce(text)
        return {**produced, "started_at": started, "finished_at": time.monotonic()}

    def cleared(self) -> dict:
        """``clipboard.clear()`` here, then the independent listing."""
        import clipboard

        clipboard.clear()
        listing = self.listing()
        return {"listing_after_clear": listing, "empty": bool(self.is_empty(listing))}


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
        copied.get("returncode") == 0
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


def step(name: str, ok: bool, **observed) -> dict:
    return {"step": name, "ok": bool(ok), **observed}


def text_appears_step(desktop: WaitDesktop) -> dict:
    """Step 1: ``wait_for_kind("text")`` from empty ends after the copy."""
    setup = desktop.cleared()
    child = start_kind_child("text", WAIT_TIMEOUT_S)
    time.sleep(COPY_DELAY_S)
    copied = desktop.copy(PRODUCED_TEXT)
    run = finish_child(child, WAIT_TIMEOUT_S + 30)
    listing_after_copy = desktop.listing()
    timely, observations, evidence = returned_after_copy(run, copied, WAIT_TIMEOUT_S)
    snapshot = (run.get("outcome") or {}).get("snapshot")
    ok = (
        setup["empty"]
        and timely
        and "text" in (snapshot or {}).get("kinds", [])
        and any("text" not in o["kinds"] for o in observations[:-1])
    )
    return step(
        f"1_wait_for_text_returns_after_independent_{desktop.producer}",
        ok,
        setup=setup,
        producer=copied,
        child=run,
        snapshot=snapshot,
        observed_kinds=[o["kinds"] for o in observations],
        listing_after_copy=listing_after_copy,
        **evidence,
    )


def nothing_copied_step(desktop: WaitDesktop) -> dict:
    """Step 2: ``wait_for_kind("html", timeout=1)`` with nothing copied."""
    setup = desktop.cleared()
    child = start_kind_child("html", NONE_TIMEOUT_S)
    run = finish_child(child, NONE_TIMEOUT_S + 30)
    bounded, observations, evidence = ended_at_timeout(run, "snapshot", NONE_TIMEOUT_S)
    return step(
        "2_wait_for_html_with_nothing_copied_returns_none_at_timeout",
        setup["empty"] and bounded,
        setup=setup,
        child=run,
        observed_kinds=[o["kinds"] for o in observations],
        **evidence,
    )


def text_change_step(desktop: WaitDesktop) -> dict:
    """Step 3: baseline old text, then the independent new text ends the wait."""
    baseline = desktop.copy(OLD_TEXT)
    child = start_text_change_child(CHANGE_TIMEOUT_S)
    time.sleep(COPY_DELAY_S)
    copied = desktop.copy(NEW_TEXT)
    run = finish_child(child, CHANGE_TIMEOUT_S + 30)
    timely, observations, evidence = returned_after_copy(run, copied, CHANGE_TIMEOUT_S)
    texts = [o["text"] for o in observations]
    text = (run.get("outcome") or {}).get("text", "missing")
    ok = (
        baseline.get("returncode") == 0
        and timely
        and texts[:1] == [OLD_TEXT]
        and text == NEW_TEXT
    )
    return step(
        "3_wait_for_text_change_returns_independent_new_text",
        ok,
        baseline_producer=baseline,
        producer=copied,
        child=run,
        text=text,
        observed_texts=texts,
        **evidence,
    )


def clear_then_recopy_step(desktop: WaitDesktop) -> dict:
    """Step 4: clearing and an identical recopy are not changes."""
    baseline = desktop.copy(OLD_TEXT)
    child = start_text_change_child(RECOPY_TIMEOUT_S)
    cleared = desktop.cleared()
    time.sleep(COPY_DELAY_S)
    recopied = desktop.copy(OLD_TEXT)
    run = finish_child(child, RECOPY_TIMEOUT_S + 30)
    bounded, observations, evidence = ended_at_timeout(run, "text", RECOPY_TIMEOUT_S)
    texts = [o["text"] for o in observations]
    first_clear = texts.index("") if "" in texts else len(texts)
    ok = (
        baseline.get("returncode") == 0
        and cleared["empty"]
        and recopied.get("returncode") == 0
        and bounded
        and texts[:1] == [OLD_TEXT]
        and OLD_TEXT in texts[first_clear + 1 :]
    )
    final_clear = desktop.cleared()
    return step(
        "4_wait_for_text_change_ignores_clear_then_identical_recopy",
        ok,
        baseline_producer=baseline,
        clear=cleared,
        producer=recopied,
        child=run,
        observed_texts=texts,
        final_clear=final_clear,
        **evidence,
    )


def run_steps(desktop: WaitDesktop) -> list[dict]:
    """Reset the seams the children rely on, then run the four steps."""
    import clipboard

    for reset in (
        clipboard.set_clipboard_inspector,
        clipboard.set_clipboard_clearer,
        clipboard.set_text_clipboard_reader,
    ):
        reset(None)
    return [
        text_appears_step(desktop),
        nothing_copied_step(desktop),
        text_change_step(desktop),
        clear_then_recopy_step(desktop),
    ]


def report(**fields) -> None:
    print(json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False))

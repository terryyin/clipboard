"""Child-wait harness and independent producer for the macOS wait probe.

``start_child`` runs the public ``clipboard.wait_for_kind`` in a child Python
whose default native inspector is wrapped only to record each observation,
and returns once that child announces its first observation;
``finish_child`` collects the child's JSON outcome. ``pbcopy_independent`` is
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

# The child records each native observation, then runs the public wait.
_CHILD = """
import json, sys, time
sys.path.insert(0, {root!r})
import clipboard
from clipboard import _offer

observations = []

def recording():
    started = time.monotonic()
    snapshot = _offer._default_clipboard_inspector()
    observations.append({{
        "started_at": started,
        "duration_s": time.monotonic() - started,
        "kinds": sorted(snapshot.kinds),
    }})
    if len(observations) == 1:
        print("observed", flush=True)
    return snapshot

clipboard.set_clipboard_inspector(recording)
started = time.monotonic()
try:
    result = clipboard.wait_for_kind({kind!r}, timeout={timeout!r})
except clipboard.ClipboardContentError as exc:
    outcome = {{"raised": "ClipboardContentError", "message": str(exc)}}
else:
    outcome = {{"raised": None, "snapshot": None if result is None else {{
        "kinds": sorted(result.kinds), "formats": list(result.formats)}}}}
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


def start_child(kind: str, timeout: float) -> subprocess.Popen:
    """Start a child ``wait_for_kind``; return after its first observation."""
    code = _CHILD.format(root=str(ROOT), kind=kind, timeout=timeout)
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

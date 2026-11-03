"""Independent JXA consumers and child-process drivers for the macOS clear probe.

The JXA readers use ``osascript -l JavaScript``, a different script stack from
the library's AppleScriptObjC, so their type listings are independent of
``clipboard.*``. The child drivers run the library under test in a separate
Python process that exits before anything is observed.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from native_probe_common import die

ROOT = Path(__file__).resolve().parents[1]
CHILD_TIMEOUT_S = 60

_JXA_TYPES = """
ObjC.import("AppKit");
var pb = $.NSPasteboard.generalPasteboard;
var types = ObjC.deepUnwrap(pb.types) || [];
JSON.stringify({types: types, changeCount: Number(pb.changeCount)});
"""

_JXA_SESSION = """
ObjC.import("CoreGraphics");
var d = ObjC.deepUnwrap(ObjC.castRefToObject($.CGSessionCopyCurrentDictionary()));
JSON.stringify({
  locked: d.CGSSessionScreenIsLocked === true || d.CGSSessionScreenIsLocked === 1,
  on_console: d.kCGSessionOnConsoleKey === true,
  login_done: d.kCGSessionLoginDoneKey === true
});
"""


def _jxa(script: str, *, failure: str) -> dict:
    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"{failure}: {exc}")
    if result.returncode != 0:
        die(f"{failure}: {(result.stderr or result.stdout or '').strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        die(f"{failure}: non-JSON output {result.stdout!r} ({exc})")


def list_types_independent() -> dict:
    """Independent consumer: JXA NSPasteboard types (no clipboard.*)."""
    return _jxa(_JXA_TYPES, failure="independent JXA type listing failed")


def session_state() -> dict:
    return _jxa(_JXA_SESSION, failure="CGSession state read failed")


def _child(code: str, *, what: str) -> dict:
    started = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(code)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=CHILD_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        die(
            f"child {what} did not finish within {CHILD_TIMEOUT_S}s "
            "(a privacy prompt or contended pasteboard may be blocking it)"
        )
    elapsed = round(time.monotonic() - started, 3)
    if result.returncode != 0:
        die(
            f"child {what} failed (returncode={result.returncode}; "
            f"stderr={(result.stderr or result.stdout).strip()!r})"
        )
    return {"exited": True, "elapsed_s": elapsed, "stdout": result.stdout.strip()}


def clear_in_child(times: int = 1) -> dict:
    """Library under test: clipboard.clear() in a child process that exits."""
    return _child(
        f"""
        import clipboard
        clipboard.set_clipboard_clearer(None)
        results = [clipboard.clear() for _ in range({times})]
        assert results == [None] * {times}, results
        print("cleared x{times}")
        """,
        what=f"clipboard.clear() x{times}",
    )


def copy_empty_in_child() -> dict:
    return _child(
        """
        import clipboard
        clipboard.copy("")
        print("copied empty")
        """,
        what='clipboard.copy("")',
    )

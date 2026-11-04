"""The macOS Aqua desktop for the shared native wait steps.

``pbcopy_independent`` is the independent producer, the JXA
``NSPasteboard types`` listing (``macos_native_clear_support``) the
independent consumer, and ``MACOS`` describes this desktop to
``native_wait_support``. ``session_state`` reads the CGSession dictionary
through JXA (independent of ``clipboard.*``).
"""

from __future__ import annotations

import os
import subprocess

from macos_native_clear_support import _jxa, list_types_independent
from native_wait_support import WaitDesktop

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


def pbcopy_independent(text: str) -> dict:
    """Independent producer: ``pbcopy`` in its own process."""
    env = {**os.environ, "LANG": "en_US.UTF-8"}
    result = subprocess.run(
        ["pbcopy"], input=text, text=True, env=env, capture_output=True, timeout=30
    )
    return {"returncode": result.returncode, "stderr": result.stderr.strip()}


MACOS = WaitDesktop(
    producer="pbcopy",
    produce=pbcopy_independent,
    listing=list_types_independent,
    is_empty=lambda listing: listing["types"] == [],
)


def session_state() -> dict:
    """``locked`` / ``on_console`` / ``login_done`` from CGSession (JXA)."""
    return _jxa(_JXA_SESSION, failure="CGSession state read failed")

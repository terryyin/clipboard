"""Held-clipboard steps for the gated Windows text probe.

The holder is ``windows_clipboard_holder.py`` in its own process, holding the
clipboard open with its own hidden window. The probe process observes the hold
independently with ``GetOpenClipboardWindow()`` before and after calling
``clipboard.paste`` / ``copy``, and the holder re-checks it before releasing.
"""

from __future__ import annotations

import ctypes
import json
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from windows_native_text_support import attempt, consume, set_clipboard, step

HOLDER = Path(__file__).with_name("windows_clipboard_holder.py")
HELD = "held text ✓"
HOLD_SECONDS = 4.0
SHORT_HOLD_SECONDS = 0.1
STEP = "5_held_clipboard_raises_then_recovers"


def open_clipboard_window() -> int:
    """``GetOpenClipboardWindow()`` seen from this process (0 when none)."""
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.GetOpenClipboardWindow.argtypes = []
    u.GetOpenClipboardWindow.restype = ctypes.c_void_p
    return u.GetOpenClipboardWindow() or 0


@contextmanager
def held(seconds: float):
    """Hold the clipboard from another process; yields its ready line.

    Readiness is the holder's own stdout line, printed only after its
    ``OpenClipboard(hwnd)`` succeeded. On exit the holder's release line is
    added under ``"release"``.
    """
    proc = subprocess.Popen(
        [sys.executable, "-I", str(HOLDER), str(seconds)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        line = proc.stdout.readline()
        ready = json.loads(line) if line.strip() else {"ready": False}
        yield ready
        rest, err = proc.communicate(timeout=seconds + 30)
        ready["release"] = json.loads(rest) if rest.strip() else {"stderr": err}
        ready["holder_exit"] = proc.returncode
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def _raised(result: dict) -> bool:
    return (
        result["value"] is None
        and bool(result["error"])
        and result["error"]["type"] == "ClipboardContentError"
        and bool(result["cause"])
        and result["cause"]["type"] == "PyperclipWindowsException"
    )


def held_clipboard_step(clipboard) -> dict:
    """During a real hold ``paste`` / ``copy`` raise; after release paste works."""
    producer = set_clipboard(HELD)
    observed: dict = {}
    with held(HOLD_SECONDS) as holder:
        if holder.get("ready"):
            ready_at = time.monotonic()
            observed["open_window_before_calls"] = open_clipboard_window()
            during_paste = attempt(clipboard.paste)
            during_copy = attempt(clipboard.copy, "must not land")
            observed["open_window_after_calls"] = open_clipboard_window()
            within = time.monotonic() - ready_at < HOLD_SECONDS
    if not holder.get("ready"):
        return step(STEP, False, "holder_could_not_open_clipboard", holder=holder)
    hwnd = holder.get("hwnd")
    release = holder.get("release", {})
    seen = [observed[k] == hwnd for k in sorted(observed)]
    established = producer["producer_exact"] and within and holder.get("holds_at_ready")
    limit = None
    if not (established and all(seen)):
        limit = "hold_not_established"
    elif not (release.get("holds_before_release") and release.get("close_ok")):
        limit = "hold_lost_before_release"
    stored = consume()
    after = attempt(clipboard.paste)
    ok = (
        _raised(during_paste)
        and _raised(during_copy)
        and stored.get("text") == HELD
        and after["value"] == HELD
    )
    return step(
        STEP,
        ok,
        limit,
        hold_seconds=HOLD_SECONDS,
        holder=holder,
        get_open_clipboard_window=observed,
        probe_saw_holder_window=all(seen),
        during_paste=during_paste,
        during_copy=during_copy,
        calls_within_hold=within,
        after_release_consumer_text=stored.get("text"),
        after_release_paste=after,
    )


def short_hold(clipboard) -> dict:
    """Recorded only: a hold shorter than pyperclip's ~0.5 s retry."""
    set_clipboard(HELD)
    with held(SHORT_HOLD_SECONDS) as holder:
        seen = open_clipboard_window() if holder.get("ready") else None
        got = attempt(clipboard.paste) if holder.get("ready") else None
    return {
        "hold_seconds": SHORT_HOLD_SECONDS,
        "holder": holder,
        "open_window_before_paste": seen,
        "paste": got,
        "succeeded": bool(got) and got["value"] == HELD,
    }

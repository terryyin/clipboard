"""Linux X11 clear: relinquish CLIPBOARD with libX11 ``XSetSelectionOwner``.

``XSetSelectionOwner(display, CLIPBOARD, None, CurrentTime)`` leaves
CLIPBOARD with no owner, so the previous owner (another application, or a
background ``xclip`` left by this library's own writers) receives
``SelectionClear`` and ``xclip -o -t TARGETS`` reports no owner. libX11 is
loaded with ``ctypes``; it is already installed wherever ``xclip`` runs.

The libX11 calls run in a child Python (``clipboard/_x11_relinquish.py`` as
a standalone script) bounded by ``_X11_CLEAR_TIMEOUT_S``: ``XOpenDisplay``
on an unresponsive server can block indefinitely, and libX11's default
error handlers exit the process. A thread could not be killed on timeout and
would keep the wedged connection inside the caller; a child is killed by
``subprocess.run`` when the bound expires.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from clipboard._desktop import _helper_failure_detail, _linux_x11_display
from clipboard._errors import ClipboardContentError

_X11_CLEAR_TIMEOUT_S = 10.0
_RELINQUISH_SCRIPT = Path(__file__).with_name("_x11_relinquish.py")
_MECHANISM = "libX11 XSetSelectionOwner(CLIPBOARD, None)"


def _relinquish_command() -> list[str]:
    # -I: no script directory, cwd, PYTHONPATH or user site on sys.path.
    return [sys.executable, "-I", str(_RELINQUISH_SCRIPT)]


def _error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(f"Linux X11 clipboard clear failed: {detail}")


def _outcome(stdout: str) -> dict | None:
    lines = (stdout or "").strip().splitlines()
    if not lines:
        return None
    try:
        outcome = json.loads(lines[-1])
    except ValueError:
        return None
    return outcome if isinstance(outcome, dict) else None


def _classified_error(outcome: dict, display: str) -> ClipboardContentError:
    kind = outcome.get("failure")
    detail = outcome.get("detail") or ""
    if kind == "libx11":
        return _error(
            "libX11 could not be loaded with ctypes; install libX11 (e.g. "
            "`sudo apt-get install libx11-6`, which xclip also needs)"
            + (f" ({detail})" if detail else "")
        )
    if kind == "display":
        return _error(
            f"could not open the X display DISPLAY={display!r} (XOpenDisplay "
            "failed); check that the X server is running and DISPLAY names it"
        )
    return _error(f"{_MECHANISM}: {detail or kind}")


def _x11_clipboard_clearer() -> None:
    """Leave X11 CLIPBOARD with no owner at all; return ``None``.

    A missing libX11 (naming ``libx11-6``), a ``DISPLAY`` that cannot be
    opened (naming ``DISPLAY`` and its value), a timeout, or any other child
    failure raises ``ClipboardContentError``.
    """
    display = _linux_x11_display() or ""
    try:
        result = subprocess.run(
            _relinquish_command(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=_X11_CLEAR_TIMEOUT_S,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            f"Linux X11 clipboard clear timed out (limit "
            f"{_X11_CLEAR_TIMEOUT_S:g}s); the X server at DISPLAY={display!r} "
            f"is not answering ({_MECHANISM})"
        ) from exc
    except OSError as exc:
        raise _error(f"could not run the libX11 clear helper ({exc})") from exc
    outcome = _outcome(result.stdout)
    if result.returncode == 0 and outcome == {"ok": True}:
        return
    if outcome is not None and "failure" in outcome:
        raise _classified_error(outcome, display)
    detail = _helper_failure_detail(result)
    raise _error(
        f"{_MECHANISM} helper exited with status {result.returncode}"
        + (f": {detail}" if detail else "")
    )

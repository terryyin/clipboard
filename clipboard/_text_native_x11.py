"""Linux X11 plain-text clipboard: owned ``xclip`` path (CLIPBOARD selection).

Reading lists ``TARGETS`` first, so absence never depends on parsing the
wording of a failed text conversion: an unowned CLIPBOARD (xclip's
``target TARGETS not available``) or an owner offering neither
``UTF8_STRING`` nor ``STRING`` reads ``""``. ``UTF8_STRING`` is decoded as
UTF-8 and ``STRING`` as Latin-1 (ICCCM). xclip exits 1 both for "no owner"
and for "Can't open display", so any other non-zero exit, timeout, or
missing helper raises ``ClipboardContentError`` quoting xclip's stderr.

Writing leaves a background ``xclip -i`` (its own session, detached stdio) as
the CLIPBOARD owner, so the text stays pasteable after Python exits, and
returns only once that owner serves exactly the written bytes as
``UTF8_STRING``. A ``TARGETS`` listing alone is not enough: the previous
owner usually lists ``UTF8_STRING`` too. Read and write each share one
10 s bound across their helper runs.
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time

from clipboard._desktop import _XCLIP_NO_TARGETS, _XCLIP_TARGETS_CMD
from clipboard._text_native_linux import (
    _LINUX_TEXT_TIMEOUT_S,
    _decode_text,
    _helper_log_suffix,
    _logged_exit_error,
    _remaining,
    _run_text_helper,
    _text_error,
    _text_exit_error,
    _text_launch_error,
)

_X11_TEXT_READ_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S
_X11_TEXT_WRITE_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S
# Each write-readiness read-back is bounded below the overall write bound.
_X11_TEXT_READBACK_TIMEOUT_S = 2.0
_X11_TEXT_POLL_INTERVAL_S = 0.05
_DESKTOP = "X11"
_PACKAGE = "xclip"
# Text targets in preference order with their ICCCM encodings.
_X11_TEXT_TARGETS = (("UTF8_STRING", "utf-8"), ("STRING", "latin-1"))
_XCLIP_WRITE_CMD = ["xclip", "-selection", "clipboard", "-i"]


def _xclip_read_cmd(target: str) -> list[str]:
    return ["xclip", "-selection", "clipboard", "-o", "-t", target]


def _run_xclip(cmd: list[str], deadline: float) -> subprocess.CompletedProcess[bytes]:
    return _run_text_helper(
        cmd,
        desktop=_DESKTOP,
        operation="read",
        package=_PACKAGE,
        deadline=deadline,
        bound=_X11_TEXT_READ_TIMEOUT_S,
    )


def _x11_text_targets(deadline: float) -> set[str] | None:
    """CLIPBOARD ``TARGETS``, or ``None`` when the selection has no owner."""
    result = _run_xclip(list(_XCLIP_TARGETS_CMD), deadline)
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", "replace")
        if _XCLIP_NO_TARGETS in stderr:
            return None
        raise _text_exit_error(_DESKTOP, "read", list(_XCLIP_TARGETS_CMD), result)
    return {
        line.strip()
        for line in (result.stdout or b"").decode("ascii", "replace").splitlines()
    }


def _x11_text_clipboard_reader() -> str:
    """Return CLIPBOARD's text exactly (``""`` when unowned or text-less)."""
    deadline = time.monotonic() + _X11_TEXT_READ_TIMEOUT_S
    targets = _x11_text_targets(deadline)
    if targets is None:
        return ""
    for target, encoding in _X11_TEXT_TARGETS:
        if target not in targets:
            continue
        cmd = _xclip_read_cmd(target)
        result = _run_xclip(cmd, deadline)
        if result.returncode != 0:
            # Advertised but not delivered: an unreadable offer, not absence.
            raise _text_exit_error(_DESKTOP, "read", cmd, result)
        return _decode_text(result.stdout or b"", encoding, _DESKTOP, f"xclip {target}")
    return ""


def _owner_serves(data: bytes, deadline: float) -> bool:
    """Whether CLIPBOARD's ``UTF8_STRING`` is exactly ``data`` (lenient probe)."""
    try:
        result = subprocess.run(
            _xclip_read_cmd("UTF8_STRING"),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=min(_X11_TEXT_READBACK_TIMEOUT_S, _remaining(deadline)),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout == data


def _stop_owner(proc: subprocess.Popen) -> None:
    """Best effort: stop an owner that never offered (its whole session).

    ``os.killpg`` is POSIX-only; without it, kill the owner process itself.
    """
    killpg = getattr(os, "killpg", None)
    try:
        if killpg is None:
            proc.kill()
        else:
            killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass


def _start_owner(data: bytes, log) -> subprocess.Popen:
    try:
        proc = subprocess.Popen(
            _XCLIP_WRITE_CMD,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
        )
    except OSError as exc:
        raise _text_launch_error(
            _DESKTOP, "write", _XCLIP_WRITE_CMD[0], _PACKAGE, exc
        ) from exc
    assert proc.stdin is not None
    try:
        proc.stdin.write(data)
        proc.stdin.close()
    except BrokenPipeError:
        pass  # xclip already exited; its status and stderr say why below.
    return proc


def _x11_text_clipboard_writer(text: str) -> None:
    """Replace CLIPBOARD with exactly ``text`` (already validated)."""
    data = text.encode("utf-8")
    deadline = time.monotonic() + _X11_TEXT_WRITE_TIMEOUT_S
    # stderr goes to an unlinked file, never a pipe the background owner holds.
    with tempfile.TemporaryFile() as log:
        proc = _start_owner(data, log)
        while True:
            status = proc.poll()
            if status not in (None, 0):
                raise _logged_exit_error(
                    _DESKTOP, "write", _XCLIP_WRITE_CMD, status, log
                )
            if _owner_serves(data, deadline):
                return
            if time.monotonic() >= deadline:
                _stop_owner(proc)
                raise _text_error(
                    _DESKTOP,
                    "write",
                    f"{' '.join(_XCLIP_WRITE_CMD)} did not serve the text as "
                    f"UTF8_STRING within the "
                    f"{_X11_TEXT_WRITE_TIMEOUT_S:g}s bound" + _helper_log_suffix(log),
                ) from subprocess.TimeoutExpired(
                    _XCLIP_WRITE_CMD, _X11_TEXT_WRITE_TIMEOUT_S
                )
            time.sleep(_X11_TEXT_POLL_INTERVAL_S)

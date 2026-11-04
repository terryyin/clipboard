"""Linux X11 plain text: owned ``xclip`` path for one selection.

The selection is a parameter: CLIPBOARD (the default, ``copy`` / ``paste``)
or PRIMARY (``copy_primary`` / ``paste_primary``); every helper run names
it with ``-selection`` and never touches the other one, and failures name
it ("clipboard text" / "primary selection text").

Reading lists ``TARGETS`` first, so absence never depends on parsing the
wording of a failed text conversion: an unowned selection (xclip's
no-owner wording, ``_desktop._xclip_reports_no_owner``) or an owner offering neither
``UTF8_STRING`` nor ``STRING`` reads ``""``. ``UTF8_STRING`` is decoded as
UTF-8 and ``STRING`` as Latin-1 (ICCCM); the listing decides which, because
a ``STRING``-only owner answers a ``UTF8_STRING`` request with exit 0 and its
raw Latin-1 bytes (xclip 0.13). xclip exits 1 both for "no owner"
and for "Can't open display", so any other non-zero exit, timeout, or
missing helper raises ``ClipboardContentError`` quoting xclip's stderr.

Writing leaves a background ``xclip -i`` (its own session, detached stdio) as
the selection owner, so the text stays pasteable after Python exits, and
returns only once that owner serves exactly the written bytes as
``UTF8_STRING``. A ``TARGETS`` listing alone is not enough: the previous
owner usually lists ``UTF8_STRING`` too. Read and write each share one
10 s bound across their helper runs.
"""

from __future__ import annotations

import subprocess
import tempfile
import time

from clipboard._desktop import (
    _XCLIP_PRIMARY_TARGETS_CMD,
    _XCLIP_TARGETS_CMD,
    _start_helper_owner,
    _stop_helper_owner,
    _xclip_reports_no_owner,
)
from clipboard._text_native_linux import (
    _CLIPBOARD,
    _LINUX_TEXT_TIMEOUT_S,
    _PRIMARY,
    _SELECTION_SUBJECTS,
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
# The selection names are xclip's ``-selection`` values; CLIPBOARD argv stays
# what ``copy`` / ``paste`` always ran.
_TARGETS_CMDS = {_CLIPBOARD: _XCLIP_TARGETS_CMD, _PRIMARY: _XCLIP_PRIMARY_TARGETS_CMD}


def _xclip_read_cmd(target: str, selection: str) -> list[str]:
    return ["xclip", "-selection", selection, "-o", "-t", target]


def _xclip_write_cmd(selection: str) -> list[str]:
    return ["xclip", "-selection", selection, "-i"]


def _run_xclip(
    cmd: list[str], deadline: float, selection: str
) -> subprocess.CompletedProcess[bytes]:
    return _run_text_helper(
        cmd,
        desktop=_DESKTOP,
        operation="read",
        package=_PACKAGE,
        deadline=deadline,
        bound=_X11_TEXT_READ_TIMEOUT_S,
        subject=_SELECTION_SUBJECTS[selection],
    )


def _x11_text_targets(deadline: float, selection: str) -> set[str] | None:
    """The selection's ``TARGETS``, or ``None`` when it has no owner."""
    cmd = list(_TARGETS_CMDS[selection])
    result = _run_xclip(cmd, deadline, selection)
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", "replace")
        if _xclip_reports_no_owner(stderr):
            return None
        raise _text_exit_error(
            _DESKTOP, "read", cmd, result, subject=_SELECTION_SUBJECTS[selection]
        )
    return {
        line.strip()
        for line in (result.stdout or b"").decode("ascii", "replace").splitlines()
    }


def _x11_text_clipboard_reader(selection: str = _CLIPBOARD) -> str:
    """Return the selection's text exactly (``""`` when unowned or text-less)."""
    subject = _SELECTION_SUBJECTS[selection]
    deadline = time.monotonic() + _X11_TEXT_READ_TIMEOUT_S
    targets = _x11_text_targets(deadline, selection)
    if targets is None:
        return ""
    for target, encoding in _X11_TEXT_TARGETS:
        if target not in targets:
            continue
        cmd = _xclip_read_cmd(target, selection)
        result = _run_xclip(cmd, deadline, selection)
        if result.returncode != 0:
            # Advertised but not delivered: an unreadable offer, not absence.
            raise _text_exit_error(_DESKTOP, "read", cmd, result, subject=subject)
        return _decode_text(
            result.stdout or b"",
            encoding,
            _DESKTOP,
            f"xclip {target}",
            subject=subject,
        )
    return ""


def _owner_serves(data: bytes, deadline: float, selection: str) -> bool:
    """Whether the selection's ``UTF8_STRING`` is exactly ``data`` (lenient)."""
    try:
        result = subprocess.run(
            _xclip_read_cmd("UTF8_STRING", selection),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=_remaining(deadline, _X11_TEXT_READBACK_TIMEOUT_S),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout == data


def _x11_text_clipboard_writer(text: str, selection: str = _CLIPBOARD) -> None:
    """Replace the selection with exactly ``text`` (already validated)."""
    subject = _SELECTION_SUBJECTS[selection]
    cmd = _xclip_write_cmd(selection)
    data = text.encode("utf-8")
    deadline = time.monotonic() + _X11_TEXT_WRITE_TIMEOUT_S
    # stderr goes to an unlinked file, never a pipe the background owner holds.
    with tempfile.TemporaryFile() as log:
        try:
            proc = _start_helper_owner(cmd, data, log)
        except OSError as exc:
            raise _text_launch_error(
                _DESKTOP, "write", cmd[0], _PACKAGE, exc, subject=subject
            ) from exc
        while True:
            status = proc.poll()
            if status not in (None, 0):
                raise _logged_exit_error(
                    _DESKTOP, "write", cmd, status, log, subject=subject
                )
            if _owner_serves(data, deadline, selection):
                return
            if time.monotonic() >= deadline:
                _stop_helper_owner(proc)
                raise _text_error(
                    _DESKTOP,
                    "write",
                    f"{' '.join(cmd)} did not serve the text as "
                    f"UTF8_STRING within the "
                    f"{_X11_TEXT_WRITE_TIMEOUT_S:g}s bound" + _helper_log_suffix(log),
                    subject=subject,
                ) from subprocess.TimeoutExpired(cmd, _X11_TEXT_WRITE_TIMEOUT_S)
            time.sleep(_X11_TEXT_POLL_INTERVAL_S)

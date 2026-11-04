"""Linux Wayland plain-text write: owned ``wl-copy`` path for one selection.

Writing pipes UTF-8 to ``wl-copy [--primary] --type text/plain;charset=utf-8``.
wl-copy forks a background source that keeps serving the selection after
Python exits; the foreground helper exits once the selection is set. The
explicit type stops wl-copy from guessing a MIME type from the content (a
script-like or markup-like text could otherwise be offered under a non-text
type); wl-copy still lists its generic text family (``text/plain``,
``UTF8_STRING``, ``TEXT``, ``STRING``) beside a text type, so independent
consumers keep finding the text. ``copy("")`` runs ``wl-copy --clear``
(pyperclip's choice), so ``paste()`` reads ``""``. A write shares one 10 s
bound across its helper runs.

PRIMARY: an unsupported compositor raises as on read
(``_text_native_wayland._check_primary_supported``). Because ``wl-copy
--primary`` can exit 0 for a write the compositor drops (observed once on
Sway with ``primary_selection disabled``), ``copy_primary`` returns only
once ``wl-paste --primary`` serves exactly the written bytes within the
same bound, as the X11 writer confirms; ``copy_primary("")`` offers empty
text (no ``--clear``) and is confirmed the same way.
"""

from __future__ import annotations

import subprocess
import tempfile
import time

from clipboard._text_native_linux import (
    _CLIPBOARD,
    _LINUX_TEXT_TIMEOUT_S,
    _PRIMARY,
    _SELECTION_SUBJECTS,
    _helper_log,
    _helper_log_suffix,
    _logged_exit_error,
    _remaining,
    _run_text_helper,
    _text_error,
    _text_launch_error,
)
from clipboard._text_native_wayland import (
    _DESKTOP,
    _PACKAGE,
    _SELECTION_FLAGS,
    _check_primary_supported,
    _wl_paste_read_cmd,
)

_WAYLAND_TEXT_WRITE_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S
_WAYLAND_PRIMARY_POLL_INTERVAL_S = 0.05
_WRITE_TYPE = "text/plain;charset=utf-8"
_WL_COPY_CLEAR_CMD = ["wl-copy", "--clear"]


def _wl_copy_write_cmd(selection: str) -> list[str]:
    return ["wl-copy", *_SELECTION_FLAGS[selection], "--type", _WRITE_TYPE]


def _run_wl_copy(
    cmd: list[str], data: bytes | None, deadline: float, selection: str
) -> None:
    """Run wl-copy to completion of its foreground part, before ``deadline``.

    stderr goes to an unlinked file, never a pipe the forked source would
    hold open; stdin is the text (or /dev/null for ``--clear``).
    """
    subject = _SELECTION_SUBJECTS[selection]
    with tempfile.TemporaryFile() as log:
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=log,
                start_new_session=True,
            )
        except OSError as exc:
            raise _text_launch_error(
                _DESKTOP, "write", cmd[0], _PACKAGE, exc, subject=subject
            ) from exc
        try:
            proc.communicate(
                input=data, timeout=_remaining(deadline, _WAYLAND_TEXT_WRITE_TIMEOUT_S)
            )
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
            raise _text_error(
                _DESKTOP,
                "write",
                f"{' '.join(cmd)} did not finish within the "
                f"{_WAYLAND_TEXT_WRITE_TIMEOUT_S:g}s bound (compositor stalled "
                "or not answering)" + _helper_log_suffix(log),
                subject=subject,
            ) from exc
        if proc.returncode != 0:
            _check_primary_supported(
                selection, "write", cmd, _helper_log(log).decode("utf-8", "replace")
            )
            raise _logged_exit_error(
                _DESKTOP, "write", cmd, proc.returncode, log, subject=subject
            )


def _confirm_primary(data: bytes, deadline: float) -> None:
    """Return once ``wl-paste --primary`` serves exactly ``data``; raise at
    ``deadline`` (a dropped write would otherwise pass as success).

    Unsupported PRIMARY raises at once; any other mismatch is polled again.
    """
    cmd = _wl_paste_read_cmd(_WRITE_TYPE, _PRIMARY)
    subject = _SELECTION_SUBJECTS[_PRIMARY]
    while True:
        result = _run_text_helper(
            cmd,
            desktop=_DESKTOP,
            operation="write",
            package=_PACKAGE,
            deadline=deadline,
            bound=_WAYLAND_TEXT_WRITE_TIMEOUT_S,
            subject=subject,
        )
        if result.returncode == 0 and (result.stdout or b"") == data:
            return
        stderr = (result.stderr or b"").decode("utf-8", "replace")
        _check_primary_supported(_PRIMARY, "write", cmd, stderr)
        if time.monotonic() >= deadline:
            detail = stderr.strip() or f"exit status {result.returncode}"
            raise _text_error(
                _DESKTOP,
                "write",
                f"{' '.join(_wl_copy_write_cmd(_PRIMARY))} exited but "
                f"{' '.join(cmd)} did not serve the written text within the "
                f"{_WAYLAND_TEXT_WRITE_TIMEOUT_S:g}s bound (last read: {detail}; "
                "the compositor may have dropped the primary selection write)",
                subject=subject,
            ) from subprocess.TimeoutExpired(cmd, _WAYLAND_TEXT_WRITE_TIMEOUT_S)
        time.sleep(_WAYLAND_PRIMARY_POLL_INTERVAL_S)


def _wayland_text_clipboard_writer(text: str, selection: str = _CLIPBOARD) -> None:
    """Replace the Wayland selection with exactly ``text`` (already validated)."""
    deadline = time.monotonic() + _WAYLAND_TEXT_WRITE_TIMEOUT_S
    if selection == _CLIPBOARD and text == "":
        _run_wl_copy(_WL_COPY_CLEAR_CMD, None, deadline, _CLIPBOARD)
        return
    data = text.encode("utf-8")
    _run_wl_copy(_wl_copy_write_cmd(selection), data, deadline, selection)
    if selection == _PRIMARY:
        _confirm_primary(data, deadline)

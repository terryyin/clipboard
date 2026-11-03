"""Linux Wayland plain-text clipboard: owned wl-clipboard path (regular selection).

Reading lists ``wl-paste --list-types`` first, so absence never depends on the
wording of a failed text conversion: wl-paste's known "nothing copied" stderr
(``_desktop._wl_paste_reports_nothing_copied``) or an offer with no text type reads
``""``. The first offered text type in ``_WAYLAND_TEXT_TYPES`` order is read
with ``wl-paste -n -t <type>`` (``-n``: wl-paste appends no newline of its
own). Every type is decoded strictly as UTF-8 except ``STRING``, which is
decoded as Latin-1 because that name declares the ICCCM ``STRING`` encoding
(as on X11); wl-copy also lists ``STRING`` for its UTF-8 text, but always
beside ``text/plain;charset=utf-8``, which is preferred. Any other non-zero
exit (for example "Failed to connect to a Wayland server" for a stale
``WAYLAND_DISPLAY``), timeout, or missing helper raises
``ClipboardContentError`` quoting wl-paste's stderr.

Writing pipes UTF-8 to ``wl-copy --type text/plain;charset=utf-8``. wl-copy
forks a background source that keeps serving the selection after Python
exits; the foreground helper exits once the selection is set. The explicit
type stops wl-copy from guessing a MIME type from the content (a script-like
or markup-like text could otherwise be offered under a non-text type);
wl-copy still lists its generic text family (``text/plain``,
``UTF8_STRING``, ``TEXT``, ``STRING``) beside a text type, so independent
consumers keep finding the text. ``copy("")`` runs ``wl-copy --clear``
(pyperclip's choice), so ``paste()`` reads ``""``. Read and write each share
one 10 s bound across their helper runs.
"""

from __future__ import annotations

import subprocess
import tempfile
import time

from clipboard._desktop import (
    _WL_PASTE_LIST_TYPES_HTML_CMD,
    _wl_paste_reports_nothing_copied,
)
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

_WAYLAND_TEXT_READ_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S
_WAYLAND_TEXT_WRITE_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S
_DESKTOP = "Wayland"
_PACKAGE = "wl-clipboard"
_WRITE_TYPE = "text/plain;charset=utf-8"
# Text types in preference order with their declared encodings.
_WAYLAND_TEXT_TYPES = (
    ("text/plain;charset=utf-8", "utf-8"),
    ("text/plain", "utf-8"),
    ("UTF8_STRING", "utf-8"),
    ("TEXT", "utf-8"),
    ("STRING", "latin-1"),
)
_LIST_TYPES_CMD = list(_WL_PASTE_LIST_TYPES_HTML_CMD)
_WL_COPY_WRITE_CMD = ["wl-copy", "--type", _WRITE_TYPE]
_WL_COPY_CLEAR_CMD = ["wl-copy", "--clear"]


def _wl_paste_read_cmd(mime_type: str) -> list[str]:
    return ["wl-paste", "-n", "-t", mime_type]


def _run_wl_paste(
    cmd: list[str], deadline: float
) -> subprocess.CompletedProcess[bytes]:
    return _run_text_helper(
        cmd,
        desktop=_DESKTOP,
        operation="read",
        package=_PACKAGE,
        deadline=deadline,
        bound=_WAYLAND_TEXT_READ_TIMEOUT_S,
    )


def _wayland_offered_types(deadline: float) -> list[str] | None:
    """The selection's MIME types, or ``None`` when nothing is copied."""
    result = _run_wl_paste(_LIST_TYPES_CMD, deadline)
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", "replace")
        if _wl_paste_reports_nothing_copied(stderr):
            return None
        raise _text_exit_error(_DESKTOP, "read", _LIST_TYPES_CMD, result)
    listing = (result.stdout or b"").decode("utf-8", "replace")
    return [line.strip() for line in listing.splitlines() if line.strip()]


def _pick_text_type(offered: list[str]) -> tuple[str, str] | None:
    """First preferred text type the offer lists (as listed) and its encoding.

    MIME types and parameter names are case-insensitive, so
    ``text/plain;charset=UTF-8`` counts as ``text/plain;charset=utf-8``.
    """
    by_key = {}
    for name in offered:
        by_key.setdefault(name.replace(" ", "").lower(), name)
    for wanted, encoding in _WAYLAND_TEXT_TYPES:
        listed = by_key.get(wanted.lower())
        if listed is not None:
            return listed, encoding
    return None


def _wayland_text_clipboard_reader() -> str:
    """Return the Wayland selection's text exactly (``""`` when absent)."""
    deadline = time.monotonic() + _WAYLAND_TEXT_READ_TIMEOUT_S
    offered = _wayland_offered_types(deadline)
    if offered is None:
        return ""
    picked = _pick_text_type(offered)
    if picked is None:
        return ""
    mime_type, encoding = picked
    cmd = _wl_paste_read_cmd(mime_type)
    result = _run_wl_paste(cmd, deadline)
    if result.returncode != 0:
        # Listed but not delivered (or replaced in between): not absence.
        raise _text_exit_error(_DESKTOP, "read", cmd, result)
    return _decode_text(
        result.stdout or b"", encoding, _DESKTOP, f"wl-paste {mime_type}"
    )


def _run_wl_copy(cmd: list[str], data: bytes | None) -> None:
    """Run wl-copy to completion of its foreground part, within the bound.

    stderr goes to an unlinked file, never a pipe the forked source would
    hold open; stdin is the text (or /dev/null for ``--clear``).
    """
    deadline = time.monotonic() + _WAYLAND_TEXT_WRITE_TIMEOUT_S
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
            raise _text_launch_error(_DESKTOP, "write", cmd[0], _PACKAGE, exc) from exc
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
            ) from exc
        if proc.returncode != 0:
            raise _logged_exit_error(_DESKTOP, "write", cmd, proc.returncode, log)


def _wayland_text_clipboard_writer(text: str) -> None:
    """Replace the Wayland selection with exactly ``text`` (already validated)."""
    if text == "":
        _run_wl_copy(_WL_COPY_CLEAR_CMD, None)
        return
    _run_wl_copy(_WL_COPY_WRITE_CMD, text.encode("utf-8"))

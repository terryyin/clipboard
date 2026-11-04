"""Linux Wayland plain text: owned wl-clipboard path for one selection.

The selection is a parameter: the regular selection (CLIPBOARD, the default,
``copy`` / ``paste``) or PRIMARY (``copy_primary`` / ``paste_primary``,
every helper run with ``--primary``); CLIPBOARD argv is what ``copy`` /
``paste`` always ran, and failures name the selection ("clipboard text" /
"primary selection text"). Writing lives in ``_text_native_wayland_writer``.

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
``ClipboardContentError`` quoting wl-paste's stderr. A read shares one 10 s
bound across its helper runs.

For PRIMARY, wl-clipboard's "compositor does not seem to support primary
selection" (``_desktop._wl_clipboard_reports_primary_unsupported``) raises
saying so (``_check_primary_supported``, which the writer shares), distinct
from nothing selected (``""``), and no other selection is tried.
"""

from __future__ import annotations

import subprocess
import time

from clipboard._desktop import (
    _WL_PASTE_LIST_TYPES_HTML_CMD,
    _WL_PASTE_PRIMARY_LIST_TYPES_CMD,
    _wl_clipboard_reports_primary_unsupported,
    _wl_paste_reports_nothing_copied,
)
from clipboard._errors import ClipboardContentError
from clipboard._text_native_linux import (
    _CLIPBOARD,
    _LINUX_TEXT_TIMEOUT_S,
    _NO_CLIPBOARD_FALLBACK,
    _PRIMARY,
    _SELECTION_SUBJECTS,
    _decode_text,
    _run_text_helper,
    _text_error,
    _text_exit_error,
)

_WAYLAND_TEXT_READ_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S
_DESKTOP = "Wayland"
_PACKAGE = "wl-clipboard"
# Text types in preference order with their declared encodings.
_WAYLAND_TEXT_TYPES = (
    ("text/plain;charset=utf-8", "utf-8"),
    ("text/plain", "utf-8"),
    ("UTF8_STRING", "utf-8"),
    ("TEXT", "utf-8"),
    ("STRING", "latin-1"),
)
# wl-clipboard's selection flags; CLIPBOARD argv carries none.
_SELECTION_FLAGS = {_CLIPBOARD: [], _PRIMARY: ["--primary"]}
_LIST_TYPES_CMDS = {
    _CLIPBOARD: _WL_PASTE_LIST_TYPES_HTML_CMD,
    _PRIMARY: _WL_PASTE_PRIMARY_LIST_TYPES_CMD,
}


def _wl_paste_read_cmd(mime_type: str, selection: str) -> list[str]:
    return ["wl-paste", *_SELECTION_FLAGS[selection], "-n", "-t", mime_type]


def _check_primary_supported(
    selection: str, operation: str, cmd: list[str], stderr: str
) -> None:
    """Raise when wl-clipboard says the compositor offers no PRIMARY."""
    if selection == _PRIMARY and _wl_clipboard_reports_primary_unsupported(stderr):
        raise _text_error(
            _DESKTOP,
            operation,
            "the compositor does not support the primary selection "
            f"({' '.join(cmd)}: {stderr.strip()}); {_NO_CLIPBOARD_FALLBACK}",
            subject=_SELECTION_SUBJECTS[selection],
        )


def _run_wl_paste(
    cmd: list[str], deadline: float, selection: str
) -> subprocess.CompletedProcess[bytes]:
    return _run_text_helper(
        cmd,
        desktop=_DESKTOP,
        operation="read",
        package=_PACKAGE,
        deadline=deadline,
        bound=_WAYLAND_TEXT_READ_TIMEOUT_S,
        subject=_SELECTION_SUBJECTS[selection],
    )


def _wl_paste_failed(
    selection: str, cmd: list[str], result: subprocess.CompletedProcess[bytes]
) -> ClipboardContentError:
    """A failed wl-paste run: PRIMARY unsupported raises, else the exit error."""
    stderr = (result.stderr or b"").decode("utf-8", "replace")
    _check_primary_supported(selection, "read", cmd, stderr)
    return _text_exit_error(
        _DESKTOP, "read", cmd, result, subject=_SELECTION_SUBJECTS[selection]
    )


def _wayland_offered_types(deadline: float, selection: str) -> list[str] | None:
    """The selection's MIME types, or ``None`` when nothing is copied."""
    cmd = list(_LIST_TYPES_CMDS[selection])
    result = _run_wl_paste(cmd, deadline, selection)
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", "replace")
        if _wl_paste_reports_nothing_copied(stderr):
            return None
        raise _wl_paste_failed(selection, cmd, result)
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


def _wayland_text_clipboard_reader(selection: str = _CLIPBOARD) -> str:
    """Return the Wayland selection's text exactly (``""`` when absent)."""
    deadline = time.monotonic() + _WAYLAND_TEXT_READ_TIMEOUT_S
    offered = _wayland_offered_types(deadline, selection)
    if offered is None:
        return ""
    picked = _pick_text_type(offered)
    if picked is None:
        return ""
    mime_type, encoding = picked
    cmd = _wl_paste_read_cmd(mime_type, selection)
    result = _run_wl_paste(cmd, deadline, selection)
    if result.returncode != 0:
        # Listed but not delivered (or replaced in between): not absence.
        raise _wl_paste_failed(selection, cmd, result)
    return _decode_text(
        result.stdout or b"",
        encoding,
        _DESKTOP,
        f"wl-paste {mime_type}",
        subject=_SELECTION_SUBJECTS[selection],
    )

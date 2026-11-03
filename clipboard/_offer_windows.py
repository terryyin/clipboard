"""Windows desktop clipboard format enumeration for offer inspect.

Uses ``ctypes`` / ``user32`` ``EnumClipboardFormats`` +
``GetClipboardFormatNameW`` (no ``win32clipboard`` / pywin32 required).
Standard CF_* ids map to stable names; registered formats (e.g.
``HTML Format``) use the system name. Enumeration does not fetch payloads.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from clipboard import _platform
from clipboard._errors import ClipboardContentError
from clipboard._offer import ClipboardOfferSnapshot, snapshot_from_native_formats

# Bound OpenClipboard retries so a locked clipboard cannot hang forever.
_OPEN_CLIPBOARD_TIMEOUT_S = 15.0
_OPEN_RETRY_SLEEP_S = 0.05

# https://learn.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats
_STANDARD_FORMAT_NAMES: dict[int, str] = {
    1: "CF_TEXT",
    2: "CF_BITMAP",
    3: "CF_METAFILEPICT",
    4: "CF_SYLK",
    5: "CF_DIF",
    6: "CF_TIFF",
    7: "CF_OEMTEXT",
    8: "CF_DIB",
    9: "CF_PALETTE",
    10: "CF_PENDATA",
    11: "CF_RIFF",
    12: "CF_WAVE",
    13: "CF_UNICODETEXT",
    14: "CF_ENHMETAFILE",
    15: "CF_HDROP",
    16: "CF_LOCALE",
    17: "CF_DIBV5",
}


def format_label_for_id(
    fmt: int,
    *,
    registered_name: str | None = None,
) -> str:
    """Map a Windows clipboard format id to a stable native label.

    Standard CF_* ids use the documented symbolic name. Registered formats
    prefer ``GetClipboardFormatName`` text (e.g. ``HTML Format``). Unknown
    ids without a name fall back to the decimal id string so they still
    appear in ``formats``.
    """
    standard = _STANDARD_FORMAT_NAMES.get(fmt)
    if standard is not None:
        return standard
    if registered_name:
        return registered_name
    return str(fmt)


def _load_user32():
    """Load ``user32`` with clipboard open/enum/empty prototypes (win32 only).

    Inspect enumerates through these; ``clipboard._clear_windows`` reuses the
    loader and ``_open_clipboard_bounded`` for ``EmptyClipboard``.
    """
    platform = _platform.current()
    if platform != "win32":
        raise ClipboardContentError(
            "Windows clipboard access requires win32 (user32 clipboard "
            f"functions); current platform is {platform!r}, or inject an "
            "inspector with set_clipboard_inspector or a clearer with "
            "set_clipboard_clearer for tests"
        )
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.EnumClipboardFormats.argtypes = [wintypes.UINT]
    user32.EnumClipboardFormats.restype = wintypes.UINT
    user32.GetClipboardFormatNameW.argtypes = [
        wintypes.UINT,
        wintypes.LPWSTR,
        ctypes.c_int,
    ]
    user32.GetClipboardFormatNameW.restype = ctypes.c_int
    return user32, ctypes


def _registered_name(user32, ctypes, fmt: int) -> str | None:
    buf = ctypes.create_unicode_buffer(256)
    n = user32.GetClipboardFormatNameW(fmt, buf, 256)
    if n <= 0:
        return None
    return buf.value or None


def _open_clipboard_bounded(user32, ctypes, *, operation: str, seam: str) -> None:
    """``OpenClipboard(NULL)``, retried until ``_OPEN_CLIPBOARD_TIMEOUT_S``.

    ``operation`` names what the caller was doing (e.g. ``enumerating
    formats``) and ``seam`` the test injection to suggest; both appear in the
    ``ClipboardContentError`` raised when the open still fails at the deadline
    (another process holds the clipboard, or access is denied).
    """
    deadline = time.monotonic() + _OPEN_CLIPBOARD_TIMEOUT_S
    while True:
        if user32.OpenClipboard(None):
            return
        if time.monotonic() >= deadline:
            err = ctypes.get_last_error()
            raise ClipboardContentError(
                f"Windows OpenClipboard failed while {operation} "
                f"(last_error={err}; timed out after "
                f"{_OPEN_CLIPBOARD_TIMEOUT_S:g}s; the clipboard may be locked, "
                "held by another process, or access was denied). Retry later "
                f"or inject {seam} for tests"
            )
        time.sleep(_OPEN_RETRY_SLEEP_S)


def _enumerate_open(
    user32,
    ctypes,
    *,
    name_lookup: Callable[[int], str | None] | None = None,
) -> tuple[str, ...]:
    """Enumerate formats while the clipboard is already open."""
    lookup = name_lookup or (lambda fmt: _registered_name(user32, ctypes, fmt))
    labels: list[str] = []
    fmt = 0
    while True:
        fmt = int(user32.EnumClipboardFormats(fmt))
        if fmt == 0:
            break
        labels.append(format_label_for_id(fmt, registered_name=lookup(fmt)))
    return tuple(labels)


def _enumerate_windows_clipboard_formats() -> tuple[str, ...]:
    """List offered Windows format names/ids without fetching payloads.

    Empty clipboard → empty tuple. OpenClipboard timeout / failure →
    ``ClipboardContentError`` (never a fabricated empty success).
    """
    user32, ctypes = _load_user32()
    _open_clipboard_bounded(
        user32,
        ctypes,
        operation="enumerating formats",
        seam="an inspector with set_clipboard_inspector",
    )
    try:
        return _enumerate_open(user32, ctypes)
    finally:
        user32.CloseClipboard()


def _windows_clipboard_inspector() -> ClipboardOfferSnapshot:
    """win32 default: map EnumClipboardFormats labels → offer snapshot."""
    return snapshot_from_native_formats(_enumerate_windows_clipboard_formats())

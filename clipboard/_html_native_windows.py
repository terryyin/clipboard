"""Windows HTML clipboard reader: ``HTML Format`` (CF_HTML) via user32/kernel32.

Uses ``ctypes`` only (no pywin32). ``ctypes`` is imported lazily inside
``_win32_api`` so this module imports on every platform; tests replace
``_win32_api`` with a fake to run without a Windows session.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ._errors import ClipboardContentError
from ._html_envelope import _cf_html_offer, _HtmlOffer

_WINDOWS_HTML_FORMAT = "HTML Format"
# OpenClipboard fails while another process holds the clipboard. Retry briefly
# so a momentary holder does not fail the read, but never wait indefinitely:
# at most (attempts - 1) * delay seconds of sleeping (0.9 s).
_OPEN_CLIPBOARD_ATTEMPTS = 10
_OPEN_CLIPBOARD_RETRY_SECONDS = 0.1


@dataclass(frozen=True)
class _Win32Api:
    """The Win32 entry points the reader needs (real ``ctypes`` or a test fake)."""

    user32: Any
    kernel32: Any
    get_last_error: Callable[[], int]
    format_error: Callable[[int], str]
    string_at: Callable[[int, int], bytes]
    sleep: Callable[[float], None]


def _declare_signatures(user32: Any, kernel32: Any) -> None:
    """Set argtypes/restype; handles and pointers are pointer-sized (64-bit)."""
    import ctypes

    handle = ctypes.c_void_p  # HWND / HANDLE / HGLOBAL / LPVOID
    uint, boolean = ctypes.c_uint, ctypes.c_int
    signatures = (
        (user32.RegisterClipboardFormatW, [ctypes.c_wchar_p], uint),
        (user32.IsClipboardFormatAvailable, [uint], boolean),
        (user32.OpenClipboard, [handle], boolean),
        (user32.CloseClipboard, [], boolean),
        (user32.GetClipboardData, [uint], handle),
        (kernel32.GlobalLock, [handle], handle),
        (kernel32.GlobalUnlock, [handle], boolean),
        (kernel32.GlobalSize, [handle], ctypes.c_size_t),
    )
    for function, argtypes, restype in signatures:
        function.argtypes = argtypes
        function.restype = restype


def _win32_api() -> _Win32Api:
    """Load user32/kernel32 with ``use_last_error`` (Windows only)."""
    import ctypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _declare_signatures(user32, kernel32)
    return _Win32Api(
        user32=user32,
        kernel32=kernel32,
        get_last_error=ctypes.get_last_error,
        format_error=lambda code: ctypes.FormatError(code).strip(),
        string_at=ctypes.string_at,
        sleep=time.sleep,
    )


def _windows_html_read_error(
    api: _Win32Api, detail: str, code: int | None = None
) -> ClipboardContentError:
    if code is None:
        code = api.get_last_error()
    win32 = f"Win32 error {code}" + (
        f": {api.format_error(code)}" if code else " (no error code)"
    )
    return ClipboardContentError(
        f"Windows HTML clipboard read failed: {detail} ({win32}); paste_html "
        "needs an interactive Windows desktop session with clipboard access"
    )


def _open_clipboard(api: _Win32Api) -> None:
    """``OpenClipboard(NULL)`` with a bounded retry while another process holds it."""
    code = 0
    for attempt in range(_OPEN_CLIPBOARD_ATTEMPTS):
        if attempt:
            api.sleep(_OPEN_CLIPBOARD_RETRY_SECONDS)
        if api.user32.OpenClipboard(None):
            return
        code = api.get_last_error()
    waited = (_OPEN_CLIPBOARD_ATTEMPTS - 1) * _OPEN_CLIPBOARD_RETRY_SECONDS
    raise _windows_html_read_error(
        api,
        f"OpenClipboard failed {_OPEN_CLIPBOARD_ATTEMPTS} times over "
        f"{waited:g}s; the clipboard is locked by another process (retry "
        "once it is released) or this process has no clipboard access",
        code,
    )


def _read_global_bytes(api: _Win32Api, data: int) -> bytes:
    """Copy a clipboard ``HGLOBAL``'s bytes; always unlocks what it locked."""
    pointer = api.kernel32.GlobalLock(data)
    if not pointer:
        raise _windows_html_read_error(
            api, f"GlobalLock failed on the {_WINDOWS_HTML_FORMAT} data handle"
        )
    try:
        size = api.kernel32.GlobalSize(data)
        if not size:
            raise _windows_html_read_error(
                api, f"GlobalSize reported no {_WINDOWS_HTML_FORMAT} data"
            )
        return api.string_at(pointer, size)
    finally:
        api.kernel32.GlobalUnlock(data)


def _windows_html_clipboard_reader() -> _HtmlOffer | None:
    """Read the registered ``HTML Format`` without mutating the clipboard.

    ``None`` when the format is not offered (text-only, image-only, file-list
    or empty clipboard). Otherwise returns the raw CF_HTML envelope bytes as an
    offer; ``clipboard._html_envelope`` cuts the fragment at its UTF-8 byte
    offsets. Never calls ``EmptyClipboard`` or ``SetClipboardData``.
    """
    api = _win32_api()
    html_format = api.user32.RegisterClipboardFormatW(_WINDOWS_HTML_FORMAT)
    if not html_format:
        raise _windows_html_read_error(
            api, f"RegisterClipboardFormatW({_WINDOWS_HTML_FORMAT!r}) failed"
        )
    if not api.user32.IsClipboardFormatAvailable(html_format):
        return None
    _open_clipboard(api)
    try:
        data = api.user32.GetClipboardData(html_format)
        if not data:
            raise _windows_html_read_error(
                api,
                f"{_WINDOWS_HTML_FORMAT} is offered but GetClipboardData "
                "returned no data (the owner failed to render it)",
            )
        return _cf_html_offer(_read_global_bytes(api, data))
    finally:
        api.user32.CloseClipboard()

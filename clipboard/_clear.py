"""Clear the current clipboard with an injectable backend (no Pillow needed).

``clear()`` asks a clearer to leave the current clipboard with no offer at all
and returns ``None``; failures raise ``ClipboardContentError``.
"""

from __future__ import annotations

from collections.abc import Callable

from . import _desktop, _platform
from ._errors import ClipboardContentError, _call_content_backend


def _unavailable_native_clearer_message() -> str:
    return (
        "clear native clipboard clearer is not available on this platform "
        f"({_platform.current()}); native clear covers macOS, Windows, and Linux "
        "X11 / Wayland desktops, so inject a clearer with "
        "set_clipboard_clearer for tests"
    )


_NO_LINUX_SESSION_MESSAGE = (
    "no desktop session is visible: neither DISPLAY nor WAYLAND_DISPLAY is "
    "set, so the Linux clipboard cannot be cleared (run inside an X11 or "
    "Wayland session, or inject a clearer with set_clipboard_clearer for tests)"
)


def _default_clipboard_clearer() -> None:
    """Platform-selected native clearer.

    macOS Aqua clears the general pasteboard through ``osascript`` / AppKit.
    On Linux, a Wayland session (``_desktop._is_linux_wayland``, so also when
    both ``DISPLAY`` and ``WAYLAND_DISPLAY`` are set) runs ``wl-copy
    --clear``; otherwise ``DISPLAY`` (``_desktop._linux_x11_display``)
    relinquishes X11 CLIPBOARD through libX11 ``XSetSelectionOwner``; no
    visible session raises ``ClipboardContentError``. Windows (``win32``) runs
    user32 ``EmptyClipboard`` after a bounded ``OpenClipboard``. Other
    platforms (no desktop clipboard this package knows) raise
    ``ClipboardContentError``.
    """
    platform = _platform.current()
    if platform == "darwin":
        from clipboard._clear_macos import _macos_clipboard_clearer

        _macos_clipboard_clearer()
        return
    if platform == "win32":
        from clipboard._clear_windows import _windows_clipboard_clearer

        _windows_clipboard_clearer()
        return
    if platform.startswith("linux"):
        if _desktop._is_linux_wayland():
            from clipboard._clear_wayland import _wayland_clipboard_clearer

            _wayland_clipboard_clearer()
            return
        if _desktop._linux_x11_display():
            from clipboard._clear_x11 import _x11_clipboard_clearer

            _x11_clipboard_clearer()
            return
        raise ClipboardContentError(_NO_LINUX_SESSION_MESSAGE)
    raise ClipboardContentError(_unavailable_native_clearer_message())


_clipboard_clearer: Callable[[], None] = _default_clipboard_clearer


def set_clipboard_clearer(clearer: Callable[[], None] | None) -> None:
    """Inject a clipboard clearer (tests / fakes); ``None`` restores default.

    The clearer takes no arguments and must leave the current clipboard with
    no offer at all or raise. ``ClipboardContentError`` passes through; other
    exceptions are wrapped as ``ClipboardContentError``.
    """
    global _clipboard_clearer
    _clipboard_clearer = _default_clipboard_clearer if clearer is None else clearer


def clear() -> None:
    """Remove every representation from the current clipboard; return ``None``.

    Does not require the optional ``clipboard[images]`` extra. Clearing an
    already empty clipboard, or clearing twice in a row, succeeds. Failures
    raise ``ClipboardContentError`` (the underlying error, if any, is
    ``__cause__``). The default clears the macOS general pasteboard, the
    Linux Wayland selection (``wl-copy --clear``, needs wl-clipboard) and
    Linux X11 CLIPBOARD (libX11 ``XSetSelectionOwner``), and the Windows
    clipboard (user32 ``EmptyClipboard``, open retried up to 15 s); other
    platforms have no native clearer, so the default raises
    ``ClipboardContentError`` naming the platform. Tests inject a fake via
    ``set_clipboard_clearer``.
    """
    _call_content_backend("clear", _clipboard_clearer)

"""Platform dispatch for native file-list clipboard readers and writers."""

from __future__ import annotations

from . import _platform
from ._desktop import _linux_wayland_without_x11
from ._errors import ClipboardContentError
from ._files_native_linux import (
    _linux_wayland_files_clipboard_reader,
    _linux_x11_files_clipboard_reader,
)
from ._files_native_macos import (
    _macos_files_clipboard_reader,
    _macos_files_clipboard_writer,
)
from ._files_native_wayland_writer import _wayland_files_clipboard_writer
from ._files_native_windows import _windows_files_clipboard_reader
from ._files_native_windows_writer import _windows_files_clipboard_writer
from ._files_native_x11_writer import _x11_files_clipboard_writer


def _unavailable_native_reader_message() -> str:
    return (
        "paste_files native file-list reader is not available on this platform "
        f"({_platform.current()}); need a usable desktop session with a file-list "
        "helper (Linux X11: text/uri-list via xclip or equivalent; Wayland: "
        "text/uri-list via wl-paste on a named compositor; Windows desktop: "
        "CF_HDROP), or inject a reader with set_files_clipboard_reader for tests"
    )


def _default_files_clipboard_reader() -> object:
    """Platform-selected file-list reader (Darwin; Linux; Windows CF_HDROP)."""
    platform = _platform.current()
    if platform == "darwin":
        return _macos_files_clipboard_reader()
    if platform.startswith("linux"):
        if _linux_wayland_without_x11():
            return _linux_wayland_files_clipboard_reader()
        return _linux_x11_files_clipboard_reader()
    if platform == "win32":
        return _windows_files_clipboard_reader()
    raise ClipboardContentError(_unavailable_native_reader_message())


def _unavailable_native_writer_message() -> str:
    return (
        "copy_files native file-list writer is not available on this platform "
        f"({_platform.current()}); no file-list copy offer adapter exists here yet "
        "(macOS Aqua, Windows desktop, Linux X11 and Linux Wayland are "
        "supported), so inject a writer with set_files_clipboard_writer for tests"
    )


def _default_files_clipboard_writer(paths: list[str]) -> None:
    """Platform-selected file-list copy writer.

    Darwin publishes file ``NSURL`` items through ``osascript`` / AppKit;
    Windows publishes ``CF_HDROP`` plus ``Preferred DropEffect`` copy through
    ``ctypes``; Linux X11 leaves a background ``xclip`` ``text/uri-list``
    owner, and a Wayland session without X11 ``DISPLAY`` (same session rule as
    the file-list reader) a background ``wl-copy`` server with the same body.
    Other platforms raise ``ClipboardContentError`` naming the platform.
    """
    platform = _platform.current()
    if platform == "darwin":
        _macos_files_clipboard_writer(paths)
        return
    if platform == "win32":
        _windows_files_clipboard_writer(paths)
        return
    if platform.startswith("linux"):
        if _linux_wayland_without_x11():
            _wayland_files_clipboard_writer(paths)
        else:
            _x11_files_clipboard_writer(paths)
        return
    raise ClipboardContentError(_unavailable_native_writer_message())

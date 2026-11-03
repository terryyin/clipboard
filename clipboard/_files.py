"""File-list clipboard read and copy write with injectable backends.

No Pillow needed: ``paste_files`` reads local file-list offers and
``copy_files`` validates local paths before handing them to a writer.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable

from ._errors import ClipboardContentError, _call_content_backend
from ._files_native import (
    _default_files_clipboard_reader,
    _default_files_clipboard_writer,
)
from ._files_offer import _normalize_files_offer

_files_clipboard_reader: Callable[[], object] = _default_files_clipboard_reader


def set_files_clipboard_reader(reader: Callable[[], object] | None) -> None:
    """Inject a file-list clipboard reader (tests / fakes).

    The reader returns a raw offer shape that ``paste_files`` normalizes:
    ``None`` / absence kinds → ``None``; path-list (``list[str]``) or structured
    ``uri-list`` / ``paths`` offers → ordered local paths; failures raise
    ``ClipboardContentError``. On macOS Aqua the default reader recovers
    Finder-equivalent ``NSFilenamesPboardType`` / file-URL offers via
    ``osascript`` / AppKit. On Linux X11 it requests ``text/uri-list`` via
    ``xclip -o -selection clipboard -t text/uri-list``; on Linux Wayland via
    ``wl-paste -t text/uri-list`` on a named compositor; on Windows desktop
    via ctypes ``CF_HDROP`` (no ``win32clipboard`` dependency; missing
    session → ``ClipboardContentError``, not silent ``None``). Other platforms
    raise until their adapters land, or tests inject a fake. Cut/move companion
    fields on structured offers are ignored.
    """
    global _files_clipboard_reader
    _files_clipboard_reader = (
        _default_files_clipboard_reader if reader is None else reader
    )


def paste_files() -> list[str] | None:
    """Return local filesystem paths from a file-list clipboard offer, or None.

    Does not require the optional ``clipboard[images]`` extra. Ordinary local
    file-list absence is ``None``. Failures other than ordinary absence raise
    ``ClipboardContentError`` (not ``ClipboardImageError``). On macOS Aqua the
    default reader uses ``osascript`` / AppKit for file-URL / filename
    pasteboard types (read-only; no filesystem open/move/delete). On Linux X11
    the default reader uses ``xclip`` ``text/uri-list``; on Linux Wayland,
    ``wl-paste`` ``text/uri-list``; on Windows desktop, ctypes ``CF_HDROP``
    path lists (same path-list normalization as injected offers). Other
    platforms raise until their adapters land; tests may inject a fake via
    ``set_files_clipboard_reader``.

    Injected readers may return path lists, structured ``uri-list`` / ``paths``
    offers (optional ignored cut markers), or absence kinds; ``paste_files``
    normalizes them the same way platform adapters do.
    """
    raw = _call_content_backend("file-list read", _files_clipboard_reader)
    return _normalize_files_offer(raw)


_files_clipboard_writer: Callable[[list[str]], None] = _default_files_clipboard_writer


def set_files_clipboard_writer(
    writer: Callable[[list[str]], None] | None,
) -> None:
    """Inject a file-list copy writer (tests / fakes); ``None`` restores default.

    The writer receives one ``list[str]`` of absolute local paths, already
    validated by ``copy_files``, and must publish them as one copy (not cut)
    file-list offer or raise. Other exceptions are wrapped as
    ``ClipboardContentError``.
    """
    global _files_clipboard_writer
    _files_clipboard_writer = (
        _default_files_clipboard_writer if writer is None else writer
    )


def _validate_copy_files_paths(paths: object) -> list[str]:
    """Reject invalid input before any clipboard replace (fail-before-replace).

    Returns absolute ``str`` paths in caller order, duplicates kept. Relative
    paths are made absolute against the current directory without resolving
    symlinks (``os.path.abspath``). Every path must exist now.
    """
    if isinstance(paths, (str, bytes, bytearray, memoryview)):
        raise ClipboardContentError(
            "copy_files requires an iterable of paths, not a bare "
            f"{type(paths).__name__} (wrap a single path in a list)"
        )
    if not isinstance(paths, Iterable):
        raise ClipboardContentError(
            "copy_files requires an iterable of str / os.PathLike paths "
            f"(got {type(paths).__name__})"
        )
    items = list(paths)
    if not items:
        raise ClipboardContentError(
            "copy_files requires at least one path "
            "(an empty file list would clear the clipboard)"
        )

    given_paths: list[str] = []
    absolute: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, (str, os.PathLike)):
            raise ClipboardContentError(
                f"copy_files path at index {index} must be str or os.PathLike "
                f"(got {type(item).__name__})"
            )
        path = os.fspath(item)
        if not isinstance(path, str):
            raise ClipboardContentError(
                f"copy_files path at index {index} must be a str path "
                f"(got {type(path).__name__} from os.fspath)"
            )
        if path == "" or "\x00" in path:
            raise ClipboardContentError(
                f"copy_files path at index {index} is not a valid path ({path!r})"
            )
        given_paths.append(path)
        absolute.append(os.path.abspath(path))

    missing = [
        given
        for given, full in zip(given_paths, absolute, strict=True)
        if not os.path.exists(full)
    ]
    if missing:
        names = ", ".join(repr(given) for given in missing)
        raise ClipboardContentError(f"copy_files path does not exist: {names}")
    return absolute


def copy_files(paths: Iterable[str | os.PathLike[str]]) -> None:
    """Replace the clipboard with one copy (not cut) file-list offer.

    ``paths`` is an ordered, non-empty iterable of ``str`` / ``os.PathLike``
    local paths to existing files or directories. Relative paths are made
    absolute against the current directory at call time (symlinks are kept,
    not resolved); order and duplicates pass through. Does not require the
    optional ``clipboard[images]`` extra.

    Invalid input (empty iterable, a bare ``str`` / ``bytes``, a non-path
    item, or a path that does not exist) raises ``ClipboardContentError``
    before the writer runs, so the current clipboard is left untouched.
    Writer, helper, access, or transfer failures also raise
    ``ClipboardContentError``. On macOS Aqua the default writer publishes one
    file-URL ``NSPasteboard`` item per path via ``osascript`` / AppKit; on
    Windows desktop it sets ``CF_HDROP`` with ``Preferred DropEffect`` copy via
    ``ctypes``; other platforms raise ``ClipboardContentError`` naming the
    platform until their writers land. Tests inject one via
    ``set_files_clipboard_writer``.
    """
    absolute = _validate_copy_files_paths(paths)
    _call_content_backend("file-list write", _files_clipboard_writer, absolute)

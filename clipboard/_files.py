"""File-list clipboard read with injectable backends (no Pillow needed)."""

from __future__ import annotations

from collections.abc import Callable

from ._errors import ClipboardContentError, _call_content_backend


def _default_files_clipboard_reader() -> list[str] | None:
    """Structure-only stub until platform file-list readers land.

    Raises rather than returning ``None`` so an unimplemented native path is
    not mistaken for ordinary file-list absence. Inject a fake via
    ``set_files_clipboard_reader`` for desktop-free tests.
    """
    raise ClipboardContentError(
        "paste_files native file-list reader is not available yet; "
        "inject a reader with set_files_clipboard_reader for tests"
    )


_files_clipboard_reader: Callable[[], list[str] | None] = (
    _default_files_clipboard_reader
)


def set_files_clipboard_reader(
    reader: Callable[[], list[str] | None] | None,
) -> None:
    """Inject a file-list clipboard reader (tests / fakes)."""
    global _files_clipboard_reader
    _files_clipboard_reader = (
        _default_files_clipboard_reader if reader is None else reader
    )


def paste_files() -> list[str] | None:
    """Return local filesystem paths from a file-list clipboard offer, or None.

    Does not require the optional ``clipboard[images]`` extra. Ordinary local
    file-list absence is ``None``. Failures other than ordinary absence raise
    ``ClipboardContentError`` (not ``ClipboardImageError``). The default reader
    is a structure-only stub that raises until platform adapters land; tests
    inject a fake via ``set_files_clipboard_reader``.
    """
    return _call_content_backend("file-list read", _files_clipboard_reader)

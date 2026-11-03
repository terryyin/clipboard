"""Plain-text clipboard contract (``copy`` / ``paste``) behind an explicit seam.

Validation, coercion, ``None`` → ``""`` normalization, and failure translation
sit above the seam so every backend shares them. The default backend selects
its owner per call by session (``_desktop_text._text_session_owner``,
pyperclip's order, minus its process-wide resolved state): Windows, WSL, X11
without ``xclip``, and other platforms delegate to pyperclip (resolved lazily,
so ``import clipboard`` never makes pyperclip pick a mechanism); a mechanism
the caller resolved in pyperclip never displaces an owned path;
macOS (``_text_native_macos``: ``pbcopy`` / ``pbpaste``), Linux X11 with
``xclip`` (``_text_native_x11``), and Linux Wayland with wl-clipboard
(``_text_native_wayland``) are owned paths.
"""

from __future__ import annotations

from collections.abc import Callable

from . import (
    _desktop_text,
    _text_native_macos,
    _text_native_wayland,
    _text_native_x11,
)
from ._errors import ClipboardContentError, _call_content_backend


def _select_text_backend() -> str:
    """Choose the default text backend at call time (never at import).

    The session rule in ``_desktop_text._text_session_owner`` decides, raising
    ``ClipboardContentError`` when no desktop session or helper is visible.
    A mechanism the caller already resolved in pyperclip (``set_clipboard`` or
    earlier pyperclip use) is deliberately ignored; delegation is explicit
    through ``set_text_clipboard_writer`` / ``set_text_clipboard_reader``.
    """
    return _desktop_text._text_session_owner()


# Owned paths by session owner; any other owner delegates to pyperclip.
_OWNED_TEXT_WRITERS: dict[str, Callable[[str], None]] = {
    _desktop_text._TEXT_OWNER_MACOS: _text_native_macos._macos_text_clipboard_writer,
    _desktop_text._TEXT_OWNER_X11: _text_native_x11._x11_text_clipboard_writer,
    _desktop_text._TEXT_OWNER_WAYLAND: (
        _text_native_wayland._wayland_text_clipboard_writer
    ),
}
_OWNED_TEXT_READERS: dict[str, Callable[[], object]] = {
    _desktop_text._TEXT_OWNER_MACOS: _text_native_macos._macos_text_clipboard_reader,
    _desktop_text._TEXT_OWNER_X11: _text_native_x11._x11_text_clipboard_reader,
    _desktop_text._TEXT_OWNER_WAYLAND: (
        _text_native_wayland._wayland_text_clipboard_reader
    ),
}


def _default_text_clipboard_writer(text: str) -> None:
    """Write through the session's backend; pyperclip's ``copy`` is looked up
    at call time because pyperclip swaps it on first use.
    """
    owned = _OWNED_TEXT_WRITERS.get(_select_text_backend())
    if owned is not None:
        owned(text)
        return
    import pyperclip

    pyperclip.copy(text)


def _default_text_clipboard_reader() -> object:
    """Read through the session's backend (pyperclip ``paste`` at call time)."""
    owned = _OWNED_TEXT_READERS.get(_select_text_backend())
    if owned is not None:
        return owned()
    import pyperclip

    return pyperclip.paste()


_text_clipboard_writer: Callable[[str], None] = _default_text_clipboard_writer
_text_clipboard_reader: Callable[[], object] = _default_text_clipboard_reader


def set_text_clipboard_writer(writer: Callable[[str], None] | None) -> None:
    """Inject a plain-text clipboard writer (fakes, or deliberate delegation
    such as ``lambda text: pyperclip.copy(text)``); ``None`` restores the
    default session-dispatched writer.

    The writer receives an already validated ``str``.
    """
    global _text_clipboard_writer
    _text_clipboard_writer = (
        _default_text_clipboard_writer if writer is None else writer
    )


def set_text_clipboard_reader(reader: Callable[[], object] | None) -> None:
    """Inject a plain-text clipboard reader (fakes, or deliberate delegation
    such as ``lambda: pyperclip.paste()``); ``None`` restores the default
    session-dispatched reader.

    A reader returning ``None`` means no text is offered; ``paste`` returns
    ``""``.
    """
    global _text_clipboard_reader
    _text_clipboard_reader = (
        _default_text_clipboard_reader if reader is None else reader
    )


def _validate_copy_text(text: object) -> str:
    """Coerce like pyperclip (``str()``) and reject text the clipboard would
    silently lose, before anything is replaced.
    """
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception as exc:
            raise ClipboardContentError(
                f"clipboard text write failed: cannot convert "
                f"{type(text).__name__} to str: {exc}"
            ) from exc
    if "\x00" in text:
        raise ClipboardContentError(
            "clipboard text write rejected: text contains a NUL character "
            "('\\x00'), which native clipboards would silently truncate"
        )
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ClipboardContentError(
            "clipboard text write rejected: text is not UTF-8 encodable "
            f"(lone surrogate or invalid code point): {exc}"
        ) from exc
    return text


def copy(text) -> None:
    """Replace the clipboard with ``text`` (non-``str`` values via ``str()``).

    Raises ``ClipboardContentError`` for text containing ``"\\x00"`` or not
    UTF-8 encodable (before replacing), and for any backend failure.
    """
    validated = _validate_copy_text(text)
    _call_content_backend("text write", _text_clipboard_writer, validated)


def paste() -> str:
    """Return the clipboard's text as ``str`` (``""`` when no text is offered,
    never ``None``).

    Line endings are returned untranslated (``splitlines()`` splits portably).
    Backend failures raise ``ClipboardContentError``.
    """
    value = _call_content_backend("text read", _text_clipboard_reader)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ClipboardContentError(
            f"clipboard text read failed: backend returned {type(value).__name__}, "
            "not str"
        )
    return value

"""Plain-text clipboard contract (``copy`` / ``paste``) behind an explicit seam.

Validation, coercion, ``None`` → ``""`` normalization, and failure translation
sit above the seam so every backend shares them. The default backend delegates
to pyperclip, resolved lazily at call time so ``import clipboard`` never makes
pyperclip pick a mechanism.
"""

from __future__ import annotations

from collections.abc import Callable

from ._errors import ClipboardContentError, _call_content_backend


def _default_text_clipboard_writer(text: str) -> None:
    """Delegate to pyperclip's current ``copy`` (looked up at call time)."""
    import pyperclip

    pyperclip.copy(text)


def _default_text_clipboard_reader() -> object:
    """Delegate to pyperclip's current ``paste`` (looked up at call time)."""
    import pyperclip

    return pyperclip.paste()


_text_clipboard_writer: Callable[[str], None] = _default_text_clipboard_writer
_text_clipboard_reader: Callable[[], object] = _default_text_clipboard_reader


def set_text_clipboard_writer(writer: Callable[[str], None] | None) -> None:
    """Inject a plain-text clipboard writer (tests / fakes); ``None`` restores
    the default pyperclip-backed writer.

    The writer receives an already validated ``str``.
    """
    global _text_clipboard_writer
    _text_clipboard_writer = (
        _default_text_clipboard_writer if writer is None else writer
    )


def set_text_clipboard_reader(reader: Callable[[], object] | None) -> None:
    """Inject a plain-text clipboard reader (tests / fakes); ``None`` restores
    the default pyperclip-backed reader.

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
    """Return the clipboard's text as ``str`` (``""`` when no text is offered).

    Line endings are returned untranslated. Backend failures raise
    ``ClipboardContentError``.
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

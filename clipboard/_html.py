"""HTML clipboard read/write with injectable backends (no Pillow needed)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from ._errors import ClipboardContentError
from ._html_envelope import _decode_html_offer
from ._html_native import (
    _default_html_clipboard_reader,
    _default_html_clipboard_writer,
)

_T = TypeVar("_T")


_html_clipboard_writer: Callable[[str, str], None] = _default_html_clipboard_writer


def set_html_clipboard_writer(
    writer: Callable[[str, str], None] | None,
) -> None:
    """Inject an HTML+plain-text dual-offer writer (tests / fakes)."""
    global _html_clipboard_writer
    _html_clipboard_writer = (
        _default_html_clipboard_writer if writer is None else writer
    )


def _call_content_backend(operation: str, backend: Callable[..., _T], *args) -> _T:
    """Run an HTML/rich clipboard backend; non-content failures become
    ``ClipboardContentError`` while backend ``ClipboardContentError`` passes as is.
    """
    try:
        return backend(*args)
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard {operation} failed: {exc}") from exc


def _validate_copy_html_args(html: object, text: object) -> tuple[str, str]:
    """Reject invalid HTML/text before any clipboard replace (fail-before-replace).

    Empty HTML (no usable fragment after strip) is invalid. ``text`` must be a
    non-empty ``str``; the plain-text alternative is caller-supplied and is not
    synthesized from HTML.
    """
    if not isinstance(html, str) or not isinstance(text, str):
        raise ClipboardContentError(
            "copy_html requires html and text as str "
            f"(got html={type(html).__name__}, text={type(text).__name__})"
        )
    if not html.strip():
        raise ClipboardContentError(
            "copy_html requires a non-empty HTML fragment "
            "(empty or whitespace-only HTML is invalid)"
        )
    if text == "":
        raise ClipboardContentError(
            "copy_html requires a non-empty plain-text alternative"
        )
    return html, text


def copy_html(html: str, text: str) -> None:
    """Publish HTML and a matching plain-text alternative as one clipboard offer.

    Does not require the optional ``clipboard[images]`` extra. Failures raise
    ``ClipboardContentError``. Invalid arguments are rejected before the
    writer runs. On macOS Aqua the default writer publishes both types as one
    ``NSPasteboard`` offer (via ``osascript`` / AppKit). Other platforms still
    need an injected writer via ``set_html_clipboard_writer`` until their
    native adapters land. Writers must publish both representations together;
    inability to offer both, or transfer failure, must surface as
    ``ClipboardContentError`` (not silent text-only success).
    """
    html, text = _validate_copy_html_args(html, text)
    _call_content_backend("HTML+text write", _html_clipboard_writer, html, text)


_html_clipboard_reader: Callable[[], object] = _default_html_clipboard_reader


def set_html_clipboard_reader(reader: Callable[[], object] | None) -> None:
    """Inject an HTML clipboard reader (tests / fakes); ``None`` restores default.

    The reader takes no arguments and returns ``None`` when no HTML is offered,
    or a package-private offer from ``clipboard._html_envelope``
    (``_cf_html_offer(bytes)`` / ``_fragment_offer(str | bytes)``).
    """
    global _html_clipboard_reader
    _html_clipboard_reader = (
        _default_html_clipboard_reader if reader is None else reader
    )


def paste_html() -> str | None:
    """Return the HTML fragment offered on the clipboard, or ``None`` if none.

    Only the selected fragment is returned: a Windows ``HTML Format`` envelope
    is cut at its UTF-8 ``StartFragment`` / ``EndFragment`` byte offsets, and a
    fragment-only ``text/html`` body is returned as is. HTML is never
    synthesized from plain text, the markup is never executed or resolved, and
    the clipboard is left unchanged. Does not require ``clipboard[images]``.
    Access, helper, or transfer failures and malformed envelopes raise
    ``ClipboardContentError`` (not ``None``). On macOS Aqua the default reader
    reads the pasteboard's ``public.html`` type (via ``osascript`` / AppKit);
    other platforms' native readers are not available yet. Tests inject a
    reader via ``set_html_clipboard_reader``.
    """
    offer = _call_content_backend("HTML read", _html_clipboard_reader)
    return _decode_html_offer(offer)

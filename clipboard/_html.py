"""HTML clipboard write with injectable backends (no Pillow needed)."""

from __future__ import annotations

from collections.abc import Callable

from ._errors import ClipboardContentError, _call_content_backend
from ._html_native import _default_html_clipboard_writer

_html_clipboard_writer: Callable[[str, str], None] = _default_html_clipboard_writer


def set_html_clipboard_writer(
    writer: Callable[[str, str], None] | None,
) -> None:
    """Inject an HTML+plain-text dual-offer writer (tests / fakes)."""
    global _html_clipboard_writer
    _html_clipboard_writer = (
        _default_html_clipboard_writer if writer is None else writer
    )


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

"""HTML + plain-text dual-offer clipboard write."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from clipboard._errors import ClipboardContentError


def _macos_html_clipboard_writer(html: str, text: str) -> None:
    """Publish HTML + plain text as one NSPasteboard dual offer.

    Uses built-in ``osascript`` / AppKit (no PyObjC / ``clipboard[images]``).
    Both ``NSPasteboardTypeHTML`` and ``NSPasteboardTypeString`` are declared
    and set in one clear/replace cycle so rich and text consumers see one offer.
    """
    with tempfile.TemporaryDirectory(prefix="clipboard-html-") as raw:
        tmp = Path(raw)
        html_path = tmp / "fragment.html"
        text_path = tmp / "alternative.txt"
        html_path.write_text(html, encoding="utf-8")
        text_path.write_text(text, encoding="utf-8")
        # Paths come from TemporaryDirectory; quote only for AppleScript literals.
        utf8 = "current application's NSUTF8StringEncoding"
        script_path = tmp / "set_dual.applescript"
        script_path.write_text(
            "\n".join(
                [
                    'use framework "AppKit"',
                    'use framework "Foundation"',
                    "use scripting additions",
                    f'set htmlPath to "{html_path}"',
                    f'set textPath to "{text_path}"',
                    (
                        "set htmlNS to current application's NSString's "
                        "stringWithContentsOfFile:htmlPath "
                        f"encoding:({utf8}) |error|:(missing value)"
                    ),
                    (
                        "set textNS to current application's NSString's "
                        "stringWithContentsOfFile:textPath "
                        f"encoding:({utf8}) |error|:(missing value)"
                    ),
                    (
                        "if htmlNS is missing value or textNS is missing value "
                        'then error "failed to read HTML/text temp files"'
                    ),
                    f"set htmlData to htmlNS's dataUsingEncoding:({utf8})",
                    (
                        "set pb to current application's "
                        "NSPasteboard's generalPasteboard()"
                    ),
                    "pb's clearContents()",
                    "set htmlType to current application's NSPasteboardTypeHTML",
                    "set strType to current application's NSPasteboardTypeString",
                    "pb's declareTypes:{htmlType, strType} owner:(missing value)",
                    "set okHtml to pb's setData:htmlData forType:htmlType",
                    "set okText to pb's setString:textNS forType:strType",
                    (
                        "if okHtml is false or okText is false then "
                        'error "NSPasteboard refused HTML or plain-text dual '
                        'offer"'
                    ),
                    'return "ok"',
                ]
            ),
            encoding="utf-8",
        )
        try:
            result = subprocess.run(
                ["osascript", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise ClipboardContentError(
                f"macOS HTML+text pasteboard write failed: {exc}"
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise ClipboardContentError(
                "macOS HTML+text pasteboard write failed"
                + (f": {detail}" if detail else "")
            )


def _default_html_clipboard_writer(html: str, text: str) -> None:
    """Platform-selected dual-offer writer; Darwin uses NSPasteboard via osascript."""
    if sys.platform == "darwin":
        _macos_html_clipboard_writer(html, text)
        return
    raise ClipboardContentError(
        "copy_html native dual-offer writer is not available on this platform "
        f"({sys.platform}); need a usable desktop session with a multi-type "
        "HTML+text helper (Linux X11: multi-type-capable xclip; Wayland: "
        "multi-type-capable helper on a named compositor; Windows desktop: "
        "HTML Format + Unicode text), or inject a writer with "
        "set_html_clipboard_writer for tests"
    )


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
    try:
        _html_clipboard_writer(html, text)
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard HTML+text write failed: {exc}") from exc

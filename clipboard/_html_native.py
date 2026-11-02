"""Platform-native HTML+plain-text clipboard writers."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from ._errors import ClipboardContentError


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

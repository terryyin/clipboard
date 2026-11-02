"""Platform-native HTML clipboard readers and HTML+plain-text writers."""

from __future__ import annotations

import base64
import binascii
import subprocess
import sys
import tempfile
from pathlib import Path

from ._errors import ClipboardContentError
from ._html_envelope import _fragment_offer, _HtmlOffer


def _osascript_failure_detail(result: subprocess.CompletedProcess[str]) -> str:
    """The helper's own failure text (stderr, else stdout), or ``""``."""
    return (result.stderr or result.stdout or "").strip()


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
            detail = _osascript_failure_detail(result)
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


# Bounded so a contended or wedged pasteboard never hangs the caller.
_MACOS_HTML_READ_TIMEOUT_SECONDS = 10.0
_MACOS_HTML_TYPE = "public.html"
# JXA: read the general pasteboard's HTML type through the ordinary AppKit API.
# Only reads (no clearContents / setData), so the offer and changeCount stay
# as they were. Raw bytes travel as base64 so any encoding survives stdout.
_MACOS_HTML_READ_JXA = f"""
ObjC.import("AppKit");
var pb = $.NSPasteboard.generalPasteboard;
var types = ObjC.deepUnwrap(pb.types) || [];
var data = pb.dataForType("{_MACOS_HTML_TYPE}");
if (!data.isNil()) {{
  "HTML:" + data.base64EncodedStringWithOptions(0).js;
}} else if (types.indexOf("{_MACOS_HTML_TYPE}") >= 0) {{
  "UNREADABLE";
}} else {{
  "NONE";
}}
"""


def _macos_html_read_error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(
        f"macOS HTML pasteboard read failed: {detail}; paste_html needs a "
        "logged-in Aqua session with the built-in osascript and pasteboard "
        "access for this process"
    )


def _macos_html_clipboard_reader() -> _HtmlOffer | None:
    """Read the general pasteboard's ``public.html`` without mutating it.

    Uses built-in ``osascript -l JavaScript`` / AppKit (no PyObjC). Returns
    ``None`` when no HTML type is offered (text-only, image-only, file-list or
    empty pasteboard); otherwise the raw HTML bytes as a fragment offer, left
    for ``clipboard._html_envelope`` to decode.
    """
    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", _MACOS_HTML_READ_JXA],
            capture_output=True,
            text=True,
            check=False,
            timeout=_MACOS_HTML_READ_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise _macos_html_read_error(
            f"osascript did not answer within {_MACOS_HTML_READ_TIMEOUT_SECONDS:g}s "
            "(pasteboard contended or helper stalled)"
        ) from exc
    except OSError as exc:
        raise _macos_html_read_error(f"could not run osascript ({exc})") from exc
    if result.returncode != 0:
        detail = _osascript_failure_detail(result)
        raise _macos_html_read_error(
            f"osascript exited with status {result.returncode}"
            + (f": {detail}" if detail else "")
        )
    answer = (result.stdout or "").strip()
    if answer == "NONE":
        return None
    if answer == "UNREADABLE":
        raise _macos_html_read_error(
            f"{_MACOS_HTML_TYPE} is offered but its data could not be obtained"
        )
    if not answer.startswith("HTML:"):
        raise _macos_html_read_error(f"unexpected helper output {answer[:80]!r}")
    try:
        raw = base64.b64decode(answer[len("HTML:") :], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise _macos_html_read_error("helper returned malformed base64") from exc
    return _fragment_offer(raw)


def _default_html_clipboard_reader() -> _HtmlOffer | None:
    """Platform-selected HTML reader; Darwin reads NSPasteboard via osascript."""
    if sys.platform == "darwin":
        return _macos_html_clipboard_reader()
    raise ClipboardContentError(
        "paste_html native HTML reader is not available on this platform "
        f"({sys.platform}) yet; inject a reader with set_html_clipboard_reader "
        "for tests"
    )

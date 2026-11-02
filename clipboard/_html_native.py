"""Platform-native HTML clipboard readers (paste_html default dispatch)."""

from __future__ import annotations

import base64
import binascii
import subprocess
import sys

from clipboard._errors import ClipboardContentError
from clipboard._html_envelope import _fragment_offer, _HtmlOffer
from clipboard._html_native_linux import (
    _linux_wayland_html_clipboard_reader,
    _linux_x11_html_clipboard_reader,
)
from clipboard._html_native_windows import _windows_html_clipboard_reader
from clipboard._image_write import _is_linux_wayland


def _osascript_failure_detail(result: subprocess.CompletedProcess[str]) -> str:
    """The helper's own failure text (stderr, else stdout), or ``""``."""
    return (result.stderr or result.stdout or "").strip()


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
    """Platform-selected HTML reader.

    Darwin reads NSPasteboard via osascript; a Linux Wayland session reads
    ``text/html`` via ``wl-paste``; other Linux sessions read X11 CLIPBOARD
    ``text/html`` via ``xclip -o``; Windows reads the registered ``HTML
    Format`` via user32/kernel32 (``ctypes``).
    """
    if sys.platform == "darwin":
        return _macos_html_clipboard_reader()
    if sys.platform == "win32":
        return _windows_html_clipboard_reader()
    if sys.platform.startswith("linux"):
        if _is_linux_wayland():
            return _linux_wayland_html_clipboard_reader()
        return _linux_x11_html_clipboard_reader()
    raise ClipboardContentError(
        "paste_html native HTML reader is not available on this platform "
        f"({sys.platform}); supported: Windows, macOS, Linux X11 / Wayland; "
        "inject a reader with "
        "set_html_clipboard_reader for tests"
    )

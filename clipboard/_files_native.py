"""Platform-native file-list clipboard readers (macOS Aqua; Linux X11)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ._errors import ClipboardContentError

# Contended pasteboard / clipboard must not hang callers indefinitely (commitment 78).
_NATIVE_FILES_READ_TIMEOUT_S = 30
# Authoritative xclip argv for CLIPBOARD text/uri-list (docs/errors reuse this).
_XCLIP_TEXT_URI_LIST = (
    "-o",
    "-selection",
    "clipboard",
    "-t",
    "text/uri-list",
)


def _macos_read_script() -> str:
    """AppleScript: read Finder-equivalent file-list types; never mutate.

    Prefers ``NSFilenamesPboardType`` (path list), then file-URL objects with
    ``NSPasteboardURLReadingFileURLsOnlyKey``. Ordinary absence → ``NONE``.
    Success → JSON array of local path strings. Read-only (no clear/declare).
    """
    return "\n".join(
        [
            'use framework "AppKit"',
            'use framework "Foundation"',
            "use scripting additions",
            "on encodeJson(obj)",
            (
                "  set jsonData to current application's "
                "NSJSONSerialization's dataWithJSONObject:obj "
                "options:0 |error|:(missing value)"
            ),
            (
                "  if jsonData is missing value then "
                'error "file-list JSON encode failed"'
            ),
            (
                "  set jsonStr to (current application's NSString's "
                "alloc()'s initWithData:jsonData encoding:"
                "(current application's NSUTF8StringEncoding))"
            ),
            "  return jsonStr as text",
            "end encodeJson",
            ("set pb to current application's NSPasteboard's generalPasteboard()"),
            (
                "set names to pb's propertyListForType:"
                "(current application's NSFilenamesPboardType)"
            ),
            "if names is not missing value then",
            "  return encodeJson(names)",
            "end if",
            (
                "set opts to current application's NSDictionary's "
                "dictionaryWithObject:(true) forKey:"
                "(current application's "
                "NSPasteboardURLReadingFileURLsOnlyKey)"
            ),
            (
                "set urls to pb's readObjectsForClasses:"
                "{(current application's NSURL)} options:opts"
            ),
            'if urls is missing value then return "NONE"',
            "set countUrls to urls's |count|() as integer",
            'if countUrls is 0 then return "NONE"',
            ("set paths to current application's NSMutableArray's array()"),
            "repeat with u in urls",
            "  set p to u's |path|()",
            "  if p is not missing value then",
            "    paths's addObject:(p as text)",
            "  end if",
            "end repeat",
            "set countPaths to paths's |count|() as integer",
            'if countPaths is 0 then return "NONE"',
            "return encodeJson(paths)",
        ]
    )


def _macos_files_clipboard_reader() -> list[str] | None:
    """Read local file paths from the macOS general pasteboard (read-only).

    Uses built-in ``osascript`` / AppKit (no PyObjC / ``clipboard[images]``).
    Does not clear, declare, or rewrite pasteboard contents and does not open
    referenced files.
    """
    with tempfile.TemporaryDirectory(prefix="clipboard-files-read-") as raw:
        script_path = Path(raw) / "read_files.applescript"
        script_path.write_text(_macos_read_script(), encoding="utf-8")
        try:
            result = subprocess.run(
                ["osascript", str(script_path)],
                capture_output=True,
                text=True,
                timeout=_NATIVE_FILES_READ_TIMEOUT_S,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ClipboardContentError(
                "clipboard file-list read failed: osascript pasteboard read timed out"
            ) from exc
        except OSError as exc:
            raise ClipboardContentError(
                f"clipboard file-list read failed: {exc}"
            ) from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ClipboardContentError(
            "clipboard file-list read failed" + (f": {detail}" if detail else "")
        )

    out = (result.stdout or "").strip()
    if not out or out == "NONE":
        return None

    try:
        # Path-list shape / empty / entry rules live in ``_normalize_files_offer``.
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise ClipboardContentError(
            "clipboard file-list read failed: "
            "corrupt macOS file-list metadata (invalid JSON)"
        ) from exc


def _linux_wayland_without_x11() -> bool:
    """True when only a Wayland session is advertised (X11 reader not selected)."""
    return bool(os.environ.get("WAYLAND_DISPLAY")) and not bool(
        os.environ.get("DISPLAY")
    )


def _xclip_uri_list_invocation() -> str:
    return "xclip " + " ".join(_XCLIP_TEXT_URI_LIST)


def _linux_x11_helper_missing_message() -> str:
    return (
        "clipboard file-list read failed: Linux X11 session/helper unavailable "
        "(need DISPLAY and xclip on PATH to request text/uri-list on CLIPBOARD "
        f"via `{_xclip_uri_list_invocation()}`); inject a reader "
        "with set_files_clipboard_reader for tests"
    )


def _uri_list_target_absent(stderr: str, stdout: str) -> bool:
    """Whether xclip's failure looks like ordinary missing text/uri-list offer."""
    detail = f"{stderr}\n{stdout}".lower()
    markers = (
        "not available",
        "no data types",
        "error: target",
        "cannot convert",
    )
    return any(marker in detail for marker in markers)


def _linux_x11_files_clipboard_reader() -> object:
    """Read ``text/uri-list`` from X11 CLIPBOARD via ``xclip`` (read-only).

    Returns a structured ``uri-list`` offer for ``_normalize_files_offer`` (same
    ``file://`` decode as the in-memory contract). Ordinary absence of that
    target is ``None``. Missing ``DISPLAY`` / ``xclip`` raises
    ``ClipboardContentError`` (never silent ``None``). Does not clear or rewrite
    CLIPBOARD and does not open referenced files. Cut/move companion types are
    not requested (ignored for library behavior).
    """
    display = os.environ.get("DISPLAY") or ""
    xclip = shutil.which("xclip")
    if not display or not xclip:
        raise ClipboardContentError(_linux_x11_helper_missing_message())

    try:
        result = subprocess.run(
            [xclip, *_XCLIP_TEXT_URI_LIST],
            capture_output=True,
            text=True,
            timeout=_NATIVE_FILES_READ_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            "clipboard file-list read failed: xclip text/uri-list read timed out"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(f"clipboard file-list read failed: {exc}") from exc

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if result.returncode != 0:
        if _uri_list_target_absent(stderr, stdout):
            return None
        detail = (stderr or stdout).strip()
        raise ClipboardContentError(
            "clipboard file-list read failed"
            + (f": {detail}" if detail else ": xclip text/uri-list transfer failed")
        )

    text = stdout
    if not text.strip():
        return None
    # Structured shape so paste_files uses the shared uri-list normalizer.
    return {"kind": "uri-list", "uri_list": text}


def _unavailable_native_reader_message() -> str:
    return (
        "paste_files native file-list reader is not available on this platform "
        f"({sys.platform}); need a usable desktop session with a file-list "
        "helper (Linux X11: text/uri-list via xclip or equivalent; Wayland: "
        "text/uri-list via wl-paste on a named compositor; Windows desktop: "
        "CF_HDROP), or inject a reader with set_files_clipboard_reader for tests"
    )


def _default_files_clipboard_reader() -> object:
    """Platform-selected file-list reader (Darwin AppKit; Linux X11 xclip)."""
    if sys.platform == "darwin":
        return _macos_files_clipboard_reader()
    if sys.platform.startswith("linux"):
        if _linux_wayland_without_x11():
            raise ClipboardContentError(_unavailable_native_reader_message())
        return _linux_x11_files_clipboard_reader()
    raise ClipboardContentError(_unavailable_native_reader_message())

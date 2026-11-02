"""macOS Aqua file-list clipboard reader (osascript / AppKit)."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from ._errors import ClipboardContentError

# Contended pasteboard must not hang callers indefinitely (commitment 78).
_NATIVE_FILES_READ_TIMEOUT_S = 30


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

"""macOS Aqua file-list clipboard reader and writer (osascript / AppKit)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from ._desktop import _helper_failure_detail
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
        detail = _helper_failure_detail(result)
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


# A contended pasteboard must not hang ``copy_files`` callers indefinitely.
_NATIVE_FILES_WRITE_TIMEOUT_S = 30

# JXA: publish one file-URL pasteboard item per path via the ordinary AppKit
# API (clearContents, then writeObjects:). File URIs arrive as a JSON array on
# stdin, so no path text is ever interpolated into script source. Reading the
# items back before returning is load-bearing, not just verification: without
# that pasteboard round trip an osascript that exits right after writeObjects:
# was observed (macOS 26) to leave only the first of several items behind.
_MACOS_FILES_WRITE_JXA = """
ObjC.import("AppKit");
function run(argv) {
  var input = $.NSFileHandle.fileHandleWithStandardInput.readDataToEndOfFile;
  var uris = $.NSJSONSerialization.JSONObjectWithDataOptionsError(input, 0, null);
  if (uris.isNil() || !uris.isKindOfClass($.NSArray)) {
    throw new Error("file URI list on stdin is not a JSON array");
  }
  var count = Number(uris.count);
  var urls = $.NSMutableArray.array;
  for (var i = 0; i < count; i++) {
    var url = $.NSURL.URLWithString(uris.objectAtIndex(i));
    if (url.isNil() || !url.isFileURL) {
      throw new Error("not a file URL: " + ObjC.unwrap(uris.objectAtIndex(i)));
    }
    urls.addObject(url);
  }
  var pb = $.NSPasteboard.generalPasteboard;
  pb.clearContents;
  if (!pb.writeObjects(urls)) {
    throw new Error("NSPasteboard writeObjects: refused the file URLs");
  }
  var items = pb.pasteboardItems;
  var kept = items.isNil() ? 0 : Number(items.count);
  if (kept !== count) {
    throw new Error("NSPasteboard kept " + kept + " of " + count + " file URLs");
  }
  for (var j = 0; j < count; j++) {
    var got = items.objectAtIndex(j).stringForType("public.file-url");
    if (got.isNil() || !got.isEqualToString(urls.objectAtIndex(j).absoluteString)) {
      throw new Error("NSPasteboard file URL " + (j + 1) + " did not read back");
    }
  }
  return "ok";
}
"""


def _file_uri(path: str) -> str:
    """Percent-encoded ``file://`` URI that keeps the caller's exact path text.

    ``NSURL fileURLWithPath:`` decomposes non-ASCII names (NFD), so readers
    would get back a different string than was copied; a pre-encoded URI keeps
    the original code points. Directories get Apple's trailing slash.
    """
    uri = Path(path).as_uri()
    if os.path.isdir(path) and not uri.endswith("/"):
        uri += "/"
    return uri


def _macos_files_write_error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(
        f"macOS file-list pasteboard write failed: {detail}; copy_files needs a "
        "logged-in Aqua session with the built-in osascript and pasteboard "
        "access for this process"
    )


def _macos_files_clipboard_writer(paths: list[str]) -> None:
    """Replace the general pasteboard with one file-URL item per path, in order.

    Uses built-in ``osascript -l JavaScript`` / AppKit (no PyObjC /
    ``clipboard[images]``). Paths travel as JSON on stdin, never as script
    text. Any helper failure, timeout, refusal, or incomplete read-back raises
    ``ClipboardContentError``.
    """
    payload = json.dumps([_file_uri(path) for path in paths])
    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", _MACOS_FILES_WRITE_JXA],
            input=payload,
            capture_output=True,
            text=True,
            timeout=_NATIVE_FILES_WRITE_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise _macos_files_write_error(
            f"osascript did not answer within {_NATIVE_FILES_WRITE_TIMEOUT_S}s "
            "(pasteboard contended or helper stalled)"
        ) from exc
    except OSError as exc:
        raise _macos_files_write_error(f"could not run osascript ({exc})") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise _macos_files_write_error(
            f"osascript exited with status {result.returncode}"
            + (f": {detail}" if detail else "")
        )
    answer = (result.stdout or "").strip()
    if answer != "ok":
        raise _macos_files_write_error(f"unexpected helper output {answer[:80]!r}")

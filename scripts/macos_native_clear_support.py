"""Independent JXA producers and consumers for the macOS clear probe.

The JXA readers use ``osascript -l JavaScript``, a different script stack from
the library's AppleScriptObjC, so their type listings are independent of
``clipboard.*``. ``independent_listing`` pairs the JXA type list with
``pbpaste`` (a second independent consumer); ``no_offer`` is its empty
predicate for ``native_clear_support.cleared_step`` (no types, no text).
``copy_empty_in_child`` runs the ``copy("")`` contrast in a child Python.
"""

from __future__ import annotations

import json
import subprocess

from macos_native_inspect_support import consume_text_independent
from native_clear_support import child_python
from native_probe_common import die

_JXA_TYPES = """
ObjC.import("AppKit");
var pb = $.NSPasteboard.generalPasteboard;
var types = ObjC.deepUnwrap(pb.types) || [];
JSON.stringify({types: types, changeCount: Number(pb.changeCount)});
"""

_JXA_SESSION = """
ObjC.import("CoreGraphics");
var d = ObjC.deepUnwrap(ObjC.castRefToObject($.CGSessionCopyCurrentDictionary()));
JSON.stringify({
  locked: d.CGSSessionScreenIsLocked === true || d.CGSSessionScreenIsLocked === 1,
  on_console: d.kCGSessionOnConsoleKey === true,
  login_done: d.kCGSessionLoginDoneKey === true
});
"""


def _jxa(script: str, *args: str, failure: str) -> dict:
    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script, *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"{failure}: {exc}")
    if result.returncode != 0:
        die(f"{failure}: {(result.stderr or result.stdout or '').strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        die(f"{failure}: non-JSON output {result.stdout!r} ({exc})")


_JXA_FILE_URL = """
ObjC.import("AppKit");
function run(argv) {
  var pb = $.NSPasteboard.generalPasteboard;
  pb.clearContents;
  var ok = pb.writeObjects($([$.NSURL.fileURLWithPath(argv[0])]));
  return JSON.stringify({written: ok === true || ok === 1});
}
"""

_JXA_CUSTOM_TYPE = """
ObjC.import("AppKit");
function run(argv) {
  var pb = $.NSPasteboard.generalPasteboard;
  pb.clearContents;
  var data = $(argv[1]).dataUsingEncoding($.NSUTF8StringEncoding);
  var ok = pb.setDataForType(data, argv[0]);
  return JSON.stringify({written: ok === true || ok === 1});
}
"""


def _jxa_write(script: str, *args: str, failure: str) -> None:
    written = _jxa(script, *args, failure=failure)
    if not isinstance(written, dict) or written.get("written") is not True:
        die(f"{failure}: the pasteboard refused the write ({written!r})")


def produce_file_url_independent(path: str) -> None:
    """Independent producer: JXA ``writeObjects([NSURL fileURLWithPath:])``."""
    _jxa_write(_JXA_FILE_URL, path, failure="independent JXA file-URL write failed")


def produce_custom_type_independent(uti: str, payload: str) -> None:
    """Independent producer: JXA ``setData:forType:`` of an unknown UTI only."""
    _jxa_write(
        _JXA_CUSTOM_TYPE, uti, payload, failure="independent JXA custom write failed"
    )


def list_types_independent() -> dict:
    """Independent consumer: JXA NSPasteboard types (no clipboard.*)."""
    return _jxa(_JXA_TYPES, failure="independent JXA type listing failed")


def independent_listing() -> dict:
    """JXA types and change count, plus what ``pbpaste`` printed."""
    return {**list_types_independent(), "pbpaste": consume_text_independent()}


def no_offer(listing: dict) -> bool:
    """Empty pasteboard: no types listed and ``pbpaste`` printed nothing."""
    return listing["types"] == [] and listing["pbpaste"] == ""


def session_state() -> dict:
    return _jxa(_JXA_SESSION, failure="CGSession state read failed")


def copy_empty_in_child() -> dict:
    """The ``copy("")`` contrast: ``clipboard.copy("")`` in a child that exits."""
    return child_python('import clipboard\nclipboard.copy("")\nprint("copied empty")')

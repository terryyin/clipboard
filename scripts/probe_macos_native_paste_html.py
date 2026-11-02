#!/usr/bin/env python3
"""Independent-producer probe: macOS pasteboard HTML -> clipboard.paste_html().

Producer: Google Chrome opens a local page with a Unicode styled link between
two ``user-select: none`` context paragraphs, then AppleScript ``select all`` /
``copy selection`` copies only the link (a real browser copy, not this
library's ``copy_html``). If Chrome cannot be driven, a JXA NSPasteboard writer
shaped like a browser offer is the recorded fallback. Afterwards an independent
JXA consumer and the pasteboard ``changeCount`` show the read did not mutate the
offer. Text-only, image-only and file-list offers must give ``None``.

Prints one JSON object on stdout. Exit 0 on success; non-zero on failure.
Requires darwin. Overwrites the clipboard. Does not run under default pytest.
"""

from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

from native_probe_common import die, macos_environment

LINK = '<a href="https://example.com/caf%C3%A9" style="color:#c00">'
LABEL = "<b>café → naïve 日本</b>"
PAGE = (
    '<!doctype html><html><head><meta charset="utf-8"><title>probe</title>'
    '</head><body><p style="user-select:none">CONTEXT-BEFORE unselected</p>'
    f"<p>{LINK}{LABEL}</a></p>"
    '<p style="user-select:none">CONTEXT-AFTER unselected</p></body></html>'
)
FRAGMENT_MARKERS = ('<a href="https://example.com/caf%C3%A9"', LABEL, "</a>")
CONTEXT_MARKERS = ("CONTEXT-BEFORE", "CONTEXT-AFTER")
CHROME_ATTEMPTS = 3
HELPER_TIMEOUT = 30

_STATE_JXA = """
ObjC.import("AppKit");
var pb = $.NSPasteboard.generalPasteboard;
var html = pb.stringForType("public.html");
JSON.stringify({change_count: pb.changeCount,
  types: ObjC.deepUnwrap(pb.types) || [],
  html: html.isNil() ? null : html.js});
"""


def _osascript(*args: str) -> str:
    result = subprocess.run(
        ["osascript", *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=HELPER_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "").strip())
    return result.stdout.strip()


def _pasteboard_state() -> dict:
    """Independent consumer: JXA NSPasteboard read (not this library)."""
    return json.loads(_osascript("-l", "JavaScript", "-e", _STATE_JXA))


def _chrome_copy(page: Path) -> str:
    script = f"""
tell application "Google Chrome"
  set w to make new window
  set URL of active tab of w to "{page.as_uri()}"
  delay 2
  tell active tab of w
    select all
    copy selection
  end tell
  delay 0.5
  close w
  return version
end tell"""
    return _osascript("-e", script)


def _fallback_copy() -> None:
    body = "<meta charset='utf-8'>" + LINK + LABEL + "</a>"
    script = f"""
ObjC.import("AppKit");
var pb = $.NSPasteboard.generalPasteboard;
pb.clearContents;
pb.setStringForType({json.dumps(body)}, "public.html");
pb.setStringForType("café → naïve 日本", "public.utf8-plain-text");
"ok";
"""
    _osascript("-l", "JavaScript", "-e", script)


def _produce(tmpdir: Path) -> dict:
    page = tmpdir / "selection.html"
    page.write_text(PAGE, encoding="utf-8")
    failures = []
    for attempt in range(1, CHROME_ATTEMPTS + 1):
        _osascript("-e", 'set the clipboard to "probe-reset"')
        try:
            version = _chrome_copy(page)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            failures.append(f"attempt {attempt}: {exc}")
            continue
        html = _pasteboard_state()["html"]
        if html and all(marker in html for marker in FRAGMENT_MARKERS):
            return {
                "kind": "browser",
                "app": "Google Chrome",
                "app_version": version,
                "method": "AppleScript select all + copy selection on a local page",
                "attempts": attempt,
            }
        failures.append(f"attempt {attempt}: no matching public.html offer")
    _fallback_copy()
    return {
        "kind": "fallback",
        "app": None,
        "method": "JXA NSPasteboard clearContents + setString:forType:",
        "fallback_reason": failures,
    }


def _probe_html(tmpdir: Path) -> dict:
    import clipboard

    producer = _produce(tmpdir)
    before = _pasteboard_state()
    first = clipboard.paste_html()
    second = clipboard.paste_html()
    after = _pasteboard_state()
    fragment_ok = isinstance(first, str) and all(m in first for m in FRAGMENT_MARKERS)
    context_excluded = isinstance(first, str) and not any(
        m in first for m in CONTEXT_MARKERS
    )
    unchanged = (
        after["html"] == before["html"]
        and after["types"] == before["types"]
        and after["change_count"] == before["change_count"]
    )
    return {
        "case": "independent_html_selection",
        "ok": fragment_ok and context_excluded and unchanged and first == second,
        "producer": producer,
        "offered_types": before["types"],
        "paste_html": first,
        "fragment_markers_ok": fragment_ok,
        "context_excluded": context_excluded,
        "repeat_read_equal": first == second,
        "independent_consumer_same_offer": after["html"] == before["html"],
        "change_count_before": before["change_count"],
        "change_count_after": after["change_count"],
        "non_mutating": unchanged,
    }


def _png_bytes() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        crc = struct.pack(">I", zlib.crc32(body))
        return struct.pack(">I", len(data)) + body + crc

    rows = b"".join(b"\x00" + b"\xff\x00\x00" * 4 for _ in range(4))
    header = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def _probe_absent(case: str, script: str) -> dict:
    import clipboard

    _osascript("-e", script)
    state = _pasteboard_state()
    result = clipboard.paste_html()
    return {
        "case": case,
        "ok": result is None and "public.html" not in state["types"],
        "offered_types": state["types"],
        "paste_html": result,
    }


def main() -> None:
    if sys.platform != "darwin":
        die(f"probe requires macOS (darwin); got {sys.platform!r}")
    try:
        import clipboard
    except ImportError as exc:
        die(f"missing clipboard import: {exc}")
    clipboard.set_html_clipboard_reader(None)

    with tempfile.TemporaryDirectory(prefix="clipboard-html-probe-") as raw:
        tmpdir = Path(raw)
        try:
            html = _probe_html(tmpdir)
            png = tmpdir / "image.png"
            png.write_bytes(_png_bytes())
            read_png = f'read (POSIX file "{png}") as «class PNGf»'
            absent = [
                _probe_absent("text_only", 'set the clipboard to "plain"'),
                _probe_absent(
                    "image_only",
                    f"set the clipboard to ({read_png})",
                ),
                _probe_absent(
                    "file_list", f'set the clipboard to (POSIX file "{png}")'
                ),
            ]
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            die(f"independent pasteboard helper failed: {exc}")

    producer = html["producer"]
    report = {
        "ok": html["ok"] and all(case["ok"] for case in absent),
        "environment": macos_environment(
            producer=producer["app"] or "JXA NSPasteboard writer (fallback)",
            producer_version=producer.get("app_version"),
            reader="clipboard.paste_html default (osascript JXA public.html)",
        ),
        "html": html,
        "absent": absent,
        "commitments": {
            "independent_producer": producer["method"],
            "independent_consumer": "JXA NSPasteboard stringForType public.html",
            "gating": "CLIPBOARD_NATIVE_PROBE=1 on darwin only",
            "authorization": "normal macOS pasteboard; no entitlement bypass",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

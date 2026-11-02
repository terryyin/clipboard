"""Independent producers/consumers for the macOS inspect probe."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from native_probe_common import die

ROOT = Path(__file__).resolve().parents[1]

PROBE_HTML = '<a href="https://example.com/inspect" style="color:#06c"><b>café</b></a>'
PROBE_TEXT = "café → https://example.com/inspect"
HTML_MARKERS = ("<a href=", "café", "</b>", "example.com/inspect")
TEXT_EXACT = PROBE_TEXT
HTML_FORMAT_IDS = ("public.html", "NSPasteboardTypeHTML", "text/html")
TEXT_FORMAT_IDS = (
    "public.utf8-plain-text",
    "public.plain-text",
    "NSPasteboardTypeString",
    "text/plain",
)
IMAGE_FORMAT_IDS = (
    "public.png",
    "public.tiff",
    "public.jpeg",
    "NSPasteboardTypePNG",
    "NSPasteboardTypeTIFF",
    "PNG",
)

# Minimal valid 1×1 PNG (no Pillow required for the image-only producer).
_MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8cfc00000000300010005fe02fe0000000049454e44ae426082"
)

_APPKIT_PREAMBLE = (
    'use framework "AppKit"\nuse framework "Foundation"\nuse scripting additions\n'
)


def _quote_as_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace('"', '\\"')


def _run_osascript_file(script_path: Path, *, failure: str) -> None:
    try:
        result = subprocess.run(
            ["osascript", str(script_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"{failure}: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        die(f"{failure}: {detail}")


def _run_osascript_source(script: str, *, failure: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"{failure}: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        die(f"{failure}: {detail}")
    return result.stdout.rstrip("\n")


def produce_html_text_independent() -> None:
    """Place HTML+text dual offer via AppKit — outside clipboard.* APIs."""
    with tempfile.TemporaryDirectory(prefix="clipboard-inspect-html-") as raw:
        tmp = Path(raw)
        html_path = tmp / "fragment.html"
        text_path = tmp / "alternative.txt"
        html_path.write_text(PROBE_HTML, encoding="utf-8")
        text_path.write_text(PROBE_TEXT, encoding="utf-8")
        utf8 = "current application's NSUTF8StringEncoding"
        html_q, text_q = _quote_as_path(html_path), _quote_as_path(text_path)
        script_path = tmp / "set_dual.applescript"
        script_path.write_text(
            _APPKIT_PREAMBLE
            + f'set htmlPath to "{html_q}"\n'
            + f'set textPath to "{text_q}"\n'
            + "set htmlNS to current application's NSString's "
            + f"stringWithContentsOfFile:htmlPath encoding:({utf8}) "
            + "|error|:(missing value)\n"
            + "set textNS to current application's NSString's "
            + f"stringWithContentsOfFile:textPath encoding:({utf8}) "
            + "|error|:(missing value)\n"
            + "if htmlNS is missing value or textNS is missing value "
            + 'then error "failed to read HTML/text temp files"\n'
            + f"set htmlData to htmlNS's dataUsingEncoding:({utf8})\n"
            + "set pb to current application's NSPasteboard's generalPasteboard()\n"
            + "pb's clearContents()\n"
            + "set htmlType to current application's NSPasteboardTypeHTML\n"
            + "set strType to current application's NSPasteboardTypeString\n"
            + "pb's declareTypes:{htmlType, strType} owner:(missing value)\n"
            + "set okHtml to pb's setData:htmlData forType:htmlType\n"
            + "set okText to pb's setString:textNS forType:strType\n"
            + "if okHtml is false or okText is false then "
            + 'error "NSPasteboard refused HTML or plain-text dual offer"\n'
            + 'return "ok"\n',
            encoding="utf-8",
        )
        _run_osascript_file(
            script_path,
            failure="independent HTML+text producer failed",
        )


def produce_image_only_independent() -> None:
    """Place image-only PNG offer via AppKit (no clipboard.* / no Pillow)."""
    with tempfile.TemporaryDirectory(prefix="clipboard-inspect-png-") as raw:
        path = Path(raw) / "pixel.png"
        path.write_bytes(_MIN_PNG)
        script_path = Path(raw) / "set_png.applescript"
        png_q = _quote_as_path(path)
        script_path.write_text(
            _APPKIT_PREAMBLE
            + f'set pngPath to "{png_q}"\n'
            + "set pngData to current application's NSData's "
            + "dataWithContentsOfFile:pngPath\n"
            + 'if pngData is missing value then error "failed to read PNG"\n'
            + "set pb to current application's NSPasteboard's generalPasteboard()\n"
            + "pb's clearContents()\n"
            + "set pngType to current application's NSPasteboardTypePNG\n"
            + "pb's declareTypes:{pngType} owner:(missing value)\n"
            + "set ok to pb's setData:pngData forType:pngType\n"
            + 'if ok is false then error "NSPasteboard refused PNG offer"\n'
            + 'return "ok"\n',
            encoding="utf-8",
        )
        _run_osascript_file(script_path, failure="independent image producer failed")


def inspect_via_library() -> dict:
    """Call clipboard.inspect() in a child process (library under test)."""
    code = textwrap.dedent(
        """
        import json
        import clipboard
        clipboard.set_clipboard_inspector(None)
        snap = clipboard.inspect()
        print(json.dumps({
            "kinds": sorted(snap.kinds),
            "formats": list(snap.formats),
        }))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        die(
            "clipboard.inspect() failed "
            f"(returncode={result.returncode}; stderr={detail!r})"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        die(f"clipboard.inspect() produced non-JSON stdout: {exc}; {result.stdout!r}")


def consume_html_independent() -> str:
    script = (
        _APPKIT_PREAMBLE
        + "set pb to current application's NSPasteboard's generalPasteboard()\n"
        + "set d to pb's dataForType:"
        + "(current application's NSPasteboardTypeHTML)\n"
        + 'if d is missing value then error "NO_HTML"\n'
        + "set s to current application's NSString's alloc()'s "
        + "initWithData:d encoding:(current application's NSUTF8StringEncoding)\n"
        + "return s as text\n"
    )
    return _run_osascript_source(script, failure="independent HTML consumer failed")


def consume_text_independent() -> str:
    result = subprocess.run(
        ["pbpaste"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        die(f"independent text consumer (pbpaste) failed: {detail}")
    return result.stdout.rstrip("\n")


def consume_image_type_present() -> bool:
    """True if pasteboard still advertises a PNG/TIFF type after inspect."""
    script = (
        _APPKIT_PREAMBLE
        + "set pb to current application's NSPasteboard's generalPasteboard()\n"
        + "set typeArray to pb's types()\n"
        + 'if typeArray is missing value then return "no"\n'
        + "set typeCount to typeArray's |count|()\n"
        + "repeat with i from 0 to (typeCount - 1)\n"
        + "    set t to (typeArray's objectAtIndex:i) as text\n"
        + '    if t is "public.png" or t is "public.tiff" '
        + 'or t is "NSPasteboardTypePNG" or t is "NSPasteboardTypeTIFF" '
        + 'or t contains "PNGf" then return "yes"\n'
        + "end repeat\n"
        + 'return "no"\n'
    )
    out = _run_osascript_source(
        script, failure="independent image type consumer failed"
    )
    return out.strip() == "yes"

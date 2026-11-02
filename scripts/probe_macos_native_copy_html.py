#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_html → macOS pasteboard dual offer.

Runs ``copy_html`` in a **subprocess that exits**, then recovers HTML and plain
text with independent consumers (AppKit/osascript + ``pbpaste``) — not
``clipboard.paste`` / same-library HTML round-trip alone.

Prints one JSON object on stdout. Exit 0 on dual-consumer success; non-zero
on failure. Requires darwin. Does not run under default pytest.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Unicode styled link + matching plain alternative (key example E1 / macOS).
PROBE_HTML = '<a href="https://example.com/probe" style="color:#c00"><b>café</b></a>'
PROBE_TEXT = "café → https://example.com/probe"
HTML_MARKERS = ("<a href=", "café", "</b>", "example.com/probe")
TEXT_EXACT = PROBE_TEXT


def _die(message: str, *, code: int = 1, **extra) -> None:
    payload = {"ok": False, "error": message, **extra}
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit(code)


def _sw_vers(key: str) -> str | None:
    try:
        out = subprocess.check_output(["sw_vers", f"-{key}"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


def _environment() -> dict:
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "macos_product": _sw_vers("ProductVersion"),
        "macos_build": _sw_vers("BuildVersion"),
        "machine": platform.machine(),
        "desktop": "Aqua (macOS WindowServer / Quartz)",
        "write_method": (
            "clipboard.copy_html → NSPasteboardTypeHTML + "
            "NSPasteboardTypeString via osascript/AppKit"
        ),
        "html_consumer": (
            "osascript AppKit NSPasteboard dataForType:NSPasteboardTypeHTML"
        ),
        "text_consumer": "pbpaste (plain string offer)",
        "helper": "osascript + pbpaste (macOS built-in)",
        "python": sys.version.split()[0],
    }


def _run_writer_subprocess() -> None:
    """Publish dual offer then exit so pasteability is proved after writer exit."""
    code = textwrap.dedent(
        f"""
        import clipboard
        clipboard.set_html_clipboard_writer(None)
        clipboard.copy_html({PROBE_HTML!r}, {PROBE_TEXT!r})
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        _die(
            "writer subprocess failed",
            writer_returncode=result.returncode,
            writer_stderr=detail,
        )


def _consume_html_independent() -> str:
    script = "\n".join(
        [
            'use framework "AppKit"',
            'use framework "Foundation"',
            "use scripting additions",
            ("set pb to current application's NSPasteboard's generalPasteboard()"),
            ("set d to pb's dataForType:(current application's NSPasteboardTypeHTML)"),
            'if d is missing value then error "NO_HTML"',
            (
                "set s to current application's NSString's alloc()'s "
                "initWithData:d encoding:"
                "(current application's NSUTF8StringEncoding)"
            ),
            "return s as text",
        ]
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        _die(f"independent HTML consumer failed: {detail}")
    return result.stdout.rstrip("\n")


def _consume_text_independent() -> str:
    result = subprocess.run(
        ["pbpaste"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        _die(f"independent text consumer (pbpaste) failed: {detail}")
    return result.stdout.rstrip("\n")


def main() -> None:
    if sys.platform != "darwin":
        _die(f"probe requires macOS (darwin); got {sys.platform!r}")

    try:
        import clipboard  # noqa: F401
    except ImportError as exc:
        _die(f"missing clipboard import: {exc}")

    _run_writer_subprocess()
    observed_html = _consume_html_independent()
    observed_text = _consume_text_independent()

    html_ok = all(marker in observed_html for marker in HTML_MARKERS)
    text_ok = observed_text == TEXT_EXACT
    ok = html_ok and text_ok

    floors = {
        "macos_product": _environment()["macos_product"],
        "macos_build": _environment()["macos_build"],
        "machine": _environment()["machine"],
        "method": _environment()["write_method"],
    }
    report = {
        "ok": ok,
        "environment": _environment(),
        "floors": floors,
        "writer_exited_before_consume": True,
        "expected": {"html": PROBE_HTML, "text": PROBE_TEXT},
        "observed": {
            "html": observed_html,
            "text": observed_text,
            "html_markers_ok": html_ok,
            "text_exact_ok": text_ok,
        },
        "commitments": {
            "independent_html_consumer": (
                "osascript AppKit NSPasteboardTypeHTML (not clipboard.paste)"
            ),
            "independent_text_consumer": "pbpaste (not clipboard.paste)",
            "writer_exit": "copy_html ran in subprocess that exited before consume",
            "authorization": "normal macOS pasteboard; no entitlement bypass",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

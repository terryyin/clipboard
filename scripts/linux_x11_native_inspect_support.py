"""Independent producers/consumers for the Linux X11 inspect probe.

Uses ``xclip`` CLI as the producer and post-inspect consumer — not
``clipboard.inspect`` / ``clipboard.copy*`` same-library round-trips alone.
Does not require ``clipboard[images]``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from native_probe_common import die

ROOT = Path(__file__).resolve().parents[1]

PROBE_HTML = '<a href="https://example.com/inspect" style="color:#06c"><b>café</b></a>'
PROBE_TEXT = "café → https://example.com/inspect"
HTML_MARKERS = ("<a href=", "café", "</b>", "example.com/inspect")
TEXT_EXACT = PROBE_TEXT
HTML_FORMAT_IDS = ("text/html",)
TEXT_FORMAT_IDS = ("text/plain", "UTF8_STRING", "STRING", "TEXT")
IMAGE_FORMAT_IDS = ("image/png", "image/jpeg", "image/bmp", "PNG")

# Minimal valid 1×1 PNG (no Pillow required for the image-only producer).
_MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8cfc00000000300010005fe02fe0000000049454e44ae426082"
)


def _run_xclip(args: list[str], *, input_bytes: bytes | None = None) -> None:
    try:
        result = subprocess.run(
            ["xclip", *args],
            input=input_bytes,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"xclip producer failed: {exc}")
    if result.returncode != 0:
        detail = (
            (result.stderr or result.stdout or b"")
            .decode("utf-8", errors="replace")
            .strip()
        )
        die(f"xclip producer failed: {detail or 'unknown error'}")


def produce_html_independent() -> None:
    """Offer ``text/html`` only via xclip (independent of clipboard.* APIs)."""
    _run_xclip(
        ["-selection", "clipboard", "-t", "text/html", "-i"],
        input_bytes=PROBE_HTML.encode("utf-8"),
    )


def produce_text_independent() -> None:
    """Offer plain text via xclip ``text/plain``."""
    _run_xclip(
        ["-selection", "clipboard", "-t", "text/plain", "-i"],
        input_bytes=PROBE_TEXT.encode("utf-8"),
    )


def produce_image_only_independent() -> None:
    """Offer PNG bytes via xclip ``image/png`` (no Pillow)."""
    _run_xclip(
        ["-selection", "clipboard", "-t", "image/png", "-i"],
        input_bytes=_MIN_PNG,
    )


def consume_target(mime: str) -> bytes:
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o", "-t", mime],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"xclip consumer failed ({mime}): {exc}")
    if result.returncode != 0:
        detail = (
            (result.stderr or result.stdout or b"")
            .decode("utf-8", errors="replace")
            .strip()
        )
        die(f"xclip consumer failed ({mime}): {detail or 'unknown error'}")
    return result.stdout or b""


def consume_html_independent() -> str:
    return consume_target("text/html").decode("utf-8", errors="replace")


def consume_text_independent() -> str:
    return consume_target("text/plain").decode("utf-8", errors="replace")


def consume_image_type_present() -> bool:
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    raw = (result.stdout or b"").decode("utf-8", errors="replace")
    return "image/png" in raw


def inspect_via_library() -> dict:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import clipboard

    clipboard.set_clipboard_inspector(None)
    snapshot = clipboard.inspect()
    return {
        "kinds": sorted(snapshot.kinds),
        "formats": list(snapshot.formats),
    }


def dump_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))

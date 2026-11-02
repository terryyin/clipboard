"""Independent producers/consumers for the Linux Wayland inspect probe.

Uses ``wl-copy`` / ``wl-paste`` as producer and post-inspect consumer — not
``clipboard.inspect`` / ``clipboard.copy*`` same-library round-trips alone.
Does not require ``clipboard[images]``. Success claims must name a compositor.
"""

from __future__ import annotations

import json
import os
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
TEXT_FORMAT_IDS = ("text/plain",)
IMAGE_FORMAT_IDS = ("image/png", "image/jpeg", "image/bmp")

# Minimal valid 1×1 PNG (no Pillow required for the image-only producer).
_MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8cfc00000000300010005fe02fe0000000049454e44ae426082"
)


def named_compositor() -> str | None:
    """Return an explicit compositor name when one can be stated.

    Prefer ``CLIPBOARD_WAYLAND_COMPOSITOR`` (CI / owner override), then
    ``XDG_CURRENT_DESKTOP`` / ``DESKTOP_SESSION``. Empty → None (no verified
    claim without a named compositor).
    """
    for key in (
        "CLIPBOARD_WAYLAND_COMPOSITOR",
        "XDG_CURRENT_DESKTOP",
        "DESKTOP_SESSION",
    ):
        value = (os.environ.get(key) or "").strip()
        if value:
            # XDG_CURRENT_DESKTOP may be colon-separated; take the first token.
            return value.split(":")[0].strip() or None
    return None


def _run_wl_copy(mime: str, *, input_bytes: bytes) -> None:
    try:
        result = subprocess.run(
            ["wl-copy", "--type", mime],
            input=input_bytes,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"wl-copy producer failed: {exc}")
    if result.returncode != 0:
        detail = (
            (result.stderr or result.stdout or b"")
            .decode("utf-8", errors="replace")
            .strip()
        )
        die(f"wl-copy producer failed: {detail or 'unknown error'}")


def produce_html_independent() -> None:
    """Offer ``text/html`` only via wl-copy (independent of clipboard.* APIs)."""
    _run_wl_copy("text/html", input_bytes=PROBE_HTML.encode("utf-8"))


def produce_text_independent() -> None:
    """Offer plain text via wl-copy ``text/plain``."""
    _run_wl_copy("text/plain", input_bytes=PROBE_TEXT.encode("utf-8"))


def produce_image_only_independent() -> None:
    """Offer PNG bytes via wl-copy ``image/png`` (no Pillow)."""
    _run_wl_copy("image/png", input_bytes=_MIN_PNG)


def consume_type(mime: str) -> bytes:
    try:
        result = subprocess.run(
            ["wl-paste", "-t", mime],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"wl-paste consumer failed ({mime}): {exc}")
    if result.returncode != 0:
        detail = (
            (result.stderr or result.stdout or b"")
            .decode("utf-8", errors="replace")
            .strip()
        )
        die(f"wl-paste consumer failed ({mime}): {detail or 'unknown error'}")
    return result.stdout or b""


def consume_html_independent() -> str:
    return consume_type("text/html").decode("utf-8", errors="replace")


def consume_text_independent() -> str:
    return consume_type("text/plain").decode("utf-8", errors="replace")


def consume_image_type_present() -> bool:
    try:
        result = subprocess.run(
            ["wl-paste", "-l"],
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


def html_inspect_case() -> dict:
    produce_html_independent()
    snapshot = inspect_via_library()
    observed_html = consume_html_independent()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_html_kind = "html" in kinds
    has_html_fmt = any(f in formats for f in HTML_FORMAT_IDS)
    html_ok = all(marker in observed_html for marker in HTML_MARKERS)
    return {
        "case": "html",
        "ok": has_html_kind and has_html_fmt and html_ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_html_kind": has_html_kind,
        "has_html_format": has_html_fmt,
        "consumer_after_inspect": {
            "html_markers_ok": html_ok,
            "html": observed_html,
        },
        "non_mutation": html_ok,
    }


def text_inspect_case() -> dict:
    produce_text_independent()
    snapshot = inspect_via_library()
    observed_text = consume_text_independent()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_text_kind = "text" in kinds
    has_text_fmt = any(f in formats for f in TEXT_FORMAT_IDS)
    text_ok = observed_text == TEXT_EXACT
    return {
        "case": "text",
        "ok": has_text_kind and has_text_fmt and text_ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_text_kind": has_text_kind,
        "has_text_format": has_text_fmt,
        "consumer_after_inspect": {
            "text_exact_ok": text_ok,
            "text": observed_text,
        },
        "non_mutation": text_ok,
    }


def image_only_inspect_case() -> dict:
    produce_image_only_independent()
    snapshot = inspect_via_library()
    still_offered = consume_image_type_present()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_image = "image" in kinds
    no_text_html = "text" not in kinds and "html" not in kinds
    has_image_fmt = any(f in IMAGE_FORMAT_IDS or "png" in f.lower() for f in formats)
    ok = has_image and no_text_html and has_image_fmt and still_offered
    return {
        "case": "image_only",
        "ok": ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_image_kind": has_image,
        "no_text_or_html_kind": no_text_html,
        "has_image_format": has_image_fmt,
        "type_still_offered_after_inspect": still_offered,
        "non_mutation": still_offered,
    }


def dump_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))

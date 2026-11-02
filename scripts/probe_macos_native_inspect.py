#!/usr/bin/env python3
"""Independent-producer probe: macOS Aqua offer → clipboard.inspect().

An **independent** producer (osascript / AppKit, not clipboard.inspect and not
a same-library round-trip alone) places an HTML+text dual offer; the library
under test calls ``inspect()``; an independent consumer then still reads the
offer (non-mutation). Optionally probes an image-only offer the same way.

Prints one JSON object on stdout. Exit 0 on HTML+text inspect success;
non-zero on failure. Requires darwin. Does not run under default pytest.
Does not require ``clipboard[images]``.
"""

from __future__ import annotations

import json
import sys

from macos_native_inspect_support import (
    HTML_FORMAT_IDS,
    HTML_MARKERS,
    IMAGE_FORMAT_IDS,
    TEXT_EXACT,
    TEXT_FORMAT_IDS,
    consume_html_independent,
    consume_image_type_present,
    consume_text_independent,
    inspect_via_library,
    produce_html_text_independent,
    produce_image_only_independent,
)
from native_probe_common import die, macos_environment


def _html_text_case() -> dict:
    produce_html_text_independent()
    snapshot = inspect_via_library()
    observed_html = consume_html_independent()
    observed_text = consume_text_independent()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_html_kind = "html" in kinds
    has_text_kind = "text" in kinds
    has_html_fmt = any(f in formats for f in HTML_FORMAT_IDS)
    has_text_fmt = any(f in formats for f in TEXT_FORMAT_IDS)
    html_ok = all(marker in observed_html for marker in HTML_MARKERS)
    text_ok = observed_text == TEXT_EXACT
    ok = (
        has_html_kind
        and has_text_kind
        and has_html_fmt
        and has_text_fmt
        and html_ok
        and text_ok
    )
    return {
        "case": "html_and_text",
        "ok": ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_html_kind": has_html_kind,
        "has_text_kind": has_text_kind,
        "has_html_format": has_html_fmt,
        "has_text_format": has_text_fmt,
        "consumer_after_inspect": {
            "html_markers_ok": html_ok,
            "text_exact_ok": text_ok,
            "html": observed_html,
            "text": observed_text,
        },
        "non_mutation": html_ok and text_ok,
    }


def _image_only_case() -> dict:
    produce_image_only_independent()
    snapshot = inspect_via_library()
    still_offered = consume_image_type_present()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_image = "image" in kinds
    no_text_html = "text" not in kinds and "html" not in kinds
    has_image_fmt = any(
        f in IMAGE_FORMAT_IDS
        or "png" in f.lower()
        or "tiff" in f.lower()
        or "PNGf" in f
        for f in formats
    )
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


def main() -> None:
    if sys.platform != "darwin":
        die(f"probe requires macOS (darwin); got {sys.platform!r}")

    try:
        import clipboard  # noqa: F401
    except ImportError as exc:
        die(f"missing clipboard import: {exc}")

    html_text = _html_text_case()
    image_only: dict | None = None
    image_error: str | None = None
    try:
        image_only = _image_only_case()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — optional case; record limit
        image_error = f"{type(exc).__name__}: {exc}"

    env = macos_environment(
        producer=(
            "osascript AppKit NSPasteboardTypeHTML + NSPasteboardTypeString "
            "(independent of clipboard.inspect / not same-library round-trip)"
        ),
        inspector="clipboard.inspect() → osascript NSPasteboard types()",
        html_consumer=(
            "osascript AppKit NSPasteboard dataForType:NSPasteboardTypeHTML"
        ),
        text_consumer="pbpaste (plain string offer)",
        image_producer=(
            "osascript AppKit NSPasteboardTypePNG from temp PNG (no Pillow)"
        ),
        helper="osascript + pbpaste (macOS built-in)",
    )
    floors = {
        "macos_product": env["macos_product"],
        "macos_build": env["macos_build"],
        "machine": env["machine"],
        "method": "osascript AppKit NSPasteboard types() → clipboard.inspect",
    }
    ok = html_text["ok"] is True
    report = {
        "ok": ok,
        "environment": env,
        "floors": floors,
        "html_and_text": html_text,
        "image_only": image_only,
        "image_only_error": image_error,
        "commitments": {
            "independent_producer": (
                "osascript AppKit dual-offer / NSPasteboardTypePNG "
                "(not clipboard.inspect same-library round-trip alone)"
            ),
            "library_under_test": "clipboard.inspect()",
            "independent_consumer_after_inspect": (
                "osascript HTML + pbpaste text; image type still listed"
            ),
            "authorization": "normal macOS pasteboard; no entitlement bypass",
            "no_images_extra": True,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Independent-producer probe: macOS pasteboard → clipboard.paste_image().

Writes a known PNG with Pillow (file factory only), places it on the pasteboard
via osascript «class PNGf» (not clipboard.paste_image / round-trip), then
consumes with paste_image() using the default ImageGrab path.

Prints one JSON object on stdout. Exit 0 on opaque success; non-zero on failure.
Requires darwin + optional images extra. Does not run under default pytest.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from macos_native_probe_common import (
    ALPHA_SIZE,
    OPAQUE_SIZE,
    alpha_preservation,
    base_environment,
    describe,
    die,
    require_darwin_and_images,
    write_alpha_rgba_png,
    write_opaque_rgb_png,
)


def _place_png_on_pasteboard(path: Path) -> None:
    # Independent producer: AppleScript pasteboard write, not this library.
    script = f'set the clipboard to (read (POSIX file "{path}") as «class PNGf»)'
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout
        die(f"osascript pasteboard write failed: {detail}")


def _paste_image_from_independent_png(path: Path):
    """Place PNG via osascript, then paste_image() with real ImageGrab."""
    import clipboard

    clipboard.set_image_grabclipboard(None)
    _place_png_on_pasteboard(path)
    return clipboard.paste_image()


def _probe_opaque(tmpdir: Path) -> dict:
    from PIL import Image, ImageGrab

    path, expected_samples = write_opaque_rgb_png(tmpdir)
    width, height = OPAQUE_SIZE

    import clipboard

    first = _paste_image_from_independent_png(path)
    second = clipboard.paste_image()  # same placement; must stay preservative
    still_offered = ImageGrab.grabclipboard()

    first_desc = describe(first)
    second_desc = describe(second)
    ok = (
        first is not None
        and second is not None
        and first.size == (width, height)
        and second.size == (width, height)
        and first_desc["samples"] == expected_samples
        and second_desc["samples"] == expected_samples
        and isinstance(still_offered, Image.Image)
    )
    return {
        "case": "opaque_rgb_png",
        "ok": ok,
        "expected_size": [width, height],
        "expected_samples": expected_samples,
        "first": first_desc,
        "second": second_desc,
        "preservative": first_desc == second_desc and first is not None,
        "imagegrab_still_image_after": isinstance(still_offered, Image.Image),
        "imagegrab_still_size": (
            list(still_offered.size) if isinstance(still_offered, Image.Image) else None
        ),
        "set_image_grabclipboard": None,
    }


def _probe_alpha(tmpdir: Path) -> dict:
    path, translucent = write_alpha_rgba_png(tmpdir)
    width, height = ALPHA_SIZE
    pasted = _paste_image_from_independent_png(path)
    desc = describe(pasted)
    alpha_preserved, alpha_note = alpha_preservation(pasted, translucent)
    return {
        "case": "rgba_translucent_png",
        "ok": pasted is not None and pasted.size == (width, height),
        "expected_size": [width, height],
        "expected_translucent_pixel": list(translucent),
        "result": desc,
        "alpha_preserved": alpha_preserved,
        "alpha_note": alpha_note,
        "set_image_grabclipboard": None,
    }


def main() -> None:
    require_darwin_and_images()

    with tempfile.TemporaryDirectory(prefix="clipboard-macos-probe-") as raw:
        tmpdir = Path(raw)
        opaque = _probe_opaque(tmpdir)
        alpha = _probe_alpha(tmpdir)

    report = {
        "ok": opaque["ok"] and alpha["ok"],
        "environment": base_environment(
            pasteboard_method=(
                "osascript set clipboard to read POSIX file as «class PNGf»"
            ),
        ),
        "opaque": opaque,
        "alpha": alpha,
        "commitments": {
            "independent_producer": (
                "Pillow wrote PNG file; osascript «class PNGf» placed it"
            ),
            "consumer": ("clipboard.paste_image() with set_image_grabclipboard(None)"),
            "authorization": "normal macOS pasteboard; no entitlement bypass",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_image() → macOS pasteboard.

Subprocess writer calls copy_image() then exits. Parent recovers the offer
via PIL.ImageGrab.grabclipboard (not clipboard.paste_image as sole proof).

Prints one JSON object on stdout. Exit 0 on opaque success; non-zero on failure.
Requires darwin + optional images extra. Does not run under default pytest.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from native_probe_common import (
    ALPHA_SIZE,
    OPAQUE_SIZE,
    alpha_preservation,
    consume_after_writer,
    describe,
    macos_environment,
    require_darwin_and_images,
    rgb_samples,
    write_alpha_rgba_png,
    write_opaque_rgb_png,
)

ROOT = Path(__file__).resolve().parents[1]
CONSUMER_API = "PIL.ImageGrab.grabclipboard"


def _grab_independent():
    from PIL import ImageGrab

    return ImageGrab.grabclipboard()


def _probe_opaque(tmpdir: Path) -> dict:
    path, expected_samples = write_opaque_rgb_png(tmpdir)
    writer, grabbed, grab_error = consume_after_writer(
        path, root=ROOT, grab=_grab_independent
    )
    desc = describe(grabbed)
    samples_match = False
    if desc is not None:
        samples_match = rgb_samples(desc["samples"]) == expected_samples
    width, height = OPAQUE_SIZE
    ok = (
        writer["returncode"] == 0
        and grabbed is not None
        and grabbed.size == (width, height)
        and samples_match
    )
    return {
        "case": "opaque_rgb_png",
        "ok": ok,
        "writer_exit": writer,
        "writer_exited_before_consume": True,
        "expected_size": [width, height],
        "expected_samples": expected_samples,
        "independent_consumer": desc,
        "grab_error": grab_error,
        "consumer_api": CONSUMER_API,
        "not_paste_image_alone": True,
    }


def _probe_alpha(tmpdir: Path) -> dict:
    path, translucent = write_alpha_rgba_png(tmpdir)
    writer, grabbed, grab_error = consume_after_writer(
        path, root=ROOT, grab=_grab_independent
    )
    desc = describe(grabbed)
    alpha_preserved, alpha_note = alpha_preservation(
        grabbed,
        translucent,
        drop_guidance=(
            "documented drop for macOS Aqua write via ImageGrab.grabclipboard "
            "consumer — do not invent opacity"
        ),
    )
    width, height = ALPHA_SIZE
    return {
        "case": "rgba_translucent_png",
        "ok": writer["returncode"] == 0
        and grabbed is not None
        and grabbed.size == (width, height),
        "writer_exit": writer,
        "expected_size": [width, height],
        "expected_translucent_pixel": list(translucent),
        "result": desc,
        "alpha_preserved": alpha_preserved,
        "alpha_note": alpha_note,
        "grab_error": grab_error,
        "consumer_api": CONSUMER_API,
        "not_paste_image_alone": True,
    }


def main() -> None:
    require_darwin_and_images()

    with tempfile.TemporaryDirectory(prefix="clipboard-macos-copy-probe-") as raw:
        tmpdir = Path(raw)
        opaque = _probe_opaque(tmpdir)
        alpha = _probe_alpha(tmpdir)

    # Opaque success is required for exit 0; alpha records preserve-or-drop.
    report = {
        "ok": opaque["ok"],
        "environment": macos_environment(
            write_method=(
                "clipboard.copy_image → osascript «class PNGf» (library Darwin default)"
            ),
            independent_consumer="PIL.ImageGrab.grabclipboard after writer exit",
        ),
        "opaque": opaque,
        "alpha": alpha,
        "commitments": {
            "writer": (
                "subprocess: clipboard.copy_image with default Darwin write; "
                "process exits before consume"
            ),
            "independent_consumer": (
                "PIL.ImageGrab.grabclipboard — not clipboard.paste_image alone"
            ),
            "authorization": "normal macOS pasteboard; no entitlement bypass",
            "hang_bound": "osascript write timeout 30s; writer subprocess timeout 60s",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

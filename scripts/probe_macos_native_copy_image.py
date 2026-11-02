#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_image() → macOS pasteboard.

Subprocess writer calls copy_image() then exits. Parent recovers the offer
via PIL.ImageGrab.grabclipboard (not clipboard.paste_image as sole proof).

Prints one JSON object on stdout. Exit 0 on opaque success; non-zero on failure.
Requires darwin + optional images extra. Does not run under default pytest.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from macos_native_probe_common import (
    ALPHA_SIZE,
    OPAQUE_SIZE,
    alpha_preservation,
    base_environment,
    describe,
    require_darwin_and_images,
    write_alpha_rgba_png,
    write_opaque_rgb_png,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_via_exiting_subprocess(path: Path) -> dict:
    """Run copy_image in a child that exits before the parent consumes."""
    child = f"""
import sys
from pathlib import Path
from PIL import Image
import clipboard

clipboard.set_image_writeclipboard(None)
image = Image.open(Path({str(path)!r}))
image.load()
clipboard.copy_image(image)
sys.exit(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", child],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip() or None,
        "stderr": result.stderr.strip() or None,
    }


def _grab_independent():
    from PIL import ImageGrab

    return ImageGrab.grabclipboard()


def _rgb_samples(samples: dict) -> dict:
    """Compare opaque identity on RGB channels even if consumer returns RGBA."""
    out = {}
    for key, value in samples.items():
        if isinstance(value, list) and len(value) >= 3:
            out[key] = value[:3]
        else:
            out[key] = value
    return out


def _consume_after_writer(path: Path):
    from PIL import Image

    writer = _write_via_exiting_subprocess(path)
    grabbed = None
    grab_error = None
    if writer["returncode"] == 0:
        try:
            grabbed = _grab_independent()
        except Exception as exc:  # noqa: BLE001 — record for JSON report
            grab_error = f"{type(exc).__name__}: {exc}"
    image = grabbed if isinstance(grabbed, Image.Image) else None
    return writer, image, grab_error


def _probe_opaque(tmpdir: Path) -> dict:
    path, expected_samples = write_opaque_rgb_png(tmpdir)
    writer, grabbed, grab_error = _consume_after_writer(path)
    desc = describe(grabbed)
    samples_match = False
    if desc is not None:
        samples_match = _rgb_samples(desc["samples"]) == expected_samples
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
        "consumer_api": "PIL.ImageGrab.grabclipboard",
        "not_paste_image_alone": True,
    }


def _probe_alpha(tmpdir: Path) -> dict:
    path, translucent = write_alpha_rgba_png(tmpdir)
    writer, grabbed, grab_error = _consume_after_writer(path)
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
        "consumer_api": "PIL.ImageGrab.grabclipboard",
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
        "environment": base_environment(
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

#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_image() → Linux X11 + xclip.

Subprocess writer calls copy_image() then exits. Parent recovers the offer via
``xclip -o -selection clipboard -t image/png`` (not clipboard.paste_image as
sole proof). Intended venue: gated GitHub Actions under Xvfb.

Prints one JSON object on stdout. Exit 0 on opaque success; non-zero on failure.
Requires Linux + DISPLAY + xclip + optional images extra. Not default pytest.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from native_probe_common import (
    ALPHA_SIZE,
    OPAQUE_SIZE,
    alpha_preservation,
    consume_after_writer,
    describe,
    linux_x11_environment,
    require_linux_x11_and_images,
    rgb_samples,
    write_alpha_rgba_png,
    write_opaque_rgb_png,
)

ROOT = Path(__file__).resolve().parents[1]
CONSUMER_API = "xclip -o -selection clipboard -t image/png"


def _grab_independent_xclip():
    """Recover PNG bytes via xclip stdout — not clipboard.paste_image."""
    from PIL import Image

    result = subprocess.run(
        ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        detail = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        raise OSError(f"xclip -o image/png failed: {detail or 'unknown error'}")
    if not result.stdout:
        raise OSError("xclip -o image/png returned empty stdout")
    image = Image.open(BytesIO(result.stdout))
    image.load()
    return image


def _probe_opaque(tmpdir: Path) -> dict:
    path, expected_samples = write_opaque_rgb_png(tmpdir)
    writer, grabbed, grab_error = consume_after_writer(
        path, root=ROOT, grab=_grab_independent_xclip
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
        path, root=ROOT, grab=_grab_independent_xclip
    )
    desc = describe(grabbed)
    alpha_preserved, alpha_note = alpha_preservation(
        grabbed,
        translucent,
        drop_guidance=(
            "documented drop for Linux X11 write via xclip image/png "
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
    require_linux_x11_and_images()

    with tempfile.TemporaryDirectory(prefix="clipboard-linux-x11-copy-probe-") as raw:
        tmpdir = Path(raw)
        opaque = _probe_opaque(tmpdir)
        alpha = _probe_alpha(tmpdir)

    report = {
        "ok": opaque["ok"],
        "environment": linux_x11_environment(
            write_method=(
                "clipboard.copy_image → xclip -selection clipboard "
                "-t image/png -i (library Linux default)"
            ),
            independent_consumer=(
                "xclip -o -selection clipboard -t image/png after writer exit"
            ),
        ),
        "opaque": opaque,
        "alpha": alpha,
        "commitments": {
            "writer": (
                "subprocess: clipboard.copy_image with default Linux xclip write; "
                "process exits before consume (xclip may keep a background owner)"
            ),
            "independent_consumer": (
                "xclip -o image/png — not clipboard.paste_image alone"
            ),
            "authorization": "normal X11 CLIPBOARD via xclip; no entitlement bypass",
            "hang_bound": "xclip write timeout 30s; writer subprocess timeout 60s",
            "venue": "gated CI under Xvfb (or local X11 with DISPLAY)",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

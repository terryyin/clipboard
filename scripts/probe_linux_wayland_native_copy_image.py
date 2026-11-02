#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_image() → Linux Wayland + wl-copy.

Subprocess writer calls copy_image() then exits. Parent recovers the offer via
``wl-paste -t image/png`` (not clipboard.paste_image as sole proof). Intended
venue: gated GitHub Actions under a named Sway compositor.

Prints one JSON object on stdout. Exit 0 on opaque success; non-zero on failure.
Requires Linux + WAYLAND_DISPLAY + wl-clipboard + optional images extra.
Not default pytest. Success is scoped to the named compositor (Sway), not
generalized to all Wayland environments.
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
    linux_wayland_environment,
    require_linux_wayland_and_images,
    rgb_samples,
    write_alpha_rgba_png,
    write_opaque_rgb_png,
)

ROOT = Path(__file__).resolve().parents[1]
CONSUMER_API = "wl-paste -t image/png"
COMPOSITOR = "Sway"


def _grab_independent_wl_paste():
    """Recover PNG bytes via wl-paste stdout — not clipboard.paste_image."""
    from PIL import Image

    result = subprocess.run(
        ["wl-paste", "-t", "image/png"],
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        detail = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        raise OSError(f"wl-paste -t image/png failed: {detail or 'unknown error'}")
    if not result.stdout:
        raise OSError("wl-paste -t image/png returned empty stdout")
    image = Image.open(BytesIO(result.stdout))
    image.load()
    return image


def _probe_opaque(tmpdir: Path) -> dict:
    path, expected_samples = write_opaque_rgb_png(tmpdir)
    writer, grabbed, grab_error = consume_after_writer(
        path, root=ROOT, grab=_grab_independent_wl_paste
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
        path, root=ROOT, grab=_grab_independent_wl_paste
    )
    desc = describe(grabbed)
    alpha_preserved, alpha_note = alpha_preservation(
        grabbed,
        translucent,
        drop_guidance=(
            "documented drop for Linux Wayland write via wl-copy image/png "
            f"under {COMPOSITOR} — do not invent opacity"
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
    require_linux_wayland_and_images()

    with tempfile.TemporaryDirectory(
        prefix="clipboard-linux-wayland-copy-probe-"
    ) as raw:
        tmpdir = Path(raw)
        opaque = _probe_opaque(tmpdir)
        alpha = _probe_alpha(tmpdir)

    report = {
        "ok": opaque["ok"],
        "environment": linux_wayland_environment(
            write_method=(
                "clipboard.copy_image → wl-copy --type image/png "
                "(library Linux Wayland default)"
            ),
            independent_consumer=("wl-paste -t image/png after writer exit"),
            compositor=COMPOSITOR,
        ),
        "opaque": opaque,
        "alpha": alpha,
        "commitments": {
            "writer": (
                "subprocess: clipboard.copy_image with default Linux wl-copy "
                "write; process exits before consume "
                "(wl-copy may keep a background owner)"
            ),
            "independent_consumer": (
                "wl-paste -t image/png — not clipboard.paste_image alone"
            ),
            "authorization": (
                "normal Wayland clipboard via wl-copy; no entitlement bypass"
            ),
            "hang_bound": "wl-copy write timeout 30s; writer subprocess timeout 60s",
            "venue": (
                f"gated CI under named compositor {COMPOSITOR} "
                "(or local Wayland with WAYLAND_DISPLAY); "
                "do not generalize beyond that compositor"
            ),
            "compositor_scope": COMPOSITOR,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Shared helpers for gated macOS Aqua native clipboard probes."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

OPAQUE_SIZE = (32, 24)
OPAQUE_COLORS = {
    "tl": (255, 0, 0),
    "tr": (0, 255, 0),
    "bl": (0, 0, 255),
    "br": (255, 255, 0),
    "center": (128, 64, 192),
}
ALPHA_SIZE = (16, 16)
ALPHA_TRANSLUCENT = (0, 0, 255, 128)


def die(message: str, *, code: int = 1) -> None:
    print(json.dumps({"ok": False, "error": message}), file=sys.stderr)
    raise SystemExit(code)


def sw_vers(key: str) -> str | None:
    try:
        out = subprocess.check_output(["sw_vers", f"-{key}"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


def base_environment(**extra: object) -> dict:
    pillow_version = None
    try:
        import PIL

        pillow_version = PIL.__version__
    except ImportError:
        pass
    env = {
        "os": platform.system(),
        "os_release": platform.release(),
        "macos_product": sw_vers("ProductVersion"),
        "macos_build": sw_vers("BuildVersion"),
        "machine": platform.machine(),
        "desktop": "Aqua (macOS WindowServer / Quartz)",
        "helper": "osascript (macOS built-in)",
        "pillow_version": pillow_version,
        "python": sys.version.split()[0],
    }
    env.update(extra)
    return env


def require_darwin_and_images() -> None:
    if sys.platform != "darwin":
        die(f"probe requires macOS (darwin); got {sys.platform!r}")
    try:
        from PIL import Image  # noqa: F401

        import clipboard  # noqa: F401
    except ImportError as exc:
        die(f"missing dependency (install clipboard[images]): {exc}")


def sample_corners(image) -> dict:
    w, h = image.size
    points = {
        "tl": image.getpixel((0, 0)),
        "tr": image.getpixel((w - 1, 0)),
        "bl": image.getpixel((0, h - 1)),
        "br": image.getpixel((w - 1, h - 1)),
        "center": image.getpixel((w // 2, h // 2)),
    }
    return {k: list(v) if isinstance(v, tuple) else v for k, v in points.items()}


def describe(image) -> dict | None:
    if image is None:
        return None
    return {
        "size": list(image.size),
        "mode": image.mode,
        "samples": sample_corners(image),
    }


def write_opaque_rgb_png(tmpdir: Path) -> tuple[Path, dict]:
    from PIL import Image

    width, height = OPAQUE_SIZE
    expected_samples = {k: list(v) for k, v in OPAQUE_COLORS.items()}
    img = Image.new("RGB", (width, height), OPAQUE_COLORS["center"])
    img.putpixel((0, 0), OPAQUE_COLORS["tl"])
    img.putpixel((width - 1, 0), OPAQUE_COLORS["tr"])
    img.putpixel((0, height - 1), OPAQUE_COLORS["bl"])
    img.putpixel((width - 1, height - 1), OPAQUE_COLORS["br"])
    path = tmpdir / "opaque.png"
    img.save(path, format="PNG")
    return path, expected_samples


def write_alpha_rgba_png(tmpdir: Path) -> tuple[Path, tuple[int, int, int, int]]:
    from PIL import Image

    width, height = ALPHA_SIZE
    img = Image.new("RGBA", (width, height), (255, 0, 0, 255))
    img.putpixel((8, 8), ALPHA_TRANSLUCENT)
    path = tmpdir / "alpha.png"
    img.save(path, format="PNG")
    return path, ALPHA_TRANSLUCENT


def alpha_preservation(
    image,
    translucent: tuple[int, int, int, int],
    *,
    drop_guidance: str = ("document as evidence limit, do not invent opacity"),
) -> tuple[bool, str]:
    """Return (preserved, note) for a translucent-center RGBA probe image."""
    if image is None:
        return False, "no image returned"
    center = image.getpixel((8, 8))
    if image.mode == "RGBA" and isinstance(center, tuple) and len(center) == 4:
        preserved = center[3] == translucent[3]
        note = (
            "RGBA mode with matching alpha at translucent pixel"
            if preserved
            else f"RGBA mode but alpha/channel mismatch: got {center!r}"
        )
        return preserved, note
    if image.mode in ("RGB", "P") or (isinstance(center, tuple) and len(center) == 3):
        return False, (
            f"desktop/Pillow returned mode={image.mode!r} without alpha "
            f"(center={center!r}); {drop_guidance}"
        )
    return False, f"unexpected mode={image.mode!r} center={center!r}"

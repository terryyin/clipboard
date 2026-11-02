"""Shared helpers for gated native clipboard probes (macOS, Linux X11/Wayland)."""

from __future__ import annotations

import json
import os
import platform
import shutil
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


def _pillow_version() -> str | None:
    try:
        import PIL

        return PIL.__version__
    except ImportError:
        return None


def macos_environment(**extra: object) -> dict:
    env = {
        "os": platform.system(),
        "os_release": platform.release(),
        "macos_product": sw_vers("ProductVersion"),
        "macos_build": sw_vers("BuildVersion"),
        "machine": platform.machine(),
        "desktop": "Aqua (macOS WindowServer / Quartz)",
        "helper": "osascript (macOS built-in)",
        "pillow_version": _pillow_version(),
        "python": sys.version.split()[0],
    }
    env.update(extra)
    return env


def xclip_version() -> str | None:
    try:
        out = subprocess.check_output(
            ["xclip", "-version"],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    first = (out or "").strip().splitlines()
    return first[0].strip() if first else None


def linux_x11_environment(**extra: object) -> dict:
    env = {
        "os": platform.system(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "desktop": "X11 under Xvfb (CI) or local X11",
        "display": os.environ.get("DISPLAY"),
        "xdg_session_type": os.environ.get("XDG_SESSION_TYPE"),
        "helper": "xclip",
        "xclip_version": xclip_version(),
        "pillow_version": _pillow_version(),
        "python": sys.version.split()[0],
        "ci": os.environ.get("CI"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "image_os": os.environ.get("ImageOS"),
    }
    env.update(extra)
    return env


def wl_clipboard_version() -> str | None:
    try:
        out = subprocess.check_output(
            ["wl-copy", "--version"],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    first = (out or "").strip().splitlines()
    return first[0].strip() if first else None


def linux_wayland_environment(**extra: object) -> dict:
    env = {
        "os": platform.system(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "desktop": "Weston (CI headless) or local Wayland",
        "compositor": "Weston",
        "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
        "xdg_session_type": os.environ.get("XDG_SESSION_TYPE"),
        "helper": "wl-copy",
        "wl_clipboard_version": wl_clipboard_version(),
        "pillow_version": _pillow_version(),
        "python": sys.version.split()[0],
        "ci": os.environ.get("CI"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "image_os": os.environ.get("ImageOS"),
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


def require_linux_x11_and_images() -> None:
    if not sys.platform.startswith("linux"):
        die(f"probe requires Linux; got {sys.platform!r}")
    if not os.environ.get("DISPLAY"):
        die("probe requires DISPLAY (run under Xvfb / xvfb-run -a)")
    if shutil.which("xclip") is None:
        die("xclip not found on PATH")
    try:
        from PIL import Image  # noqa: F401

        import clipboard  # noqa: F401
    except ImportError as exc:
        die(f"missing dependency (install clipboard[images]): {exc}")


def require_linux_wayland_and_images() -> None:
    if not sys.platform.startswith("linux"):
        die(f"probe requires Linux; got {sys.platform!r}")
    if not os.environ.get("WAYLAND_DISPLAY"):
        die("probe requires WAYLAND_DISPLAY (run under Weston / named compositor)")
    if shutil.which("wl-copy") is None or shutil.which("wl-paste") is None:
        die("wl-copy/wl-paste not found on PATH (install wl-clipboard)")
    try:
        from PIL import Image  # noqa: F401

        import clipboard  # noqa: F401
    except ImportError as exc:
        die(f"missing dependency (install clipboard[images]): {exc}")


def write_via_exiting_copy_image_subprocess(path: Path, *, root: Path) -> dict:
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
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip() or None,
        "stderr": result.stderr.strip() or None,
    }


def consume_after_writer(path: Path, *, root: Path, grab):
    """Writer-exit then independent grab; record grab errors for JSON."""
    from PIL import Image

    writer = write_via_exiting_copy_image_subprocess(path, root=root)
    grabbed = None
    grab_error = None
    if writer["returncode"] == 0:
        try:
            result = grab()
        except Exception as exc:  # noqa: BLE001 — record for JSON report
            grab_error = f"{type(exc).__name__}: {exc}"
        else:
            grabbed = result if isinstance(result, Image.Image) else None
    return writer, grabbed, grab_error


def rgb_samples(samples: dict) -> dict:
    """Compare opaque identity on RGB channels even if consumer returns RGBA."""
    out = {}
    for key, value in samples.items():
        if isinstance(value, list) and len(value) >= 3:
            out[key] = value[:3]
        else:
            out[key] = value
    return out


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

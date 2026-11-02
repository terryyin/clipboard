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
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


def _die(message: str, *, code: int = 1) -> None:
    print(json.dumps({"ok": False, "error": message}), file=sys.stderr)
    raise SystemExit(code)


def _environment() -> dict:
    pillow_version = None
    try:
        import PIL

        pillow_version = PIL.__version__
    except ImportError:
        pass
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "macos_product": _sw_vers("ProductVersion"),
        "macos_build": _sw_vers("BuildVersion"),
        "machine": platform.machine(),
        "desktop": "Aqua (macOS WindowServer / Quartz)",
        "pasteboard_method": (
            "osascript set clipboard to read POSIX file as «class PNGf»"
        ),
        "helper": "osascript (macOS built-in)",
        "pillow_version": pillow_version,
        "python": sys.version.split()[0],
    }


def _sw_vers(key: str) -> str | None:
    try:
        out = subprocess.check_output(["sw_vers", f"-{key}"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


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
        _die(f"osascript pasteboard write failed: {detail}")


def _paste_image_from_independent_png(path: Path):
    """Place PNG via osascript, then paste_image() with real ImageGrab."""
    import clipboard

    clipboard.set_image_grabclipboard(None)
    _place_png_on_pasteboard(path)
    return clipboard.paste_image()


def _sample_corners(image) -> dict:
    w, h = image.size
    points = {
        "tl": image.getpixel((0, 0)),
        "tr": image.getpixel((w - 1, 0)),
        "bl": image.getpixel((0, h - 1)),
        "br": image.getpixel((w - 1, h - 1)),
        "center": image.getpixel((w // 2, h // 2)),
    }
    return {k: list(v) if isinstance(v, tuple) else v for k, v in points.items()}


def _describe(image) -> dict | None:
    if image is None:
        return None
    return {
        "size": list(image.size),
        "mode": image.mode,
        "samples": _sample_corners(image),
    }


def _probe_opaque(tmpdir: Path) -> dict:
    from PIL import Image, ImageGrab

    # Known opaque RGB: distinct corner colors for identity check.
    width, height = 32, 24
    expected = {
        "tl": (255, 0, 0),
        "tr": (0, 255, 0),
        "bl": (0, 0, 255),
        "br": (255, 255, 0),
        "center": (128, 64, 192),
    }
    expected_samples = {k: list(v) for k, v in expected.items()}
    img = Image.new("RGB", (width, height), expected["center"])
    img.putpixel((0, 0), expected["tl"])
    img.putpixel((width - 1, 0), expected["tr"])
    img.putpixel((0, height - 1), expected["bl"])
    img.putpixel((width - 1, height - 1), expected["br"])
    path = tmpdir / "opaque.png"
    img.save(path, format="PNG")

    import clipboard

    first = _paste_image_from_independent_png(path)
    second = clipboard.paste_image()  # same placement; must stay preservative
    still_offered = ImageGrab.grabclipboard()

    first_desc = _describe(first)
    second_desc = _describe(second)
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
    from PIL import Image

    width, height = 16, 16
    # Fully opaque red + one translucent blue pixel.
    img = Image.new("RGBA", (width, height), (255, 0, 0, 255))
    translucent = (0, 0, 255, 128)
    img.putpixel((8, 8), translucent)
    path = tmpdir / "alpha.png"
    img.save(path, format="PNG")

    pasted = _paste_image_from_independent_png(path)
    desc = _describe(pasted)
    alpha_preserved = False
    alpha_note = "no image returned"
    if pasted is not None:
        center = pasted.getpixel((8, 8))
        if pasted.mode == "RGBA" and isinstance(center, tuple) and len(center) == 4:
            alpha_preserved = center[3] == translucent[3]
            alpha_note = (
                "RGBA mode with matching alpha at translucent pixel"
                if alpha_preserved
                else f"RGBA mode but alpha/channel mismatch: got {center!r}"
            )
        elif pasted.mode in ("RGB", "P") or (
            isinstance(center, tuple) and len(center) == 3
        ):
            alpha_note = (
                f"desktop/Pillow returned mode={pasted.mode!r} without alpha "
                f"(center={center!r}); document as evidence limit, "
                "do not invent opacity"
            )
        else:
            alpha_note = f"unexpected mode={pasted.mode!r} center={center!r}"

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
    if sys.platform != "darwin":
        _die(f"probe requires macOS (darwin); got {sys.platform!r}")

    try:
        from PIL import Image  # noqa: F401

        import clipboard  # noqa: F401
    except ImportError as exc:
        _die(f"missing dependency (install clipboard[images]): {exc}")

    with tempfile.TemporaryDirectory(prefix="clipboard-macos-probe-") as raw:
        tmpdir = Path(raw)
        opaque = _probe_opaque(tmpdir)
        alpha = _probe_alpha(tmpdir)

    report = {
        "ok": opaque["ok"] and alpha["ok"],
        "environment": _environment(),
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

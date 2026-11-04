"""Clipboard image write (copy_image) and platform PNG offer helpers."""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from clipboard import _platform
from clipboard._desktop import _helper_failure_detail, _is_linux_wayland
from clipboard._errors import ClipboardImageError
from clipboard._image_read import _pillow_image, _raise_image_failure
from clipboard._image_write_linux import _write_linux_wl_copy, _write_linux_xclip

if TYPE_CHECKING:
    from PIL import Image


@contextmanager
def _temporary_png_offer(image: Image.Image) -> Iterator:
    """Yield a PNG path kept alive until the helper has finished reading it."""
    with tempfile.TemporaryDirectory(prefix="clipboard-copy-image-") as raw:
        path = Path(raw) / "offer.png"
        image.save(path, format="PNG")
        yield path


def _write_macos_pngf(image: Image.Image) -> None:
    """Publish a transferable PNG via osascript «class PNGf» (no pyobjc)."""
    with _temporary_png_offer(image) as path:
        # osascript reads the file into the pasteboard before TemporaryDirectory
        # cleanup; normal macOS pasteboard authorization (no entitlement bypass).
        posix = str(path.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        script = f'set the clipboard to (read (POSIX file "{posix}") as «class PNGf»)'
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise OSError("osascript clipboard write timed out") from exc
        if result.returncode != 0:
            raise OSError(
                "osascript clipboard write failed: "
                f"{_helper_failure_detail(result, fallback='unknown error')}"
            )


def _default_writeclipboard(image: Image.Image) -> None:
    """Platform default image write; Windows stays unimplemented (evidence-limited)."""
    platform = _platform.current()
    if platform == "darwin":
        _write_macos_pngf(image)
        return
    if platform.startswith("linux"):
        if _is_linux_wayland():
            _write_linux_wl_copy(image)
        else:
            _write_linux_xclip(image)
        return
    raise NotImplementedError(
        "clipboard image write is not implemented for this platform"
    )


_writeclipboard: Callable = _default_writeclipboard


def set_image_writeclipboard(writeclipboard: Callable | None) -> None:
    """Inject a clipboard image-write callable (tests / fakes)."""
    global _writeclipboard
    _writeclipboard = (
        _default_writeclipboard if writeclipboard is None else writeclipboard
    )


def _transferable_raster(Image, image: Image.Image) -> Image.Image:
    """Return an RGB/RGBA raster ready to offer, or raise before replace."""
    if not isinstance(image, Image.Image):
        raise TypeError(
            f"copy_image requires a Pillow Image, got {type(image).__name__}"
        )
    image.load()
    if image.width <= 0 or image.height <= 0:
        raise ValueError("copy_image requires a non-empty raster")
    if image.mode in ("RGB", "RGBA"):
        return image
    if image.mode in ("LA", "PA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        return image.convert("RGBA")
    return image.convert("RGB")


def copy_image(image: Image.Image) -> None:
    """Copy a Pillow Image onto the clipboard.

    Requires the optional ``clipboard[images]`` extra (Pillow). Invalid or
    unloadable input raises ``ClipboardImageError`` before any replace.
    Non-RGB(A) modes are converted to a transferable RGB/RGBA raster. Backend
    / transfer failures raise ``ClipboardImageError``. Tests may inject a fake
    via ``set_image_writeclipboard``.
    """
    Image = _pillow_image("copy_image")
    try:
        raster = _transferable_raster(Image, image)
    except (TypeError, ValueError, OSError) as exc:
        _raise_image_failure(exc, operation="write")

    try:
        _writeclipboard(raster)
    except ClipboardImageError:
        raise
    except (OSError, NotImplementedError) as exc:
        # Includes PermissionError, ChildProcessError, default stub.
        _raise_image_failure(exc, operation="write")

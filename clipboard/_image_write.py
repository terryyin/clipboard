"""Clipboard image write (copy_image) and platform PNG offer helpers."""

from __future__ import annotations

import subprocess
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from clipboard import _platform
from clipboard._desktop import (
    _helper_failure_detail,
    _is_linux_wayland,
    _start_helper_owner,
    _stop_helper_owner,
)
from clipboard._errors import ClipboardImageError
from clipboard._image_read import _pillow_image, _raise_image_failure
from clipboard._text_native_linux import (
    _LINUX_TEXT_TIMEOUT_S,
    _helper_log_suffix,
    _remaining,
)

if TYPE_CHECKING:
    from PIL import Image

_PNG = "image/png"
_XCLIP_IMAGE_WRITE_CMD = ["xclip", "-selection", "clipboard", "-t", _PNG, "-i"]
_XCLIP_IMAGE_READ_CMD = ["xclip", "-selection", "clipboard", "-o", "-t", _PNG]
# One bound across launch, hand-over and read-back (``copy`` / ``copy_files``).
_X11_IMAGE_WRITE_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S
# Each read-back is bounded below the overall write bound (text writer's cap).
_X11_IMAGE_READBACK_TIMEOUT_S = 2.0
_X11_IMAGE_POLL_INTERVAL_S = 0.05


@contextmanager
def _temporary_png_offer(image: Image.Image) -> Iterator:
    """Yield a PNG path kept alive until the helper has finished reading it."""
    with tempfile.TemporaryDirectory(prefix="clipboard-copy-image-") as raw:
        path = Path(raw) / "offer.png"
        image.save(path, format="PNG")
        yield path


def _png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


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


def _xclip_serves_png(png_bytes: bytes, deadline: float) -> bool:
    """Whether CLIPBOARD's ``image/png`` is exactly ``png_bytes`` (lenient)."""
    try:
        result = subprocess.run(
            _XCLIP_IMAGE_READ_CMD,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=_remaining(deadline, _X11_IMAGE_READBACK_TIMEOUT_S),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout == png_bytes


def _write_linux_xclip(image: Image.Image) -> None:
    """Publish PNG bytes on X11 CLIPBOARD via ``xclip`` (``image/png``).

    Leaves ``xclip`` running in its own session as the CLIPBOARD owner so the
    writing Python process can exit while the offer stays pasteable (issue #5
    writer-exit); the PNG reaches it through the shared owner launcher, never
    a pipe. Returns only once ``image/png`` reads back exactly the written
    PNG: a previous image owner already lists ``image/png`` in TARGETS. One
    10 s bound covers launch, hand-over and read-back; when it passes, the
    owner's session is stopped and ``OSError`` names ``xclip`` and the bound.
    """
    png_bytes = _png_bytes(image)
    command = " ".join(_XCLIP_IMAGE_WRITE_CMD)
    deadline = time.monotonic() + _X11_IMAGE_WRITE_TIMEOUT_S
    # stderr goes to an unlinked file, never a pipe the background owner holds.
    with tempfile.TemporaryFile() as log:
        try:
            proc = _start_helper_owner(_XCLIP_IMAGE_WRITE_CMD, png_bytes, log)
        except FileNotFoundError as exc:
            raise OSError(
                "xclip is required for clipboard image write on Linux X11; "
                "install xclip and ensure it is on PATH"
            ) from exc
        except OSError as exc:
            raise OSError(f"xclip clipboard write could not start ({exc})") from exc
        while True:
            status = proc.poll()
            if status not in (None, 0):
                raise OSError(
                    f"xclip clipboard write failed: {command} exited with status "
                    f"{status}" + _helper_log_suffix(log)
                )
            if _xclip_serves_png(png_bytes, deadline):
                return
            if time.monotonic() >= deadline:
                _stop_helper_owner(proc)
                raise OSError(
                    f"xclip clipboard write failed: {command} did not serve the "
                    f"PNG as {_PNG} within the {_X11_IMAGE_WRITE_TIMEOUT_S:g}s bound"
                    + _helper_log_suffix(log)
                ) from subprocess.TimeoutExpired(
                    _XCLIP_IMAGE_WRITE_CMD, _X11_IMAGE_WRITE_TIMEOUT_S
                )
            time.sleep(_X11_IMAGE_POLL_INTERVAL_S)


def _write_linux_wl_copy(image: Image.Image) -> None:
    """Publish PNG bytes on Wayland via ``wl-copy`` (``image/png``).

    ``wl-copy`` reads stdin, then the foreground helper exits while a
    background owner keeps the offer pasteable after the writing Python
    process exits (issue #5 writer-exit).
    """
    png_bytes = _png_bytes(image)
    # Same pipe rule as xclip -quiet: wl-copy may background a server process.
    try:
        proc = subprocess.Popen(
            ["wl-copy", "--type", "image/png"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise OSError(
            "wl-copy is required for clipboard image write on Linux Wayland; "
            "install wl-clipboard and ensure wl-copy is on PATH"
        ) from exc
    try:
        proc.communicate(input=png_bytes, timeout=30)
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.wait(timeout=5)
        raise OSError("wl-copy clipboard write timed out") from exc
    if proc.returncode != 0:
        raise OSError(f"wl-copy clipboard write failed: exit {proc.returncode}")


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

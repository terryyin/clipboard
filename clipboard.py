"""Cross-platform clipboard access, provided by pyperclip."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from pyperclip import copy as copy
from pyperclip import paste as paste

if TYPE_CHECKING:
    from PIL import Image

VERSION = "0.0.5"


class ClipboardImageError(Exception):
    """Image clipboard read or write failed; not ordinary absence (``None``)."""


def _pillow_image(operation: str):
    """Return ``PIL.Image``, or raise ``ImportError`` for the images extra."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            f"{operation} requires the optional images extra "
            "(Pillow). Install with: pip install 'clipboard[images]'"
        ) from exc
    return Image


class ClipboardContentError(Exception):
    """HTML/rich clipboard content operation failed."""


def _default_grabclipboard():
    from PIL.ImageGrab import grabclipboard

    return grabclipboard()


_grabclipboard: Callable = _default_grabclipboard


def set_image_grabclipboard(grabclipboard: Callable | None) -> None:
    """Inject an ImageGrab.grabclipboard-compatible callable (tests / fakes)."""
    global _grabclipboard
    _grabclipboard = _default_grabclipboard if grabclipboard is None else grabclipboard


def _macos_html_clipboard_writer(html: str, text: str) -> None:
    """Publish HTML + plain text as one NSPasteboard dual offer.

    Uses built-in ``osascript`` / AppKit (no PyObjC / ``clipboard[images]``).
    Both ``NSPasteboardTypeHTML`` and ``NSPasteboardTypeString`` are declared
    and set in one clear/replace cycle so rich and text consumers see one offer.
    """
    with tempfile.TemporaryDirectory(prefix="clipboard-html-") as raw:
        tmp = Path(raw)
        html_path = tmp / "fragment.html"
        text_path = tmp / "alternative.txt"
        html_path.write_text(html, encoding="utf-8")
        text_path.write_text(text, encoding="utf-8")
        # Paths come from TemporaryDirectory; quote only for AppleScript literals.
        utf8 = "current application's NSUTF8StringEncoding"
        script_path = tmp / "set_dual.applescript"
        script_path.write_text(
            "\n".join(
                [
                    'use framework "AppKit"',
                    'use framework "Foundation"',
                    "use scripting additions",
                    f'set htmlPath to "{html_path}"',
                    f'set textPath to "{text_path}"',
                    (
                        "set htmlNS to current application's NSString's "
                        "stringWithContentsOfFile:htmlPath "
                        f"encoding:({utf8}) |error|:(missing value)"
                    ),
                    (
                        "set textNS to current application's NSString's "
                        "stringWithContentsOfFile:textPath "
                        f"encoding:({utf8}) |error|:(missing value)"
                    ),
                    (
                        "if htmlNS is missing value or textNS is missing value "
                        'then error "failed to read HTML/text temp files"'
                    ),
                    f"set htmlData to htmlNS's dataUsingEncoding:({utf8})",
                    (
                        "set pb to current application's "
                        "NSPasteboard's generalPasteboard()"
                    ),
                    "pb's clearContents()",
                    "set htmlType to current application's NSPasteboardTypeHTML",
                    "set strType to current application's NSPasteboardTypeString",
                    "pb's declareTypes:{htmlType, strType} owner:(missing value)",
                    "set okHtml to pb's setData:htmlData forType:htmlType",
                    "set okText to pb's setString:textNS forType:strType",
                    (
                        "if okHtml is false or okText is false then "
                        'error "NSPasteboard refused HTML or plain-text dual '
                        'offer"'
                    ),
                    'return "ok"',
                ]
            ),
            encoding="utf-8",
        )
        try:
            result = subprocess.run(
                ["osascript", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise ClipboardContentError(
                f"macOS HTML+text pasteboard write failed: {exc}"
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise ClipboardContentError(
                "macOS HTML+text pasteboard write failed"
                + (f": {detail}" if detail else "")
            )


def _default_html_clipboard_writer(html: str, text: str) -> None:
    """Platform-selected dual-offer writer; Darwin uses NSPasteboard via osascript."""
    if sys.platform == "darwin":
        _macos_html_clipboard_writer(html, text)
        return
    raise ClipboardContentError(
        "copy_html native dual-offer writer is not available on this platform "
        f"({sys.platform}); need a usable desktop session with a multi-type "
        "HTML+text helper (Linux X11: multi-type-capable xclip; Wayland: "
        "multi-type-capable helper on a named compositor; Windows desktop: "
        "HTML Format + Unicode text), or inject a writer with "
        "set_html_clipboard_writer for tests"
    )


_html_clipboard_writer: Callable[[str, str], None] = _default_html_clipboard_writer


def set_html_clipboard_writer(
    writer: Callable[[str, str], None] | None,
) -> None:
    """Inject an HTML+plain-text dual-offer writer (tests / fakes)."""
    global _html_clipboard_writer
    _html_clipboard_writer = (
        _default_html_clipboard_writer if writer is None else writer
    )


def _validate_copy_html_args(html: object, text: object) -> tuple[str, str]:
    """Reject invalid HTML/text before any clipboard replace (fail-before-replace).

    Empty HTML (no usable fragment after strip) is invalid. ``text`` must be a
    non-empty ``str``; the plain-text alternative is caller-supplied and is not
    synthesized from HTML.
    """
    if not isinstance(html, str) or not isinstance(text, str):
        raise ClipboardContentError(
            "copy_html requires html and text as str "
            f"(got html={type(html).__name__}, text={type(text).__name__})"
        )
    if not html.strip():
        raise ClipboardContentError(
            "copy_html requires a non-empty HTML fragment "
            "(empty or whitespace-only HTML is invalid)"
        )
    if text == "":
        raise ClipboardContentError(
            "copy_html requires a non-empty plain-text alternative"
        )
    return html, text


def copy_html(html: str, text: str) -> None:
    """Publish HTML and a matching plain-text alternative as one clipboard offer.

    Does not require the optional ``clipboard[images]`` extra. Failures raise
    ``ClipboardContentError``. Invalid arguments are rejected before the
    writer runs. On macOS Aqua the default writer publishes both types as one
    ``NSPasteboard`` offer (via ``osascript`` / AppKit). Other platforms still
    need an injected writer via ``set_html_clipboard_writer`` until their
    native adapters land. Writers must publish both representations together;
    inability to offer both, or transfer failure, must surface as
    ``ClipboardContentError`` (not silent text-only success).
    """
    html, text = _validate_copy_html_args(html, text)
    try:
        _html_clipboard_writer(html, text)
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard HTML+text write failed: {exc}") from exc


@contextmanager
def _temporary_png_offer(image: Image.Image) -> Iterator:
    """Yield a PNG path kept alive until the helper has finished reading it."""
    with tempfile.TemporaryDirectory(prefix="clipboard-copy-image-") as raw:
        path = Path(raw) / "offer.png"
        image.save(path, format="PNG")
        yield path


def _helper_failure_detail(result) -> str:
    return (result.stderr or result.stdout or "").strip() or "unknown error"


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
                f"osascript clipboard write failed: {_helper_failure_detail(result)}"
            )


def _xclip_clipboard_targets() -> bytes:
    """Return CLIPBOARD TARGETS bytes, or empty on helper failure."""
    import subprocess

    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"],
            capture_output=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return b""
    if result.returncode != 0:
        return b""
    return result.stdout or b""


def _wait_xclip_image_png_offer(*, timeout_s: float = 5.0) -> None:
    """Block until CLIPBOARD advertises ``image/png``, or raise."""
    import time

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if b"image/png" in _xclip_clipboard_targets():
            return
        time.sleep(0.05)
    raise OSError("xclip clipboard write did not publish image/png in time")


def _write_linux_xclip(image: Image.Image) -> None:
    """Publish PNG bytes on X11 CLIPBOARD via ``xclip`` (``image/png``).

    Feeds PNG on stdin and leaves ``xclip`` running as the CLIPBOARD owner so
    the writing Python process can exit while the offer stays pasteable
    (issue #5 writer-exit). Waiting for ``xclip`` to exit hangs under Xvfb;
    instead wait until TARGETS includes ``image/png``.
    """
    import subprocess

    png_bytes = _png_bytes(image)
    try:
        proc = subprocess.Popen(
            [
                "xclip",
                "-selection",
                "clipboard",
                "-t",
                "image/png",
                "-i",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        raise OSError(
            "xclip is required for clipboard image write on Linux X11; "
            "install xclip and ensure it is on PATH"
        ) from exc
    assert proc.stdin is not None
    try:
        proc.stdin.write(png_bytes)
        proc.stdin.close()
    except BrokenPipeError as exc:
        raise OSError("xclip clipboard write failed: broken pipe") from exc
    exit_code = proc.poll()
    if exit_code not in (None, 0):
        raise OSError(f"xclip clipboard write failed: exit {exit_code}")
    _wait_xclip_image_png_offer()


def _is_linux_wayland() -> bool:
    import os

    session = (os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
    return session == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def _write_linux_wl_copy(image: Image.Image) -> None:
    """Publish PNG bytes on Wayland via ``wl-copy`` (``image/png``).

    ``wl-copy`` reads stdin, then the foreground helper exits while a
    background owner keeps the offer pasteable after the writing Python
    process exits (issue #5 writer-exit).
    """
    import subprocess

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
    import sys

    if sys.platform == "darwin":
        _write_macos_pngf(image)
        return
    if sys.platform.startswith("linux"):
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


def _raise_image_failure(exc: BaseException, *, operation: str) -> NoReturn:
    raise ClipboardImageError(f"clipboard image {operation} failed: {exc}") from exc


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


def paste_image() -> Image.Image | None:
    """Return a Pillow Image from the clipboard, or None when none is offered.

    Requires the optional ``clipboard[images]`` extra (Pillow). The read does
    not modify clipboard contents. Failures other than ordinary absence raise
    ``ClipboardImageError`` (access, helper, transfer, or malformed data).

    Non-image clipboard offers — including a Windows filename / file-list
    result from ``ImageGrab.grabclipboard`` and URL-only strings — are
    ordinary absence (``None``). Paths from those offers are not opened.
    """
    Image = _pillow_image("paste_image")

    try:
        result = _grabclipboard()
    except (OSError, NotImplementedError) as exc:
        # Includes PermissionError, ChildProcessError, UnidentifiedImageError.
        _raise_image_failure(exc, operation="read")

    if isinstance(result, Image.Image):
        return result

    # Image-typed payload that ImageGrab would normally open before returning.
    if isinstance(result, (bytes, bytearray, memoryview)):
        try:
            image = Image.open(BytesIO(bytes(result)))
            image.load()
        except OSError as exc:
            _raise_image_failure(exc, operation="read")
        return image

    # list[str], URL strings, None, and other non-image offers → absence.
    return None


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

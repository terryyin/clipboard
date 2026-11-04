"""Linux copy_image writers: X11 ``xclip`` and Wayland ``wl-copy`` PNG owners.

Both start their helper through the shared owner launcher in
``clipboard._desktop`` (an unlinked temp-file stdin, own session) and share
one 10 s bound with ``copy`` / ``copy_files``; each confirms its own offer
(X11: exact ``image/png`` read-back; Wayland: wl-copy's foreground exit).
Failures raise ``OSError`` for ``copy_image`` to map to ``ClipboardImageError``.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from io import BytesIO
from typing import TYPE_CHECKING

from clipboard._desktop import _start_helper_owner, _stop_helper_owner
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
_WL_COPY_IMAGE_WRITE_CMD = ["wl-copy", "--type", _PNG]
# Same bound on Wayland, across launch, hand-over and wl-copy's foreground exit.
_WAYLAND_IMAGE_WRITE_TIMEOUT_S = _LINUX_TEXT_TIMEOUT_S


def _png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _start_png_owner(cmd: list[str], png_bytes: bytes, log, missing: str):
    """Launch the PNG's owner; a missing helper raises ``OSError(missing)``."""
    try:
        return _start_helper_owner(cmd, png_bytes, log)
    except FileNotFoundError as exc:
        raise OSError(missing) from exc
    except OSError as exc:
        raise OSError(f"{cmd[0]} clipboard write could not start ({exc})") from exc


def _png_owner_exit_error(cmd: list[str], status: int, log) -> OSError:
    return OSError(
        f"{cmd[0]} clipboard write failed: {' '.join(cmd)} exited with status "
        f"{status}" + _helper_log_suffix(log)
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
        proc = _start_png_owner(
            _XCLIP_IMAGE_WRITE_CMD,
            png_bytes,
            log,
            "xclip is required for clipboard image write on Linux X11; "
            "install xclip and ensure it is on PATH",
        )
        while True:
            status = proc.poll()
            if status not in (None, 0):
                raise _png_owner_exit_error(_XCLIP_IMAGE_WRITE_CMD, status, log)
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

    ``wl-copy`` reads the PNG through the shared owner launcher (own session,
    never a pipe), then the foreground helper exits while a background owner
    keeps the offer pasteable after the writing Python process exits (issue
    #5 writer-exit). One 10 s bound covers launch, hand-over and the
    foreground exit; when it passes, the owner's session is stopped and
    ``OSError`` names ``wl-copy``, the bound and its stderr.
    """
    png_bytes = _png_bytes(image)
    command = " ".join(_WL_COPY_IMAGE_WRITE_CMD)
    deadline = time.monotonic() + _WAYLAND_IMAGE_WRITE_TIMEOUT_S
    # stderr goes to an unlinked file, never a pipe the background owner holds.
    with tempfile.TemporaryFile() as log:
        proc = _start_png_owner(
            _WL_COPY_IMAGE_WRITE_CMD,
            png_bytes,
            log,
            "wl-copy is required for clipboard image write on Linux Wayland; "
            "install wl-clipboard and ensure wl-copy is on PATH",
        )
        try:
            status = proc.wait(
                timeout=_remaining(deadline, _WAYLAND_IMAGE_WRITE_TIMEOUT_S)
            )
        except subprocess.TimeoutExpired as exc:
            _stop_helper_owner(proc)
            raise OSError(
                f"wl-copy clipboard write failed: {command} did not finish within "
                f"the {_WAYLAND_IMAGE_WRITE_TIMEOUT_S:g}s bound (compositor stalled "
                "or not answering)" + _helper_log_suffix(log)
            ) from exc
        if status != 0:
            raise _png_owner_exit_error(_WL_COPY_IMAGE_WRITE_CMD, status, log)

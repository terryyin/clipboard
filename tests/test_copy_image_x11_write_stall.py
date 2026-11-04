"""Real-process stall bound for copy_image's Linux X11 ``xclip`` writer.

Drives a ``sys.executable`` owner that never reads stdin (a stalled-display
stand-in) through public ``copy_image``: a PNG larger than a typical pipe
buffer must not hang, and a previous owner still listing ``image/png`` must
not pass for the new offer. ``xclip`` reads are stubbed at
``subprocess.run`` so no desktop is needed.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

import pytest
from PIL import Image

import clipboard
from clipboard import _image_write

# Typical pipe buffer; a PNG larger than this blocked the old pipe write.
_PIPE_BUFFER_FLOOR = 64 * 1024
_STALL_CMD = [sys.executable, "-c", "import time; time.sleep(3600)"]


def _noise_png_image(side: int) -> Image.Image:
    """An RGB raster whose PNG barely compresses (random bytes)."""
    return Image.frombytes("RGB", (side, side), os.urandom(side * side * 3))


def _run_stalled_copy(monkeypatch, image, *, run_xclip, bound_s=1.0):
    """copy_image through ``_write_linux_xclip`` with a non-reading owner.

    Returns ``(outcome, owners, signalled)``; ``run_xclip`` answers every
    ``xclip`` read (TARGETS / ``-o``) the writer makes.
    """
    clipboard.set_image_writeclipboard(_image_write._write_linux_xclip)
    monkeypatch.setattr(_image_write, "_X11_IMAGE_WRITE_TIMEOUT_S", bound_s)

    owners: list[subprocess.Popen] = []
    launched: list[list[str]] = []
    real_popen = subprocess.Popen

    def popen(cmd, *args, **kwargs):
        launched.append(list(cmd))
        # The xclip owner becomes the never-reading stand-in.
        proc = real_popen(_STALL_CMD, *args, **kwargs)
        owners.append(proc)
        return proc

    monkeypatch.setattr(subprocess, "Popen", popen)

    real_run = subprocess.run

    def run(cmd, *args, **kwargs):
        if cmd and cmd[0] == "xclip":
            return run_xclip(list(cmd))
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)

    signalled: list[int] = []

    def killpg(pid, sig):
        # os.killpg is POSIX-only; terminate our own child directly.
        signalled.append(pid)
        for proc in owners:
            if proc.pid == pid:
                proc.kill()

    monkeypatch.setattr(os, "killpg", killpg, raising=False)

    watchdog_s = bound_s + 5.0
    outcome: dict = {"error": None, "elapsed": None, "returned": False}

    def run_copy():
        started = time.monotonic()
        try:
            clipboard.copy_image(image)
            outcome["returned"] = True
        except Exception as exc:  # noqa: BLE001 — capture for the watchdog thread
            outcome["error"] = exc
        outcome["elapsed"] = time.monotonic() - started

    thread = threading.Thread(target=run_copy, daemon=True)
    thread.start()
    try:
        thread.join(timeout=watchdog_s)
        assert not thread.is_alive(), f"copy_image() still blocked past {watchdog_s:g}s"
    finally:
        for proc in owners:
            proc.kill()
            proc.wait(timeout=10)
        thread.join(timeout=10)
    assert launched and launched[0][0] == "xclip", launched
    return outcome, owners, signalled


def _assert_bounded_failure(outcome, owners, signalled, *, bound_s=1.0):
    assert not outcome["returned"], "copy_image() reported success"
    error = outcome["error"]
    assert isinstance(error, clipboard.ClipboardImageError), error
    message = str(error)
    assert "xclip" in message
    assert f"{bound_s:g}s bound" in message
    assert outcome["elapsed"] is not None and outcome["elapsed"] < bound_s + 2.0
    assert len(owners) == 1
    assert signalled == [owners[0].pid], "owner session was not stopped"


def test_large_png_raises_within_bound_when_owner_never_reads_stdin(
    monkeypatch, restore_image_writeclipboard
):
    """Example 1: a PNG above a pipe buffer must not hang copy_image()."""
    image = _noise_png_image(200)
    assert len(_image_write._png_bytes(image)) > _PIPE_BUFFER_FLOOR

    def unowned(cmd):
        no_owner = b"xclip: Error: There is no owner for the CLIPBOARD selection\n"
        return subprocess.CompletedProcess(cmd, 1, b"", no_owner)

    outcome, owners, signalled = _run_stalled_copy(
        monkeypatch, image, run_xclip=unowned
    )
    _assert_bounded_failure(outcome, owners, signalled)


def test_previous_image_owner_does_not_pass_for_the_new_png(
    monkeypatch, restore_image_writeclipboard
):
    """Example 2: an earlier owner listing image/png is not the new offer."""
    image = Image.new("RGB", (8, 8), color="red")
    previous_png = _image_write._png_bytes(Image.new("RGB", (8, 8), color="blue"))
    assert previous_png != _image_write._png_bytes(image)

    def previous_owner(cmd):
        target = cmd[cmd.index("-t") + 1] if "-t" in cmd else ""
        if target == "TARGETS":
            return subprocess.CompletedProcess(cmd, 0, b"TARGETS\nimage/png\n", b"")
        if target == "image/png":
            return subprocess.CompletedProcess(cmd, 0, previous_png, b"")
        return subprocess.CompletedProcess(cmd, 1, b"", b"unsupported target\n")

    outcome, owners, signalled = _run_stalled_copy(
        monkeypatch, image, run_xclip=previous_owner
    )
    _assert_bounded_failure(outcome, owners, signalled)


def test_unwritable_temp_file_raises_image_error_before_any_helper_starts(
    unwritable_temp_files, restore_image_writeclipboard
):
    """The payload file cannot be written → ClipboardImageError, no xclip run."""
    clipboard.set_image_writeclipboard(_image_write._write_linux_xclip)

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(Image.new("RGB", (1, 1), color="red"))

    assert isinstance(raised.value.__cause__, OSError)
    assert "xclip" in str(raised.value)
    assert unwritable_temp_files == []

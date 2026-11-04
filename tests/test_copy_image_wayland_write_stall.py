"""Real-process stall bound for copy_image's Linux Wayland ``wl-copy`` writer.

Drives a ``sys.executable`` stand-in for a ``wl-copy`` whose compositor never
answers (it writes one line to stderr and never exits) through public
``copy_image`` with a PNG larger than a typical pipe buffer: the write must
raise within the bound, quote the helper's stderr, and stop the owner's
session. No compositor or wl-clipboard is needed.
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
from clipboard import _image_write_linux

# Typical pipe buffer; a PNG larger than this blocked a pipe hand-over.
_PIPE_BUFFER_FLOOR = 64 * 1024
_STDERR_LINE = "wl-copy stand-in: compositor is not answering"
_STALL_CMD = [
    sys.executable,
    "-c",
    "import sys, time; "
    f"sys.stderr.write({_STDERR_LINE!r} + '\\n'); sys.stderr.flush(); "
    "time.sleep(3600)",
]
_BOUND_S = 2.0


def _noise_png_image(side: int) -> Image.Image:
    """An RGB raster whose PNG barely compresses (random bytes)."""
    return Image.frombytes("RGB", (side, side), os.urandom(side * side * 3))


def test_stalled_wl_copy_raises_within_bound_quoting_its_stderr(
    monkeypatch, restore_image_writeclipboard
):
    """Example 4: wl-copy never finishes → ClipboardImageError within the bound."""
    image = _noise_png_image(200)
    assert len(_image_write_linux._png_bytes(image)) > _PIPE_BUFFER_FLOOR
    clipboard.set_image_writeclipboard(_image_write_linux._write_linux_wl_copy)
    monkeypatch.setattr(_image_write_linux, "_WAYLAND_IMAGE_WRITE_TIMEOUT_S", _BOUND_S)

    owners: list[subprocess.Popen] = []
    launches: list[dict] = []
    real_popen = subprocess.Popen

    def popen(cmd, *args, **kwargs):
        launches.append({"cmd": list(cmd), **kwargs})
        # The wl-copy owner becomes the never-finishing stand-in.
        proc = real_popen(_STALL_CMD, *args, **kwargs)
        owners.append(proc)
        return proc

    monkeypatch.setattr(subprocess, "Popen", popen)

    def run(cmd, *args, **kwargs):
        raise AssertionError(f"no helper run expected: {cmd}")

    monkeypatch.setattr(subprocess, "run", run)

    signalled: list[int] = []

    def killpg(pid, sig):
        # os.killpg is POSIX-only; terminate our own child directly.
        signalled.append(pid)
        for proc in owners:
            if proc.pid == pid:
                proc.kill()

    monkeypatch.setattr(os, "killpg", killpg, raising=False)

    watchdog_s = _BOUND_S + 5.0
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

    [launch] = launches
    assert launch["cmd"][0] == "wl-copy"
    assert launch["start_new_session"] is True
    assert launch["stdin"] is not subprocess.PIPE

    assert not outcome["returned"], "copy_image() reported success"
    error = outcome["error"]
    assert isinstance(error, clipboard.ClipboardImageError), error
    message = str(error)
    assert "wl-copy" in message
    assert f"{_BOUND_S:g}s bound" in message
    assert _STDERR_LINE in message
    assert outcome["elapsed"] is not None and outcome["elapsed"] < _BOUND_S + 2.0
    assert signalled == [owners[0].pid], "owner session was not stopped"


def test_unwritable_temp_file_raises_image_error_before_any_helper_starts(
    unwritable_temp_files, restore_image_writeclipboard
):
    """The payload file cannot be written → ClipboardImageError, no wl-copy run."""
    clipboard.set_image_writeclipboard(_image_write_linux._write_linux_wl_copy)

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(Image.new("RGB", (1, 1), color="red"))

    assert isinstance(raised.value.__cause__, OSError)
    assert "wl-copy" in str(raised.value)
    assert unwritable_temp_files == []

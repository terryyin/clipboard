"""Real-process stall bound for copy_files' Linux X11 ``xclip`` writer.

Drives a ``sys.executable`` owner that never reads stdin so a URI list larger
than a typical pipe buffer cannot hang Python. Companion to the FakeX11Files
suite in ``test_copy_files_x11_writer.py``.
"""

from __future__ import annotations

import os
import shutil
import sys
import threading
import time

import clipboard
from clipboard import _desktop, _files_native_x11_writer
from clipboard._files_offer import _uri_list_body

SESSION_VARS = ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE")
# Typical pipe buffer; a URI list larger than this blocked the old pipe write.
_PIPE_BUFFER_FLOOR = 64 * 1024


def test_large_uri_list_raises_within_bound_when_owner_never_reads_stdin(
    monkeypatch, tmp_path
):
    """Real non-reading owner: body above a pipe buffer must not hang Python."""
    for name in SESSION_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name, *a, **k: f"/usr/bin/{name}" if name == "xclip" else None,
    )
    # Sleep forever; never read stdin (stalled-display stand-in).
    stall_cmd = [sys.executable, "-c", "import time; time.sleep(3600)"]
    monkeypatch.setattr(
        _files_native_x11_writer, "_XCLIP_URI_LIST_WRITE_CMD", stall_cmd
    )
    monkeypatch.setattr(_files_native_x11_writer, "_xclip_targets_lenient", lambda: b"")
    bound_s = 1.0
    monkeypatch.setattr(_files_native_x11_writer, "_X11_FILES_WRITE_TIMEOUT_S", bound_s)

    killed: list[int] = []
    real_killpg = getattr(os, "killpg", None)

    def killpg(pid, sig):
        killed.append(pid)
        try:
            if real_killpg is not None:
                real_killpg(pid, sig)
            else:
                os.kill(pid, sig)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    monkeypatch.setattr(_desktop.os, "killpg", killpg, raising=False)

    # ~2000 long paths → body well above a typical 64 KiB pipe buffer.
    paths = [str(tmp_path / f"{'n' * 80}_{i}.txt") for i in range(2000)]
    body = _uri_list_body(paths)
    assert len(body) > _PIPE_BUFFER_FLOOR

    margin_s = 2.0
    outcome: dict = {"error": None, "elapsed": None}

    def run_writer():
        started = time.monotonic()
        try:
            _files_native_x11_writer._x11_files_clipboard_writer(paths)
        except Exception as exc:  # noqa: BLE001 — capture for the watchdog thread
            outcome["error"] = exc
        outcome["elapsed"] = time.monotonic() - started

    thread = threading.Thread(target=run_writer)
    thread.start()
    thread.join(timeout=bound_s + margin_s + 3.0)
    assert not thread.is_alive(), (
        f"writer still blocked past {bound_s + margin_s + 3.0:g}s watchdog"
    )
    error = outcome["error"]
    assert isinstance(error, clipboard.ClipboardContentError), error
    message = str(error)
    assert "did not offer the file list as text/uri-list" in message
    assert f"{bound_s:g}s bound" in message
    assert outcome["elapsed"] is not None and outcome["elapsed"] < bound_s + margin_s
    assert killed, "owner process group was not signalled"

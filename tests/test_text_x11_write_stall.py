"""Real-process stall bound for the owned Linux X11 text writer (``xclip``).

Drives a ``sys.executable`` owner that never reads stdin (a stalled-display
stand-in) so text larger than a typical pipe buffer cannot hang ``copy()``.
Companion to the in-memory ``FakeX11`` suite in ``test_text_x11.py``.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time

import clipboard
from clipboard import _text_native_x11

# Typical pipe buffer; text larger than this blocked the old pipe write.
_PIPE_BUFFER_FLOOR = 64 * 1024


def test_large_text_raises_within_bound_when_owner_never_reads_stdin(
    text_session, monkeypatch, tmp_path
):
    """Real non-reading owner: text above a pipe buffer must not hang copy()."""
    text_session("linux", {"DISPLAY": ":0"}, ("xclip",))
    # Sleep forever; never read stdin.
    stall_cmd = [sys.executable, "-c", "import time; time.sleep(3600)"]
    monkeypatch.setattr(_text_native_x11, "_XCLIP_WRITE_CMD", stall_cmd)
    # Read-backs never serve: the helper does not exist.
    missing = str(tmp_path / "no-such-xclip")
    monkeypatch.setattr(
        _text_native_x11, "_xclip_read_cmd", lambda target: [missing, target]
    )
    bound_s = 1.0
    monkeypatch.setattr(_text_native_x11, "_X11_TEXT_WRITE_TIMEOUT_S", bound_s)

    owners: list[subprocess.Popen] = []
    real_popen = subprocess.Popen

    def popen(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        owners.append(proc)
        return proc

    monkeypatch.setattr(subprocess, "Popen", popen)

    signalled: list[int] = []

    def killpg(pid, sig):
        # os.killpg is POSIX-only; terminate our own child directly.
        signalled.append(pid)
        for proc in owners:
            if proc.pid == pid:
                proc.kill()

    monkeypatch.setattr(_text_native_x11.os, "killpg", killpg, raising=False)

    text = "a" * 200_000
    assert len(text.encode("utf-8")) > _PIPE_BUFFER_FLOOR

    margin_s = 2.0
    watchdog_s = bound_s + margin_s + 3.0
    outcome: dict = {"error": None, "elapsed": None}

    def run_copy():
        started = time.monotonic()
        try:
            clipboard.copy(text)
        except Exception as exc:  # noqa: BLE001 — capture for the watchdog thread
            outcome["error"] = exc
        outcome["elapsed"] = time.monotonic() - started

    thread = threading.Thread(target=run_copy, daemon=True)
    thread.start()
    try:
        thread.join(timeout=watchdog_s)
        assert not thread.is_alive(), f"copy() still blocked past {watchdog_s:g}s"
    finally:
        for proc in owners:
            proc.kill()
            proc.wait(timeout=10)
        thread.join(timeout=10)

    error = outcome["error"]
    assert isinstance(error, clipboard.ClipboardContentError), error
    message = str(error)
    assert "did not serve the text as UTF8_STRING" in message
    assert f"{bound_s:g}s bound" in message
    assert outcome["elapsed"] is not None and outcome["elapsed"] < bound_s + margin_s
    assert len(owners) == 1
    assert signalled == [owners[0].pid], "owner process group was not signalled"

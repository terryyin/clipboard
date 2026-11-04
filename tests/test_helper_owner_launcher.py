"""The shared background clipboard-owner launcher in ``clipboard._desktop``.

``_start_helper_owner`` hands its payload over through an unlinked temporary
file (never a pipe), in the helper's own session with stdout discarded and
stderr in the caller's log; ``OSError`` propagates before any helper starts.
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile

import pytest

from clipboard import _desktop

CMD = ["xclip", "-selection", "clipboard", "-i"]


def test_payload_is_a_file_stdin_in_its_own_session(monkeypatch):
    launches: list[dict] = []
    owner = object()

    def popen(cmd, **kwargs):
        stdin = kwargs["stdin"]
        launches.append({"cmd": cmd, "payload": stdin.read(), **kwargs})
        return owner

    monkeypatch.setattr(subprocess, "Popen", popen)
    with tempfile.TemporaryFile() as log:
        assert _desktop._start_helper_owner(CMD, b"payload \x00 bytes", log) is owner

    [launch] = launches
    assert launch["cmd"] == CMD
    assert launch["payload"] == b"payload \x00 bytes"
    assert launch["stdin"] is not subprocess.PIPE
    assert launch["stdout"] is subprocess.DEVNULL
    assert launch["stderr"] is log
    assert launch["start_new_session"] is True


def test_unwritable_temp_file_propagates_before_popen(unwritable_temp_files):
    with pytest.raises(OSError) as raised:
        _desktop._start_helper_owner(CMD, b"payload", log=None)

    assert raised.value.errno == 28
    assert unwritable_temp_files == []


def test_missing_helper_propagates_for_the_caller_to_map(monkeypatch):
    def popen(cmd, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", cmd[0])

    monkeypatch.setattr(subprocess, "Popen", popen)
    with tempfile.TemporaryFile() as log, pytest.raises(FileNotFoundError):
        _desktop._start_helper_owner(CMD, b"payload", log)


class _Owner:
    pid = 4242


def test_stop_signals_the_owner_session(monkeypatch):
    signalled: list[tuple[int, int]] = []
    # os.killpg is POSIX-only; supply it through the fake.
    monkeypatch.setattr(
        os, "killpg", lambda pid, sig: signalled.append((pid, sig)), raising=False
    )

    _desktop._stop_helper_owner(_Owner())

    assert signalled == [(4242, signal.SIGTERM)]


@pytest.mark.parametrize("gone", [ProcessLookupError, PermissionError])
def test_stop_tolerates_an_owner_already_gone(monkeypatch, gone):
    def killpg(pid, sig):
        raise gone()

    monkeypatch.setattr(os, "killpg", killpg, raising=False)

    _desktop._stop_helper_owner(_Owner())

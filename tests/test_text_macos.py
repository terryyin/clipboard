"""Desktop-free tests for the owned macOS text path (``pbcopy`` / ``pbpaste``).

``subprocess.run`` is replaced by a fake that records argv, environment and
stdin, so no real pasteboard is touched. ``text_session("darwin")`` routes the
public ``copy`` / ``paste`` through the default backend.
"""

import os
import subprocess

import pytest
from fake_pyperclip import FakePyperclip

import clipboard
from clipboard import _text_native_macos

TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "


class FakeHelpers:
    """Stand-in for ``subprocess.run``: an in-memory pasteboard of bytes."""

    def __init__(self):
        self.board = b""
        self.calls = []
        self.error = None
        self.returncode = 0
        self.stderr = b""
        self.stdout = None

    def run(self, cmd, *, input=None, capture_output, check, timeout, env):
        assert capture_output is True and check is False
        self.calls.append({"cmd": cmd, "input": input, "timeout": timeout, "env": env})
        if self.error is not None:
            raise self.error
        if self.returncode != 0:
            return subprocess.CompletedProcess(cmd, self.returncode, b"", self.stderr)
        if cmd == ["pbcopy"]:
            self.board = input
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        assert cmd == ["pbpaste"] and input is None
        out = self.board if self.stdout is None else self.stdout
        return subprocess.CompletedProcess(cmd, 0, out, b"")


@pytest.fixture
def helpers(text_session, monkeypatch):
    fake = FakeHelpers()
    monkeypatch.setattr(_text_native_macos.subprocess, "run", fake.run)
    text_session("darwin")
    fake.pyperclip = FakePyperclip(monkeypatch)
    return fake


def test_copy_runs_pbcopy_with_utf8_bytes_and_forced_locale(helpers, monkeypatch):
    monkeypatch.setenv("LC_ALL", "C")
    monkeypatch.setenv("LANG", "C")
    before = dict(os.environ)

    clipboard.copy(TEXT)

    (call,) = helpers.calls
    assert call["cmd"] == ["pbcopy"]
    assert call["input"] == TEXT.encode("utf-8")
    assert call["timeout"] == _text_native_macos._MACOS_TEXT_WRITE_TIMEOUT_S
    assert call["env"] == {**before, "LC_ALL": "en_US.UTF-8"}
    assert dict(os.environ) == before
    assert helpers.pyperclip.writes == []


def test_paste_runs_pbpaste_and_decodes_utf8_exactly(helpers, monkeypatch):
    monkeypatch.delenv("LC_ALL", raising=False)
    before = dict(os.environ)
    helpers.board = "  héllo 👋 ﾃｽﾄ\r\nline 2\n\t".encode()

    assert clipboard.paste() == "  héllo 👋 ﾃｽﾄ\r\nline 2\n\t"

    (call,) = helpers.calls
    assert call["cmd"] == ["pbpaste"]
    assert call["input"] is None
    assert call["timeout"] == 15.0
    assert call["env"] == {**before, "LC_ALL": "en_US.UTF-8"}
    assert dict(os.environ) == before
    assert helpers.pyperclip.reads == 0


def test_round_trip_and_empty_text(helpers):
    clipboard.copy(TEXT)
    assert clipboard.paste() == TEXT
    clipboard.copy("")
    assert helpers.calls[-1]["input"] == b""
    result = clipboard.paste()
    assert result == ""
    assert type(result) is str


def test_cleared_pasteboard_reads_empty_string(helpers):
    helpers.stdout = b""

    assert clipboard.paste() == ""


def test_undecodable_output_is_a_content_error(helpers):
    helpers.stdout = b"h\x8ello"

    with pytest.raises(clipboard.ClipboardContentError, match="not UTF-8") as caught:
        clipboard.paste()
    assert isinstance(caught.value.__cause__, UnicodeDecodeError)


def test_rejected_text_never_runs_pbcopy(helpers):
    for bad in ("a\x00b", "\ud800"):
        with pytest.raises(clipboard.ClipboardContentError):
            clipboard.copy(bad)
    assert helpers.calls == []


@pytest.mark.parametrize("operation", ["write", "read"])
def test_non_zero_exit_quotes_helper_stderr(helpers, operation):
    helpers.returncode = 1
    helpers.stderr = b"pasteboard server unavailable\n"

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        _call(operation)
    message = str(caught.value)
    assert f"text {operation} failed" in message
    assert "exited 1" in message
    assert "pasteboard server unavailable" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)
    assert caught.value.__cause__.returncode == 1


@pytest.mark.parametrize("operation", ["write", "read"])
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (subprocess.TimeoutExpired("pbcopy", 15.0), "timed out"),
        (FileNotFoundError(2, "No such file or directory"), "not found on PATH"),
        (PermissionError(13, "Permission denied"), "Permission denied"),
    ],
)
def test_helper_exceptions_become_content_errors(helpers, operation, error, expected):
    helpers.error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        _call(operation)
    assert caught.value.__cause__ is error
    assert helpers.pyperclip.writes == []
    assert helpers.pyperclip.reads == 0


def _call(operation):
    if operation == "write":
        clipboard.copy("x")
    else:
        clipboard.paste()

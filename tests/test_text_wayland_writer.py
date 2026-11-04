"""Desktop-free tests for the owned Linux Wayland text writer (wl-copy).

wl-copy and wl-paste run against the in-memory Wayland selection
(``install_fake_wayland``), so no compositor is touched; the public ``copy``
runs on the default backend and its text reaches wl-copy through the shared
owner launcher.
"""

import subprocess

import pytest
from fake_wl_clipboard_text import STALE_SOCKET, TEXT, install_fake_wayland

import clipboard


@pytest.fixture
def wayland(text_session, monkeypatch):
    return install_fake_wayland(text_session, monkeypatch)


def test_copy_hands_utf8_to_wl_copy_with_an_explicit_text_type(wayland):
    wayland.offers = {"text/plain": b"previous"}

    clipboard.copy(TEXT)

    (proc,) = wayland.popens
    assert proc.cmd == ["wl-copy", "--type", "text/plain;charset=utf-8"]
    # Through the shared launcher: a file stdin, never a pipe.
    assert proc.stdin is not subprocess.PIPE
    assert proc.input == TEXT.encode("utf-8")
    (bound,) = wayland.wait_timeouts
    assert 9.0 < bound <= 10.0
    assert wayland.pyperclip.writes == []
    assert clipboard.paste() == TEXT


def test_copy_empty_clears_the_selection_then_paste_is_empty(wayland):
    wayland.offers = {"text/plain": b"keep"}

    clipboard.copy("")

    (proc,) = wayland.popens
    assert proc.cmd == ["wl-copy", "--clear"]
    assert proc.stdin is subprocess.DEVNULL
    assert proc.input is None
    assert clipboard.paste() == ""


def test_rejected_text_never_starts_wl_copy(wayland):
    for bad in ("a\x00b", "\ud800"):
        with pytest.raises(clipboard.ClipboardContentError):
            clipboard.copy(bad)
    assert wayland.popens == []


@pytest.mark.parametrize("text", ["x", ""])
def test_wl_copy_failure_raises_quoting_its_stderr(wayland, text):
    wayland.offers = {"text/plain": b"previous"}
    wayland.copy_exit = (1, STALE_SOCKET)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy(text)
    message = str(caught.value)
    assert "Wayland clipboard text write failed" in message
    assert "exited with status 1" in message
    assert "Failed to connect to a Wayland server" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)
    assert wayland.offers == {"text/plain": b"previous"}


def test_stalled_wl_copy_is_killed_and_raises_after_the_bound(wayland):
    wayland.stalls = True

    with pytest.raises(
        clipboard.ClipboardContentError, match="did not finish within the 10s bound"
    ) as caught:
        clipboard.copy("x")
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert wayland.popens[0].killed is True


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            FileNotFoundError(2, "No such file", "wl-copy"),
            "wl-copy was not found on PATH; install wl-clipboard",
        ),
        (PermissionError(13, "Permission denied"), "Permission denied"),
    ],
)
def test_writer_launch_failures_become_content_errors(wayland, error, expected):
    wayland.popen_error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        clipboard.copy("x")
    assert caught.value.__cause__ is error
    assert wayland.pyperclip.writes == []


def test_unwritable_temp_file_raises_before_wl_copy_starts(
    wayland, unwritable_temp_files
):
    wayland.offers = {"text/plain": b"previous"}

    with pytest.raises(clipboard.ClipboardContentError, match="wl-copy") as caught:
        clipboard.copy("x")
    assert isinstance(caught.value.__cause__, OSError)
    assert unwritable_temp_files == []
    assert wayland.offers == {"text/plain": b"previous"}
    assert wayland.pyperclip.writes == []

"""Desktop-free failure and bound tests for Wayland ``copy_primary`` /
``paste_primary``.

The unsupported wording is wl-clipboard 2.2.1's own. Sway with
``primary_selection disabled`` has recorded conflicting observations (one
drop while ``wl-copy --primary`` exits 0, one write-through); ``drops_primary``
stands in for the drop observation. Every failure names the primary
selection and leaves CLIPBOARD neither read nor changed.
"""

import subprocess

import pytest
from fake_wl_clipboard_text import install_fake_wayland, text_offer

import clipboard
from clipboard import _text_native_wayland_writer

UTF8 = "text/plain;charset=utf-8"
P_LIST = ["wl-paste", "--primary", "--list-types"]
P_READ = ["wl-paste", "--primary", "-n", "-t", UTF8]
P_WRITE = ["wl-copy", "--primary", "--type", UTF8]
STALE_SOCKET = b"Failed to connect to a Wayland server: No such file or directory\n"


@pytest.fixture
def wayland(text_session, monkeypatch):
    fake = install_fake_wayland(text_session, monkeypatch)
    fake.offers = text_offer("copied")
    fake.primary = text_offer("selected")
    return fake


def _unsupported_error(call):
    with pytest.raises(clipboard.ClipboardContentError) as caught:
        call()
    message = str(caught.value)
    assert "primary selection" in message
    assert "Wayland" in message
    assert "support" in message
    return caught.value


def test_unsupported_primary_raises_and_clipboard_is_neither_read_nor_changed(
    wayland,
):
    wayland.primary_unsupported = True

    error = _unsupported_error(clipboard.paste_primary)
    assert " ".join(P_LIST) in str(error)
    error = _unsupported_error(lambda: clipboard.copy_primary("x"))
    assert " ".join(P_WRITE) in str(error)

    assert wayland.only_primary_ran()
    assert [proc.cmd for proc in wayland.popens] == [P_WRITE]
    assert wayland.offers == text_offer("copied")
    assert wayland.pyperclip.reads == 0
    assert wayland.pyperclip.writes == []


def test_unsupported_is_not_nothing_selected(wayland):
    wayland.primary = None
    assert clipboard.paste_primary() == ""

    wayland.primary_unsupported = True
    _unsupported_error(clipboard.paste_primary)


def test_dropped_write_raises_after_the_bound_instead_of_succeeding(
    wayland, monkeypatch
):
    monkeypatch.setattr(
        _text_native_wayland_writer, "_WAYLAND_TEXT_WRITE_TIMEOUT_S", 0.2
    )
    wayland.drops_primary = True
    wayland.primary = None

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_primary("x")
    message = str(caught.value)
    assert "primary selection" in message
    assert "0.2s bound" in message
    assert " ".join(P_READ) in message
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert wayland.only_primary_ran()
    assert len(wayland.calls) >= 2  # polled, not a single read
    assert wayland.offers == text_offer("copied")


def test_write_and_read_back_share_one_bound(wayland, monkeypatch):
    clock = [100.0, 100.0, 107.5]
    monkeypatch.setattr(
        _text_native_wayland_writer.time,
        "monotonic",
        lambda: clock.pop(0) if clock else 107.5,
    )

    clipboard.copy_primary("x")

    assert wayland.wait_timeouts == [10.0]
    assert [c["timeout"] for c in wayland.calls] == [2.5]


def test_write_failure_names_the_primary_selection(wayland):
    wayland.copy_exit = (1, STALE_SOCKET)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_primary("x")
    message = str(caught.value)
    assert "primary selection" in message
    assert " ".join(P_WRITE) in message
    assert "Failed to connect to a Wayland server" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)
    assert wayland.offers == text_offer("copied")


def test_read_failure_names_the_primary_selection(wayland):
    wayland.run_failure = (1, STALE_SOCKET)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.paste_primary()
    message = str(caught.value)
    assert "primary selection" in message
    assert " ".join(P_LIST) in message
    assert "Failed to connect to a Wayland server" in message


def test_missing_wl_paste_at_run_time_names_the_install_hint(wayland):
    error = FileNotFoundError(2, "No such file", "wl-paste")
    wayland.run_error = error

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.paste_primary()
    assert "wl-clipboard" in str(caught.value)
    assert caught.value.__cause__ is error
    assert wayland.pyperclip.reads == 0

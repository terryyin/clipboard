"""Desktop-free proofs that ``clipboard.wait_for_text_change`` fails fast.

Read failures, including the baseline read, raise at once and are never
retried; invalid arguments raise before the clipboard is read.
"""

from __future__ import annotations

import pytest
from fake_pyperclip import FakePyperclip
from fake_wait_clock import (
    INVALID_WAIT_OPTIONS,
    START,
    install_fake_clock,
    option_id,
    reader_installer,
)

import clipboard
from clipboard import _wait


@pytest.fixture
def clock(monkeypatch):
    return install_fake_clock(monkeypatch)


@pytest.fixture
def reader(clock, restore_text_clipboard):
    return reader_installer(clock)


def test_baseline_read_failure_raises_at_once(clock, reader):
    failure = clipboard.ClipboardContentError("access denied")
    fake = reader(failure, "new")

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_text_change(timeout=10)

    assert raised.value is failure
    assert fake.calls == [START]
    assert clock.sleeps == []


def test_failure_after_several_reads_raises_at_once_never_retried(clock, reader):
    failure = clipboard.ClipboardContentError("helper timed out")
    fake = reader("old", "old", "", failure, "new")

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_text_change(timeout=10)

    assert raised.value is failure
    assert fake.calls == [START, START + 0.5, START + 1.0, START + 1.5]
    assert clock.sleeps == [0.5, 0.5, 0.5]


def test_unexpected_reader_error_is_a_content_error_at_once(clock, reader):
    fake = reader("old", RuntimeError("boom"))

    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.wait_for_text_change(timeout=10)
    assert len(fake.calls) == 2
    assert clock.sleeps == [0.5]


def test_non_str_text_is_a_content_error_at_once(clock, reader):
    fake = reader(b"old")

    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.wait_for_text_change(timeout=10)
    assert fake.calls == [START]


def test_keyboard_interrupt_propagates(clock, reader):
    reader("old", KeyboardInterrupt())

    with pytest.raises(KeyboardInterrupt):
        clipboard.wait_for_text_change(timeout=10)


@pytest.mark.parametrize(("named", "options"), INVALID_WAIT_OPTIONS, ids=option_id)
def test_invalid_argument_raises_before_any_read(clock, reader, named, options):
    fake = reader("old", "new")

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_text_change(**options)

    assert named in str(raised.value)
    assert fake.calls == []
    assert clock.sleeps == []


def test_timeout_is_required(clock, reader):
    fake = reader("old", "new")

    with pytest.raises(TypeError, match="timeout"):
        clipboard.wait_for_text_change()  # type: ignore[call-arg]
    assert fake.calls == []


def test_arguments_are_keyword_only(clock, reader):
    fake = reader("old")

    with pytest.raises(TypeError):
        clipboard.wait_for_text_change(1)  # type: ignore[misc]
    assert fake.calls == []


def test_default_reader_on_a_delegated_session_reads_through_pyperclip(
    clock, monkeypatch, text_session
):
    """The default ``paste`` backend delegating to pyperclip is the observation."""
    fake = FakePyperclip(monkeypatch)
    text_session("cygwin")
    fake.contents = "old"

    def copy_new_on_second_wait(seconds: float) -> None:
        clock.sleep(seconds)
        if len(clock.sleeps) == 2:
            fake.contents = "new"

    monkeypatch.setattr(_wait, "_sleep", copy_new_on_second_wait)

    assert clipboard.wait_for_text_change(timeout=10) == "new"
    assert fake.reads == 3


def test_linux_without_session_raises_at_the_baseline_read(clock, text_session):
    text_session("linux")

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_text_change(timeout=10)

    assert "DISPLAY" in str(raised.value)
    assert clock.sleeps == []
    assert clock.now == START


def test_wait_for_text_change_is_public():
    assert "wait_for_text_change" in clipboard.__all__
    assert callable(clipboard.wait_for_text_change)

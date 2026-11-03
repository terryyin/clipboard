"""Desktop-free Windows ``clear()``: user32 is the scripted ``FakeWin32``.

The default clearer on ``win32`` opens through inspect's bounded
``OpenClipboard`` retry, calls ``EmptyClipboard``, and always closes.
"""

import pytest
from win32_clipboard_fake import ACCESS_DENIED, FakeWin32

import clipboard
from clipboard import _offer_windows

_PRIOR_OFFER = b"Version:0.9\r\n<b>prior</b>"


@pytest.fixture
def windows_clipboard(monkeypatch, restore_clipboard_clearer, fake_platform):
    """Default clearer on a pretend ``win32`` with a scripted user32."""

    def install(**kwargs):
        fake = FakeWin32(envelope=_PRIOR_OFFER, clear_allowed=True, **kwargs)
        fake_platform("win32")
        monkeypatch.setattr(
            _offer_windows, "_load_user32", lambda: (fake.user32, fake.ctypes)
        )
        monkeypatch.setattr(_offer_windows, "_OPEN_RETRY_SLEEP_S", 0.001)
        clipboard.set_clipboard_clearer(None)
        return fake

    return install


def test_win32_default_clearer_opens_empties_and_closes(windows_clipboard):
    fake = windows_clipboard()
    assert clipboard.clear() is None
    assert fake.calls == ["OpenClipboard", "EmptyClipboard", "CloseClipboard"]
    assert fake.envelope is None
    assert not fake.is_open


def test_win32_clear_twice_in_a_row_succeeds(windows_clipboard):
    fake = windows_clipboard()
    assert clipboard.clear() is None
    assert clipboard.clear() is None
    assert fake.calls == ["OpenClipboard", "EmptyClipboard", "CloseClipboard"] * 2
    assert not fake.is_open


def test_empty_clipboard_failure_raises_last_error_and_still_closes(
    windows_clipboard,
):
    fake = windows_clipboard(empty_error=ACCESS_DENIED)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    message = str(excinfo.value)
    assert "EmptyClipboard failed" in message
    assert f"last_error={ACCESS_DENIED}" in message
    assert f"message {ACCESS_DENIED}" in message
    assert fake.calls == ["OpenClipboard", "EmptyClipboard", "CloseClipboard"]
    assert not fake.is_open
    assert fake.envelope == _PRIOR_OFFER


def test_open_failing_until_the_deadline_names_the_held_clipboard(
    windows_clipboard, monkeypatch
):
    monkeypatch.setattr(_offer_windows, "_OPEN_CLIPBOARD_TIMEOUT_S", 0.05)
    fake = windows_clipboard(open_failures=10**9)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    message = str(excinfo.value)
    assert "OpenClipboard failed while clearing the clipboard" in message
    assert "nothing was cleared" in message
    assert "held by another process" in message
    assert f"last_error={ACCESS_DENIED}" in message
    assert "timed out after 0.05s" in message
    assert "set_clipboard_clearer" in message
    assert set(fake.calls) == {"OpenClipboard"}
    assert len(fake.calls) > 1  # retried, not a single attempt
    assert fake.envelope == _PRIOR_OFFER


def test_open_released_before_the_deadline_clears(windows_clipboard):
    fake = windows_clipboard(open_failures=3)
    assert clipboard.clear() is None
    assert fake.calls == ["OpenClipboard"] * 4 + ["EmptyClipboard", "CloseClipboard"]
    assert fake.envelope is None
    assert not fake.is_open

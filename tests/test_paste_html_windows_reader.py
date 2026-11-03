"""Desktop-free tests for the Windows ``HTML Format`` reader behind paste_html.

``clipboard._html_native_windows._win32_api`` is replaced with a fake
user32/kernel32, so no test here needs Windows or touches a real clipboard.
"""

from __future__ import annotations

import ctypes
from types import SimpleNamespace

import pytest
from html_offer import FRAGMENT, build_cf_html
from win32_clipboard_fake import ACCESS_DENIED, FakeWin32

import clipboard
from clipboard import _html_native_windows

ENVELOPE = build_cf_html(
    FRAGMENT,
    before="<html><head><title>Ünïcode 東京</title></head><body><p>ñ context</p>",
    after="<p>après</p></body></html>",
)


@pytest.fixture
def win32(monkeypatch, restore_html_clipboard_reader, fake_platform):
    """Default reader on a pretend Windows with a scripted Win32 API."""
    fake_platform("win32")
    clipboard.set_html_clipboard_reader(None)

    def install(envelope: bytes | None = ENVELOPE, **kwargs) -> FakeWin32:
        fake = FakeWin32(envelope=envelope, **kwargs)
        monkeypatch.setattr(_html_native_windows, "_win32_api", fake.api)
        return fake

    return install


def _assert_released(fake: FakeWin32) -> None:
    assert not fake.is_open and not fake.locked
    assert "EmptyClipboard" not in fake.calls
    assert "SetClipboardData" not in fake.calls


def test_format_unavailable_is_none_without_opening(win32):
    fake = win32(envelope=None)
    assert clipboard.paste_html() is None
    assert fake.calls == ["RegisterClipboardFormatW", "IsClipboardFormatAvailable"]


def test_html_format_fragment_is_extracted_by_byte_offsets(win32):
    fake = win32()
    assert clipboard.paste_html() == FRAGMENT
    assert fake.calls == [
        "RegisterClipboardFormatW",
        "IsClipboardFormatAvailable",
        "OpenClipboard",
        "GetClipboardData",
        "GlobalLock",
        "GlobalSize",
        "GlobalUnlock",
        "CloseClipboard",
    ]
    _assert_released(fake)


def test_contention_resolved_after_retry(win32):
    fake = win32(open_failures=2)
    assert clipboard.paste_html() == FRAGMENT
    assert fake.calls.count("OpenClipboard") == 3
    assert fake.sleeps == [_html_native_windows._OPEN_CLIPBOARD_RETRY_SECONDS] * 2
    _assert_released(fake)


def test_contention_past_the_bound_is_actionable_error(win32):
    fake = win32(open_failures=1000)
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    attempts = _html_native_windows._OPEN_CLIPBOARD_ATTEMPTS
    assert fake.calls.count("OpenClipboard") == attempts
    assert len(fake.sleeps) == attempts - 1
    assert 0.5 <= sum(fake.sleeps) <= 2.0
    message = str(info.value)
    assert "locked by another process" in message
    assert f"Win32 error {ACCESS_DENIED}: message {ACCESS_DENIED}" in message
    assert not isinstance(info.value, clipboard.ClipboardImageError)
    assert "CloseClipboard" not in fake.calls  # never opened, so never closed
    _assert_released(fake)


@pytest.mark.parametrize(
    ("kwargs", "message", "code"),
    [
        ({"data_missing": True}, "GetClipboardData returned no data", 1418),
        ({"lock_fails": True}, "GlobalLock failed", 6),
        ({"register_fails": True}, "RegisterClipboardFormatW", 87),
    ],
    ids=["no-data", "no-lock", "no-format"],
)
def test_win32_failure_is_content_error(win32, kwargs, message, code):
    fake = win32(**kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert "Windows HTML clipboard read failed" in str(info.value)
    assert message in str(info.value)
    assert f"Win32 error {code}" in str(info.value)
    if "OpenClipboard" in fake.calls:
        assert fake.calls[-1] == "CloseClipboard"
    _assert_released(fake)


def test_unlock_and_close_run_when_copy_fails(win32, monkeypatch):
    fake = win32()

    def broken_copy(pointer, size):
        raise OSError("access violation")

    api = fake.api()
    monkeypatch.setattr(
        _html_native_windows,
        "_win32_api",
        lambda: _html_native_windows._Win32Api(
            **{**api.__dict__, "string_at": broken_copy}
        ),
    )
    with pytest.raises(clipboard.ClipboardContentError, match="access violation"):
        clipboard.paste_html()
    assert fake.calls[-2:] == ["GlobalUnlock", "CloseClipboard"]
    _assert_released(fake)


def test_malformed_envelope_from_windows_is_content_error(win32):
    win32(envelope=b"Version:0.9\r\nStartHTML:-1\r\n<b>no offsets</b>")
    with pytest.raises(clipboard.ClipboardContentError, match="missing StartFragment"):
        clipboard.paste_html()


def test_signatures_use_pointer_sized_handles():
    names = (
        "RegisterClipboardFormatW IsClipboardFormatAvailable OpenClipboard "
        "CloseClipboard GetClipboardData GlobalLock GlobalUnlock GlobalSize"
    ).split()
    functions = {name: SimpleNamespace() for name in names}
    user32 = SimpleNamespace(**functions)
    kernel32 = user32
    _html_native_windows._declare_signatures(user32, kernel32)
    assert functions["OpenClipboard"].argtypes == [ctypes.c_void_p]
    assert functions["GetClipboardData"].restype is ctypes.c_void_p
    assert functions["GlobalLock"].argtypes == [ctypes.c_void_p]
    assert functions["GlobalLock"].restype is ctypes.c_void_p
    assert functions["GlobalUnlock"].argtypes == [ctypes.c_void_p]
    assert functions["GlobalSize"].restype is ctypes.c_size_t
    assert functions["RegisterClipboardFormatW"].argtypes == [ctypes.c_wchar_p]
    assert functions["CloseClipboard"].argtypes == []

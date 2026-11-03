"""Desktop-free tests for copy_files' Windows CF_HDROP default writer.

``clipboard._files_native_windows_writer._win32_files_write_api`` is replaced
with ``FakeWin32FilesWriter``, so these run on every CI host without touching a
real clipboard. Only the shared ``sys.platform`` is faked to ``win32``; the
writer path does no other platform-dependent work, so this is safe on
Linux and macOS hosts too.
"""

from __future__ import annotations

import struct

import pytest
from win32_files_writer_fake import (
    DROP_EFFECT_FORMAT_ID,
    OWNER_WINDOW,
    FakeWin32FilesWriter,
)

import clipboard
from clipboard import _files_native_windows_writer

NAMES = ["report final.pdf", "données é.csv"]
CF_HDROP = 15
GMEM_MOVEABLE = 0x0002


@pytest.fixture
def sources(tmp_path):
    for name in NAMES:
        (tmp_path / name).write_text("x", encoding="utf-8")
    return [str(tmp_path / name) for name in NAMES]


@pytest.fixture
def win32(monkeypatch, restore_files_clipboard_writer):
    """Default writer on a (pretend or real) win32 with a scripted Win32 API."""
    monkeypatch.setattr(clipboard._files_native.sys, "platform", "win32")
    clipboard.set_files_clipboard_writer(None)

    def install(**kwargs):
        fake = FakeWin32FilesWriter(**kwargs)
        monkeypatch.setattr(
            _files_native_windows_writer, "_win32_files_write_api", fake.api
        )
        return fake

    return install


def _hdrop_paths(data: bytes) -> list[str]:
    body = data[20:].decode("utf-16-le")
    assert body.endswith("\0\0")
    return body[:-2].split("\0")


def test_copy_files_sets_wide_dropfiles_and_copy_drop_effect(sources, win32):
    fake = win32()

    clipboard.copy_files(sources + [sources[0]])

    expected = sources + [sources[0]]
    assert set(fake.clipboard) == {CF_HDROP, DROP_EFFECT_FORMAT_ID}
    hdrop = fake.memory[fake.clipboard[CF_HDROP]]
    # pFiles=20, pt=(0, 0), fNC=0, fWide=1
    assert struct.unpack("<IiiII", hdrop[:20]) == (20, 0, 0, 0, 1)
    assert hdrop[20:] == ("\0".join(expected) + "\0\0").encode("utf-16-le")
    assert _hdrop_paths(hdrop) == expected
    assert "données é.csv" in _hdrop_paths(hdrop)[1]
    assert fake.memory[fake.clipboard[DROP_EFFECT_FORMAT_ID]] == b"\x01\x00\x00\x00"
    assert set(fake.alloc_flags.values()) == {GMEM_MOVEABLE}
    assert fake.freed == []  # the system owns both globals now
    assert fake.locked == set()
    assert fake.names()[-6:] == [
        "OpenClipboard",
        "EmptyClipboard",
        "SetClipboardData",
        "SetClipboardData",
        "CloseClipboard",
        "DestroyWindow",
    ]
    assert ("OpenClipboard", OWNER_WINDOW) in fake.calls
    assert fake.sleeps == []


def test_contended_open_is_retried_then_written(sources, win32):
    fake = win32(open_failures=3)

    clipboard.copy_files(sources)

    assert fake.names().count("OpenClipboard") == 4
    retry_s = _files_native_windows_writer._OPEN_CLIPBOARD_RETRY_S
    assert fake.sleeps == [retry_s] * 3
    assert CF_HDROP in fake.clipboard


def test_open_past_the_reader_bound_raises_and_leaves_clipboard(sources, win32):
    fake = win32(open_failures=10_000)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files(sources)

    attempts = _files_native_windows_writer._OPEN_CLIPBOARD_WRITE_ATTEMPTS
    assert attempts == 601
    assert fake.names().count("OpenClipboard") == attempts
    assert sum(fake.sleeps) == pytest.approx(
        _files_native_windows_writer._NATIVE_FILES_READ_TIMEOUT_S
    )
    message = str(raised.value)
    assert "OpenClipboard failed 601 times over 30s" in message
    assert "Win32 error 5: message 5" in message
    assert "not changed" in message
    assert "EmptyClipboard" not in fake.names()
    assert "CloseClipboard" not in fake.names()
    assert sorted(fake.freed) == sorted(fake.memory)  # both globals released
    assert not fake.window_alive


@pytest.mark.parametrize(
    ("fail_on", "fragment", "freed", "clipboard_formats"),
    [
        ({"RegisterClipboardFormatW": 1}, "RegisterClipboardFormatW", 0, set()),
        ({"GlobalAlloc": 1}, "GlobalAlloc of", 0, set()),
        ({"GlobalAlloc": 2}, "GlobalAlloc of 4 bytes", 1, set()),
        ({"GlobalLock": 1}, "GlobalLock failed", 1, set()),
        ({"CreateWindowExW": 1}, "CreateWindowExW failed", 2, set()),
        ({"EmptyClipboard": 1}, "EmptyClipboard failed", 2, set()),
        ({"SetClipboardData": 1}, "SetClipboardData(CF_HDROP) failed", 2, set()),
        (
            {"SetClipboardData": 2},
            "SetClipboardData('Preferred DropEffect') failed",
            1,
            {CF_HDROP},
        ),
    ],
)
def test_win32_failure_is_content_error_with_detail(
    sources, win32, fail_on, fragment, freed, clipboard_formats
):
    fake = win32(fail_on=fail_on, error=1418)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files(sources)

    message = str(raised.value)
    assert message.startswith("Windows file-list clipboard write failed: ")
    assert fragment in message
    assert "Win32 error 1418: message 1418" in message
    assert len(fake.freed) == freed
    assert set(fake.clipboard) == clipboard_formats
    for memory in fake.clipboard.values():
        assert memory not in fake.freed
    assert not fake.is_open  # CloseClipboard always ran once opened
    assert not fake.window_alive
    assert fake.locked == set()


def test_missing_path_never_touches_win32(sources, win32):
    fake = win32()
    with pytest.raises(clipboard.ClipboardContentError, match="missing.txt"):
        clipboard.copy_files([sources[0], "missing.txt"])
    assert fake.calls == []

"""Desktop-free Windows inspect enumerator proofs (no real win32 session)."""

from __future__ import annotations

import pytest

import clipboard
from clipboard import _offer, _offer_windows


def test_format_label_maps_standard_cf_ids():
    """11.1: CF_* numeric ids map to stable Windows format names."""
    assert _offer_windows.format_label_for_id(13) == "CF_UNICODETEXT"
    assert _offer_windows.format_label_for_id(8) == "CF_DIB"
    assert _offer_windows.format_label_for_id(17) == "CF_DIBV5"
    assert _offer_windows.format_label_for_id(15) == "CF_HDROP"
    assert _offer_windows.format_label_for_id(1) == "CF_TEXT"
    assert _offer_windows.format_label_for_id(2) == "CF_BITMAP"


def test_format_label_prefers_registered_name_for_non_standard():
    assert (
        _offer_windows.format_label_for_id(49300, registered_name="HTML Format")
        == "HTML Format"
    )
    assert _offer_windows.format_label_for_id(49999) == "49999"


def test_windows_format_names_map_to_kinds_via_snapshot():
    """11.1: CF_* / HTML Format names → kinds through snapshot helpers."""
    snapshot = _offer.snapshot_from_native_formats(
        (
            "HTML Format",
            "CF_UNICODETEXT",
            "CF_HDROP",
            "CF_DIB",
            "com.example.undecodable",
        )
    )
    assert snapshot.kinds == frozenset({"html", "text", "files", "image"})
    assert snapshot.formats[0] == "HTML Format"
    assert "CF_UNICODETEXT" in snapshot.formats
    assert "CF_HDROP" in snapshot.formats
    assert "CF_DIB" in snapshot.formats
    assert "com.example.undecodable" in snapshot.formats


def test_open_clipboard_failure_raises_clipboard_content_error_not_empty(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    """OpenClipboard timeout/fail → ClipboardContentError, never empty."""

    class FakeUser32:
        def OpenClipboard(self, _hwnd):
            return 0

        def CloseClipboard(self):
            return 1

        def EnumClipboardFormats(self, _fmt):
            raise AssertionError("must not enumerate when OpenClipboard fails")

        def GetClipboardFormatNameW(self, *_args):
            raise AssertionError("must not name formats when open fails")

    class FakeCtypes:
        @staticmethod
        def get_last_error():
            return 5

        @staticmethod
        def create_unicode_buffer(_n):
            raise AssertionError("unused")

    monkeypatch.setattr(
        _offer_windows,
        "_load_user32",
        lambda: (FakeUser32(), FakeCtypes),
    )
    monkeypatch.setattr(_offer_windows, "_OPEN_CLIPBOARD_TIMEOUT_S", 0.01)
    monkeypatch.setattr(_offer_windows, "_OPEN_RETRY_SLEEP_S", 0.001)
    fake_platform("win32")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value)
    assert "OpenClipboard failed while enumerating formats" in message
    assert "last_error=5" in message
    assert "timed out after 0.01s" in message
    assert "locked" in message and "held by another process" in message
    assert "set_clipboard_inspector" in message
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_non_win32_load_user32_raises_actionable_error(fake_platform):
    fake_platform("darwin")
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        _offer_windows._load_user32()
    message = str(raised.value)
    assert "win32" in message
    assert "EnumClipboardFormats" in message or "user32" in message


def test_enumerate_open_maps_cf_ids_and_html_format_name():
    """Enum path: CF_* ids + registered HTML Format → snapshot labels."""

    class FakeUser32:
        def __init__(self):
            self._seq = [13, 49322, 8, 15, 0]
            self._i = 0

        def EnumClipboardFormats(self, _fmt):
            value = self._seq[self._i]
            self._i += 1
            return value

    labels = _offer_windows._enumerate_open(
        FakeUser32(),
        object(),
        name_lookup=lambda fmt: "HTML Format" if fmt == 49322 else None,
    )
    assert labels == (
        "CF_UNICODETEXT",
        "HTML Format",
        "CF_DIB",
        "CF_HDROP",
    )
    snapshot = _offer.snapshot_from_native_formats(labels)
    assert snapshot.kinds == frozenset({"text", "html", "image", "files"})


def test_enumerated_formats_map_through_inspector(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    """Mocked EnumClipboardFormats labels → inspect() kinds + formats."""

    monkeypatch.setattr(
        _offer_windows,
        "_enumerate_windows_clipboard_formats",
        lambda: (
            "HTML Format",
            "CF_UNICODETEXT",
            "CF_DIB",
            "CF_HDROP",
        ),
    )
    fake_platform("win32")
    clipboard.set_clipboard_inspector(None)

    snapshot = clipboard.inspect()
    assert snapshot.kinds == frozenset({"html", "text", "image", "files"})
    assert snapshot.formats == (
        "HTML Format",
        "CF_UNICODETEXT",
        "CF_DIB",
        "CF_HDROP",
    )


def test_empty_windows_enumeration_yields_empty_snapshot(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    monkeypatch.setattr(
        _offer_windows,
        "_enumerate_windows_clipboard_formats",
        lambda: (),
    )
    fake_platform("win32")
    clipboard.set_clipboard_inspector(None)

    snapshot = clipboard.inspect()
    assert snapshot.kinds == frozenset()
    assert snapshot.formats == ()

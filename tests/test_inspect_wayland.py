"""Desktop-free Linux Wayland inspect enumerator proofs (no real session)."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

import clipboard
from clipboard import _desktop


def test_missing_wl_paste_raises_clipboard_content_error_not_empty(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    """Missing wl-paste → ClipboardContentError, never empty success."""

    def boom(*_args, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", "wl-paste")

    monkeypatch.setattr(_desktop.subprocess, "run", boom)
    fake_platform("linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value)
    assert "wl-paste" in message
    assert "wl-paste -l" in message or "-l" in message
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    assert raised.value.__cause__ is not None


def test_missing_wayland_display_raises_clipboard_content_error_not_empty(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    """Unavailable Wayland session (no WAYLAND_DISPLAY) → ClipboardContentError."""
    fake_platform("linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value)
    assert "WAYLAND_DISPLAY" in message
    assert "wl-paste" in message
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_wl_paste_helper_failure_raises_clipboard_content_error_not_empty(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    """Non-zero wl-paste -l → ClipboardContentError, not empty snapshot."""

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Failed to connect to a Wayland server\n",
        )

    monkeypatch.setattr(_desktop.subprocess, "run", fake_run)
    fake_platform("linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value)
    assert "wl-paste" in message.lower() or "enumeration failed" in message.lower()
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_wl_paste_mime_list_maps_to_kinds_via_snapshot(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    """MIME ids from wl-paste -l map through snapshot_from_native_formats."""

    def fake_run(cmd, **_kwargs):
        assert cmd[:2] == ["wl-paste", "-l"]
        return SimpleNamespace(
            returncode=0,
            stdout="text/html\ntext/plain\nimage/png\n",
            stderr="",
        )

    monkeypatch.setattr(_desktop.subprocess, "run", fake_run)
    fake_platform("linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    clipboard.set_clipboard_inspector(None)

    snapshot = clipboard.inspect()
    assert snapshot.kinds == frozenset({"html", "text", "image"})
    assert "text/html" in snapshot.formats
    assert "text/plain" in snapshot.formats
    assert "image/png" in snapshot.formats


def test_wl_paste_timeout_raises_clipboard_content_error(
    monkeypatch, restore_clipboard_inspector, fake_platform
):
    def boom(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="wl-paste", timeout=15)

    monkeypatch.setattr(_desktop.subprocess, "run", boom)
    fake_platform("linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    assert "timed out" in str(raised.value).lower()
    assert "wl-paste" in str(raised.value)

"""Desktop-free Linux X11 inspect enumerator proofs (no real DISPLAY/xclip)."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

import clipboard
from clipboard import _desktop, _offer


def test_missing_xclip_raises_clipboard_content_error_not_empty(
    monkeypatch, restore_clipboard_inspector
):
    """14.2: missing xclip → ClipboardContentError, never empty success."""

    def boom(*_args, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", "xclip")

    monkeypatch.setattr(_desktop.subprocess, "run", boom)
    monkeypatch.setattr(_offer.sys, "platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":99")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value)
    assert "xclip" in message
    assert "TARGETS" in message
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    assert raised.value.__cause__ is not None


def test_missing_display_raises_clipboard_content_error_not_empty(
    monkeypatch, restore_clipboard_inspector
):
    """Unavailable X11 session (no DISPLAY) → ClipboardContentError."""
    monkeypatch.setattr(_offer.sys, "platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.delenv("DISPLAY", raising=False)
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value)
    assert "DISPLAY" in message
    assert "xclip" in message
    assert "TARGETS" in message
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_xclip_helper_failure_raises_clipboard_content_error_not_empty(
    monkeypatch, restore_clipboard_inspector
):
    """Non-zero xclip TARGETS → ClipboardContentError, not empty snapshot."""

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Error: Can't open display: (null)\n",
        )

    monkeypatch.setattr(_desktop.subprocess, "run", fake_run)
    monkeypatch.setattr(_offer.sys, "platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":99")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value)
    assert "TARGETS" in message
    assert "xclip" in message.lower() or "enumeration failed" in message.lower()
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_xclip_targets_map_to_kinds_via_snapshot(
    monkeypatch, restore_clipboard_inspector
):
    """11.3: TARGETS MIME/atom ids map through snapshot_from_native_formats."""

    def fake_run(cmd, **_kwargs):
        assert cmd[:1] == ["xclip"]
        assert "-selection" in cmd and "clipboard" in cmd
        assert "-t" in cmd and "TARGETS" in cmd
        return SimpleNamespace(
            returncode=0,
            stdout="TARGETS\nTIMESTAMP\ntext/html\nUTF8_STRING\nimage/png\n",
            stderr="",
        )

    monkeypatch.setattr(_desktop.subprocess, "run", fake_run)
    monkeypatch.setattr(_offer.sys, "platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":99")
    clipboard.set_clipboard_inspector(None)

    snapshot = clipboard.inspect()
    assert snapshot.kinds == frozenset({"html", "text", "image"})
    assert "text/html" in snapshot.formats
    assert "UTF8_STRING" in snapshot.formats
    assert "image/png" in snapshot.formats
    assert "TARGETS" in snapshot.formats


def test_wayland_session_does_not_use_x11_enumerator(
    monkeypatch, restore_clipboard_inspector
):
    """Wayland-only session stays off the X11 path (routes to wl-paste -l)."""
    called = {"xclip": False}

    def boom(cmd, *_args, **_kwargs):
        if cmd and cmd[0] == "xclip":
            called["xclip"] = True
            raise AssertionError("xclip must not run on Wayland-only session")
        raise FileNotFoundError(2, "No such file or directory", "wl-paste")

    monkeypatch.setattr(_desktop.subprocess, "run", boom)
    monkeypatch.setattr(_offer.sys, "platform", "linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("DISPLAY", raising=False)
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    assert called["xclip"] is False
    message = str(raised.value).lower()
    assert "wl-paste" in message
    assert "xclip" not in message


def test_xclip_timeout_raises_clipboard_content_error(
    monkeypatch, restore_clipboard_inspector
):
    def boom(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="xclip", timeout=15)

    monkeypatch.setattr(_desktop.subprocess, "run", boom)
    monkeypatch.setattr(_offer.sys, "platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("DISPLAY", ":99")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    assert "timed out" in str(raised.value).lower()
    assert "TARGETS" in str(raised.value)

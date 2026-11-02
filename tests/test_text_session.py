"""Text session owner selection (pyperclip 1.11.0 ``determine_clipboard`` order).

Each case patches platform, environment, ``shutil.which``, the ``/proc/version``
path, and Qt discovery through ``text_session`` and asserts the selected owner.
"""

import sys

import pytest
from fake_pyperclip import FakePyperclip

import clipboard
from clipboard import _desktop_text, _text


@pytest.mark.parametrize(
    ("platform", "env", "helpers", "proc_version", "qt", "owner"),
    [
        ("win32", {}, (), None, False, "pyperclip"),
        ("darwin", {}, (), None, False, "macos"),
        ("cygwin", {}, (), None, False, "pyperclip"),
        ("freebsd14", {"DISPLAY": ":0"}, ("xclip",), None, False, "pyperclip"),
        (
            "linux",
            {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"},
            ("wl-copy", "wl-paste", "xclip"),
            "Linux version 5.15.153.1-Microsoft-standard-WSL2",
            False,
            "pyperclip",
        ),
        (
            "linux",
            {"WAYLAND_DISPLAY": "wayland-0"},
            ("wl-copy", "wl-paste"),
            "Linux version 6.8.0",
            False,
            "wayland",
        ),
        (
            "linux",
            {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"},
            ("wl-copy", "wl-paste", "xclip"),
            "Linux version 6.8.0",
            False,
            "wayland",
        ),
        (
            "linux",
            {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"},
            ("wl-copy", "xclip"),
            "Linux version 6.8.0",
            False,
            "x11",
        ),
        ("linux", {"DISPLAY": ":0"}, ("xclip", "xsel"), None, True, "x11"),
        ("linux", {"DISPLAY": ":0"}, ("xsel",), None, False, "pyperclip"),
        (
            "linux",
            {"DISPLAY": ":0"},
            ("klipper", "qdbus"),
            None,
            False,
            "pyperclip",
        ),
        ("linux", {"DISPLAY": ":0"}, (), None, True, "pyperclip"),
    ],
    ids=[
        "windows",
        "macos",
        "cygwin",
        "other-unix",
        "wsl-before-desktop",
        "wayland",
        "wayland-before-x11",
        "wayland-needs-both-helpers",
        "x11-xclip-before-xsel",
        "x11-xsel",
        "x11-klipper",
        "x11-qt",
    ],
)
def test_session_selects_pyperclip_order_owner(
    text_session, monkeypatch, platform, env, helpers, proc_version, qt, owner
):
    FakePyperclip(monkeypatch)
    text_session(platform, env, helpers, proc_version, qt)

    assert _text._select_text_backend() == owner


def test_klipper_without_qdbus_is_not_a_fallback(text_session, monkeypatch):
    FakePyperclip(monkeypatch)
    text_session("linux", {"DISPLAY": ":0"}, ("klipper",))

    with pytest.raises(clipboard.ClipboardContentError, match="xclip"):
        _text._select_text_backend()


def test_unreadable_proc_version_is_not_wsl(text_session, monkeypatch):
    FakePyperclip(monkeypatch)
    text_session("linux", {"DISPLAY": ":0"}, ("xclip",), proc_version=None)

    assert _text._select_text_backend() == "x11"


def test_qt_discovery_does_not_import_qt(monkeypatch):
    import importlib.util

    real_find_spec = importlib.util.find_spec
    looked_up = []

    def fake_find_spec(name, *args, **kwargs):
        if name in ("qtpy", "PyQt5"):
            looked_up.append(name)
            return object() if name == "PyQt5" else None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    assert _desktop_text._qt_binding_installed() is True
    assert looked_up == ["qtpy", "PyQt5"]
    assert "PyQt5" not in sys.modules

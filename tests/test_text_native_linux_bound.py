"""Linux text helpers never get a timeout above their operation's bound.

A coarse monotonic clock (Windows) can return the same tick when the
deadline is set and when the remaining time is computed; for some clock
values ``(t + 10.0) - t`` rounds to just above ``10.0``.
"""

import subprocess

import pytest
from fake_wl_clipboard_text import FakeWayland
from fake_xclip_text import FakeX11

import clipboard
from clipboard import _text_native_linux

# A clock reading for which the deadline arithmetic rounds above the bound.
FROZEN_CLOCK = 1014.07


@pytest.fixture
def frozen_clock(monkeypatch):
    bound = _text_native_linux._LINUX_TEXT_TIMEOUT_S
    assert (FROZEN_CLOCK + bound) - FROZEN_CLOCK > bound
    monkeypatch.setattr(_text_native_linux.time, "monotonic", lambda: FROZEN_CLOCK)


def _install(fake, monkeypatch):
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(subprocess, "Popen", fake.popen)
    return fake


@pytest.fixture
def wayland(text_session, monkeypatch, frozen_clock):
    text_session("linux", {"WAYLAND_DISPLAY": "wayland-0"}, ("wl-copy", "wl-paste"))
    return _install(FakeWayland(), monkeypatch)


@pytest.fixture
def x11(text_session, monkeypatch, frozen_clock):
    text_session("linux", {"DISPLAY": ":0"}, ("xclip",))
    return _install(FakeX11(), monkeypatch)


def test_wayland_read_timeouts_stay_within_the_bound(wayland):
    wayland.offers = {"text/plain;charset=utf-8": b"x"}

    assert clipboard.paste() == "x"
    assert [c["timeout"] for c in wayland.calls] == [10.0, 10.0]


def test_wayland_write_timeout_stays_within_the_bound(wayland):
    clipboard.copy("x")

    assert wayland.communicate_timeouts == [10.0]


def test_x11_read_timeouts_stay_within_the_bound(x11):
    x11.offers = {"UTF8_STRING": b"x"}

    assert clipboard.paste() == "x"
    assert [c["timeout"] for c in x11.calls] == [10.0, 10.0]

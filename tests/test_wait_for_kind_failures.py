"""Desktop-free proofs that ``clipboard.wait_for_kind`` fails fast.

Observation failures raise at once and are never retried; invalid arguments
raise before the clipboard is observed.
"""

from __future__ import annotations

import math

import pytest
from fake_wait_clock import (
    EMPTY,
    START,
    TEXT,
    inspector_installer,
    install_fake_clock,
)

import clipboard


@pytest.fixture
def clock(monkeypatch):
    return install_fake_clock(monkeypatch)


@pytest.fixture
def inspector(clock, restore_clipboard_inspector):
    return inspector_installer(clock)


def test_first_observation_failure_raises_at_once(clock, inspector):
    fake = inspector(clipboard.ClipboardContentError("enumeration denied"))

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_kind("text", timeout=10)

    assert raised.value.args == ("enumeration denied",)
    assert fake.calls == [START]
    assert clock.sleeps == []


def test_failure_after_absent_observations_raises_at_once_never_retried(
    clock, inspector
):
    failure = clipboard.ClipboardContentError("helper timed out")
    fake = inspector(EMPTY, EMPTY, failure, TEXT)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_kind("text", timeout=10)

    assert raised.value is failure
    assert fake.calls == [START, START + 0.5, START + 1.0]
    assert clock.sleeps == [0.5, 0.5]


def test_unexpected_inspector_error_is_a_content_error_at_once(clock, inspector):
    fake = inspector(RuntimeError("boom"))

    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.wait_for_kind("text", timeout=10)
    assert len(fake.calls) == 1
    assert clock.sleeps == []


def test_keyboard_interrupt_propagates(clock, inspector):
    inspector(EMPTY, KeyboardInterrupt())

    with pytest.raises(KeyboardInterrupt):
        clipboard.wait_for_kind("text", timeout=10)


def test_linux_without_session_raises_at_once(
    clock, monkeypatch, fake_platform, restore_clipboard_inspector
):
    fake_platform("linux")
    for name in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE"):
        monkeypatch.delenv(name, raising=False)
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_kind("text", timeout=10)

    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    assert "DISPLAY" in str(raised.value)
    assert clock.sleeps == []
    assert clock.now == START


def test_platform_without_inspect_raises_naming_it_at_once(
    clock, fake_platform, restore_clipboard_inspector
):
    fake_platform("sunos5")
    clipboard.set_clipboard_inspector(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_kind("image", timeout=10)

    assert "sunos5" in str(raised.value)
    assert clock.sleeps == []


class _OnlyIsSet:
    def is_set(self) -> bool:
        return False


@pytest.mark.parametrize(
    ("named", "kind", "options"),
    [
        ("kind", "rtf", {"timeout": 1}),
        ("kind", "TEXT", {"timeout": 1}),
        ("kind", "", {"timeout": 1}),
        ("kind", None, {"timeout": 1}),
        ("kind", ["text"], {"timeout": 1}),
        ("timeout", "text", {"timeout": -1}),
        ("timeout", "text", {"timeout": -0.001}),
        ("timeout", "text", {"timeout": math.nan}),
        ("timeout", "text", {"timeout": math.inf}),
        ("timeout", "text", {"timeout": -math.inf}),
        ("timeout", "text", {"timeout": True}),
        ("timeout", "text", {"timeout": False}),
        ("timeout", "text", {"timeout": "1"}),
        ("timeout", "text", {"timeout": None}),
        ("interval", "text", {"timeout": 1, "interval": 0}),
        ("interval", "text", {"timeout": 1, "interval": 0.0}),
        ("interval", "text", {"timeout": 1, "interval": -0.5}),
        ("interval", "text", {"timeout": 1, "interval": math.nan}),
        ("interval", "text", {"timeout": 1, "interval": math.inf}),
        ("interval", "text", {"timeout": 1, "interval": True}),
        ("interval", "text", {"timeout": 1, "interval": "0.5"}),
        ("interval", "text", {"timeout": 1, "interval": None}),
        ("cancel", "text", {"timeout": 1, "cancel": object()}),
        ("cancel", "text", {"timeout": 1, "cancel": _OnlyIsSet()}),
        ("cancel", "text", {"timeout": 1, "cancel": True}),
    ],
    ids=lambda value: repr(value) if not isinstance(value, dict) else None,
)
def test_invalid_argument_raises_before_any_observation(
    clock, inspector, named, kind, options
):
    fake = inspector(TEXT)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.wait_for_kind(kind, **options)

    assert named in str(raised.value)
    assert fake.calls == []
    assert clock.sleeps == []


def test_every_kind_in_the_vocabulary_is_accepted(clock, inspector):
    offered = clipboard.ClipboardOfferSnapshot(
        kinds=frozenset({"text", "image", "html", "files"}), formats=()
    )
    inspector(offered)

    for kind in ("text", "image", "html", "files"):
        assert clipboard.wait_for_kind(kind, timeout=0) is offered


def test_wait_for_kind_is_public():
    assert "wait_for_kind" in clipboard.__all__
    assert callable(clipboard.wait_for_kind)

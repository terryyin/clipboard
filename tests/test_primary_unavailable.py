"""Desktop-free tests: where PRIMARY cannot be reached, nothing else is used.

``copy_primary`` / ``paste_primary`` raise ``ClipboardContentError`` naming
the platform, session or helper, and run no helper process and no pyperclip
mechanism, so CLIPBOARD is neither read nor written (seed
SEED-001#primary-selection examples 7–8 and the no-fallback restriction).
"""

import subprocess

import pytest
from fake_pyperclip import FakePyperclip

import clipboard

WSL = "Linux version 5.15.153.1-microsoft-standard-WSL2 (gcc)"


@pytest.fixture
def nothing_runs(monkeypatch):
    """Record (and refuse) every helper process and pyperclip call."""
    started = []

    def refuse(cmd, *args, **kwargs):
        started.append(cmd)
        raise AssertionError(f"helper started: {cmd!r}")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    pyperclip = FakePyperclip(monkeypatch)
    yield started
    assert started == []
    assert pyperclip.reads == 0
    assert pyperclip.writes == []


def _both_raise(*names):
    for call in (lambda: clipboard.copy_primary("x"), clipboard.paste_primary):
        with pytest.raises(clipboard.ClipboardContentError) as caught:
            call()
        message = str(caught.value)
        assert "primary selection" in message
        for name in names:
            assert name in message


@pytest.mark.parametrize(
    ("platform", "names"),
    [
        ("darwin", ("macOS",)),
        ("win32", ("Windows",)),
        ("sunos5", ("sunos5",)),
    ],
)
def test_non_linux_platforms_are_not_available(
    text_session, nothing_runs, platform, names
):
    text_session(platform, {"DISPLAY": ":0"}, ("xclip", "pbcopy", "pbpaste"))

    _both_raise(*names)


def test_wsl_is_not_available(text_session, nothing_runs):
    text_session("linux", {"DISPLAY": ":0"}, ("xclip",), proc_version=WSL)

    _both_raise("WSL")


def test_linux_without_a_session_raises(text_session, nothing_runs):
    text_session("linux", {}, ("xclip", "wl-copy", "wl-paste"))

    _both_raise("DISPLAY", "WAYLAND_DISPLAY")


@pytest.mark.parametrize(
    "helpers",
    [("wl-copy",), ("wl-paste", "xclip", "xsel"), ("xsel",), ()],
)
def test_wayland_without_wl_clipboard_names_wl_clipboard(
    text_session, nothing_runs, helpers
):
    # Wayland-only session: no DISPLAY, so neither xclip nor pyperclip serves.
    text_session("linux", {"WAYLAND_DISPLAY": "wayland-0"}, helpers)

    _both_raise("WAYLAND_DISPLAY", "wl-clipboard")


@pytest.mark.parametrize(
    ("helpers", "qt"),
    [(("xsel",), False), (("klipper", "qdbus"), False), ((), True), ((), False)],
)
def test_x11_without_xclip_names_xclip(text_session, nothing_runs, helpers, qt):
    text_session("linux", {"DISPLAY": ":0"}, helpers, qt=qt)

    _both_raise("xclip", "apt-get install xclip")


def test_x11_with_xsel_only_still_pastes_clipboard_through_pyperclip(
    text_session, monkeypatch
):
    text_session("linux", {"DISPLAY": ":0"}, ("xsel",))
    pyperclip = FakePyperclip(monkeypatch)
    pyperclip.contents = "copied"

    assert clipboard.paste() == "copied"
    _both_raise("xclip")
    assert pyperclip.reads == 1
    assert pyperclip.writes == []


def test_mixed_session_incomplete_wl_clipboard_with_xsel_names_both_helpers(
    text_session, nothing_runs
):
    # DISPLAY + WAYLAND_DISPLAY, only xsel: text would use pyperclip, but
    # PRIMARY names both owned helpers and runs nothing.
    text_session(
        "linux",
        {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"},
        ("xsel",),
    )

    _both_raise("xclip", "wl-clipboard")


def test_validation_precedes_the_platform_check(text_session, nothing_runs):
    text_session("darwin")

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_primary("a\x00b")
    message = str(caught.value)
    # Rejected as input (shared with ``copy``), not as an unavailable platform.
    assert "macOS" not in message
    assert "primary selection" in message

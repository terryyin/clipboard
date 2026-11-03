"""Desktop-free session dispatch for the default text backend (``copy`` / ``paste``).

Each test sets a session shape through ``text_session`` and a fake pyperclip so
delegation, diagnoses, and owned-path isolation are observed without touching a
real clipboard. Owner selection rules live in ``test_text_session.py``.
"""

import pyperclip
import pytest
from fake_pyperclip import FakePyperclip

import clipboard
from clipboard import _text


@pytest.mark.parametrize(
    ("platform", "env", "helpers", "owner"),
    [
        ("darwin", {}, (), "macos"),
        ("linux", {"DISPLAY": ":0"}, ("xclip",), "x11"),
        (
            "linux",
            {"WAYLAND_DISPLAY": "wayland-0"},
            ("wl-copy", "wl-paste"),
            "wayland",
        ),
    ],
)
def test_resolved_pyperclip_state_does_not_displace_owned_backend(
    text_session, monkeypatch, platform, env, helpers, owner
):
    fake = FakePyperclip(monkeypatch, available=True)
    text_session(platform, env, helpers)
    written = []
    monkeypatch.setitem(_text._OWNED_TEXT_WRITERS, owner, written.append)
    monkeypatch.setitem(_text._OWNED_TEXT_READERS, owner, lambda: "from owner")

    assert _text._select_text_backend() == owner
    clipboard.copy("chosen")
    assert clipboard.paste() == "from owner"
    assert written == ["chosen"]
    assert fake.writes == []
    assert fake.reads == 0


def test_resolved_pyperclip_without_session_is_still_diagnosed(
    text_session, monkeypatch
):
    fake = FakePyperclip(monkeypatch, available=True)
    text_session("linux")

    for call in (lambda: clipboard.copy("x"), clipboard.paste):
        with pytest.raises(
            clipboard.ClipboardContentError, match="no desktop session is visible"
        ):
            call()
    assert fake.writes == []
    assert fake.reads == 0


def test_explicit_hooks_delegate_to_pyperclip_and_none_restores_owner(
    text_session, monkeypatch
):
    fake = FakePyperclip(monkeypatch, available=True)
    text_session("darwin")
    owned = []
    monkeypatch.setitem(_text._OWNED_TEXT_WRITERS, "macos", owned.append)
    monkeypatch.setitem(_text._OWNED_TEXT_READERS, "macos", lambda: "owner")

    clipboard.set_text_clipboard_writer(lambda text: pyperclip.copy(text))
    clipboard.set_text_clipboard_reader(lambda: pyperclip.paste())
    clipboard.copy("via pyperclip")
    assert clipboard.paste() == "via pyperclip"
    assert fake.writes == ["via pyperclip"]
    assert owned == []

    error = pyperclip.PyperclipException("no mechanism")
    fake.copy_error = error
    with pytest.raises(clipboard.ClipboardContentError, match="text write") as caught:
        clipboard.copy("x")
    assert caught.value.__cause__ is error

    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)
    clipboard.copy("owned again")
    assert owned == ["owned again"]
    assert clipboard.paste() == "owner"


@pytest.mark.parametrize(
    ("platform", "proc_version"),
    [
        ("win32", None),
        ("linux", "Linux version 5.15.153.1-microsoft-standard-WSL2"),
        ("linux", "Linux version 4.4.0-19041-MICROSOFT (Microsoft@Microsoft.com)"),
        ("cygwin", None),
    ],
)
def test_delegated_sessions_round_trip_through_pyperclip(
    text_session, monkeypatch, platform, proc_version
):
    fake = FakePyperclip(monkeypatch)
    text_session(platform, proc_version=proc_version)

    clipboard.copy("héllo 👋\r\nline 2")
    assert fake.writes == ["héllo 👋\r\nline 2"]
    assert clipboard.paste() == "héllo 👋\r\nline 2"


@pytest.mark.parametrize(
    "error",
    [
        pyperclip.PyperclipException("powershell exited with 1"),
        FileNotFoundError(2, "No such file or directory", "powershell.exe"),
    ],
)
def test_wsl_bridge_failures_become_content_errors(text_session, monkeypatch, error):
    fake = FakePyperclip(monkeypatch)
    fake.copy_error = error
    fake.paste_error = error
    text_session("linux", proc_version="Linux version 5.15-microsoft-standard-WSL2")

    with pytest.raises(clipboard.ClipboardContentError, match="text write") as wrote:
        clipboard.copy("x")
    assert wrote.value.__cause__ is error
    with pytest.raises(clipboard.ClipboardContentError, match="text read") as read:
        clipboard.paste()
    assert read.value.__cause__ is error


def test_wsl_bridge_returning_none_pastes_empty_string(text_session, monkeypatch):
    fake = FakePyperclip(monkeypatch)
    text_session("linux", proc_version="Linux version 5.15-microsoft-standard-WSL2")

    result = clipboard.paste()
    assert result == ""
    assert type(result) is str
    assert fake.reads == 1


def test_display_without_any_helper_names_install_hints(text_session, monkeypatch):
    fake = FakePyperclip(monkeypatch)
    text_session("linux", {"DISPLAY": ":0"})

    for call in (lambda: clipboard.copy("x"), clipboard.paste):
        with pytest.raises(clipboard.ClipboardContentError) as caught:
            call()
        message = str(caught.value)
        assert "DISPLAY" in message
        assert "xclip" in message
        assert "wl-clipboard" in message
        assert "apt-get install" in message
    assert fake.writes == []
    assert fake.reads == 0


def test_wayland_without_wl_clipboard_names_install_hints(text_session, monkeypatch):
    FakePyperclip(monkeypatch)
    text_session("linux", {"WAYLAND_DISPLAY": "wayland-0"}, ("wl-copy",))

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.paste()
    assert "WAYLAND_DISPLAY" in str(caught.value)
    assert "wl-clipboard" in str(caught.value)


def test_no_desktop_session_is_diagnosed_not_empty(text_session, monkeypatch):
    fake = FakePyperclip(monkeypatch)
    fake.contents = "would be wrong to return"
    # Helpers installed do not matter without a session (SSH into Linux).
    text_session("linux", {"XDG_SESSION_TYPE": "tty"}, ("xclip", "wl-copy", "wl-paste"))

    for call in (lambda: clipboard.copy("x"), clipboard.paste):
        with pytest.raises(
            clipboard.ClipboardContentError, match="no desktop session is visible"
        ) as caught:
            call()
        assert "DISPLAY" in str(caught.value)
        assert "WAYLAND_DISPLAY" in str(caught.value)
    assert fake.writes == []
    assert fake.reads == 0


# The owned macOS, X11, and Wayland paths have their own dispatch tests
# (``test_text_macos.py``, ``test_text_x11.py``, ``test_text_wayland.py``),
# each asserting that pyperclip is never reached.


def test_selection_follows_session_at_call_time(text_session, monkeypatch):
    fake = FakePyperclip(monkeypatch)
    text_session("linux")
    with pytest.raises(clipboard.ClipboardContentError, match="no desktop session"):
        clipboard.paste()

    text_session("linux", {"DISPLAY": ":0"}, ("xsel",))
    fake.contents = "now visible"
    assert clipboard.paste() == "now visible"


def test_injected_seam_bypasses_dispatch(
    text_session, monkeypatch, fake_text_clipboard
):
    FakePyperclip(monkeypatch)
    text_session("linux")

    clipboard.copy("seam")
    assert clipboard.paste() == "seam"

"""Desktop-free contract for clipboard.clear behind set_clipboard_clearer.

Platform clearers are covered in ``test_clear_{macos,wayland,x11}.py``; here
the seam, the fallback for platforms without a native clearer, and Linux with
no visible session. No test touches the real clipboard.
"""

import pytest

import clipboard
from clipboard import _clear_macos, _clear_wayland, _clear_x11


def test_clear_is_public_without_images_extra():
    assert "clear" in clipboard.__all__
    assert "set_clipboard_clearer" in clipboard.__all__
    assert callable(clipboard.clear)
    assert callable(clipboard.set_clipboard_clearer)


def test_clear_calls_injected_clearer_once_and_returns_none(
    restore_clipboard_clearer,
):
    calls: list[None] = []
    clipboard.set_clipboard_clearer(lambda: calls.append(None))

    assert clipboard.clear() is None
    assert calls == [None]


def test_clear_twice_in_a_row_succeeds(restore_clipboard_clearer):
    calls: list[None] = []
    clipboard.set_clipboard_clearer(lambda: calls.append(None))

    assert clipboard.clear() is None
    assert clipboard.clear() is None
    assert calls == [None, None]


def test_clearer_content_error_passes_through_unchanged(restore_clipboard_clearer):
    original = clipboard.ClipboardContentError("clipboard held by another process")

    def failing_clearer() -> None:
        raise original

    clipboard.set_clipboard_clearer(failing_clearer)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    assert excinfo.value is original


@pytest.mark.parametrize(
    "failure",
    [OSError("helper vanished"), RuntimeError("native call failed")],
    ids=["OSError", "RuntimeError"],
)
def test_clearer_other_failure_becomes_content_error_with_cause(
    restore_clipboard_clearer, failure
):
    def failing_clearer() -> None:
        raise failure

    clipboard.set_clipboard_clearer(failing_clearer)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    assert excinfo.value.__cause__ is failure
    assert str(failure) in str(excinfo.value)


def test_set_clipboard_clearer_none_restores_default(restore_clipboard_clearer):
    clipboard.set_clipboard_clearer(lambda: None)
    clipboard.set_clipboard_clearer(None)
    assert clipboard._clipboard_clearer is clipboard._default_clipboard_clearer


@pytest.mark.parametrize("platform", ["win32", "sunos5"])
def test_default_clearer_names_platform_and_seam(
    restore_clipboard_clearer, monkeypatch, platform
):
    """Platforms without a native clearer yet say so and run no helper."""
    monkeypatch.setattr(clipboard.sys, "platform", platform)
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)

    def no_helper(*args, **kwargs):
        raise AssertionError("default clearer must not run a helper here")

    monkeypatch.setattr(_clear_macos.subprocess, "run", no_helper)
    monkeypatch.setattr(_clear_wayland.subprocess, "run", no_helper)
    monkeypatch.setattr(_clear_x11.subprocess, "run", no_helper)
    clipboard.set_clipboard_clearer(None)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    message = str(excinfo.value)
    assert "not available" in message
    assert f"({platform})" in message
    assert "set_clipboard_clearer" in message


def test_linux_without_any_session_says_no_desktop_session(linux_clear_session):
    helper = linux_clear_session()
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    message = str(excinfo.value)
    assert "no desktop session is visible" in message
    assert "DISPLAY" in message and "WAYLAND_DISPLAY" in message
    assert helper.calls == []

"""Desktop-free contract for clipboard.clear behind set_clipboard_clearer."""

import pytest

import clipboard


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


@pytest.mark.parametrize("platform", ["darwin", "linux", "win32", "sunos5"])
def test_default_clearer_names_platform_and_seam(
    restore_clipboard_clearer, monkeypatch, platform
):
    """No native clearer exists yet on any platform; the default says so."""
    monkeypatch.setattr(clipboard.sys, "platform", platform)
    clipboard.set_clipboard_clearer(None)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    message = str(excinfo.value)
    assert "not available" in message
    assert f"({platform})" in message
    assert "set_clipboard_clearer" in message

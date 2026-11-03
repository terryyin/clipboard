"""Desktop-free contract for clipboard.clear behind set_clipboard_clearer.

The macOS clearer's ``subprocess.run`` is replaced, so no test here touches
the real pasteboard or needs an Aqua session.
"""

import subprocess

import pytest

import clipboard
from clipboard import _clear_macos


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


@pytest.mark.parametrize("platform", ["linux", "win32", "sunos5"])
def test_default_clearer_names_platform_and_seam(
    restore_clipboard_clearer, monkeypatch, platform
):
    """Platforms without a native clearer yet say so and run no helper."""
    monkeypatch.setattr(clipboard.sys, "platform", platform)

    def no_helper(*args, **kwargs):
        raise AssertionError("default clearer must not run a helper here")

    monkeypatch.setattr(_clear_macos.subprocess, "run", no_helper)
    clipboard.set_clipboard_clearer(None)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    message = str(excinfo.value)
    assert "not available" in message
    assert f"({platform})" in message
    assert "set_clipboard_clearer" in message


class _Helper:
    """Stand-in for ``subprocess.run``: records calls, answers or raises."""

    def __init__(self, *, returncode=0, stdout="ok\n", stderr="", raises=None):
        self.result = subprocess.CompletedProcess([], returncode, stdout, stderr)
        self.raises = raises
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.raises is not None:
            raise self.raises
        return self.result


@pytest.fixture
def darwin_helper(monkeypatch, restore_clipboard_clearer):
    """Default clearer on a pretend Darwin with a scripted osascript."""
    monkeypatch.setattr(clipboard.sys, "platform", "darwin")
    clipboard.set_clipboard_clearer(None)

    def install(**kwargs):
        helper = _Helper(**kwargs)
        monkeypatch.setattr(_clear_macos.subprocess, "run", helper)
        return helper

    return install


def test_darwin_default_clearer_runs_bounded_osascript_clear(darwin_helper):
    helper = darwin_helper()
    assert clipboard.clear() is None
    [(args, kwargs)] = helper.calls
    assert args[:2] == ["osascript", "-e"]
    script = args[-1]
    assert "generalPasteboard()" in script
    assert "clearContents()" in script
    for writer in ("declareTypes", "setData", "setString"):
        assert writer not in script
    assert kwargs["timeout"] == _clear_macos._MACOS_CLEAR_TIMEOUT_S
    assert kwargs["check"] is False


def test_darwin_default_clearer_twice_runs_helper_twice(darwin_helper):
    helper = darwin_helper()
    assert clipboard.clear() is None
    assert clipboard.clear() is None
    assert len(helper.calls) == 2


@pytest.mark.parametrize(
    ("helper_kwargs", "message", "cause"),
    [
        (
            {"returncode": 1, "stderr": "execution error: not authorized (-1743)"},
            "macOS pasteboard clear failed: execution error: not authorized",
            None,
        ),
        (
            {"raises": subprocess.TimeoutExpired("osascript", 15)},
            "macOS pasteboard clear timed out (limit 15s)",
            subprocess.TimeoutExpired,
        ),
        (
            {"raises": FileNotFoundError(2, "No such file", "osascript")},
            "macOS pasteboard clear failed: could not run osascript",
            FileNotFoundError,
        ),
    ],
    ids=["exit", "timeout", "no-osascript"],
)
def test_darwin_clearer_failure_is_content_error_with_detail(
    darwin_helper, helper_kwargs, message, cause
):
    darwin_helper(**helper_kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    assert not isinstance(excinfo.value, clipboard.ClipboardImageError)
    assert message in str(excinfo.value)
    if cause is not None:
        assert isinstance(excinfo.value.__cause__, cause)

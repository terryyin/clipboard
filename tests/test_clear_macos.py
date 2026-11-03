"""Desktop-free macOS ``clear()``: ``osascript`` is a scripted fake."""

import subprocess

import pytest
from fake_clear_helpers import FakeClearHelper

import clipboard
from clipboard import _clear_macos


@pytest.fixture
def darwin_helper(monkeypatch, restore_clipboard_clearer, fake_platform):
    """Default clearer on a pretend Darwin with a scripted osascript."""
    fake_platform("darwin")
    clipboard.set_clipboard_clearer(None)

    def install(**kwargs):
        helper = FakeClearHelper(**kwargs)
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

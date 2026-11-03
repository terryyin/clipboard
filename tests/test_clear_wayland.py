"""Desktop-free Linux Wayland ``clear()``: ``wl-copy`` is a scripted fake."""

import subprocess

import pytest

import clipboard
from clipboard import _clear_wayland


@pytest.mark.parametrize(
    "session",
    [
        {"wayland": "wayland-1"},
        {"wayland": "wayland-1", "display": ":0"},
        {"session_type": "wayland"},
    ],
    ids=["wayland", "wayland-and-x11-selects-wayland", "session-type-wayland"],
)
def test_wayland_default_clearer_runs_bounded_wl_copy_clear(
    linux_clear_session, session
):
    helper = linux_clear_session(**session)
    assert clipboard.clear() is None
    [(args, kwargs)] = helper.calls
    assert args == ["wl-copy", "--clear"]
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["timeout"] == _clear_wayland._WAYLAND_CLEAR_TIMEOUT_S
    assert kwargs["check"] is False
    # stderr is a file, never a pipe a forked helper could hold open.
    assert kwargs["stderr"] not in (subprocess.PIPE, None)
    assert kwargs.get("capture_output") is not True


def test_wayland_default_clearer_twice_runs_helper_twice(linux_clear_session):
    helper = linux_clear_session(wayland="wayland-1")
    assert clipboard.clear() is None
    assert clipboard.clear() is None
    assert len(helper.calls) == 2


def test_both_sessions_select_wayland_not_x11(linux_clear_session):
    """The fixture fails any X11 child run, so only wl-copy ran."""
    helper = linux_clear_session(display=":0", wayland="wayland-1")
    assert clipboard.clear() is None
    assert [args for args, _ in helper.calls] == [["wl-copy", "--clear"]]


@pytest.mark.parametrize(
    ("helper_kwargs", "message", "cause"),
    [
        (
            {"raises": FileNotFoundError(2, "No such file", "wl-copy")},
            "wl-copy was not found on PATH; install wl-clipboard",
            FileNotFoundError,
        ),
        (
            {
                "returncode": 1,
                "stderr": "Failed to connect to a Wayland server\n",
            },
            "Linux Wayland clipboard clear failed: wl-copy --clear exited with "
            "status 1: Failed to connect to a Wayland server",
            None,
        ),
        (
            {"raises": subprocess.TimeoutExpired("wl-copy", 10)},
            "Linux Wayland clipboard clear timed out (limit 10s)",
            subprocess.TimeoutExpired,
        ),
        (
            {"raises": PermissionError(13, "Permission denied", "wl-copy")},
            "Linux Wayland clipboard clear failed: could not run wl-copy",
            PermissionError,
        ),
    ],
    ids=["no-wl-copy", "exit", "timeout", "oserror"],
)
def test_wayland_clearer_failure_is_content_error_with_detail(
    linux_clear_session, helper_kwargs, message, cause
):
    linux_clear_session(wayland="wayland-1", **helper_kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    assert not isinstance(excinfo.value, clipboard.ClipboardImageError)
    assert message in str(excinfo.value)
    if cause is not None:
        assert isinstance(excinfo.value.__cause__, cause)

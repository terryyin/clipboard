"""Desktop-free Linux X11 ``clear()``: the libX11 child is a scripted fake.

One test runs a real (hung) child to prove the timeout bound.
"""

import subprocess
import sys
import time

import pytest
from fake_clear_helpers import FakeX11ClearChild

import clipboard
from clipboard import _clear_x11

_REAL_RUN = subprocess.run


@pytest.fixture
def x11_session(linux_clear_session):
    """Default clearer on a pretend X11-only Linux with a scripted child."""

    def install(*, display=":0", **kwargs):
        wl_copy = linux_clear_session(display=display)
        kwargs.setdefault("outcome", {"ok": True})
        child = FakeX11ClearChild(**kwargs)
        wl_copy.x11_child = child
        return child

    return install


def test_x11_default_clearer_runs_bounded_libx11_child(x11_session):
    child = x11_session()
    assert clipboard.clear() is None
    [(args, kwargs)] = child.calls
    assert args == [sys.executable, "-I", str(_clear_x11._RELINQUISH_SCRIPT)]
    assert _clear_x11._RELINQUISH_SCRIPT.is_file()
    assert _clear_x11._RELINQUISH_SCRIPT.name == "_x11_relinquish.py"
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["timeout"] == _clear_x11._X11_CLEAR_TIMEOUT_S
    assert kwargs["check"] is False


def test_x11_default_clearer_twice_runs_child_twice(x11_session):
    child = x11_session()
    assert clipboard.clear() is None
    assert clipboard.clear() is None
    assert len(child.calls) == 2


@pytest.mark.parametrize(
    ("child_kwargs", "message", "cause"),
    [
        (
            {
                "returncode": 3,
                "outcome": {
                    "failure": "libx11",
                    "detail": "libX11.so.6: cannot open shared object file",
                },
            },
            "libX11 could not be loaded with ctypes; install libX11 (e.g. "
            "`sudo apt-get install libx11-6`",
            None,
        ),
        (
            {
                "returncode": 3,
                "outcome": {"failure": "display", "detail": "XOpenDisplay NULL"},
            },
            "could not open the X display DISPLAY=':0'",
            None,
        ),
        (
            {"returncode": 3, "outcome": {"failure": "atom", "detail": "no atom"}},
            "Linux X11 clipboard clear failed: libX11 "
            "XSetSelectionOwner(CLIPBOARD, None): no atom",
            None,
        ),
        (
            {
                "returncode": 1,
                "outcome": None,
                "stderr": "X Error of failed request:  BadAtom\n",
            },
            "helper exited with status 1: X Error of failed request:  BadAtom",
            None,
        ),
        (
            {"raises": subprocess.TimeoutExpired("python", 10)},
            "Linux X11 clipboard clear timed out (limit 10s); the X server at "
            "DISPLAY=':0' is not answering",
            subprocess.TimeoutExpired,
        ),
        (
            {"raises": PermissionError(13, "Permission denied", "python")},
            "Linux X11 clipboard clear failed: could not run the libX11 clear helper",
            PermissionError,
        ),
    ],
    ids=["no-libx11", "display", "atom", "x-error-exit", "timeout", "oserror"],
)
def test_x11_clearer_failure_is_content_error_with_detail(
    x11_session, child_kwargs, message, cause
):
    x11_session(**child_kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    assert not isinstance(excinfo.value, clipboard.ClipboardImageError)
    assert message in str(excinfo.value)
    if cause is not None:
        assert isinstance(excinfo.value.__cause__, cause)


def test_x11_clear_times_out_within_bound_on_a_hung_child(
    linux_clear_session, monkeypatch
):
    """A real child that never answers is killed at the bound and reported."""
    linux_clear_session(display=":0").x11_child = _REAL_RUN
    monkeypatch.setattr(_clear_x11, "_X11_CLEAR_TIMEOUT_S", 0.5)
    monkeypatch.setattr(
        _clear_x11,
        "_relinquish_command",
        lambda: [sys.executable, "-c", "import time; time.sleep(30)"],
    )
    started = time.monotonic()
    with pytest.raises(clipboard.ClipboardContentError) as excinfo:
        clipboard.clear()
    assert time.monotonic() - started < 5
    assert "timed out (limit 0.5s)" in str(excinfo.value)
    assert "DISPLAY=':0'" in str(excinfo.value)

"""Desktop-free tests for the macOS ``public.html`` reader behind paste_html.

``subprocess.run`` in ``clipboard._html_native_macos`` is replaced, so no test
here touches the real pasteboard or needs an Aqua session.
"""

import base64
import subprocess

import pytest

import clipboard
from clipboard import _html_native, _html_native_macos
from clipboard._html_envelope import _fragment_offer

FRAGMENT = '<a href="https://example.com/caf%C3%A9"><b>café → 日本</b></a>'
BROWSER_BODY = "<meta charset='utf-8'>" + FRAGMENT


class _Helper:
    """Stand-in for ``subprocess.run``: records calls, answers or raises."""

    def __init__(self, *, stdout="", returncode=0, stderr="", raises=None):
        self.result = subprocess.CompletedProcess([], returncode, stdout, stderr)
        self.raises = raises
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.raises is not None:
            raise self.raises
        return self.result


@pytest.fixture
def darwin_helper(monkeypatch, restore_html_clipboard_reader):
    """Default reader on a pretend Darwin with a scripted osascript."""
    monkeypatch.setattr(_html_native.sys, "platform", "darwin")
    clipboard.set_html_clipboard_reader(None)

    def install(**kwargs):
        helper = _Helper(**kwargs)
        monkeypatch.setattr(_html_native_macos.subprocess, "run", helper)
        return helper

    return install


def _html_answer(body: bytes) -> str:
    return "HTML:" + base64.b64encode(body).decode("ascii") + "\n"


def test_darwin_default_reader_returns_fragment(darwin_helper):
    helper = darwin_helper(stdout=_html_answer(BROWSER_BODY.encode("utf-8")))
    assert clipboard.paste_html() == BROWSER_BODY
    (args, kwargs), *_ = helper.calls
    assert args[:3] == ["osascript", "-l", "JavaScript"]
    assert "public.html" in args[-1]
    assert kwargs["timeout"] == _html_native_macos._MACOS_HTML_READ_TIMEOUT_SECONDS


def test_reader_passes_raw_bytes_through_undecoded(darwin_helper):
    raw = FRAGMENT.encode("utf-8")
    darwin_helper(stdout=_html_answer(raw))
    assert _html_native_macos._macos_html_clipboard_reader() == _fragment_offer(raw)


def test_reader_script_only_reads_the_pasteboard(darwin_helper):
    helper = darwin_helper(stdout="NONE\n")
    clipboard.paste_html()
    script = helper.calls[0][0][-1]
    for mutator in ("clearContents", "setData", "setString", "declareTypes"):
        assert mutator not in script


def test_empty_html_offer_is_empty_string(darwin_helper):
    darwin_helper(stdout="HTML:\n")
    assert clipboard.paste_html() == ""


def test_no_html_type_is_none(darwin_helper):
    darwin_helper(stdout="NONE\n")
    assert clipboard.paste_html() is None


@pytest.mark.parametrize(
    ("helper_kwargs", "message"),
    [
        (
            {"returncode": 1, "stderr": "execution error: not authorized (-1743)"},
            "not authorized",
        ),
        ({"raises": subprocess.TimeoutExpired("osascript", 10)}, "did not answer"),
        (
            {"raises": FileNotFoundError(2, "No such file", "osascript")},
            "could not run osascript",
        ),
        ({"stdout": "UNREADABLE\n"}, "could not be obtained"),
        ({"stdout": "surprise\n"}, "unexpected helper output"),
        ({"stdout": "HTML:not*base64\n"}, "malformed base64"),
    ],
    ids=["exit", "timeout", "no-osascript", "unreadable", "garbled", "base64"],
)
def test_helper_failure_is_content_error(darwin_helper, helper_kwargs, message):
    darwin_helper(**helper_kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert not isinstance(info.value, clipboard.ClipboardImageError)
    assert "macOS HTML pasteboard read failed" in str(info.value)
    assert message in str(info.value)


def test_non_darwin_default_reader_is_not_available(
    monkeypatch, restore_html_clipboard_reader
):
    # Windows, Linux X11 and Wayland have readers (tests/test_paste_html_*
    # _reader.py); an unsupported platform such as Solaris does not.
    monkeypatch.setattr(_html_native.sys, "platform", "sunos5")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def no_helper(*args, **kwargs):
        raise AssertionError("default reader must not run a helper here")

    monkeypatch.setattr(_html_native_macos.subprocess, "run", no_helper)
    clipboard.set_html_clipboard_reader(None)
    with pytest.raises(clipboard.ClipboardContentError, match="not available"):
        clipboard.paste_html()

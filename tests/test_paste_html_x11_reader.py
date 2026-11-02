"""Desktop-free tests for the Linux X11 ``text/html`` reader behind paste_html.

``subprocess.run`` is replaced with a scripted ``xclip``, so no test here
touches a real X11 CLIPBOARD or needs DISPLAY / xclip installed.
"""

import subprocess

import pytest

import clipboard
from clipboard import _desktop, _html_native, _html_native_linux
from clipboard._html_envelope import _fragment_offer

FRAGMENT = '<a href="https://example.com/caf%C3%A9"><b>café → naïve 日本</b></a>'
HTML_TARGETS = b"TIMESTAMP\nTARGETS\nMULTIPLE\ntext/html\nUTF8_STRING\n"
TEXT_TARGETS = b"TIMESTAMP\nTARGETS\nUTF8_STRING\nSTRING\nTEXT\n"
IMAGE_TARGETS = b"TIMESTAMP\nTARGETS\nimage/png\n"
FILES_TARGETS = b"TIMESTAMP\nTARGETS\ntext/uri-list\nx-special/gnome-copied-files\n"
NO_OWNER = b"Error: target TARGETS not available\n"
NO_DISPLAY = b"Error: Can't open display: (null)\n"


def _done(returncode=0, stdout=b"", stderr=b""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class _Xclip:
    """Stand-in for ``subprocess.run``: answers (or raises) per ``-t`` target."""

    def __init__(self, answers=None, raises=None):
        self.answers = answers or {}
        self.raises = raises
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.raises is not None:
            raise self.raises
        target = args[args.index("-t") + 1]
        if target not in self.answers:
            raise AssertionError(f"unexpected xclip target {target!r}")
        answer = self.answers[target]
        if isinstance(answer, BaseException):
            raise answer
        return answer


@pytest.fixture
def x11_xclip(monkeypatch, restore_html_clipboard_reader):
    """Default reader on a pretend Linux X11 session with a scripted xclip."""
    monkeypatch.setattr(_html_native.sys, "platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    clipboard.set_html_clipboard_reader(None)

    def install(**kwargs):
        helper = _Xclip(**kwargs)
        # TARGETS listing lives in ``_desktop``; text/html read stays local.
        monkeypatch.setattr(_desktop.subprocess, "run", helper)
        monkeypatch.setattr(_html_native_linux.subprocess, "run", helper)
        return helper

    return install


def test_text_html_target_returns_fragment(x11_xclip):
    helper = x11_xclip(
        answers={
            "TARGETS": _done(stdout=HTML_TARGETS),
            "text/html": _done(stdout=FRAGMENT.encode("utf-8")),
        }
    )
    assert clipboard.paste_html() == FRAGMENT
    assert [args for args, _ in helper.calls] == [
        ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"],
        ["xclip", "-selection", "clipboard", "-o", "-t", "text/html"],
    ]


def test_reader_passes_raw_bytes_through_undecoded(x11_xclip):
    raw = b"\xff\xfe" + FRAGMENT.encode("utf-16-le")
    x11_xclip(
        answers={
            "TARGETS": _done(stdout=HTML_TARGETS),
            "text/html": _done(stdout=raw),
        }
    )
    assert _html_native_linux._linux_x11_html_clipboard_reader() == (
        _fragment_offer(raw)
    )
    assert clipboard.paste_html() == FRAGMENT


def test_empty_html_offer_is_empty_string(x11_xclip):
    x11_xclip(answers={"TARGETS": _done(stdout=HTML_TARGETS), "text/html": _done()})
    assert clipboard.paste_html() == ""


@pytest.mark.parametrize(
    "targets",
    [TEXT_TARGETS, IMAGE_TARGETS, FILES_TARGETS, b"text/html-ish\nTEXT\n"],
    ids=["text-only", "image-only", "file-list", "lookalike"],
)
def test_targets_without_text_html_is_none(x11_xclip, targets):
    helper = x11_xclip(answers={"TARGETS": _done(stdout=targets)})
    assert clipboard.paste_html() is None
    assert len(helper.calls) == 1


def test_unowned_clipboard_is_none(x11_xclip):
    # xclip 0.13 on an empty (unowned) CLIPBOARD: exit 1 with this stderr.
    helper = x11_xclip(answers={"TARGETS": _done(1, stderr=NO_OWNER)})
    assert clipboard.paste_html() is None
    assert len(helper.calls) == 1


def test_every_helper_call_is_bounded_and_read_only(x11_xclip):
    helper = x11_xclip(
        answers={
            "TARGETS": _done(stdout=HTML_TARGETS),
            "text/html": _done(stdout=b"<i>x</i>"),
        }
    )
    clipboard.paste_html()
    assert helper.calls
    for args, kwargs in helper.calls:
        assert args[0] == "xclip"
        assert "-o" in args
        assert not {"-i", "-in", "-loops", "-l"} & set(args)
        assert kwargs["timeout"] == _html_native_linux._X11_HTML_READ_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    ("helper_kwargs", "message"),
    [
        (
            {"raises": FileNotFoundError(2, "No such file", "xclip")},
            "xclip was not found on PATH",
        ),
        ({"raises": PermissionError(13, "denied", "xclip")}, "could not run xclip"),
        (
            {"raises": subprocess.TimeoutExpired("xclip", 10)},
            "did not answer TARGETS within 10s",
        ),
        (
            {"answers": {"TARGETS": _done(1, stderr=NO_DISPLAY)}},
            "Can't open display",
        ),
        (
            {
                "answers": {
                    "TARGETS": _done(stdout=HTML_TARGETS),
                    "text/html": _done(
                        1, stderr=b"Error: target text/html not available\n"
                    ),
                }
            },
            "xclip -t text/html exited with status 1",
        ),
    ],
    ids=["no-xclip", "not-executable", "timeout", "no-display", "html-unreadable"],
)
def test_helper_failure_is_actionable_content_error(x11_xclip, helper_kwargs, message):
    x11_xclip(**helper_kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert not isinstance(info.value, clipboard.ClipboardImageError)
    text = str(info.value)
    assert "Linux X11 HTML clipboard read failed" in text
    assert message in text
    assert "xclip" in text and "apt install xclip" in text


def test_timeout_on_html_body_is_content_error(x11_xclip):
    x11_xclip(
        answers={
            "TARGETS": _done(stdout=HTML_TARGETS),
            "text/html": subprocess.TimeoutExpired("xclip", 10),
        }
    )
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert "did not answer text/html within 10s" in str(info.value)

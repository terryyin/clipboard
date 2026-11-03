"""Desktop-free tests for the Linux Wayland ``text/html`` reader behind paste_html.

``subprocess.run`` is replaced with a scripted ``wl-paste``, so no test here
touches a real Wayland clipboard or needs a compositor / wl-clipboard.
"""

import subprocess

import pytest
from html_offer import FRAGMENT

import clipboard
from clipboard import _desktop, _html_native_linux

LIST_TYPES = ("wl-paste", "--list-types")
READ_HTML = ("wl-paste", "--no-newline", "--type", "text/html")
HTML_TYPES = b"text/html\ntext/plain;charset=utf-8\nUTF8_STRING\n"
TEXT_TYPES = b"text/plain;charset=utf-8\ntext/plain\nUTF8_STRING\nTEXT\nSTRING\n"
IMAGE_TYPES = b"image/png\n"
FILES_TYPES = b"text/uri-list\nx-special/gnome-copied-files\n"
# wl-clipboard 2.2.x / 2.3.x and 2.0 / 2.1 on an empty selection (exit 1).
NOTHING_COPIED = b"Nothing is copied\n"
NO_SELECTION = b"No selection\n"
NO_COMPOSITOR = (
    b"Failed to connect to a Wayland server: No such file or directory\n"
    b"Note: WAYLAND_DISPLAY is set to wayland-1\n"
)
NO_SEAT = (
    b"The compositor does not seem to implement seat,"
    b" which is required for wl-clipboard to work\n"
)


def _done(returncode=0, stdout=b"", stderr=b""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class _WlPaste:
    """Stand-in for ``subprocess.run``: answers (or raises) per exact argv."""

    def __init__(self, answers=None, raises=None):
        self.answers = answers or {}
        self.raises = raises
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.raises is not None:
            raise self.raises
        key = tuple(args)
        if key not in self.answers:
            raise AssertionError(f"unexpected helper argv {args!r}")
        answer = self.answers[key]
        if isinstance(answer, BaseException):
            raise answer
        return answer


@pytest.fixture
def wayland_wl_paste(monkeypatch, restore_html_clipboard_reader, fake_platform):
    """Default reader on a pretend Linux Wayland session with a scripted wl-paste."""
    fake_platform("linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-1")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    clipboard.set_html_clipboard_reader(None)

    def install(**kwargs):
        helper = _WlPaste(**kwargs)
        # ``--list-types`` lives in ``_desktop``; ``--type`` read stays local.
        monkeypatch.setattr(_desktop.subprocess, "run", helper)
        monkeypatch.setattr(_html_native_linux.subprocess, "run", helper)
        return helper

    return install


def test_text_html_type_returns_fragment_with_exact_argv(wayland_wl_paste):
    helper = wayland_wl_paste(
        answers={
            LIST_TYPES: _done(stdout=HTML_TYPES),
            READ_HTML: _done(stdout=FRAGMENT.encode("utf-8")),
        }
    )
    assert clipboard.paste_html() == FRAGMENT
    assert [args for args, _ in helper.calls] == [list(LIST_TYPES), list(READ_HTML)]


def test_session_type_alone_selects_wayland_reader(wayland_wl_paste, monkeypatch):
    monkeypatch.delenv("WAYLAND_DISPLAY")
    helper = wayland_wl_paste(answers={LIST_TYPES: _done(stdout=TEXT_TYPES)})
    assert clipboard.paste_html() is None
    assert [args[0] for args, _ in helper.calls] == ["wl-paste"]


def test_utf16_bom_body_decodes_through_paste_html(wayland_wl_paste):
    raw = b"\xff\xfe" + FRAGMENT.encode("utf-16-le")
    wayland_wl_paste(
        answers={LIST_TYPES: _done(stdout=HTML_TYPES), READ_HTML: _done(stdout=raw)}
    )
    assert clipboard.paste_html() == FRAGMENT


@pytest.mark.parametrize(
    "types",
    [
        TEXT_TYPES,
        IMAGE_TYPES,
        FILES_TYPES,
        b"text/html;charset=utf-8\ntext/html-ish\n",
        b"",
    ],
    ids=["text-only", "image-only", "file-list", "lookalike", "no-types"],
)
def test_types_without_text_html_is_none(wayland_wl_paste, types):
    helper = wayland_wl_paste(answers={LIST_TYPES: _done(stdout=types)})
    assert clipboard.paste_html() is None
    assert len(helper.calls) == 1


@pytest.mark.parametrize(
    "stderr", [NOTHING_COPIED, NO_SELECTION], ids=["wl-clipboard-2.2+", "2.0-2.1"]
)
def test_empty_clipboard_is_none(wayland_wl_paste, stderr):
    helper = wayland_wl_paste(answers={LIST_TYPES: _done(1, stderr=stderr)})
    assert clipboard.paste_html() is None
    assert len(helper.calls) == 1


def test_every_helper_call_is_bounded_and_read_only(wayland_wl_paste):
    helper = wayland_wl_paste(
        answers={
            LIST_TYPES: _done(stdout=HTML_TYPES),
            READ_HTML: _done(stdout=b"<i>x</i>"),
        }
    )
    clipboard.paste_html()
    assert len(helper.calls) == 2
    for args, kwargs in helper.calls:
        assert args[0] == "wl-paste"
        assert not {"wl-copy", "--clear", "--watch", "--primary", "-p"} & set(args)
        assert kwargs["stdin"] is subprocess.DEVNULL
        assert (
            kwargs["timeout"] == _html_native_linux._WAYLAND_HTML_READ_TIMEOUT_SECONDS
        )


@pytest.mark.parametrize(
    ("helper_kwargs", "message"),
    [
        (
            {"raises": FileNotFoundError(2, "No such file", "wl-paste")},
            "wl-paste was not found on PATH",
        ),
        (
            {"raises": PermissionError(13, "denied", "wl-paste")},
            "could not run wl-paste",
        ),
        (
            {"raises": subprocess.TimeoutExpired("wl-paste", 10)},
            "did not answer --list-types within 10s",
        ),
        (
            {"answers": {LIST_TYPES: _done(1, stderr=NO_COMPOSITOR)}},
            "Failed to connect to a Wayland server",
        ),
        (
            {"answers": {LIST_TYPES: _done(1, stderr=NO_SEAT)}},
            "does not seem to implement seat",
        ),
        (
            {
                "answers": {
                    LIST_TYPES: _done(stdout=HTML_TYPES),
                    READ_HTML: _done(1, stderr=NOTHING_COPIED),
                }
            },
            "wl-paste --type text/html exited with status 1: Nothing is copied",
        ),
    ],
    ids=[
        "no-wl-paste",
        "not-executable",
        "timeout",
        "no-compositor",
        "no-seat",
        "html-unreadable",
    ],
)
def test_helper_failure_is_actionable_content_error(
    wayland_wl_paste, helper_kwargs, message
):
    wayland_wl_paste(**helper_kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert not isinstance(info.value, clipboard.ClipboardImageError)
    text = str(info.value)
    assert "Linux Wayland HTML clipboard read failed" in text
    assert message in text
    assert "wl-paste" in text and "apt install wl-clipboard" in text


def test_timeout_on_html_body_is_content_error(wayland_wl_paste):
    wayland_wl_paste(
        answers={
            LIST_TYPES: _done(stdout=HTML_TYPES),
            READ_HTML: subprocess.TimeoutExpired("wl-paste", 10),
        }
    )
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert "did not answer --type text/html within 10s" in str(info.value)

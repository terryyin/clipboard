"""Exercise the public text API without requiring a desktop clipboard in CI."""

import json
import subprocess
import sys
from importlib.metadata import version

import pyperclip
import pytest

import clipboard


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "",
        "Hello, 世界 👋",
        "  héllo 👋\nline 2 ",
        "line 1\nline 2",
        "line 1\r\nline 2\r\n",
        "\t leading and trailing whitespace \n",
    ],
)
def test_copy_paste_round_trip_through_text_seam(fake_text_clipboard, value):
    clipboard.copy(value)

    assert fake_text_clipboard.writes == [value]
    result = clipboard.paste()
    assert result == value
    assert type(result) is str


@pytest.mark.parametrize(("value", "expected"), [(42, "42"), (1.5, "1.5")])
def test_copy_coerces_non_str_like_pyperclip(fake_text_clipboard, value, expected):
    clipboard.copy(value)

    assert fake_text_clipboard.writes == [expected]
    assert clipboard.paste() == expected


def test_copy_reports_unconvertible_value(fake_text_clipboard):
    class Unprintable:
        def __str__(self):
            raise ValueError("no text form")

    with pytest.raises(clipboard.ClipboardContentError, match="no text form"):
        clipboard.copy(Unprintable())
    assert fake_text_clipboard.writes == []


@pytest.mark.parametrize(
    ("value", "problem"),
    [("a\x00b", "NUL"), ("\ud800", "UTF-8"), ("ok\udfffok", "UTF-8")],
)
def test_copy_rejects_lossy_text_before_writing(fake_text_clipboard, value, problem):
    fake_text_clipboard.contents = "previous"

    with pytest.raises(clipboard.ClipboardContentError, match=problem):
        clipboard.copy(value)

    assert fake_text_clipboard.writes == []
    assert clipboard.paste() == "previous"


def test_paste_returns_empty_string_when_reader_offers_no_text(
    restore_text_clipboard,
):
    clipboard.set_text_clipboard_reader(lambda: None)

    result = clipboard.paste()
    assert result == ""
    assert type(result) is str


@pytest.mark.parametrize(
    "error",
    [
        pyperclip.PyperclipException("no mechanism"),
        FileNotFoundError(2, "No such file or directory", "xclip"),
        OSError("display gone"),
        RuntimeError("helper crashed"),
    ],
)
def test_backend_failures_become_content_errors(restore_text_clipboard, error):
    def failing_writer(text):
        raise error

    def failing_reader():
        raise error

    clipboard.set_text_clipboard_writer(failing_writer)
    clipboard.set_text_clipboard_reader(failing_reader)

    with pytest.raises(clipboard.ClipboardContentError, match="text write") as wrote:
        clipboard.copy("x")
    assert wrote.value.__cause__ is error

    with pytest.raises(clipboard.ClipboardContentError, match="text read") as read:
        clipboard.paste()
    assert read.value.__cause__ is error


def test_paste_rejects_non_str_reader_result(restore_text_clipboard):
    clipboard.set_text_clipboard_reader(lambda: b"bytes")

    with pytest.raises(clipboard.ClipboardContentError, match="bytes"):
        clipboard.paste()


def test_set_none_restores_default_text_backends(fake_text_clipboard):
    assert clipboard._text_clipboard_writer is not (
        clipboard._default_text_clipboard_writer
    )

    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)

    assert clipboard._text_clipboard_writer is clipboard._default_text_clipboard_writer
    assert clipboard._text_clipboard_reader is clipboard._default_text_clipboard_reader


_SUBPROCESS_PRELUDE = """
import json
import sys
import pyperclip

contents = None
def as_wsl_session():
    # A delegated session shape on every CI host (Linux without DISPLAY,
    # macOS, Windows): WSL keeps pyperclip's bridge.
    from clipboard import _desktop_text, _platform
    _platform.current = lambda: "linux"
    _desktop_text._read_proc_version = lambda: "Linux 5.15-microsoft-standard-WSL2"
def copy(value):
    global contents
    contents = value
def paste():
    return contents
"""


def _run(script, *args):
    result = subprocess.run(
        [sys.executable, "-c", script, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_import_does_not_resolve_pyperclip_mechanism():
    # A fresh interpreter gives the same first-import behavior as a consumer.
    observed = _run(
        """
import json
import pyperclip
import clipboard
print(json.dumps(pyperclip.is_available()))
"""
    )
    assert observed is False


@pytest.mark.parametrize("value", ["", "Hello, 世界 👋", "line 1\r\nline 2"])
def test_default_backend_delegates_to_lazily_resolved_pyperclip(value):
    # The default seam must reach whatever mechanism pyperclip resolves on
    # first use (here an in-memory one), not a mechanism bound at import.
    observed = _run(
        _SUBPROCESS_PRELUDE
        + """
pyperclip.determine_clipboard = lambda: (copy, paste)

import clipboard
as_wsl_session()
assert not pyperclip.is_available()
clipboard.copy(json.loads(sys.argv[1]))
print(json.dumps([clipboard.paste(), pyperclip.is_available()]))
""",
        json.dumps(value),
    )
    assert observed == [value, True]


def test_set_clipboard_alone_does_not_displace_owned_backend():
    observed = _run(
        """
import json
import pyperclip

pyperclip.set_clipboard("pbcopy")
assert pyperclip.is_available()
from clipboard import _platform, _text
_platform.current = lambda: "darwin"
print(json.dumps(_text._select_text_backend()))
"""
    )
    assert observed == "macos"


def test_default_backend_translates_pyperclip_failure():
    observed = _run(
        _SUBPROCESS_PRELUDE
        + """

def fail(*args):
    raise pyperclip.PyperclipException("no copy/paste mechanism")

pyperclip.determine_clipboard = lambda: (fail, fail)

import clipboard
as_wsl_session()
out = []
for call in (lambda: clipboard.copy("x"), clipboard.paste):
    try:
        call()
    except clipboard.ClipboardContentError as exc:
        out.append([str(exc), type(exc.__cause__).__name__])
print(json.dumps(out))
"""
    )
    assert [cause for _, cause in observed] == [
        "PyperclipException",
        "PyperclipException",
    ]
    assert all("no copy/paste mechanism" in message for message, _ in observed)


def test_public_version_matches_distribution():
    assert clipboard.VERSION == version("clipboard")

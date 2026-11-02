"""Desktop-free tests for the owned Linux Wayland text path (wl-clipboard).

``subprocess.run`` and ``subprocess.Popen`` are replaced by an in-memory model
of the Wayland selection and wl-copy / wl-paste, so no compositor is touched.
``text_session("linux", {"WAYLAND_DISPLAY": "wayland-0"}, ("wl-copy",
"wl-paste"))`` routes the public ``copy`` / ``paste`` through the default
backend.
"""

import subprocess

import pytest
from fake_pyperclip import FakePyperclip
from fake_wl_clipboard_text import WL_COPY_TEXT_FAMILY, FakeWayland

import clipboard
from clipboard import _text, _text_native_wayland

TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "
LIST = ["wl-paste", "--list-types"]
STALE_SOCKET = b"Failed to connect to a Wayland server: No such file or directory\n"


def read(mime_type):
    return ["wl-paste", "-n", "-t", mime_type]


@pytest.fixture
def wayland(text_session, monkeypatch):
    fake = FakeWayland()
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(subprocess, "Popen", fake.popen)
    text_session("linux", {"WAYLAND_DISPLAY": "wayland-0"}, ("wl-copy", "wl-paste"))
    fake.pyperclip = FakePyperclip(monkeypatch)
    return fake


def test_wayland_session_selects_the_owned_path(wayland):
    assert _text._select_text_backend() == "wayland"


def test_paste_lists_types_then_reads_the_utf8_type_exactly(wayland):
    wayland.offers = dict.fromkeys(WL_COPY_TEXT_FAMILY, TEXT.encode())
    wayland.offers["STRING"] = b"wrong"

    assert clipboard.paste() == TEXT
    assert [c["cmd"] for c in wayland.calls] == [LIST, read("text/plain;charset=utf-8")]
    assert wayland.pyperclip.reads == 0


@pytest.mark.parametrize(
    ("listed", "chosen"),
    [
        (["text/html", "text/plain", "UTF8_STRING"], "text/plain"),
        (["TEXT", "UTF8_STRING", "STRING"], "UTF8_STRING"),
        (["STRING", "TEXT"], "TEXT"),
        (["image/png", "text/plain;charset=UTF-8"], "text/plain;charset=UTF-8"),
    ],
)
def test_first_preferred_text_type_is_read(wayland, listed, chosen):
    wayland.offers = dict.fromkeys(listed, b"x")

    assert clipboard.paste() == "x"
    assert wayland.calls[-1]["cmd"] == read(chosen)


def test_string_only_offer_is_decoded_as_latin_1(wayland):
    wayland.offers = {"STRING": "café ½ naïve".encode("latin-1")}

    assert clipboard.paste() == "café ½ naïve"


def test_text_ending_in_newline_is_returned_untouched(wayland):
    wayland.offers = {"text/plain;charset=utf-8": b"line 1\r\nline 2\n"}

    assert clipboard.paste() == "line 1\r\nline 2\n"


@pytest.mark.parametrize(
    "offers", [None, {"image/png": b"\x89PNG"}, {"text/html": b"<b>x</b>"}]
)
def test_nothing_copied_or_no_text_type_reads_empty_string(wayland, offers):
    wayland.offers = offers

    result = clipboard.paste()
    assert result == ""
    assert type(result) is str
    assert [c["cmd"] for c in wayland.calls] == [LIST]


def test_no_selection_wording_reads_empty_string(wayland):
    wayland.run_failure = (1, b"No selection\n")

    assert clipboard.paste() == ""


def test_undecodable_utf8_offer_is_a_content_error(wayland):
    wayland.offers = {"text/plain": b"h\xe9llo"}

    with pytest.raises(clipboard.ClipboardContentError, match="not valid utf-8") as e:
        clipboard.paste()
    assert isinstance(e.value.__cause__, UnicodeDecodeError)


@pytest.mark.parametrize(
    ("stderr", "quoted"),
    [
        (STALE_SOCKET, "Failed to connect to a Wayland server"),
        (b"wl-paste: something unexpected\n", "something unexpected"),
        (b"Nothing is copied (yet)\n", "Nothing is copied (yet)"),
        (b"", "exited with status 1"),
    ],
)
def test_other_wl_paste_failures_raise_quoting_stderr(wayland, stderr, quoted):
    wayland.run_failure = (1, stderr)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.paste()
    message = str(caught.value)
    assert "Wayland clipboard text read failed" in message
    assert "wl-paste --list-types exited with status 1" in message
    assert quoted in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)


def test_listed_text_that_is_not_delivered_is_an_error(wayland, monkeypatch):
    wayland.offers = {"text/plain": b"x"}

    def replaced_after_listing(cmd, **kwargs):
        if cmd != LIST:
            wayland.offers = {"image/png": b"\x89PNG"}
        return wayland.run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", replaced_after_listing)
    with pytest.raises(
        clipboard.ClipboardContentError, match="No suitable type of content copied"
    ):
        clipboard.paste()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (subprocess.TimeoutExpired(LIST, 10.0), "did not answer within the 10s bound"),
        (
            FileNotFoundError(2, "No such file", "wl-paste"),
            "sudo apt-get install wl-clipboard",
        ),
        (PermissionError(13, "Permission denied"), "Permission denied"),
    ],
)
def test_reader_helper_exceptions_become_content_errors(wayland, error, expected):
    wayland.run_error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        clipboard.paste()
    assert caught.value.__cause__ is error
    assert wayland.pyperclip.reads == 0


def test_reader_shares_one_bound_across_its_helper_runs(wayland, monkeypatch):
    wayland.offers = {"text/plain": b"x"}
    clock = [100.0, 100.0, 107.5]
    monkeypatch.setattr(
        _text_native_wayland.time,
        "monotonic",
        lambda: clock.pop(0) if clock else 107.5,
    )

    assert clipboard.paste() == "x"
    assert [c["timeout"] for c in wayland.calls] == [10.0, 2.5]


def test_copy_pipes_utf8_to_wl_copy_with_an_explicit_text_type(wayland):
    wayland.offers = {"text/plain": b"previous"}

    clipboard.copy(TEXT)

    (proc,) = wayland.popens
    assert proc.cmd == ["wl-copy", "--type", "text/plain;charset=utf-8"]
    assert proc.stdin is subprocess.PIPE
    assert proc.input == TEXT.encode("utf-8")
    (bound,) = wayland.communicate_timeouts
    assert 9.0 < bound <= 10.0
    assert wayland.pyperclip.writes == []
    assert clipboard.paste() == TEXT


def test_copy_empty_clears_the_selection_then_paste_is_empty(wayland):
    wayland.offers = {"text/plain": b"keep"}

    clipboard.copy("")

    (proc,) = wayland.popens
    assert proc.cmd == ["wl-copy", "--clear"]
    assert proc.stdin is subprocess.DEVNULL
    assert proc.input is None
    assert clipboard.paste() == ""


def test_rejected_text_never_starts_wl_copy(wayland):
    for bad in ("a\x00b", "\ud800"):
        with pytest.raises(clipboard.ClipboardContentError):
            clipboard.copy(bad)
    assert wayland.popens == []


@pytest.mark.parametrize("text", ["x", ""])
def test_wl_copy_failure_raises_quoting_its_stderr(wayland, text):
    wayland.offers = {"text/plain": b"previous"}
    wayland.copy_exit = (1, STALE_SOCKET)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy(text)
    message = str(caught.value)
    assert "Wayland clipboard text write failed" in message
    assert "exited with status 1" in message
    assert "Failed to connect to a Wayland server" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)
    assert wayland.offers == {"text/plain": b"previous"}


def test_stalled_wl_copy_is_killed_and_raises_after_the_bound(wayland):
    wayland.stalls = True

    with pytest.raises(
        clipboard.ClipboardContentError, match="did not finish within the 10s bound"
    ) as caught:
        clipboard.copy("x")
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert wayland.popens[0].killed is True


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            FileNotFoundError(2, "No such file", "wl-copy"),
            "wl-copy was not found on PATH; install wl-clipboard",
        ),
        (PermissionError(13, "Permission denied"), "Permission denied"),
    ],
)
def test_writer_launch_failures_become_content_errors(wayland, error, expected):
    wayland.popen_error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        clipboard.copy("x")
    assert caught.value.__cause__ is error
    assert wayland.pyperclip.writes == []

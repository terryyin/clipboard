"""Desktop-free tests for the owned Linux X11 text path (``xclip``).

``subprocess.run`` and ``subprocess.Popen`` are replaced by an in-memory model
of the X11 CLIPBOARD and its xclip owners, so no display is touched.
``text_session("linux", {"DISPLAY": ":0"}, ("xclip",))`` routes the public
``copy`` / ``paste`` through the default backend.
"""

import subprocess

import pytest
from fake_pyperclip import FakePyperclip
from fake_xclip_text import FakeX11

import clipboard
from clipboard import _desktop, _text_native_x11

TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "
TARGETS = ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"]
UTF8 = ["xclip", "-selection", "clipboard", "-o", "-t", "UTF8_STRING"]
STRING = ["xclip", "-selection", "clipboard", "-o", "-t", "STRING"]
WRITE = ["xclip", "-selection", "clipboard", "-i"]
DEAD_DISPLAY = b"Error: Can't open display: :99\n"


@pytest.fixture
def x11(text_session, monkeypatch):
    fake = FakeX11()
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(subprocess, "Popen", fake.popen)
    monkeypatch.setattr(
        _desktop.os,
        "killpg",
        lambda pid, sig: fake.killed.append(pid),
        raising=False,  # os.killpg is POSIX-only; these tests also run on Windows
    )
    text_session("linux", {"DISPLAY": ":0"}, ("xclip",))
    fake.pyperclip = FakePyperclip(monkeypatch)
    return fake


def test_paste_lists_targets_then_reads_utf8_string_exactly(x11):
    x11.offers = {"UTF8_STRING": TEXT.encode(), "STRING": b"wrong"}

    assert clipboard.paste() == TEXT
    assert [c["cmd"] for c in x11.calls] == [TARGETS, UTF8]
    assert x11.pyperclip.reads == 0


def test_string_only_owner_is_decoded_as_latin_1(x11):
    x11.offers = {"STRING": "café ½ naïve".encode("latin-1")}

    assert clipboard.paste() == "café ½ naïve"
    assert [c["cmd"] for c in x11.calls] == [TARGETS, STRING]


@pytest.mark.parametrize("offers", [None, {"image/png": b"\x89PNG"}, {"TEXT": b"x"}])
def test_no_owner_or_no_text_target_reads_empty_string(x11, offers):
    x11.offers = offers

    result = clipboard.paste()
    assert result == ""
    assert type(result) is str
    assert [c["cmd"] for c in x11.calls] == [TARGETS]


def test_newer_xclip_no_owner_wording_reads_empty_string(x11, monkeypatch):
    newer = b"xclip: Error: There is no owner for the CLIPBOARD selection\n"

    def no_owner(cmd, **_kwargs):
        x11.calls.append({"cmd": cmd})
        return subprocess.CompletedProcess(cmd, 1, b"", newer)

    monkeypatch.setattr(subprocess, "run", no_owner)

    assert clipboard.paste() == ""
    assert [c["cmd"] for c in x11.calls] == [TARGETS]


def test_undecodable_utf8_string_is_a_content_error(x11):
    x11.offers = {"UTF8_STRING": b"h\xe9llo"}

    with pytest.raises(
        clipboard.ClipboardContentError, match="not valid utf-8"
    ) as caught:
        clipboard.paste()
    assert isinstance(caught.value.__cause__, UnicodeDecodeError)


@pytest.mark.parametrize(
    ("stderr", "quoted"),
    [
        (DEAD_DISPLAY, "Can't open display: :99"),
        (b"xclip: something unexpected\n", "something unexpected"),
        (b"", "exited with status 1"),
    ],
)
def test_other_xclip_failures_raise_quoting_stderr(x11, stderr, quoted):
    x11.run_failure = (1, stderr)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.paste()
    message = str(caught.value)
    assert "X11 clipboard text read failed" in message
    assert quoted in message
    assert "-t TARGETS exited with status 1" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)


def test_advertised_text_that_is_not_delivered_is_an_error(x11, monkeypatch):
    x11.offers = {"UTF8_STRING": TEXT.encode()}

    def vanish_after_listing(cmd, **kwargs):
        if cmd[-1] != "TARGETS":
            x11.offers = {}
        return x11.run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", vanish_after_listing)
    with pytest.raises(
        clipboard.ClipboardContentError, match="UTF8_STRING not available"
    ):
        clipboard.paste()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            subprocess.TimeoutExpired(TARGETS, 10.0),
            "did not answer within the 10s bound",
        ),
        (FileNotFoundError(2, "No such file", "xclip"), "sudo apt-get install xclip"),
        (PermissionError(13, "Permission denied"), "Permission denied"),
    ],
)
def test_reader_helper_exceptions_become_content_errors(x11, error, expected):
    # A stalled owner (seed example 7) surfaces as the bounded run's timeout.
    x11.run_error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        clipboard.paste()
    assert caught.value.__cause__ is error
    assert x11.pyperclip.reads == 0


def test_reader_shares_one_bound_across_its_helper_runs(x11, monkeypatch):
    x11.offers = {"UTF8_STRING": b"x"}
    # Deadline at 100 s; the text read starts 7.5 s later with 2.5 s left.
    clock = [100.0, 100.0, 107.5]
    monkeypatch.setattr(
        _text_native_x11.time, "monotonic", lambda: clock.pop(0) if clock else 107.5
    )

    assert clipboard.paste() == "x"
    assert [c["timeout"] for c in x11.calls] == [10.0, 2.5]


def test_copy_feeds_a_background_owner_and_waits_for_its_bytes(x11):
    x11.offers = {"UTF8_STRING": b"previous owner's text"}
    x11.delay = 2

    clipboard.copy(TEXT)

    (popen,) = x11.popens
    assert popen["cmd"] == WRITE
    assert popen["owner"].data == TEXT.encode("utf-8")
    # The previous owner's UTF8_STRING was never mistaken for the new offer.
    readbacks = [c["cmd"] for c in x11.calls]
    assert readbacks == [UTF8, UTF8, UTF8]
    assert x11.offers == {"UTF8_STRING": TEXT.encode("utf-8")}
    assert x11.pyperclip.writes == []
    assert clipboard.paste() == TEXT


def test_copy_empty_then_paste_is_empty(x11):
    x11.offers = {"UTF8_STRING": b"keep"}

    clipboard.copy("")
    assert x11.popens[0]["owner"].data == b""
    assert clipboard.paste() == ""


def test_rejected_text_never_starts_xclip(x11):
    for bad in ("a\x00b", "\ud800"):
        with pytest.raises(clipboard.ClipboardContentError):
            clipboard.copy(bad)
    assert x11.popens == []


def test_owner_exiting_early_raises_quoting_its_stderr(x11):
    x11.owner_exit = (1, DEAD_DISPLAY)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy("x")
    message = str(caught.value)
    assert "X11 clipboard text write failed" in message
    assert "exited with status 1" in message
    assert "Can't open display: :99" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)


def test_owner_that_never_offers_raises_after_the_bound(x11, monkeypatch):
    monkeypatch.setattr(_text_native_x11, "_X11_TEXT_WRITE_TIMEOUT_S", 0.2)
    x11.offers = {"UTF8_STRING": b"previous"}
    x11.never_offers = True

    with pytest.raises(
        clipboard.ClipboardContentError, match="did not serve the text as UTF8_STRING"
    ) as caught:
        clipboard.copy("x")
    assert "0.2s bound" in str(caught.value)
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert x11.killed == [4242]


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (FileNotFoundError(2, "No such file", "xclip"), "sudo apt-get install xclip"),
        (PermissionError(13, "Permission denied"), "Permission denied"),
    ],
)
def test_writer_launch_failures_become_content_errors(x11, error, expected):
    x11.popen_error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        clipboard.copy("x")
    assert caught.value.__cause__ is error
    assert x11.pyperclip.writes == []

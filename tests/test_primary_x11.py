"""Desktop-free tests for ``copy_primary`` / ``paste_primary`` on Linux X11.

The in-memory ``FakeX11`` keeps CLIPBOARD and PRIMARY as separate selections
with separate owners, so these show that PRIMARY calls run only
``xclip -selection primary`` and that ``copy`` / ``paste`` keep running only
``-selection clipboard`` (seed SEED-001#primary-selection examples 1–4, 9).
"""

import subprocess

import pytest
from fake_pyperclip import FakePyperclip
from fake_xclip_text import FakeX11

import clipboard
from clipboard import _desktop, _text_native_x11


def _xclip(selection, *args):
    return ["xclip", "-selection", selection, *args]


P_TARGETS = _xclip("primary", "-o", "-t", "TARGETS")
P_UTF8 = _xclip("primary", "-o", "-t", "UTF8_STRING")
P_STRING = _xclip("primary", "-o", "-t", "STRING")
P_WRITE = _xclip("primary", "-i")
C_TARGETS = _xclip("clipboard", "-o", "-t", "TARGETS")
C_UTF8 = _xclip("clipboard", "-o", "-t", "UTF8_STRING")
C_WRITE = _xclip("clipboard", "-i")
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
    fake.offers = {"UTF8_STRING": b"copied"}
    fake.primary = {"UTF8_STRING": b"selected"}
    return fake


def _cmds(x11):
    return [c["cmd"] for c in x11.calls]


def test_paste_primary_reads_primary_and_paste_still_reads_clipboard(x11):
    assert clipboard.paste_primary() == "selected"
    assert _cmds(x11) == [P_TARGETS, P_UTF8]

    x11.calls.clear()
    assert clipboard.paste() == "copied"
    assert _cmds(x11) == [C_TARGETS, C_UTF8]
    assert x11.pyperclip.reads == 0


def test_copy_primary_owns_primary_and_leaves_clipboard(x11):
    x11.delay = 1

    clipboard.copy_primary("for middle click")

    (popen,) = x11.popens
    assert popen["cmd"] == P_WRITE
    assert popen["owner"].data == b"for middle click"
    # The previous PRIMARY owner was never mistaken for the new offer.
    assert _cmds(x11) == [P_UTF8, P_UTF8]
    assert x11.primary == {"UTF8_STRING": b"for middle click"}
    assert x11.offers == {"UTF8_STRING": b"copied"}
    assert clipboard.paste() == "copied"
    assert clipboard.paste_primary() == "for middle click"
    assert x11.pyperclip.writes == []


def test_copy_leaves_primary(x11):
    clipboard.copy("new copy")

    assert [p["cmd"] for p in x11.popens] == [C_WRITE]
    assert all(cmd[2] == "clipboard" for cmd in _cmds(x11))
    assert clipboard.paste() == "new copy"
    assert clipboard.paste_primary() == "selected"


def test_copy_primary_coerces_like_copy(x11):
    clipboard.copy_primary(42)

    assert x11.popens[0]["owner"].data == b"42"


@pytest.mark.parametrize(
    "stderr",
    [
        b"Error: target TARGETS not available\n",  # xclip 0.13 (observed on Xvfb)
        b"xclip: Error: There is no owner for the PRIMARY selection\n",
    ],
)
def test_unowned_primary_reads_empty_string(x11, monkeypatch, stderr):
    def no_owner(cmd, **_kwargs):
        x11.calls.append({"cmd": cmd})
        return subprocess.CompletedProcess(cmd, 1, b"", stderr)

    monkeypatch.setattr(subprocess, "run", no_owner)

    result = clipboard.paste_primary()
    assert result == ""
    assert type(result) is str
    assert _cmds(x11) == [P_TARGETS]


@pytest.mark.parametrize("primary", [None, {"image/png": b"\x89PNG"}])
def test_primary_without_text_reads_empty_string(x11, primary):
    x11.primary = primary

    assert clipboard.paste_primary() == ""
    assert _cmds(x11) == [P_TARGETS]


def test_string_only_primary_is_decoded_as_latin_1(x11):
    x11.primary = {"STRING": "café ½".encode("latin-1")}

    assert clipboard.paste_primary() == "café ½"
    assert _cmds(x11) == [P_TARGETS, P_STRING]


def test_line_endings_are_untranslated(x11):
    x11.primary = {"UTF8_STRING": b"a\r\nb\n"}

    assert clipboard.paste_primary() == "a\r\nb\n"


@pytest.mark.parametrize("bad", ["a\x00b", "\ud800"])
def test_rejected_text_never_starts_xclip_and_primary_stays(x11, bad):
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.copy_primary(bad)

    assert x11.popens == []
    assert x11.calls == []
    assert clipboard.paste_primary() == "selected"


def test_injected_text_seams_never_receive_primary_traffic(x11):
    seen = []
    clipboard.set_text_clipboard_writer(lambda text: seen.append(("write", text)))
    clipboard.set_text_clipboard_reader(lambda: seen.append("read") or "seam")

    clipboard.copy_primary("x")
    assert clipboard.paste_primary() == "x"

    assert [p["cmd"] for p in x11.popens] == [P_WRITE]
    assert _cmds(x11)[-2:] == [P_TARGETS, P_UTF8]
    assert seen == []
    assert x11.offers == {"UTF8_STRING": b"copied"}


def test_read_failure_names_the_primary_selection(x11):
    x11.run_failure = (1, DEAD_DISPLAY)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.paste_primary()
    message = str(caught.value)
    assert "primary selection" in message
    assert " ".join(P_TARGETS) in message
    assert "Can't open display: :99" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)


def test_write_failure_names_the_primary_selection(x11):
    x11.owner_exit = (1, DEAD_DISPLAY)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_primary("x")
    message = str(caught.value)
    assert "primary selection" in message
    assert " ".join(P_WRITE) in message
    assert "Can't open display: :99" in message
    assert x11.offers == {"UTF8_STRING": b"copied"}


def test_owner_that_never_offers_raises_after_the_bound(x11, monkeypatch):
    monkeypatch.setattr(_text_native_x11, "_X11_TEXT_WRITE_TIMEOUT_S", 0.2)
    x11.never_offers = True

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_primary("x")
    assert "primary selection" in str(caught.value)
    assert "0.2s bound" in str(caught.value)
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert x11.killed == [4242]
    assert all(cmd[2] == "primary" for cmd in _cmds(x11))


def test_missing_xclip_at_run_time_names_the_install_hint(x11):
    error = FileNotFoundError(2, "No such file", "xclip")
    x11.run_error = error

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.paste_primary()
    assert "xclip" in str(caught.value)
    assert caught.value.__cause__ is error
    assert x11.pyperclip.reads == 0

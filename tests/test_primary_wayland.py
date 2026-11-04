"""Desktop-free tests for ``copy_primary`` / ``paste_primary`` on Linux Wayland.

The in-memory ``FakeWayland`` keeps the regular selection (CLIPBOARD) and
PRIMARY apart, so these show that PRIMARY calls run only wl-clipboard
``--primary`` argv and that ``copy`` / ``paste`` keep their argv without it
(seed SEED-001#primary-selection examples 5–6). Unsupported compositors,
dropped writes, bounds and helper failures are in
``test_primary_wayland_failures``.
"""

import subprocess

import pytest
from fake_wl_clipboard_text import install_fake_wayland, text_offer

import clipboard

UTF8 = "text/plain;charset=utf-8"
P_LIST = ["wl-paste", "--primary", "--list-types"]
P_READ = ["wl-paste", "--primary", "-n", "-t", UTF8]
P_WRITE = ["wl-copy", "--primary", "--type", UTF8]
C_LIST = ["wl-paste", "--list-types"]
C_READ = ["wl-paste", "-n", "-t", UTF8]
C_WRITE = ["wl-copy", "--type", UTF8]


@pytest.fixture
def wayland(text_session, monkeypatch):
    fake = install_fake_wayland(text_session, monkeypatch)
    fake.offers = text_offer("copied")
    fake.primary = text_offer("selected")
    return fake


def _cmds(wayland):
    return [c["cmd"] for c in wayland.calls]


def test_paste_primary_reads_primary_and_paste_still_reads_clipboard(wayland):
    assert clipboard.paste_primary() == "selected"
    assert _cmds(wayland) == [P_LIST, P_READ]

    wayland.calls.clear()
    assert clipboard.paste() == "copied"
    assert _cmds(wayland) == [C_LIST, C_READ]
    assert wayland.pyperclip.reads == 0


def test_copy_primary_sets_primary_confirms_it_and_leaves_clipboard(wayland):
    clipboard.copy_primary("for middle click")

    (proc,) = wayland.popens
    assert proc.cmd == P_WRITE
    # Through the shared launcher: a file stdin, never a pipe.
    assert proc.stdin is not subprocess.PIPE
    assert proc.input == b"for middle click"
    # Exact read-back of the written type confirms the write.
    assert _cmds(wayland) == [P_READ]
    assert wayland.primary == text_offer("for middle click")
    assert wayland.offers == text_offer("copied")
    assert clipboard.paste() == "copied"
    assert clipboard.paste_primary() == "for middle click"
    assert wayland.pyperclip.writes == []


def test_copy_leaves_primary(wayland):
    clipboard.copy("new copy")

    assert [proc.cmd for proc in wayland.popens] == [C_WRITE]
    assert clipboard.paste() == "new copy"
    assert clipboard.paste_primary() == "selected"


@pytest.mark.parametrize("stderr", [b"Nothing is copied\n", b"No selection\n"])
def test_nothing_selected_reads_empty_string(wayland, monkeypatch, stderr):
    def nothing(cmd, **_kwargs):
        wayland.calls.append({"cmd": cmd})
        return subprocess.CompletedProcess(cmd, 1, b"", stderr)

    monkeypatch.setattr(subprocess, "run", nothing)

    result = clipboard.paste_primary()
    assert result == ""
    assert type(result) is str
    assert _cmds(wayland) == [P_LIST]


@pytest.mark.parametrize("primary", [None, {"image/png": b"\x89PNG"}])
def test_primary_without_text_reads_empty_string(wayland, primary):
    wayland.primary = primary

    assert clipboard.paste_primary() == ""
    assert _cmds(wayland) == [P_LIST]


def test_copy_primary_empty_offers_empty_text(wayland):
    clipboard.copy_primary("")

    (proc,) = wayland.popens
    assert proc.cmd == P_WRITE
    assert proc.input == b""
    assert clipboard.paste_primary() == ""
    assert wayland.offers == text_offer("copied")


def test_line_endings_are_untranslated(wayland):
    wayland.primary = {UTF8: b"a\r\nb\n"}

    assert clipboard.paste_primary() == "a\r\nb\n"


@pytest.mark.parametrize("bad", ["a\x00b", "\ud800"])
def test_rejected_text_never_starts_wl_copy_and_primary_stays(wayland, bad):
    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_primary(bad)
    assert "primary selection" in str(caught.value)

    assert wayland.popens == []
    assert wayland.calls == []
    assert clipboard.paste_primary() == "selected"


def test_injected_text_seams_never_receive_primary_traffic(wayland):
    seen = []
    clipboard.set_text_clipboard_writer(lambda text: seen.append(("write", text)))
    clipboard.set_text_clipboard_reader(lambda: seen.append("read") or "seam")

    clipboard.copy_primary("x")
    assert clipboard.paste_primary() == "x"

    assert seen == []
    assert wayland.only_primary_ran()
    assert wayland.offers == text_offer("copied")


def test_mixed_x11_and_wayland_session_follows_the_text_rule(text_session, wayland):
    text_session(
        "linux",
        {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"},
        ("wl-copy", "wl-paste", "xclip"),
    )

    assert clipboard.paste_primary() == "selected"
    clipboard.copy_primary("y")

    assert wayland.only_primary_ran()
    assert all(cmd[0].startswith("wl-") for cmd in _cmds(wayland))

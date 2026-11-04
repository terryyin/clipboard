"""Desktop-free tests for copy_files' Linux X11 ``xclip`` default writer.

The package platform is faked through the ``fake_platform`` fixture (not the
shared ``sys.platform``), and ``subprocess.run`` / ``Popen``, ``shutil.which``,
``os.killpg`` and the session variables are faked, so these run on every CI
host without a display, ``xclip``, or a real clipboard. The large-list stall
bound lives in ``test_copy_files_x11_writer_stall.py``.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from fake_xclip_files import URI_LIST, FakeX11Files

import clipboard
from clipboard import _desktop, _files_native_x11_writer

NAMES = ["report final.pdf", "données é.csv"]
WRITE = ["xclip", "-selection", "clipboard", "-t", URI_LIST]
TARGETS = ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"]
READ = ["xclip", "-selection", "clipboard", "-o", "-t", URI_LIST]
SESSION_VARS = ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE")


@pytest.fixture
def sources(tmp_path):
    for name in NAMES:
        (tmp_path / name).write_text("x", encoding="utf-8")
    (tmp_path / "a dir").mkdir()
    return tmp_path


@pytest.fixture
def x11(monkeypatch, restore_files_clipboard_writer, fake_platform):
    """Default writer on a pretend Linux X11 session with a scripted xclip."""
    fake = FakeX11Files()
    fake_platform("linux")
    clipboard.set_files_clipboard_writer(None)
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(subprocess, "Popen", fake.popen)
    monkeypatch.setattr(
        _desktop.os,
        "killpg",
        lambda pid, sig: fake.killed.append(pid),
        raising=False,  # os.killpg is POSIX-only; these tests also run on Windows
    )

    def session(env=None, helpers=("xclip",)):
        for name in SESSION_VARS:
            monkeypatch.delenv(name, raising=False)
        for name, value in (env or {}).items():
            monkeypatch.setenv(name, value)
        found = set(helpers)
        monkeypatch.setattr(
            shutil,
            "which",
            lambda name, *a, **k: f"/usr/bin/{name}" if name in found else None,
        )

    session({"DISPLAY": ":0"})
    fake.session = session
    return fake


def test_body_is_crlf_percent_encoded_file_uris_fed_to_background_xclip(sources, x11):
    paths = [str(sources / name) for name in NAMES]
    paths += [str(sources / "a dir"), paths[0]]

    clipboard.copy_files(paths)

    (launch,) = x11.popens
    assert launch["cmd"] == WRITE
    body = launch["owner"].data
    assert body == b"".join(Path(p).as_uri().encode() + b"\r\n" for p in paths)
    assert body.isascii() and body.endswith(b"\r\n")
    lines = body.split(b"\r\n")[:-1]
    assert len(lines) == 4 and lines[0] == lines[3]
    assert lines[0].endswith(b"/report%20final.pdf")
    assert lines[1].endswith(b"/donn%C3%A9es%20%C3%A9.csv")
    assert lines[2].endswith(b"/a%20dir")
    assert all(line.startswith(b"file:///") for line in lines)
    assert x11.calls == [TARGETS, READ]


def test_returns_only_once_targets_lists_uri_list_with_the_written_body(sources, x11):
    # A previous file-manager owner already offers text/uri-list.
    x11.offers = {"UTF8_STRING": b"old", URI_LIST: b"file:///old\r\n"}
    x11.delay = 2

    clipboard.copy_files([str(sources / NAMES[0])])

    assert x11.calls == [TARGETS, READ, TARGETS, READ]
    assert x11.offers[URI_LIST] == x11.popens[0]["owner"].data


def test_waits_while_targets_lacks_uri_list(sources, x11):
    x11.offers = {"UTF8_STRING": b"previous text"}
    x11.delay = 3

    clipboard.copy_files([str(sources / NAMES[1])])

    assert x11.calls == [TARGETS, TARGETS, TARGETS, TARGETS, READ]


def test_owner_that_never_offers_raises_after_the_bound(sources, x11, monkeypatch):
    monkeypatch.setattr(_files_native_x11_writer, "_X11_FILES_WRITE_TIMEOUT_S", 0.2)
    x11.offers = {"UTF8_STRING": b"previous text"}
    x11.never_offers = True

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_files([str(sources / NAMES[0])])
    message = str(caught.value)
    assert "Linux X11 clipboard file-list write failed" in message
    assert "did not offer the file list as text/uri-list" in message
    assert "0.2s bound" in message
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert x11.killed == [5151]
    assert x11.calls and all(call == TARGETS for call in x11.calls)


def test_missing_xclip_has_install_hint_and_launches_nothing(sources, x11):
    x11.session({"DISPLAY": ":0"}, helpers=())

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_files([str(sources / NAMES[0])])
    message = str(caught.value)
    assert "xclip was not found on PATH" in message
    assert "sudo apt-get install xclip" in message
    assert x11.popens == [] and x11.calls == []


def test_no_display_raises_before_any_helper(sources, x11):
    x11.session({}, helpers=("xclip",))

    with pytest.raises(clipboard.ClipboardContentError, match="DISPLAY is unset"):
        clipboard.copy_files([str(sources / NAMES[0])])
    assert x11.popens == [] and x11.calls == []


def test_x11_is_selected_when_both_display_and_wayland_are_set(sources, x11):
    x11.session({"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"})

    clipboard.copy_files([str(sources / NAMES[0])])

    assert [p["cmd"] for p in x11.popens] == [WRITE]


def test_helper_exit_is_content_error_quoting_stderr(sources, x11):
    x11.owner_exit = (1, b"Error: Can't open display: :0\n")

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        clipboard.copy_files([str(sources / NAMES[0])])
    message = str(caught.value)
    assert "exited with status 1" in message
    assert "Can't open display: :0" in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)
    assert x11.calls == []


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (FileNotFoundError(2, "No such file", "xclip"), "sudo apt-get install xclip"),
        (PermissionError(13, "Permission denied"), "could not run xclip"),
    ],
)
def test_launch_failures_become_content_errors(sources, x11, error, expected):
    x11.popen_error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        clipboard.copy_files([str(sources / NAMES[0])])
    assert caught.value.__cause__ is error


def test_missing_path_never_launches_xclip(sources, x11):
    with pytest.raises(clipboard.ClipboardContentError, match="missing.txt"):
        clipboard.copy_files([str(sources / NAMES[0]), "missing.txt"])
    assert x11.popens == [] and x11.calls == []

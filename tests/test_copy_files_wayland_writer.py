"""Desktop-free tests for copy_files' Linux Wayland ``wl-copy`` default writer.

The package platform is faked through the ``fake_platform`` fixture (not the
shared ``sys.platform``), and ``subprocess.run`` / ``Popen``, ``shutil.which``
and the session variables are faked, so these run on every CI host without a
compositor, wl-clipboard, or a real clipboard.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from fake_wl_copy_files import LIST_TYPES, READ, URI_LIST, FakeWaylandFiles

import clipboard
from clipboard import _files_native_wayland_writer
from clipboard._files_offer import _uri_list_body

NAMES = ["report final.pdf", "données é.csv"]
WRITE = ["wl-copy", "--type", URI_LIST]
SESSION_VARS = ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE")
HELPERS = ("wl-copy", "wl-paste")
NO_COMPOSITOR = b"Failed to connect to a Wayland server: No such file or directory\n"


@pytest.fixture
def sources(tmp_path):
    for name in NAMES:
        (tmp_path / name).write_text("x", encoding="utf-8")
    (tmp_path / "a dir").mkdir()
    return tmp_path


@pytest.fixture
def wayland(monkeypatch, restore_files_clipboard_writer, fake_platform):
    """Default writer on a pretend Linux Wayland-only session."""
    fake = FakeWaylandFiles()
    fake_platform("linux")
    clipboard.set_files_clipboard_writer(None)
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(subprocess, "Popen", fake.popen)

    def session(env=None, helpers=HELPERS):
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

    session({"WAYLAND_DISPLAY": "wayland-1", "XDG_SESSION_TYPE": "wayland"})
    fake.session = session
    return fake


def _copy_one(sources):
    clipboard.copy_files([str(sources / NAMES[0])])


def test_body_is_the_x11_uri_list_piped_to_wl_copy_then_read_back(sources, wayland):
    paths = [str(sources / name) for name in NAMES]
    paths += [str(sources / "a dir"), paths[0]]

    clipboard.copy_files(paths)

    (launch,) = wayland.popens
    assert launch.cmd == WRITE
    assert launch.input == _uri_list_body(paths)
    assert launch.input == b"".join(Path(p).as_uri().encode() + b"\r\n" for p in paths)
    lines = launch.input.split(b"\r\n")[:-1]
    assert lines[0].endswith(b"/report%20final.pdf")
    assert lines[1].endswith(b"/donn%C3%A9es%20%C3%A9.csv")
    assert lines[2].endswith(b"/a%20dir") and lines[3] == lines[0]
    assert wayland.calls == [LIST_TYPES, READ]


def test_waits_until_uri_list_is_listed(sources, wayland):
    wayland.offers = {"text/plain;charset=utf-8": b"previous text"}
    wayland.delay = 3

    _copy_one(sources)

    assert wayland.calls == [LIST_TYPES] * 4 + [READ]


def test_waits_while_a_previous_owner_serves_another_uri_list(sources, wayland):
    wayland.offers = {URI_LIST: b"file:///old\r\n"}
    wayland.delay = 2

    _copy_one(sources)

    assert wayland.calls == [LIST_TYPES, READ] * 2
    assert wayland.offers[URI_LIST] == wayland.popens[0].input


@pytest.mark.parametrize(
    ("script", "last_check"),
    [
        ({"never_offers": True}, "Nothing is copied"),
        ({"served": b"file:///other\r\n"}, "differ from the"),
        (
            {"run_failure": (1, b"Failed to connect to a Wayland server\n")},
            "wl-paste --list-types exited with status 1",
        ),
    ],
)
def test_no_matching_offer_within_the_bound_raises(
    sources, wayland, monkeypatch, script, last_check
):
    monkeypatch.setattr(
        _files_native_wayland_writer, "_WAYLAND_FILES_WRITE_TIMEOUT_S", 0.2
    )
    wayland.server_stderr = b"wl-copy: compositor said no\n"
    for name, value in script.items():
        setattr(wayland, name, value)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        _copy_one(sources)
    message = str(caught.value)
    assert "Linux Wayland clipboard file-list write failed" in message
    assert "did not offer the file list within the 0.2s bound" in message
    assert last_check in message
    assert "compositor said no" in message
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert len(wayland.popens) == 1


@pytest.mark.parametrize("helpers", [("wl-paste",), ("wl-copy",), ()])
def test_missing_helper_has_install_hint_and_launches_nothing(
    sources, wayland, helpers
):
    wayland.session({"WAYLAND_DISPLAY": "wayland-1"}, helpers=helpers)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        _copy_one(sources)
    message = str(caught.value)
    assert "was not found on PATH" in message
    assert "sudo apt-get install wl-clipboard" in message
    assert wayland.popens == [] and wayland.calls == []


def test_unset_wayland_display_is_an_unsupported_session(sources, wayland):
    # Routed here only via the session rule; the writer re-checks for itself.
    wayland.session({}, helpers=HELPERS)

    with pytest.raises(clipboard.ClipboardContentError, match="unsupported session"):
        _files_native_wayland_writer._wayland_files_clipboard_writer(
            [str(sources / NAMES[0])]
        )
    assert wayland.popens == [] and wayland.calls == []


def test_unusable_compositor_is_an_unsupported_session(sources, wayland):
    wayland.copy_exit = (1, NO_COMPOSITOR)

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        _copy_one(sources)
    message = str(caught.value)
    assert "unsupported session: no usable Wayland compositor" in message
    assert "WAYLAND_DISPLAY='wayland-1'" in message
    assert "Failed to connect to a Wayland server" in message
    assert wayland.calls == []


def test_wl_copy_exit_is_a_transfer_failure_quoting_stderr(sources, wayland):
    wayland.copy_exit = (1, b"wl-copy: compositor denied access to the selection\n")

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        _copy_one(sources)
    message = str(caught.value)
    assert "wl-copy --type text/uri-list exited with status 1" in message
    assert "denied access" in message and "unsupported session" not in message
    assert isinstance(caught.value.__cause__, subprocess.CalledProcessError)
    assert wayland.calls == []


def test_stalled_wl_copy_is_killed_and_raises(sources, wayland):
    wayland.stalls = True

    with pytest.raises(clipboard.ClipboardContentError) as caught:
        _copy_one(sources)
    assert "did not finish within the 10s bound" in str(caught.value)
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert wayland.popens[0].killed is True and wayland.calls == []


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (FileNotFoundError(2, "No such file", "wl-copy"), "apt-get install wl-clip"),
        (PermissionError(13, "Permission denied"), "could not run wl-copy"),
    ],
)
def test_launch_failures_become_content_errors(sources, wayland, error, expected):
    wayland.popen_error = error

    with pytest.raises(clipboard.ClipboardContentError, match=expected) as caught:
        _copy_one(sources)
    assert caught.value.__cause__ is error


def test_x11_is_selected_when_both_display_and_wayland_are_set(sources, wayland):
    wayland.session({"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-1"}, helpers=())

    with pytest.raises(clipboard.ClipboardContentError, match="xclip was not found"):
        _copy_one(sources)
    assert wayland.popens == []


def test_missing_path_never_launches_wl_copy(sources, wayland):
    with pytest.raises(clipboard.ClipboardContentError, match="missing.txt"):
        clipboard.copy_files([str(sources / NAMES[0]), "missing.txt"])
    assert wayland.popens == [] and wayland.calls == []

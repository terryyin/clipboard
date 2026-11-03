"""Desktop-free tests for copy_files' platform-selected default writer.

Platforms without a writer raise naming the platform; on a pretend Darwin,
``subprocess.run`` in ``clipboard._files_native_macos`` is replaced, so no test
here touches the real pasteboard or needs an Aqua session.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import clipboard
from clipboard import _files_native_macos

AWKWARD_NAMES = ["report final.pdf", "données é.csv"]
if sys.platform != "win32":
    # Windows file names cannot contain ``"``, and ``\\`` is its separator.
    AWKWARD_NAMES.append('quote " back\\slash.txt')


class _Helper:
    """Stand-in for ``subprocess.run``: records calls, answers or raises."""

    def __init__(self, *, stdout="ok\n", returncode=0, stderr="", raises=None):
        self.result = subprocess.CompletedProcess([], returncode, stdout, stderr)
        self.raises = raises
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.raises is not None:
            raise self.raises
        return self.result


@pytest.fixture
def sources(tmp_path):
    for name in AWKWARD_NAMES:
        (tmp_path / name).write_text("x", encoding="utf-8")
    (tmp_path / "a dir").mkdir()
    return tmp_path


# Linux X11 and Wayland-only sessions: tests/test_copy_files_x11_writer.py.
@pytest.mark.parametrize("platform", ["aix", "freebsd14"])
def test_default_writer_raises_naming_platform(
    sources, restore_files_clipboard_writer, monkeypatch, platform
):
    monkeypatch.setattr(clipboard._files_native.sys, "platform", platform)
    clipboard.set_files_clipboard_writer(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files([str(sources / AWKWARD_NAMES[0])])
    assert "not available on this platform" in str(raised.value)
    assert f"({platform})" in str(raised.value)


def test_reset_writer_restores_default(restore_files_clipboard_writer):
    clipboard.set_files_clipboard_writer(lambda paths: None)
    clipboard.set_files_clipboard_writer(None)
    assert (
        clipboard._files_clipboard_writer is clipboard._default_files_clipboard_writer
    )
    assert (
        clipboard._files._files_clipboard_writer
        is clipboard._files_native._default_files_clipboard_writer
    )


@pytest.fixture
def darwin_helper(monkeypatch, restore_files_clipboard_writer):
    """Default writer on a pretend Darwin with a scripted osascript."""
    if sys.platform == "win32":
        # Patching the shared ``sys.platform`` to darwin on Windows sends
        # ``Path.as_uri`` into urllib's macOS-only ``_scproxy`` import.
        pytest.skip("pretend-Darwin writer tests need a POSIX host")
    monkeypatch.setattr(clipboard._files_native.sys, "platform", "darwin")
    clipboard.set_files_clipboard_writer(None)

    def install(**kwargs):
        helper = _Helper(**kwargs)
        monkeypatch.setattr(_files_native_macos.subprocess, "run", helper)
        return helper

    return install


def test_paths_travel_as_file_uris_on_stdin_not_script_text(sources, darwin_helper):
    helper = darwin_helper()
    paths = [str(sources / name) for name in AWKWARD_NAMES] + [str(sources / "a dir")]

    clipboard.copy_files(paths)

    ((args, kwargs),) = helper.calls
    assert args[:4] == ["osascript", "-l", "JavaScript", "-e"]
    assert len(args) == 5
    script = args[4]
    assert "clearContents" in script and "writeObjects" in script
    assert "pasteboardItems" in script  # read-back before exit
    for name in AWKWARD_NAMES:
        assert name not in script
    assert kwargs["timeout"] == _files_native_macos._NATIVE_FILES_WRITE_TIMEOUT_S
    uris = json.loads(kwargs["input"])
    assert kwargs["input"].isascii()
    assert uris == [Path(p).as_uri() for p in paths[:-1]] + [
        Path(paths[-1]).as_uri() + "/"
    ]
    # The URI decodes back to the caller's exact code points (no NFD rewrite).
    assert "donn%C3%A9es%20%C3%A9.csv" in uris[1]


@pytest.mark.parametrize(
    ("helper_kwargs", "fragment"),
    [
        (
            {
                "returncode": 1,
                "stdout": "",
                "stderr": "execution error: Error: NSPasteboard writeObjects: "
                "refused the file URLs (-2700)",
            },
            "writeObjects: refused",
        ),
        (
            {
                "returncode": 1,
                "stdout": "",
                "stderr": "Error: NSPasteboard kept 1 of 2 file URLs",
            },
            "kept 1 of 2",
        ),
        ({"returncode": 1, "stdout": "", "stderr": ""}, "status 1"),
        ({"stdout": "surprise\n"}, "unexpected helper output 'surprise'"),
        ({"stdout": ""}, "unexpected helper output ''"),
    ],
)
def test_helper_failure_is_content_error_with_detail(
    sources, darwin_helper, helper_kwargs, fragment
):
    darwin_helper(**helper_kwargs)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files([str(sources / AWKWARD_NAMES[0])])
    message = str(raised.value)
    assert "macOS file-list pasteboard write failed" in message
    assert fragment in message


@pytest.mark.parametrize(
    ("raises", "fragment"),
    [
        (FileNotFoundError("osascript"), "could not run osascript"),
        (
            subprocess.TimeoutExpired(["osascript"], 30),
            "did not answer within 30s",
        ),
    ],
)
def test_missing_or_stalled_osascript_is_content_error(
    sources, darwin_helper, raises, fragment
):
    darwin_helper(raises=raises)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files([str(sources / AWKWARD_NAMES[0])])
    assert fragment in str(raised.value)
    assert raised.value.__cause__ is raises


def test_missing_path_never_runs_osascript(sources, darwin_helper):
    helper = darwin_helper()
    with pytest.raises(clipboard.ClipboardContentError, match="missing.txt"):
        clipboard.copy_files([str(sources / AWKWARD_NAMES[0]), "missing.txt"])
    assert helper.calls == []

"""In-memory copy_files Behavior: validation, absolute paths, injected writer.

Observes plan 008 slice 1 / seed key examples 2-4 without a real clipboard.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from paste_files_offer import FakeFilesClipboard

import clipboard

UNICODE_NAME = "données é.csv"
SPACED_DIR = "report final dir"


@pytest.fixture
def sources(tmp_path, monkeypatch):
    """A cwd holding ``out/données é.csv`` (file) and ``out/report final dir``."""
    out = tmp_path / "out"
    out.mkdir()
    (out / UNICODE_NAME).write_text("data", encoding="utf-8")
    (out / SPACED_DIR).mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


class RecordingWriter:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, paths: list[str]) -> None:
        self.calls.append(paths)


@pytest.fixture
def writer(restore_files_clipboard_writer):
    recording = RecordingWriter()
    clipboard.set_files_clipboard_writer(recording)
    return recording


def test_copy_files_public_surface():
    assert callable(clipboard.copy_files)
    assert callable(clipboard.set_files_clipboard_writer)
    assert "copy_files" in clipboard.__all__
    assert "set_files_clipboard_writer" in clipboard.__all__


# --- Example 4: relative + directory paths reach the writer absolute, in order ---


def test_valid_paths_reach_writer_absolute_ordered_with_duplicates(sources, writer):
    relative_file = f"out/{UNICODE_NAME}"
    directory = Path(sources / "out" / SPACED_DIR)  # os.PathLike, absolute

    result = clipboard.copy_files([relative_file, directory, relative_file])

    assert result is None
    expected_file = os.path.join(str(sources), "out", UNICODE_NAME)
    assert writer.calls == [[expected_file, str(directory), expected_file]]
    assert all(isinstance(p, str) for p in writer.calls[0])
    assert all(os.path.isabs(p) for p in writer.calls[0])


def test_generator_input_is_accepted(sources, writer):
    clipboard.copy_files(p for p in [f"out/{UNICODE_NAME}"])
    assert writer.calls == [[os.path.join(str(sources), "out", UNICODE_NAME)]]


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="needs os.symlink")
def test_symlink_is_kept_not_resolved(sources, writer):
    link = sources / "link to data.csv"
    try:
        link.symlink_to(sources / "out" / UNICODE_NAME)
    except OSError as exc:  # e.g. Windows without symlink privilege
        pytest.skip(f"cannot create symlink: {exc}")

    clipboard.copy_files(["link to data.csv"])

    assert writer.calls == [[os.path.join(str(sources), "link to data.csv")]]


# --- Examples 2-3: invalid input fails before the writer runs ---


@pytest.mark.parametrize(
    ("paths", "message"),
    [
        ([], "at least one path"),
        ((), "at least one path"),
        (iter([]), "at least one path"),
        (f"out/{UNICODE_NAME}", "bare str"),
        (b"out/data.csv", "bare bytes"),
        ([42], "index 0 must be str or os.PathLike"),
        ([f"out/{UNICODE_NAME}", b"out/data.csv"], "index 1 must be str"),
        (42, "iterable"),
        ([""], "not a valid path"),
    ],
)
def test_invalid_input_raises_before_writer(sources, writer, paths, message):
    with pytest.raises(clipboard.ClipboardContentError, match=message):
        clipboard.copy_files(paths)
    assert writer.calls == []


def test_missing_path_is_named_and_writer_never_called(sources, writer):
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files([f"out/{UNICODE_NAME}", "missing.txt"])

    assert "missing.txt" in str(raised.value)
    assert "does not exist" in str(raised.value)
    assert writer.calls == []


def test_missing_path_leaves_prior_offer_untouched(
    sources, restore_files_clipboard_writer
):
    """A fake clipboard holding text is not replaced when validation fails."""
    board = {"text": "keep"}

    def replacing_writer(paths: list[str]) -> None:
        board.clear()
        board["paths"] = paths

    clipboard.set_files_clipboard_writer(replacing_writer)
    with pytest.raises(clipboard.ClipboardContentError, match="missing.txt"):
        clipboard.copy_files([f"out/{UNICODE_NAME}", "missing.txt"])
    assert board == {"text": "keep"}


# --- Writer failures ---


def test_non_content_writer_exception_is_wrapped(
    sources, restore_files_clipboard_writer
):
    def boom(paths: list[str]) -> None:
        raise OSError("denied")

    clipboard.set_files_clipboard_writer(boom)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files([f"out/{UNICODE_NAME}"])
    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert "file-list write failed: denied" in str(raised.value)
    assert isinstance(raised.value.__cause__, OSError)


def test_writer_content_error_passes_through(sources, restore_files_clipboard_writer):
    def boom(paths: list[str]) -> None:
        raise clipboard.ClipboardContentError("helper missing")

    clipboard.set_files_clipboard_writer(boom)
    with pytest.raises(clipboard.ClipboardContentError, match="^helper missing$"):
        clipboard.copy_files([f"out/{UNICODE_NAME}"])


# --- Default writer ---


@pytest.mark.parametrize("platform", ["darwin", "linux", "win32", "aix"])
def test_default_writer_raises_naming_platform(
    sources, restore_files_clipboard_writer, monkeypatch, platform
):
    monkeypatch.setattr(clipboard._files_native.sys, "platform", platform)
    clipboard.set_files_clipboard_writer(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_files([f"out/{UNICODE_NAME}"])
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


# --- Consistency round trip through the injected paste_files reader ---


def _paths_offer(paths: list[str]) -> object:
    return {"kind": "paths", "paths": paths}


def _uri_list_offer(paths: list[str]) -> object:
    return {
        "kind": "uri-list",
        "uri_list": "".join(Path(p).as_uri() + "\r\n" for p in paths),
    }


@pytest.mark.parametrize(
    "encode",
    [
        _paths_offer,
        pytest.param(
            _uri_list_offer,
            marks=pytest.mark.skipif(
                sys.platform == "win32",
                reason="file URIs decode to POSIX-style paths",
            ),
        ),
    ],
)
def test_round_trip_through_fake_offer_returns_absolute_paths(
    sources, restore_files_clipboard_writer, restore_files_clipboard_reader, encode
):
    fake = FakeFilesClipboard()

    def offer_writer(paths: list[str]) -> None:
        fake.offer = encode(paths)

    clipboard.set_files_clipboard_writer(offer_writer)
    clipboard.set_files_clipboard_reader(fake.reader)

    clipboard.copy_files([f"out/{UNICODE_NAME}", f"out/{SPACED_DIR}"])

    assert clipboard.paste_files() == [
        os.path.join(str(sources), "out", UNICODE_NAME),
        os.path.join(str(sources), "out", SPACED_DIR),
    ]


def test_copy_files_works_without_images_extra(tmp_path):
    (tmp_path / UNICODE_NAME).write_text("x", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import builtins
import os
import sys

real_import = builtins.__import__

def block_pil(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "PIL" or name.startswith("PIL."):
        raise ImportError("No module named 'PIL'")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = block_pil

import clipboard

offers = []
clipboard.set_files_clipboard_writer(offers.append)
clipboard.copy_files([sys.argv[1]])
assert offers == [[os.path.abspath(sys.argv[1])]], offers
assert "PIL" not in sys.modules
clipboard.set_files_clipboard_writer(None)
""",
            UNICODE_NAME,
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

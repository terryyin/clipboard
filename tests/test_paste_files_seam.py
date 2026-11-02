"""Structure seam for paste_files: public surface + injectable reader (no desktop)."""

import subprocess
import sys

import pytest

import clipboard


def test_paste_files_public_surface():
    assert callable(clipboard.paste_files)
    assert issubclass(clipboard.ClipboardContentError, Exception)
    assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
    assert callable(clipboard.set_files_clipboard_reader)


def test_default_reader_raises_on_windows_stub(
    restore_files_clipboard_reader, monkeypatch
):
    """Windows / other platforms stay unavailable until their adapters land."""
    monkeypatch.setattr(clipboard._files_native.sys, "platform", "win32")
    clipboard.set_files_clipboard_reader(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.paste_files()
    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    assert "not available on this platform" in str(raised.value)


def test_injected_reader_returns_paths(restore_files_clipboard_reader):
    paths = ["/tmp/a file.png", "/tmp/unicodé.txt"]

    clipboard.set_files_clipboard_reader(lambda: paths)
    assert clipboard.paste_files() == paths


def test_injected_reader_absence_is_none(restore_files_clipboard_reader):
    clipboard.set_files_clipboard_reader(lambda: None)
    assert clipboard.paste_files() is None


def test_injected_reader_failure_is_content_error(
    restore_files_clipboard_reader,
):
    def boom() -> list[str] | None:
        raise OSError("denied")

    clipboard.set_files_clipboard_reader(boom)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.paste_files()
    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_injected_clipboard_content_error_propagates(
    restore_files_clipboard_reader,
):
    def boom() -> list[str] | None:
        raise clipboard.ClipboardContentError("corrupt file-list metadata")

    clipboard.set_files_clipboard_reader(boom)
    with pytest.raises(clipboard.ClipboardContentError, match="corrupt"):
        clipboard.paste_files()


def test_reset_reader_restores_default(restore_files_clipboard_reader, monkeypatch):
    clipboard.set_files_clipboard_reader(lambda: ["/tmp/x"])
    clipboard.set_files_clipboard_reader(None)
    assert (
        clipboard._files._files_clipboard_reader
        is clipboard._files_native._default_files_clipboard_reader
    )
    monkeypatch.setattr(clipboard._files_native.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(
        clipboard._files_native_linux.shutil, "which", lambda _name: None
    )
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.paste_files()


def test_paste_files_importable_without_images_extra():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import builtins

real_import = builtins.__import__

def block_pil(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "PIL" or name.startswith("PIL."):
        raise ImportError("No module named 'PIL'")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = block_pil

import clipboard

assert callable(clipboard.paste_files)
assert issubclass(clipboard.ClipboardContentError, Exception)
assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
assert callable(clipboard.set_files_clipboard_reader)

clipboard.set_files_clipboard_reader(lambda: ["/tmp/no-pillow"])
assert clipboard.paste_files() == ["/tmp/no-pillow"]
clipboard.set_files_clipboard_reader(None)
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

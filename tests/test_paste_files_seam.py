"""Structure seam for paste_files: public surface + injectable reader (no desktop)."""

import pytest

import clipboard


def test_paste_files_public_surface():
    assert callable(clipboard.paste_files)
    assert issubclass(clipboard.ClipboardContentError, Exception)
    assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
    assert callable(clipboard.set_files_clipboard_reader)


def test_default_reader_raises_on_unknown_platform(
    restore_files_clipboard_reader, fake_platform
):
    """Platforms without a file-list adapter raise ClipboardContentError."""
    fake_platform("aix")
    clipboard.set_files_clipboard_reader(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.paste_files()
    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    assert "(aix)" in str(raised.value)


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


def test_reset_reader_restores_default(
    restore_files_clipboard_reader, monkeypatch, fake_platform
):
    clipboard.set_files_clipboard_reader(lambda: ["/tmp/x"])
    clipboard.set_files_clipboard_reader(None)
    assert (
        clipboard._files._files_clipboard_reader
        is clipboard._files_native._default_files_clipboard_reader
    )
    fake_platform("linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(
        clipboard._files_native_linux.shutil, "which", lambda _name: None
    )
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.paste_files()

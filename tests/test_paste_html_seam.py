"""Structure seam for paste_html: public surface + injectable reader (no desktop)."""

import subprocess
import sys

import pytest

import clipboard
from clipboard._html_envelope import _fragment_offer


def test_paste_html_public_surface():
    assert callable(clipboard.paste_html)
    assert callable(clipboard.set_html_clipboard_reader)


def test_injected_reader_value_is_returned(restore_html_clipboard_reader):
    clipboard.set_html_clipboard_reader(lambda: _fragment_offer("<b>fragment</b>"))
    assert clipboard.paste_html() == "<b>fragment</b>"


def test_injected_reader_absence_is_none(restore_html_clipboard_reader):
    clipboard.set_html_clipboard_reader(lambda: None)
    assert clipboard.paste_html() is None


def test_reset_reader_restores_default(monkeypatch, restore_html_clipboard_reader):
    # A platform with no native reader yet, and no helper may run, so the
    # default reader never touches a real pasteboard or X11 CLIPBOARD.
    monkeypatch.setattr(clipboard._html_native.sys, "platform", "win32")

    def no_helper(*args, **kwargs):
        raise AssertionError("default reader must not run a helper here")

    monkeypatch.setattr(clipboard._html_native.subprocess, "run", no_helper)
    clipboard.set_html_clipboard_reader(lambda: _fragment_offer("<i>x</i>"))
    clipboard.set_html_clipboard_reader(None)
    assert (
        clipboard._html._html_clipboard_reader
        is clipboard._html_native._default_html_clipboard_reader
    )
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.paste_html()


@pytest.mark.parametrize(
    "exc",
    [OSError("denied"), RuntimeError("boom"), ValueError("bad"), NotImplementedError()],
)
def test_reader_failure_surfaces_as_content_error(restore_html_clipboard_reader, exc):
    def failing_reader():
        raise exc

    clipboard.set_html_clipboard_reader(failing_reader)
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert not isinstance(info.value, clipboard.ClipboardImageError)
    assert info.value.__cause__ is exc


def test_reader_content_error_propagates_unchanged(restore_html_clipboard_reader):
    original = clipboard.ClipboardContentError("helper missing")

    def failing_reader():
        raise original

    clipboard.set_html_clipboard_reader(failing_reader)
    with pytest.raises(clipboard.ClipboardContentError) as info:
        clipboard.paste_html()
    assert info.value is original


def test_paste_html_works_without_images_extra():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import builtins
import sys

real_import = builtins.__import__

def block_pil(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "PIL" or name.startswith("PIL."):
        raise ImportError("No module named 'PIL'")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = block_pil

import clipboard
from clipboard._html_envelope import _fragment_offer

clipboard.set_html_clipboard_reader(lambda: _fragment_offer("<b>ok</b>"))
assert clipboard.paste_html() == "<b>ok</b>"
clipboard.set_html_clipboard_reader(lambda: None)
assert clipboard.paste_html() is None
clipboard.set_html_clipboard_reader(None)
sys.platform = "linux"  # default reader must not touch a real pasteboard
try:
    clipboard.paste_html()
except clipboard.ClipboardContentError:
    pass
else:
    raise AssertionError("default reader should raise ClipboardContentError")
assert not any(m == "PIL" or m.startswith("PIL.") for m in sys.modules)
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

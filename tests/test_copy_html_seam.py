"""Structure seam for copy_html: public surface + injectable writer (no desktop)."""

import subprocess
import sys

import pytest

import clipboard


def test_copy_html_public_surface():
    assert callable(clipboard.copy_html)
    assert issubclass(clipboard.ClipboardContentError, Exception)
    assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
    assert callable(clipboard.set_html_clipboard_writer)


def test_default_copy_html_raises_content_error():
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.copy_html("<b>hi</b>", "hi")


def test_injected_writer_receives_both_representations(
    restore_html_clipboard_writer,
):
    received: list[tuple[str, str]] = []

    def fake_writer(html: str, text: str) -> None:
        received.append((html, text))

    clipboard.set_html_clipboard_writer(fake_writer)
    clipboard.copy_html("<i>styled</i>", "styled")
    assert received == [("<i>styled</i>", "styled")]


def test_reset_writer_restores_default_stub(restore_html_clipboard_writer):
    clipboard.set_html_clipboard_writer(lambda html, text: None)
    clipboard.set_html_clipboard_writer(None)
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.copy_html("<p>x</p>", "x")


def test_copy_html_importable_without_images_extra():
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

assert callable(clipboard.copy_html)
assert issubclass(clipboard.ClipboardContentError, Exception)
assert callable(clipboard.set_html_clipboard_writer)

offers = []
clipboard.set_html_clipboard_writer(
    lambda html, text: offers.append((html, text))
)
clipboard.copy_html("<b>ok</b>", "ok")
assert offers == [("<b>ok</b>", "ok")]
clipboard.set_html_clipboard_writer(None)
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

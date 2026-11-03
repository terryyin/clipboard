"""Structure seam for copy_html: public surface + injectable writer (no desktop)."""

import pytest

import clipboard


def test_copy_html_public_surface():
    assert callable(clipboard.copy_html)
    assert issubclass(clipboard.ClipboardContentError, Exception)
    assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
    assert callable(clipboard.set_html_clipboard_writer)


def test_default_copy_html_raises_on_non_darwin(
    restore_html_clipboard_writer, fake_platform
):
    """Non-Darwin default raises until later platform writers land.

    Force a non-Darwin platform so default pytest never touches the pasteboard;
    Darwin's native dual-offer path stays gated to the native probe. Message
    actionability (multi-type helper naming) is covered in the contract suite.
    """
    fake_platform("linux")
    clipboard.set_html_clipboard_writer(None)
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


def test_reset_writer_restores_default(restore_html_clipboard_writer, fake_platform):
    clipboard.set_html_clipboard_writer(lambda html, text: None)
    clipboard.set_html_clipboard_writer(None)
    assert clipboard._html_clipboard_writer is clipboard._default_html_clipboard_writer
    fake_platform("linux")
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.copy_html("<p>x</p>", "x")

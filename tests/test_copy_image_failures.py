"""copy_image rejects invalid input and surfaces backend failures distinctly."""

import sys

import pytest
from image_offer import fake_offer
from PIL import Image


def _assert_offer_untouched(offer, *, text, image):
    assert offer["replace_calls"] == 0
    assert offer["text"] == text
    assert offer["image"] is image


@pytest.mark.parametrize(
    "invalid",
    [
        "not-an-image",
        "/tmp/photo.png",
        b"raw-bytes",
        ["C:\\Users\\example\\photo.png"],
        "https://example.com/photo.png",
        None,
        42,
    ],
    ids=[
        "string",
        "file-path",
        "bytes",
        "file-list",
        "url",
        "none",
        "int",
    ],
)
def test_invalid_input_raises_before_replace(invalid, restore_image_writeclipboard):
    import clipboard

    prior = Image.new("RGB", (2, 2), color="yellow")
    offer, writeclipboard = fake_offer(text="keep me", image=prior)
    clipboard.set_image_writeclipboard(writeclipboard)

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(invalid)

    _assert_offer_untouched(offer, text="keep me", image=prior)
    assert "clipboard image write failed" in str(raised.value).lower()
    assert isinstance(raised.value.__cause__, TypeError)


def test_empty_image_raises_before_replace(restore_image_writeclipboard):
    import clipboard

    prior = Image.new("RGB", (2, 2), color="yellow")
    offer, writeclipboard = fake_offer(text="keep me", image=prior)
    clipboard.set_image_writeclipboard(writeclipboard)

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(Image.new("RGB", (0, 0)))

    _assert_offer_untouched(offer, text="keep me", image=prior)
    assert isinstance(raised.value.__cause__, ValueError)


def test_unloadable_image_raises_before_replace(restore_image_writeclipboard):
    """Closed / unloadable Image fails before any replace."""
    import clipboard

    prior = Image.new("RGB", (2, 2), color="yellow")
    offer, writeclipboard = fake_offer(text="keep me", image=prior)
    clipboard.set_image_writeclipboard(writeclipboard)
    bad = Image.new("RGB", (2, 2), color="red")
    bad.close()

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(bad)

    _assert_offer_untouched(offer, text="keep me", image=prior)
    assert "clipboard image write failed" in str(raised.value).lower()
    assert isinstance(raised.value.__cause__, ValueError)


@pytest.mark.parametrize(
    "failure",
    [
        OSError("clipboard helper unavailable"),
        PermissionError("pasteboard access denied"),
        NotImplementedError("image write not available in this session"),
        ChildProcessError("xclip error: transfer failed"),
    ],
    ids=["unavailable", "access-denied", "unsupported", "transfer-failure"],
)
def test_backend_failure_raises_clipboard_image_error(
    failure, restore_image_writeclipboard
):
    import clipboard

    prior = Image.new("RGB", (2, 2), color="cyan")
    offer, _ = fake_offer(text="keep", image=prior)

    def failing_write(raster):
        offer["replace_calls"] += 1
        raise failure

    clipboard.set_image_writeclipboard(failing_write)

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(Image.new("RGB", (1, 1), color="red"))

    assert raised.value.__cause__ is failure
    assert "clipboard image write failed" in str(raised.value).lower()
    # Failure during replace: prior offer not rewritten by a successful write.
    assert offer["text"] == "keep"
    assert offer["image"] is prior


@pytest.mark.skipif(
    sys.platform == "darwin" or sys.platform.startswith("linux"),
    reason="Darwin/Linux default write is native; stub NotImplementedError elsewhere",
)
def test_default_write_stub_wrapped_as_clipboard_image_error(
    restore_image_writeclipboard,
):
    import clipboard

    clipboard.set_image_writeclipboard(None)
    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(Image.new("RGB", (1, 1)))
    assert isinstance(raised.value.__cause__, NotImplementedError)
    assert "not implemented for this platform" in str(raised.value.__cause__)


def test_missing_xclip_raises_clipboard_image_error(
    monkeypatch, tmp_path, restore_image_writeclipboard
):
    """Missing xclip helper → ClipboardImageError (R.8a), not silent success."""
    import clipboard

    monkeypatch.setenv("PATH", str(tmp_path))
    clipboard.set_image_writeclipboard(clipboard._write_linux_xclip)

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(Image.new("RGB", (1, 1), color="red"))

    assert isinstance(raised.value.__cause__, OSError)
    assert "xclip" in str(raised.value.__cause__).lower()


def test_missing_wl_copy_raises_clipboard_image_error(
    monkeypatch, tmp_path, restore_image_writeclipboard
):
    """Missing wl-copy helper → ClipboardImageError (R.8a), not silent success."""
    import clipboard

    monkeypatch.setenv("PATH", str(tmp_path))
    clipboard.set_image_writeclipboard(clipboard._write_linux_wl_copy)

    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.copy_image(Image.new("RGB", (1, 1), color="red"))

    assert isinstance(raised.value.__cause__, OSError)
    assert "wl-copy" in str(raised.value.__cause__).lower()

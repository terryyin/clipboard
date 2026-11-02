"""Failure must stay distinct from ordinary image absence (None)."""

import pytest
from PIL import UnidentifiedImageError


@pytest.mark.parametrize(
    "failure",
    [
        PermissionError("pasteboard access denied"),
        NotImplementedError(
            "wl-paste or xclip is required for ImageGrab.grabclipboard() on Linux"
        ),
        OSError("clipboard helper unavailable"),
        ChildProcessError("xclip error: transfer failed"),
        UnidentifiedImageError("cannot identify image file"),
    ],
    ids=[
        "access-denied",
        "missing-helper",
        "unavailable-desktop",
        "transfer-failure",
        "unidentified-image",
    ],
)
def test_access_and_helper_failures_are_not_absence(
    failure, restore_image_grabclipboard
):
    """Access / helper / decode failures raise; they must not become None."""
    import clipboard

    def raise_failure():
        raise failure

    clipboard.set_image_grabclipboard(raise_failure)
    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.paste_image()
    assert raised.value.__cause__ is failure
    assert "clipboard image read failed" in str(raised.value).lower()


def test_malformed_image_bytes_are_not_absence(restore_image_grabclipboard):
    """Corrupt image-typed bytes → distinguishable failure, not None or Image."""
    import clipboard

    clipboard.set_image_grabclipboard(lambda: b"not-a-real-image-payload")
    with pytest.raises(clipboard.ClipboardImageError) as raised:
        clipboard.paste_image()
    assert isinstance(raised.value.__cause__, UnidentifiedImageError)


def test_text_only_still_absence_without_exception(restore_image_grabclipboard):
    """Text-only / empty image offer remains None with no ClipboardImageError."""
    import clipboard

    clipboard.set_image_grabclipboard(lambda: None)
    assert clipboard.paste_image() is None

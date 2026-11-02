"""Contract tests for successful copy_image via an injectable write backend."""

import pytest
from image_offer import fake_offer
from PIL import Image


def test_copy_image_is_public_and_callable():
    import clipboard

    assert callable(clipboard.copy_image)
    assert callable(clipboard.set_image_writeclipboard)


def test_valid_rgb_reaches_backend_as_transferable_raster(
    restore_image_writeclipboard,
):
    import clipboard

    prior = Image.new("RGB", (1, 1), color="green")
    offer, writeclipboard = fake_offer(text="stale", image=prior)
    clipboard.set_image_writeclipboard(writeclipboard)
    image = Image.new("RGB", (3, 4), color="blue")

    clipboard.copy_image(image)

    assert offer["replace_calls"] == 1
    assert offer["image"] is image
    assert offer["image"] is not prior
    assert offer["image"].mode == "RGB"
    assert offer["image"].size == (3, 4)
    assert offer["text"] == ""


def test_valid_rgba_reaches_backend_preserving_alpha(restore_image_writeclipboard):
    import clipboard

    offer, writeclipboard = fake_offer()
    clipboard.set_image_writeclipboard(writeclipboard)
    image = Image.new("RGBA", (2, 2), color=(255, 0, 0, 128))

    clipboard.copy_image(image)

    assert offer["replace_calls"] == 1
    assert offer["image"] is image
    assert offer["image"].mode == "RGBA"
    assert offer["text"] == ""


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("L", "RGB"),
        ("CMYK", "RGB"),
        ("1", "RGB"),
        ("LA", "RGBA"),
    ],
)
def test_non_rgba_modes_convert_before_offer(
    mode, expected, restore_image_writeclipboard
):
    import clipboard

    received: list[Image.Image] = []
    clipboard.set_image_writeclipboard(lambda image: received.append(image))
    source = Image.new(mode, (2, 3), color=0)

    clipboard.copy_image(source)

    assert len(received) == 1
    assert received[0].mode == expected
    assert received[0].size == (2, 3)
    assert received[0] is not source


def test_palette_with_transparency_converts_to_rgba(restore_image_writeclipboard):
    import clipboard

    received: list[Image.Image] = []
    clipboard.set_image_writeclipboard(lambda image: received.append(image))
    source = Image.new("P", (2, 2))
    source.putpalette([i % 256 for i in range(768)])
    source.info["transparency"] = 0

    clipboard.copy_image(source)

    assert len(received) == 1
    assert received[0].mode == "RGBA"

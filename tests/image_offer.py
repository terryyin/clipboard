"""In-memory text+image offer stand-in for injectable writeclipboard tests."""

from PIL import Image


def fake_offer(*, text="prior text", image=None):
    """Write replaces both text and image kinds on success."""
    offer = {"text": text, "image": image, "replace_calls": 0}

    def writeclipboard(raster: Image.Image) -> None:
        offer["replace_calls"] += 1
        offer["text"] = ""
        offer["image"] = raster

    return offer, writeclipboard

"""Structure tests for injectable copy_image write seam (no desktop)."""

import subprocess
import sys

import pytest
from PIL import Image


def test_copy_image_is_public_and_callable():
    import clipboard

    assert callable(clipboard.copy_image)
    assert callable(clipboard.set_image_writeclipboard)


def test_injected_writeclipboard_receives_image(restore_image_writeclipboard):
    """Fake writer sees the Image without a real pasteboard."""
    import clipboard

    received: list[Image.Image] = []

    clipboard.set_image_writeclipboard(lambda image: received.append(image))
    image = Image.new("RGB", (3, 4), color="blue")
    clipboard.copy_image(image)

    assert len(received) == 1
    assert received[0] is image
    assert received[0].size == (3, 4)
    assert received[0].mode == "RGB"


def test_reset_writeclipboard_restores_default_stub(restore_image_writeclipboard):
    import clipboard

    clipboard.set_image_writeclipboard(lambda image: None)
    clipboard.set_image_writeclipboard(None)

    with pytest.raises(NotImplementedError, match="not implemented yet"):
        clipboard.copy_image(Image.new("RGB", (1, 1)))


def test_copy_image_without_pillow_raises_import_error():
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

assert callable(clipboard.copy_image)

try:
    clipboard.copy_image(object())
except ImportError as exc:
    message = str(exc).lower()
    assert "images" in message or "pillow" in message
    assert "copy_image" in message
else:
    raise SystemExit("expected ImportError from copy_image without Pillow")
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

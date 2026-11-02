"""Contract tests for paste_image via an injectable image backend (no desktop)."""

import builtins
import json
import os
import subprocess
import sys
from importlib.metadata import metadata, requires
from pathlib import Path

import pytest


@pytest.fixture
def restore_image_grabclipboard():
    import clipboard

    yield
    clipboard.set_image_grabclipboard(None)


def _install_offered_path_open_spies(monkeypatch, paths: list[str]) -> list[str]:
    """Spy common open/read entry points; record hits that name an offered path."""
    from PIL import Image

    path_hits: list[str] = []

    def record_if_offered(target) -> None:
        try:
            as_str = os.fspath(target)
        except TypeError:
            return
        for path in paths:
            if path == as_str or path in as_str or as_str in path:
                path_hits.append(as_str)

    def wrap(real):
        def tracking(first, *args, **kwargs):
            record_if_offered(first)
            return real(first, *args, **kwargs)

        return tracking

    def wrap_method(real):
        def tracking(self, *args, **kwargs):
            record_if_offered(self)
            return real(self, *args, **kwargs)

        return tracking

    monkeypatch.setattr(builtins, "open", wrap(builtins.open))
    monkeypatch.setattr(os, "open", wrap(os.open))
    monkeypatch.setattr(Image, "open", wrap(Image.open))
    monkeypatch.setattr(Path, "open", wrap_method(Path.open))
    monkeypatch.setattr(Path, "read_bytes", wrap_method(Path.read_bytes))
    return path_hits


def test_images_extra_declares_pillow():
    extras = metadata("clipboard").get_all("Provides-Extra") or []
    assert "images" in extras
    image_reqs = [
        req for req in (requires("clipboard") or []) if 'extra == "images"' in req
    ]
    assert image_reqs
    assert any("pillow" in req.lower() for req in image_reqs)


def test_text_api_importable_without_pillow():
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

assert clipboard.VERSION
assert callable(clipboard.copy)
assert callable(clipboard.paste)
assert callable(clipboard.paste_image)

try:
    clipboard.paste_image()
except ImportError as exc:
    message = str(exc).lower()
    assert "images" in message or "pillow" in message
else:
    raise SystemExit("expected ImportError from paste_image without Pillow")
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


@pytest.mark.parametrize(
    ("text", "image_spec", "expect_image"),
    [
        ("hello text", None, False),
        ("still here", {"size": [4, 5], "mode": "RGB"}, True),
    ],
)
def test_paste_image_absence_and_raster_preservative(text, image_spec, expect_image):
    # Subprocess mirrors text tests: first-import + injectable grabclipboard stub.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import json
import sys

import pyperclip
from PIL import Image

payload = json.loads(sys.argv[1])
text = payload["text"]
image_spec = payload["image_spec"]

contents = {"text": text, "image": None}
if image_spec is not None:
    contents["image"] = Image.new(
        image_spec["mode"], tuple(image_spec["size"]), color="red"
    )

def copy(value):
    contents["text"] = value

def paste():
    return contents["text"]

pyperclip.determine_clipboard = lambda: (copy, paste)

import clipboard

clipboard.set_image_grabclipboard(lambda: contents["image"])

before_text = clipboard.paste()
first = clipboard.paste_image()
after_text = clipboard.paste()
second = clipboard.paste_image()

def describe(image):
    if image is None:
        return None
    return {"size": list(image.size), "mode": image.mode}

print(
    json.dumps(
        {
            "before_text": before_text,
            "after_text": after_text,
            "first": describe(first),
            "second": describe(second),
            "same_object": first is second and first is contents["image"],
        }
    )
)
""",
            json.dumps({"text": text, "image_spec": image_spec}),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(result.stdout)
    assert observed["before_text"] == text
    assert observed["after_text"] == text
    if expect_image:
        assert observed["first"] == image_spec
        assert observed["second"] == image_spec
        assert observed["same_object"] is True
    else:
        assert observed["first"] is None
        assert observed["second"] is None


def test_file_list_offer_is_absence_without_filesystem_open(
    monkeypatch, restore_image_grabclipboard
):
    """Windows-shaped filename list → None; offered paths are never opened."""
    import clipboard

    paths = [
        r"C:\Users\example\Desktop\photo.png",
        r"C:\Users\example\Pictures\scan.jpg",
    ]
    path_hits = _install_offered_path_open_spies(monkeypatch, paths)

    clipboard.set_image_grabclipboard(lambda: list(paths))
    result = clipboard.paste_image()

    assert result is None
    assert path_hits == []


def test_url_only_offer_is_absence(restore_image_grabclipboard):
    """URL-only grabclipboard result is absence, not an image success."""
    import clipboard

    clipboard.set_image_grabclipboard(lambda: "https://example.com/photo.png")
    assert clipboard.paste_image() is None

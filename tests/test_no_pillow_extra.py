"""Public APIs that must work when Pillow is not installed."""

from __future__ import annotations

import subprocess
import sys

import pytest

_BLOCK_PIL = """\
import builtins
import sys

real_import = builtins.__import__

def block_pil(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "PIL" or name.startswith("PIL."):
        raise ImportError("No module named 'PIL'")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = block_pil
"""

# One subprocess body per public surface that must not require Pillow.
_SCENARIOS = {
    "paste_html": """\
import clipboard
from clipboard._html_envelope import _fragment_offer

clipboard.set_html_clipboard_reader(lambda: _fragment_offer("<b>ok</b>"))
assert clipboard.paste_html() == "<b>ok</b>"
clipboard.set_html_clipboard_reader(lambda: None)
assert clipboard.paste_html() is None
clipboard.set_html_clipboard_reader(None)
from clipboard import _platform
_platform.current = lambda: "sunos5"
try:
    clipboard.paste_html()
except clipboard.ClipboardContentError as exc:
    assert "(sunos5)" in str(exc), exc
else:
    raise AssertionError("default reader should raise ClipboardContentError")
assert not any(m == "PIL" or m.startswith("PIL.") for m in sys.modules)
""",
    "copy_html": """\
import clipboard

assert callable(clipboard.copy_html)
assert issubclass(clipboard.ClipboardContentError, Exception)
assert callable(clipboard.set_html_clipboard_writer)

offers = []
clipboard.set_html_clipboard_writer(lambda html, text: offers.append((html, text)))
clipboard.copy_html("<b>ok</b>", "ok")
assert offers == [("<b>ok</b>", "ok")]
clipboard.set_html_clipboard_writer(None)
""",
    "paste_image": """\
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
    "copy_image": """\
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
    "paste_files": """\
import clipboard

assert callable(clipboard.paste_files)
assert issubclass(clipboard.ClipboardContentError, Exception)
assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
assert callable(clipboard.set_files_clipboard_reader)

clipboard.set_files_clipboard_reader(lambda: ["/tmp/no-pillow"])
assert clipboard.paste_files() == ["/tmp/no-pillow"]
clipboard.set_files_clipboard_reader(None)
""",
    "paste_files_uri_list": """\
import clipboard

clipboard.set_files_clipboard_reader(
    lambda: {
        "kind": "uri-list",
        "uri_list": (
            "file:///tmp/photos/a%20file.png\\n"
            "file:///tmp/docs/unicod%C3%A9%20report.txt\\n"
        ),
    }
)
assert clipboard.paste_files() == [
    "/tmp/photos/a file.png",
    "/tmp/docs/unicodé report.txt",
]
clipboard.set_files_clipboard_reader(None)
""",
    "inspect": """\
import clipboard

assert callable(clipboard.inspect)
assert issubclass(clipboard.ClipboardContentError, Exception)
assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
assert callable(clipboard.set_clipboard_inspector)

clipboard.set_clipboard_inspector(
    lambda: clipboard.ClipboardOfferSnapshot(
        kinds=frozenset({"text"}),
        formats=("text/plain",),
    )
)
snapshot = clipboard.inspect()
assert snapshot.kinds == frozenset({"text"})
assert snapshot.formats == ("text/plain",)
clipboard.set_clipboard_inspector(None)
""",
    "clear": """\
import clipboard

assert callable(clipboard.clear)
assert callable(clipboard.set_clipboard_clearer)
assert "clear" in clipboard.__all__
assert "set_clipboard_clearer" in clipboard.__all__

calls = []
clipboard.set_clipboard_clearer(lambda: calls.append(None))
assert clipboard.clear() is None
assert calls == [None]
clipboard.set_clipboard_clearer(None)
assert not any(m == "PIL" or m.startswith("PIL.") for m in sys.modules)
""",
}


@pytest.mark.parametrize("surface", list(_SCENARIOS), ids=list(_SCENARIOS))
def test_public_function_without_pillow(surface: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", _BLOCK_PIL + _SCENARIOS[surface]],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

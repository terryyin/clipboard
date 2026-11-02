"""Structure seam for inspect: public surface + injectable enumerator (no desktop)."""

import subprocess
import sys

import pytest

import clipboard


def test_inspect_public_surface():
    assert callable(clipboard.inspect)
    assert issubclass(clipboard.ClipboardContentError, Exception)
    assert clipboard.ClipboardContentError is not clipboard.ClipboardImageError
    assert callable(clipboard.set_clipboard_inspector)
    assert hasattr(clipboard, "ClipboardOfferSnapshot")
    assert hasattr(clipboard, "ClipboardKind")


def test_default_inspect_raises_clipboard_content_error(
    restore_clipboard_inspector,
):
    """Default stub fails until later desktop enumerators land."""
    clipboard.set_clipboard_inspector(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_injected_inspector_returns_empty_snapshot(restore_clipboard_inspector):
    def fake_empty() -> clipboard.ClipboardOfferSnapshot:
        return clipboard.ClipboardOfferSnapshot(kinds=frozenset(), formats=())

    clipboard.set_clipboard_inspector(fake_empty)
    snapshot = clipboard.inspect()
    assert snapshot.kinds == frozenset()
    assert snapshot.formats == ()


def test_injected_inspector_returns_kinds_and_formats(restore_clipboard_inspector):
    expected = clipboard.ClipboardOfferSnapshot(
        kinds=frozenset({"html", "text"}),
        formats=("public.html", "public.utf8-plain-text"),
    )

    clipboard.set_clipboard_inspector(lambda: expected)
    assert clipboard.inspect() is expected


def test_injected_inspector_failure_is_clipboard_content_error(
    restore_clipboard_inspector,
):
    def boom() -> clipboard.ClipboardOfferSnapshot:
        raise clipboard.ClipboardContentError("enumeration denied")

    clipboard.set_clipboard_inspector(boom)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()
    assert raised.value.args == ("enumeration denied",)
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_unexpected_inspector_exception_wrapped(
    restore_clipboard_inspector,
):
    def boom() -> clipboard.ClipboardOfferSnapshot:
        raise RuntimeError("native helper crashed")

    clipboard.set_clipboard_inspector(boom)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()
    assert "native helper crashed" in str(raised.value)
    assert raised.value.__cause__ is not None


def test_reset_inspector_restores_default(restore_clipboard_inspector):
    clipboard.set_clipboard_inspector(
        lambda: clipboard.ClipboardOfferSnapshot(kinds=frozenset(), formats=())
    )
    clipboard.set_clipboard_inspector(None)
    assert clipboard._clipboard_inspector is clipboard._default_clipboard_inspector
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.inspect()


def test_inspect_importable_without_images_extra():
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
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

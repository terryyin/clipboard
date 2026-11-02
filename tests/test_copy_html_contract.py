"""In-memory copy_html Behavior contract (desktop-free dual-offer fake)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, NoReturn

import pytest

import clipboard


@dataclass
class FakeDualOfferClipboard:
    """In-memory offer model: sole text/image or dual html+text in one update."""

    offer: dict[str, Any] | None = None
    replace_calls: int = 0
    writer_invocations: list[tuple[str, str]] = field(default_factory=list)

    def seed_text(self, text: str) -> None:
        self.offer = {"kind": "text", "text": text}

    def seed_image(self, label: str = "prior-image") -> None:
        self.offer = {"kind": "image", "label": label}

    def dual_writer(self, html: str, text: str) -> None:
        """Publish both representations as one clipboard update."""
        self.writer_invocations.append((html, text))
        self.offer = {"kind": "html+text", "html": html, "text": text}
        self.replace_calls += 1

    def _reject(self, html: str, text: str, exc: BaseException) -> NoReturn:
        """Record an attempted write, then fail without replacing the offer."""
        self.writer_invocations.append((html, text))
        raise exc

    def one_type_only_writer(self, html: str, text: str) -> None:
        """Simulate a helper that cannot offer HTML and plain text together."""
        self._reject(
            html,
            text,
            clipboard.ClipboardContentError(
                "cannot offer HTML and plain text together (one-type-only helper path)"
            ),
        )

    def refuse_text_only_partial_writer(self, html: str, text: str) -> None:
        """Refuse a text-only partial offer so it cannot count as success."""
        self._reject(
            html,
            text,
            clipboard.ClipboardContentError(
                "refusing text-only partial offer; dual HTML+text required"
            ),
        )

    def transfer_fail_writer(self, html: str, text: str) -> None:
        self._reject(html, text, OSError("clipboard transfer failed"))


def test_valid_html_and_text_publish_both_in_one_update(
    restore_html_clipboard_writer,
):
    fake = FakeDualOfferClipboard()
    clipboard.set_html_clipboard_writer(fake.dual_writer)

    html = '<a href="https://example.com"><b>Report</b></a>'
    text = "Report — https://example.com"
    clipboard.copy_html(html, text)

    assert fake.replace_calls == 1
    assert fake.writer_invocations == [(html, text)]
    # One update: both representations on the same offer; neither alone.
    assert fake.offer == {"kind": "html+text", "html": html, "text": text}


@pytest.mark.parametrize(
    "html, text",
    [
        (None, "ok"),
        ("<b>x</b>", None),
        (b"<b>x</b>", "ok"),
        ("<b>x</b>", b"ok"),
        (123, "ok"),
        ("<b>x</b>", 123),
        ("", "ok"),
        ("   \n\t  ", "ok"),
        ("<b>x</b>", ""),
    ],
    ids=[
        "html-none",
        "text-none",
        "html-bytes",
        "text-bytes",
        "html-int",
        "text-int",
        "html-empty",
        "html-whitespace",
        "text-empty",
    ],
)
def test_invalid_args_fail_before_replace(html, text, restore_html_clipboard_writer):
    fake = FakeDualOfferClipboard()
    fake.seed_text("prior sole text")
    prior = dict(fake.offer)
    clipboard.set_html_clipboard_writer(fake.dual_writer)

    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.copy_html(html, text)

    assert fake.writer_invocations == []
    assert fake.replace_calls == 0
    assert fake.offer == prior


def test_one_type_only_backend_errors_without_partial_success(
    restore_html_clipboard_writer,
):
    fake = FakeDualOfferClipboard()
    fake.seed_text("keep me")
    prior = dict(fake.offer)
    clipboard.set_html_clipboard_writer(fake.one_type_only_writer)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_html("<i>styled</i>", "styled")

    assert (
        "together" in str(raised.value).lower()
        or "one-type" in str(raised.value).lower()
    )
    assert fake.replace_calls == 0
    assert fake.offer == prior


def test_text_only_path_is_not_silent_success(restore_html_clipboard_writer):
    fake = FakeDualOfferClipboard()
    fake.seed_image("prior-png")
    prior = dict(fake.offer)
    clipboard.set_html_clipboard_writer(fake.refuse_text_only_partial_writer)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_html("<p>x</p>", "x")

    assert "partial" in str(raised.value).lower() or "dual" in str(raised.value).lower()
    assert fake.offer == prior
    assert fake.replace_calls == 0


def test_transfer_failure_raises_actionable_content_error(
    restore_html_clipboard_writer,
):
    fake = FakeDualOfferClipboard()
    fake.seed_text("prior")
    prior = dict(fake.offer)
    clipboard.set_html_clipboard_writer(fake.transfer_fail_writer)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_html("<b>hi</b>", "hi")

    assert (
        "transfer" in str(raised.value).lower()
        or "write failed" in str(raised.value).lower()
    )
    assert isinstance(raised.value.__cause__, OSError)
    assert fake.offer == prior
    assert fake.replace_calls == 0


@pytest.mark.parametrize(
    "seed",
    ["text", "image"],
    ids=["replaces-prior-text", "replaces-prior-image"],
)
def test_successful_write_replaces_prior_sole_content(
    seed, restore_html_clipboard_writer
):
    fake = FakeDualOfferClipboard()
    if seed == "text":
        fake.seed_text("old sole text")
    else:
        fake.seed_image("old sole image")
    assert fake.offer is not None
    assert fake.offer["kind"] != "html+text"

    clipboard.set_html_clipboard_writer(fake.dual_writer)
    clipboard.copy_html("<table><tr><td>cell</td></tr></table>", "cell")

    assert fake.replace_calls == 1
    assert fake.offer == {
        "kind": "html+text",
        "html": "<table><tr><td>cell</td></tr></table>",
        "text": "cell",
    }


def test_macos_denied_pasteboard_write_is_content_error(
    restore_html_clipboard_writer, monkeypatch
):
    """Denied/unavailable pasteboard write surfaces as ClipboardContentError."""

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=1,
            stdout="",
            stderr="osascript: pasteboard access denied",
        )

    monkeypatch.setattr(clipboard.sys, "platform", "darwin")
    monkeypatch.setattr(clipboard.subprocess, "run", fake_run)
    clipboard.set_html_clipboard_writer(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_html("<b>x</b>", "x")
    assert "pasteboard write failed" in str(raised.value).lower()


def test_macos_missing_osascript_is_content_error(
    restore_html_clipboard_writer, monkeypatch
):
    def boom(*args, **kwargs):
        raise FileNotFoundError("osascript")

    monkeypatch.setattr(clipboard.sys, "platform", "darwin")
    monkeypatch.setattr(clipboard.subprocess, "run", boom)
    clipboard.set_html_clipboard_writer(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_html("<b>x</b>", "x")
    assert raised.value.__cause__ is not None


def test_unsupported_platform_default_writer_is_content_error(
    restore_html_clipboard_writer, monkeypatch
):
    monkeypatch.setattr(clipboard.sys, "platform", "linux")
    clipboard.set_html_clipboard_writer(None)
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.copy_html("<b>x</b>", "x")
    message = str(raised.value).lower()
    assert "not available" in message
    assert "multi-type" in message
    assert "xclip" in message

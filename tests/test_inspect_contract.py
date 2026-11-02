"""In-memory inspect() Behavior contract (desktop-free fake offer model)."""

from __future__ import annotations

import pytest
from fake_offer_clipboard import FakeOfferClipboard

import clipboard


def test_html_and_text_offer_reports_both_kinds_and_native_ids(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    fake.seed(
        ["public.html", "public.utf8-plain-text", "com.example.undecodable"],
        payloads={
            "public.html": "<b>Report</b>",
            "public.utf8-plain-text": "Report",
        },
    )
    clipboard.set_clipboard_inspector(fake.inspector)

    snapshot = clipboard.inspect()

    assert snapshot.kinds == frozenset({"html", "text"})
    assert snapshot.formats == (
        "public.html",
        "public.utf8-plain-text",
        "com.example.undecodable",
    )
    assert fake.payload_fetches == []


def test_image_only_offer_reports_image_without_text_or_html(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    # paste() would look empty; kind presence must come from type ids.
    fake.seed(
        ["public.png"],
        payloads={"public.png": b"\x89PNG\r\n\x1a\n"},
        paste_text="",
    )
    clipboard.set_clipboard_inspector(fake.inspector)

    assert fake.paste_text() == ""
    snapshot = clipboard.inspect()

    assert snapshot.kinds == frozenset({"image"})
    assert snapshot.formats == ("public.png",)
    assert fake.payload_fetches == []


def test_empty_offer_yields_empty_snapshot_not_error(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    fake.clear()
    clipboard.set_clipboard_inspector(fake.inspector)

    snapshot = clipboard.inspect()

    assert snapshot.kinds == frozenset()
    assert snapshot.formats == ()
    assert fake.payload_fetches == []


def test_file_list_native_id_reports_files_without_filesystem_read(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    fake.seed(
        ["CF_HDROP", "com.example.other-undecodable"],
        payloads={"CF_HDROP": b"fake-hdrop"},
    )
    clipboard.set_clipboard_inspector(fake.inspector)

    snapshot = clipboard.inspect()

    assert snapshot.kinds == frozenset({"files"})
    assert "CF_HDROP" in snapshot.formats
    assert "com.example.other-undecodable" in snapshot.formats
    assert fake.filesystem_reads == []
    assert fake.payload_fetches == []


def test_access_denied_raises_clipboard_content_error_not_empty(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    fake.seed(["public.utf8-plain-text"])
    fake.deny_access(
        "clipboard access denied: pasteboard authorization refused "
        "(grant clipboard access or inject an inspector for tests)"
    )
    clipboard.set_clipboard_inspector(fake.inspector)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    assert "access denied" in str(raised.value).lower()
    assert "clipboard" in str(raised.value).lower()
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_enumeration_transfer_failure_raises_clipboard_content_error(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    fake.seed(["text/html", "text/plain"])
    fake.fail_enumeration("native helper crashed while listing TARGETS")
    clipboard.set_clipboard_inspector(fake.inspector)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    message = str(raised.value).lower()
    assert "native helper crashed" in message or "listing" in message
    assert raised.value.__cause__ is not None
    assert not isinstance(raised.value, clipboard.ClipboardImageError)


def test_missing_helper_message_is_actionable_not_empty_success(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    fake.deny_access(
        "missing Linux clipboard enumeration helper: install xclip "
        "(xclip -o -t TARGETS) or wl-paste -l, or inject an inspector for tests"
    )
    clipboard.set_clipboard_inspector(fake.inspector)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.inspect()

    text = str(raised.value)
    assert "xclip" in text or "wl-paste" in text
    assert "helper" in text.lower()


def test_inspect_does_not_mutate_fake_offer_model(
    restore_clipboard_inspector,
):
    fake = FakeOfferClipboard()
    fake.seed(
        ["text/html", "text/plain"],
        payloads={"text/html": "<i>x</i>", "text/plain": "x"},
    )
    prior = {
        "formats": list(fake.formats),
        "payloads": dict(fake.payloads),
        "paste_text": fake.paste_text_value,
    }
    clipboard.set_clipboard_inspector(fake.inspector)

    first = clipboard.inspect()
    second = clipboard.inspect()

    assert first.kinds == frozenset({"html", "text"})
    assert second.kinds == first.kinds
    assert second.formats == first.formats
    assert fake.formats == prior["formats"]
    assert fake.payloads == prior["payloads"]
    assert fake.paste_text_value == prior["paste_text"]
    assert fake.payload_fetches == []
    assert fake.filesystem_reads == []


def test_kinds_derived_from_type_list_alone_not_payload_presence(
    restore_clipboard_inspector,
):
    """Commitment 16/37: type enumeration suffices; payloads unused."""
    fake = FakeOfferClipboard()
    fake.seed(
        ["HTML Format", "CF_UNICODETEXT"],
        payloads={},  # no bodies stored
    )
    clipboard.set_clipboard_inspector(fake.inspector)

    snapshot = clipboard.inspect()

    assert snapshot.kinds == frozenset({"html", "text"})
    assert snapshot.formats == ("HTML Format", "CF_UNICODETEXT")
    assert fake.payload_fetches == []


def test_empty_and_access_failure_remain_distinguishable(
    restore_clipboard_inspector,
):
    empty = FakeOfferClipboard()
    empty.clear()
    clipboard.set_clipboard_inspector(empty.inspector)
    empty_snapshot = clipboard.inspect()
    assert empty_snapshot.kinds == frozenset()
    assert empty_snapshot.formats == ()

    denied = FakeOfferClipboard()
    denied.deny_access(
        "clipboard unavailable: no usable desktop session for format enumeration"
    )
    clipboard.set_clipboard_inspector(denied.inspector)
    with pytest.raises(clipboard.ClipboardContentError):
        clipboard.inspect()

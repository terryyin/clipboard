"""In-memory paste_html Behavior contract (desktop-free fake clipboard model)."""

from __future__ import annotations

import pytest
from html_offer import (
    FRAGMENT_PLATFORM,
    WINDOWS,
    build_cf_html,
    paste_fails,
    paste_unchanged,
)

import clipboard
from clipboard._html_envelope import _cf_html_offer, _fragment_offer, _HtmlOffer

# --- 2 / 28: fragment-only text/html offers -------------------------------


@pytest.mark.parametrize(
    "body",
    ["<b>Hello</b> 世界 🎉", "<b>Hello</b> 世界 🎉".encode()],
    ids=["str", "utf8-bytes"],
)
def test_fragment_offer_returns_unicode_fragment(fake_html_clipboard, body):
    fake_html_clipboard.representations = {
        "text/html": body,
        "text/plain": "Hello 世界 🎉",
    }
    result = paste_unchanged(fake_html_clipboard)
    assert result == "<b>Hello</b> 世界 🎉"
    assert isinstance(result, str)
    assert fake_html_clipboard.reads == 1


@pytest.mark.parametrize(
    "raw",
    [
        b"\xef\xbb\xbf<p>\xc3\xa9</p>",
        "<p>é</p>".encode("utf-16"),
        b"\xfe\xff" + "<p>é</p>".encode("utf-16-be"),
    ],
    ids=["utf8-bom", "utf16-bom-native", "utf16-be-bom"],
)
def test_fragment_offer_bom_marked_bytes_decode(fake_html_clipboard, raw):
    fake_html_clipboard.representations = {"text/html": raw}
    assert paste_unchanged(fake_html_clipboard) == "<p>é</p>"


def test_fragment_offer_without_envelope_is_returned_directly(fake_html_clipboard):
    fake_html_clipboard.representations = {
        "text/html": "<meta charset='utf-8'><i>plain</i>"
    }
    assert paste_unchanged(fake_html_clipboard) == "<meta charset='utf-8'><i>plain</i>"


def test_fragment_offer_invalid_utf8_raises(fake_html_clipboard):
    fake_html_clipboard.representations = {"text/html": b"<p>\xc3(</p>"}
    error = paste_fails(fake_html_clipboard, "text/html body is not valid UTF-8")
    assert isinstance(error.__cause__, UnicodeDecodeError)


@pytest.mark.parametrize("body", ["", b""], ids=["str", "bytes"])
def test_empty_fragment_offer_returns_empty_string(fake_html_clipboard, body):
    fake_html_clipboard.representations = {"text/html": body, "text/plain": "x"}
    result = paste_unchanged(fake_html_clipboard)
    assert result == ""
    assert result is not None


@pytest.mark.parametrize(
    "raw",
    [
        "<p>é</p>".encode("utf-16-le"),
        "<p>é</p>".encode("utf-16-be"),
        "<p>x</p>".encode("utf-16-le"),
        "<p>世界</p>".encode("utf-16-be"),
    ],
    ids=["le-latin1", "be-latin1", "le-ascii", "be-cjk"],
)
def test_bomless_utf16_fragment_raises(fake_html_clipboard, raw):
    fake_html_clipboard.representations = {"text/html": raw}
    paste_fails(
        fake_html_clipboard,
        r"text/html body (is not valid UTF-8 \(or BOM-marked UTF-16\)"
        r"|contains NUL characters \(likely UTF-16 without a byte-order mark\));"
        " refusing to guess",
    )


@pytest.mark.parametrize(
    "body",
    ["<b>終端</b>\x00", "<b>終端</b>".encode() + b"\x00\x00"],
    ids=["str", "bytes"],
)
def test_trailing_nul_terminators_are_stripped(fake_html_clipboard, body):
    fake_html_clipboard.representations = {"text/html": body}
    assert paste_unchanged(fake_html_clipboard) == "<b>終端</b>"


@pytest.mark.parametrize(
    "body", ["<b>a\x00b</b>", b"\x00<b>x</b>"], ids=["str-inner", "bytes-leading"]
)
def test_embedded_nul_in_fragment_body_raises(fake_html_clipboard, body):
    fake_html_clipboard.representations = {"text/html": body}
    paste_fails(fake_html_clipboard, "contains NUL characters")


ACTIVE_MARKUP = (
    "<script>window.pwned = 1</script>"
    '<img src="http://example.invalid/track.png">'
    '<a href="file:///etc/passwd">local</a>'
    '<link rel="stylesheet" href="https://example.invalid/x.css">'
)


@pytest.mark.parametrize("platform", [WINDOWS, FRAGMENT_PLATFORM])
def test_active_markup_is_returned_verbatim_without_resolving(
    fake_html_clipboard, monkeypatch, platform
):
    def forbidden(*args, **kwargs):
        raise AssertionError("paste_html must not fetch, open, or execute anything")

    import socket
    import subprocess
    import urllib.request
    import webbrowser

    for target, name in [
        (socket, "create_connection"),
        (urllib.request, "urlopen"),
        (subprocess, "run"),
        (subprocess, "Popen"),
        (webbrowser, "open"),
    ]:
        monkeypatch.setattr(target, name, forbidden)
    monkeypatch.setattr("builtins.open", forbidden)
    fake_html_clipboard.platform = platform
    fake_html_clipboard.representations = {
        "HTML Format": build_cf_html(
            ACTIVE_MARKUP, source_url="https://example.invalid/"
        ),
        "text/html": ACTIVE_MARKUP,
    }
    assert paste_unchanged(fake_html_clipboard) == ACTIVE_MARKUP


# --- 3 / 3.q / 17 / E3 / 8.4 / 23 / 8.5: ordinary absence -----------------


@pytest.mark.parametrize("platform", [WINDOWS, FRAGMENT_PLATFORM])
@pytest.mark.parametrize(
    "representations",
    [
        {},
        {"text/plain": "<b>looks like markup</b> & text"},
        {"text/plain": "plain", "text/rtf": r"{\rtf1 {\b bold}}"},
        {"image/png": b"\x89PNG\r\n\x1a\n"},
        {"text/uri-list": "file:///tmp/a.txt\r\n"},
    ],
    ids=["empty", "text-only", "text+rtf", "image-only", "file-list"],
)
def test_non_html_offers_return_none(fake_html_clipboard, platform, representations):
    fake_html_clipboard.platform = platform
    fake_html_clipboard.representations = representations
    assert paste_unchanged(fake_html_clipboard) is None
    assert fake_html_clipboard.reads == 1


# --- 4 / 4.1 / 4.3 / 4.q: backend failures --------------------------------


@pytest.mark.parametrize(
    ("failure", "match"),
    [
        (PermissionError("clipboard access denied"), "HTML read failed: .*denied"),
        (
            OSError("clipboard is locked by another process"),
            "HTML read failed: .*locked",
        ),
        (
            BrokenPipeError("helper closed pipe mid-transfer"),
            "HTML read failed: .*transfer",
        ),
        (
            clipboard.ClipboardContentError("xclip not found; install xclip"),
            "xclip not found",
        ),
    ],
    ids=["denied", "unavailable", "transfer", "helper-missing"],
)
def test_backend_failures_raise_content_error_not_none(
    fake_html_clipboard, failure, match
):
    fake_html_clipboard.representations = {"text/html": "<b>kept</b>"}
    fake_html_clipboard.failure = failure
    error = paste_fails(fake_html_clipboard, match)
    assert error is failure or error.__cause__ is failure


@pytest.mark.parametrize(
    "value",
    ["<b>bare str</b>", b"<b>bare bytes</b>", 42, ["<b>x</b>"]],
    ids=["str", "bytes", "int", "list"],
)
def test_unexpected_reader_value_is_contract_failure(
    restore_html_clipboard_reader, value
):
    clipboard.set_html_clipboard_reader(lambda: value)
    with pytest.raises(clipboard.ClipboardContentError, match="unexpected value"):
        clipboard.paste_html()


@pytest.mark.parametrize(
    ("offer", "match"),
    [
        (_cf_html_offer("Version:0.9\r\n"), "envelope as bytes"),
        (_fragment_offer(3.5), "unsupported type float"),
        (_HtmlOffer("rtf", b"{\\rtf1}"), "unknown kind 'rtf'"),
    ],
    ids=["cf-html-str", "fragment-float", "unknown-kind"],
)
def test_malformed_offer_value_is_contract_failure(
    restore_html_clipboard_reader, offer, match
):
    clipboard.set_html_clipboard_reader(lambda: offer)
    with pytest.raises(clipboard.ClipboardContentError, match=match):
        clipboard.paste_html()

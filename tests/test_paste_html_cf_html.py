"""Windows HTML Format (CF_HTML) fragment extraction through paste_html (fake)."""

from __future__ import annotations

import pytest
from html_offer import WINDOWS, build_cf_html, paste_fails, paste_unchanged, set_header

CONTEXT_BEFORE = "<html><body><p>未選択の前文 😀 context</p><div>"
CONTEXT_AFTER = "</div><p>after 🎈 unselected</p></body></html>"
FRAGMENT = "<b>選択 🎉 émoji</b> &amp; more"


@pytest.fixture
def windows_board(fake_html_clipboard):
    fake_html_clipboard.platform = WINDOWS
    return fake_html_clipboard


def offer(board, envelope: bytes) -> None:
    board.representations = {
        "HTML Format": envelope,
        "text/plain": "選択 🎉 émoji & more",
    }


def test_non_ascii_fragment_uses_utf8_byte_offsets(windows_board):
    envelope = build_cf_html(FRAGMENT, before=CONTEXT_BEFORE, after=CONTEXT_AFTER)
    # Character offsets would land elsewhere: the context is multi-byte.
    text = envelope.decode("utf-8")
    start = int(text.split("StartFragment:")[1][:10])
    assert text[start : start + len(FRAGMENT)] != FRAGMENT
    offer(windows_board, envelope)
    result = paste_unchanged(windows_board)
    assert result == FRAGMENT
    for excluded in ("Version:", "StartHTML", "未選択", "unselected", "<html>", "<!--"):
        assert excluded not in result


@pytest.mark.parametrize(
    "markers", [True, False], ids=["comment-markers", "no-markers"]
)
@pytest.mark.parametrize(
    "selection", [None, True, False], ids=["no-selection", "selection", "selection-1"]
)
@pytest.mark.parametrize(
    "source_url",
    [None, "https://example.com/%E9%A1%B5?q=1"],
    ids=["no-url", "source-url"],
)
def test_header_variants_yield_only_the_fragment(
    windows_board, markers, selection, source_url
):
    envelope = build_cf_html(
        FRAGMENT,
        before=CONTEXT_BEFORE,
        after=CONTEXT_AFTER,
        markers=markers,
        selection=selection,
        source_url=source_url,
    )
    if selection is False:
        assert b"StartSelection:-000000001" in envelope
    offer(windows_board, envelope)
    assert paste_unchanged(windows_board) == FRAGMENT


def test_byte_offsets_are_authoritative_over_comment_markers(windows_board):
    # Markers wrap the whole div; offsets select only the inner <b>.
    envelope = build_cf_html(
        "<b>offset pick</b>",
        before="<html><body><!--StartFragment--><div>",
        after="</div><!--EndFragment--></body></html>",
        markers=False,
    )
    offer(windows_board, envelope)
    assert paste_unchanged(windows_board) == "<b>offset pick</b>"


def test_lf_line_endings_and_trailing_nul_are_tolerated(windows_board):
    offer(windows_board, build_cf_html(FRAGMENT, newline="\n") + b"\x00")
    assert paste_unchanged(windows_board) == FRAGMENT


def test_empty_fragment_range_returns_empty_string(windows_board):
    envelope = build_cf_html("", before=CONTEXT_BEFORE, after=CONTEXT_AFTER)
    assert _offset(envelope, "StartFragment") == _offset(envelope, "EndFragment")
    offer(windows_board, envelope)
    result = paste_unchanged(windows_board)
    assert result == ""
    assert result is not None


def test_raw_utf8_source_url_does_not_shift_fragment(windows_board):
    url = "https://例え.jp/ö"
    envelope = build_cf_html(
        FRAGMENT, before=CONTEXT_BEFORE, after=CONTEXT_AFTER, source_url=url
    )
    assert f"SourceURL:{url}".encode() in envelope
    offer(windows_board, envelope)
    result = paste_unchanged(windows_board)
    assert result == FRAGMENT
    assert "例え" not in result and "SourceURL" not in result


def _powershell_as_html_envelope(fragment: str, title: str) -> bytes:
    """Mimic Windows PowerShell ``Set-Clipboard -AsHtml`` (SetClipboardCommand).

    ``sb.AppendLine(Header)`` then ``StartHTML = Header.Length``: StartHTML
    points at the header's own CRLF, inside the header block, while the
    fragment offsets are correct UTF-8 byte counts.
    """
    names = ("StartHTML", "EndHTML", "StartFragment", "EndFragment")
    names += ("StartSelection", "EndSelection")

    def header(values: dict[str, int]) -> str:
        lines = ["Version:0.9"] + [f"{n}:{values.get(n, 0):09d}" for n in names]
        return "\r\n".join(lines)

    head_chars = len(header({}))
    pre = (
        '\r\n<!DOCTYPE HTML  PUBLIC "-//W3C//DTD HTML 4.0  Transitional//EN">\r\n'
        f"<html><head><title>{title}</title></head><body><!--StartFragment-->"
    ).encode()
    frag = fragment.encode()
    post = b"<!--EndFragment--></body></html>"
    start = head_chars + len(pre)
    values = {
        "StartHTML": head_chars,
        "EndHTML": start + len(frag) + len(post),
        "StartFragment": start,
        "EndFragment": start + len(frag),
    }
    values["StartSelection"] = values["StartFragment"]
    values["EndSelection"] = values["EndFragment"]
    return header(values).encode() + pre + frag + post


def test_start_html_inside_header_like_powershell_as_html(windows_board):
    envelope = _powershell_as_html_envelope(FRAGMENT, "Ünïcödé 東京 context")
    head_end = envelope.index(b"\r\n<!DOCTYPE") + 2
    assert _offset(envelope, "StartHTML") == head_end - 2  # at the header CRLF
    offer(windows_board, envelope)
    assert paste_unchanged(windows_board) == FRAGMENT


def test_nul_inside_fragment_range_raises(windows_board):
    offer(windows_board, build_cf_html("<b>a\x00b</b>", before=CONTEXT_BEFORE))
    error = paste_fails(windows_board, "fragment bytes .* contain NUL characters")
    assert "Windows HTML Format envelope is malformed" in str(error)


def _good() -> bytes:
    return build_cf_html(FRAGMENT, before=CONTEXT_BEFORE, after=CONTEXT_AFTER)


def _offset(envelope: bytes, name: str) -> int:
    return int(envelope.split(name.encode() + b":")[1].split(b"\r\n")[0])


CORRUPTIONS = {
    "missing-start-fragment": (
        lambda e: set_header(e, "StartFragment", None),
        "missing StartFragment",
    ),
    "missing-end-fragment": (
        lambda e: set_header(e, "EndFragment", None),
        "missing EndFragment",
    ),
    "non-numeric": (
        lambda e: set_header(e, "StartFragment", "12abc"),
        "StartFragment is not a number",
    ),
    "empty-value": (
        lambda e: set_header(e, "EndFragment", ""),
        "EndFragment is not a number",
    ),
    "negative": (
        lambda e: set_header(e, "StartFragment", "-5"),
        "StartFragment is negative",
    ),
    "minus-one-required": (
        lambda e: set_header(e, "EndFragment", "-1"),
        "EndFragment is negative",
    ),
    "end-beyond-envelope": (
        lambda e: set_header(e, "EndFragment", str(len(e) + 10)),
        "beyond the envelope length",
    ),
    "start-after-end": (
        lambda e: set_header(e, "StartFragment", str(_offset(e, "EndFragment") + 1)),
        "is after EndFragment",
    ),
    "start-in-header": (
        lambda e: set_header(e, "StartFragment", "3"),
        "points into the header",
    ),
    "fragment-before-html": (
        lambda e: set_header(e, "StartHTML", str(_offset(e, "StartFragment") + 1)),
        "outside the HTML range",
    ),
    "fragment-after-html": (
        lambda e: set_header(e, "EndHTML", str(_offset(e, "EndFragment") - 1)),
        "outside the HTML range",
    ),
    "html-range-reversed": (
        lambda e: set_header(e, "StartHTML", str(_offset(e, "EndHTML") + 1)),
        "HTML range .* is outside the envelope .* or reversed",
    ),
    "html-beyond-envelope": (
        lambda e: set_header(e, "EndHTML", str(len(e) + 1)),
        "HTML range .* is outside the envelope",
    ),
    "html-half-missing": (
        lambda e: set_header(e, "EndHTML", None),
        "only one of StartHTML",
    ),
    "splits-code-point": (
        lambda e: set_header(e, "StartFragment", str(_offset(e, "StartFragment") + 4)),
        "not valid UTF-8 .*splits a character",
    ),
    "duplicate-header": (
        lambda e: e.replace(b"Version:0.9", b"StartHTML:0", 1),
        "duplicate StartHTML",
    ),
    "not-an-envelope": (lambda e: b"<b>raw html</b>", "missing StartFragment"),
}


@pytest.mark.parametrize(
    ("corrupt", "match"), CORRUPTIONS.values(), ids=CORRUPTIONS.keys()
)
def test_corrupt_metadata_raises_without_fragment_or_mutation(
    windows_board, corrupt, match
):
    envelope = corrupt(_good())
    offer(windows_board, envelope)
    error = paste_fails(windows_board, match)
    assert "Windows HTML Format envelope is malformed" in str(error)
    assert "no trustworthy fragment" in str(error)


def test_invalid_utf8_inside_fragment_raises(windows_board):
    envelope = build_cf_html("<b>ok</b>")
    start = _offset(envelope, "StartFragment")
    broken = envelope[: start + 3] + b"\xff" + envelope[start + 4 :]
    offer(windows_board, broken)
    error = paste_fails(windows_board, "fragment bytes .* are not valid UTF-8")
    assert isinstance(error.__cause__, UnicodeDecodeError)

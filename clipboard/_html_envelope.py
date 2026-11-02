"""Private HTML read offer value and native envelope decoding for ``paste_html``.

An HTML clipboard reader returns ``None`` (no HTML offered) or an
``_HtmlOffer`` naming which native representation it read:

* ``_CF_HTML`` -- the Windows ``HTML Format`` envelope as raw ``bytes``. Its
  ``StartFragment`` / ``EndFragment`` header values are byte offsets into the
  UTF-8 envelope; only the bytes between them are returned.
* ``_FRAGMENT`` -- a fragment-only ``text/html`` body (macOS / Linux) as
  ``str`` or ``bytes`` (UTF-8, or UTF-16 with a byte-order mark).

Nothing here parses, executes, or resolves the markup itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ._errors import ClipboardContentError

_CF_HTML = "cf_html"
_FRAGMENT = "fragment"


@dataclass(frozen=True)
class _HtmlOffer:
    """Native HTML representation read from the clipboard (package-private)."""

    kind: str
    data: object


def _cf_html_offer(envelope: bytes) -> _HtmlOffer:
    return _HtmlOffer(_CF_HTML, envelope)


def _fragment_offer(body: str | bytes) -> _HtmlOffer:
    return _HtmlOffer(_FRAGMENT, body)


_HEADER_LINE = re.compile(rb"([A-Za-z]+):([^\r\n]*)(?:\r\n|\n|\r)")
_REQUIRED_OFFSET_KEYS = ("StartFragment", "EndFragment")
_OPTIONAL_OFFSET_KEYS = ("StartHTML", "EndHTML", "StartSelection", "EndSelection")
_NUMBER = re.compile(r"-?[0-9]+")


def _envelope_error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(
        f"paste_html: Windows HTML Format envelope is malformed: {detail}; "
        "no trustworthy fragment can be extracted"
    )


def _parse_header(envelope: bytes) -> tuple[dict[str, int], int]:
    """Return the offset headers and the byte length of the header block."""
    offsets: dict[str, int] = {}
    pos = 0
    while (line := _HEADER_LINE.match(envelope, pos)) is not None:
        key = line.group(1).decode("ascii")
        pos = line.end()
        if key not in _REQUIRED_OFFSET_KEYS and key not in _OPTIONAL_OFFSET_KEYS:
            continue  # Version, SourceURL, and other metadata stay internal.
        raw = line.group(2).decode("latin-1").strip()
        if key in offsets:
            raise _envelope_error(f"duplicate {key} header")
        if not _NUMBER.fullmatch(raw):
            raise _envelope_error(f"{key} is not a number ({raw!r})")
        value = int(raw)
        if value < 0 and not (value == -1 and key in _OPTIONAL_OFFSET_KEYS):
            raise _envelope_error(f"{key} is negative ({value})")
        offsets[key] = value
    return offsets, pos


def _fragment_range(
    offsets: dict[str, int], header_end: int, length: int
) -> tuple[int, int]:
    """Validate the header offsets and return the fragment's byte range."""
    for key in _REQUIRED_OFFSET_KEYS:
        if key not in offsets:
            raise _envelope_error(f"missing {key} header")
    start, end = offsets["StartFragment"], offsets["EndFragment"]
    if start > end:
        raise _envelope_error(f"StartFragment ({start}) is after EndFragment ({end})")
    if start < header_end:
        raise _envelope_error(
            f"StartFragment ({start}) points into the header block "
            f"(header ends at byte {header_end})"
        )
    if end > length:
        raise _envelope_error(
            f"EndFragment ({end}) is beyond the envelope length ({length})"
        )
    html_start = offsets.get("StartHTML", -1)
    html_end = offsets.get("EndHTML", -1)
    if (html_start == -1) != (html_end == -1):
        raise _envelope_error("only one of StartHTML / EndHTML is present")
    if html_start != -1:
        if not header_end <= html_start <= html_end <= length:
            raise _envelope_error(
                f"HTML range {html_start}..{html_end} is outside the envelope "
                f"body {header_end}..{length} or reversed"
            )
        if not html_start <= start <= end <= html_end:
            raise _envelope_error(
                f"fragment range {start}..{end} is outside the HTML range "
                f"{html_start}..{html_end}"
            )
    return start, end


def _extract_cf_html_fragment(envelope: bytes) -> str:
    """Return the UTF-8 fragment between StartFragment and EndFragment bytes."""
    offsets, header_end = _parse_header(envelope)
    start, end = _fragment_range(offsets, header_end, len(envelope))
    try:
        fragment = envelope[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _envelope_error(
            f"fragment bytes {start}..{end} are not valid UTF-8 "
            "(invalid encoding or an offset splits a character)"
        ) from exc
    if "\x00" in fragment:
        raise _envelope_error(
            f"fragment bytes {start}..{end} contain NUL characters "
            "(not UTF-8 HTML, or the offsets cover a terminator)"
        )
    return fragment


def _decode_fragment_body(body: object) -> str:
    """Decode a ``text/html`` body; trailing NUL terminators are dropped."""
    text = _decode_fragment_text(body).rstrip("\x00")
    if "\x00" in text:
        raise ClipboardContentError(
            "paste_html: clipboard text/html body contains NUL characters "
            "(likely UTF-16 without a byte-order mark); refusing to guess "
            "its encoding"
        )
    return text


def _decode_fragment_text(body: object) -> str:
    if isinstance(body, str):
        return body
    if not isinstance(body, (bytes, bytearray)):
        raise ClipboardContentError(
            "paste_html: HTML reader returned a text/html body of unsupported "
            f"type {type(body).__name__} (expected str or bytes)"
        )
    raw = bytes(body)
    try:
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return raw.decode("utf-16")
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ClipboardContentError(
            "paste_html: clipboard text/html body is not valid UTF-8 "
            "(or BOM-marked UTF-16); refusing to guess its encoding"
        ) from exc


def _decode_html_offer(offer: object) -> str | None:
    """Turn a reader result into the public ``paste_html`` result."""
    if offer is None:
        return None
    if not isinstance(offer, _HtmlOffer):
        raise ClipboardContentError(
            "paste_html: HTML reader returned an unexpected value of type "
            f"{type(offer).__name__} (expected None or an HTML offer); "
            "this is a reader backend contract failure"
        )
    if offer.kind == _CF_HTML:
        if not isinstance(offer.data, (bytes, bytearray)):
            raise ClipboardContentError(
                "paste_html: Windows HTML Format offer must carry the raw "
                f"envelope as bytes (got {type(offer.data).__name__})"
            )
        return _extract_cf_html_fragment(bytes(offer.data))
    if offer.kind == _FRAGMENT:
        return _decode_fragment_body(offer.data)
    raise ClipboardContentError(
        f"paste_html: HTML reader returned an offer of unknown kind {offer.kind!r}"
    )

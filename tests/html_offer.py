"""In-memory HTML clipboard model and CF_HTML envelope builder for paste_html tests."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

import pytest

import clipboard
from clipboard._html_envelope import _cf_html_offer, _fragment_offer, _HtmlOffer

WINDOWS = "windows"
FRAGMENT_PLATFORM = "fragment"  # macOS / Linux: fragment-only text/html
# Desktop-free reader sample (one test-side home; probes use scripts/native_probe_*).
FRAGMENT = '<a href="https://example.com/caf%C3%A9"><b>café → naïve 日本</b></a>'


def build_cf_html(
    fragment: str,
    *,
    before: str = "<html><body>",
    after: str = "</body></html>",
    markers: bool = True,
    source_url: str | None = None,
    selection: bool | None = None,
    newline: str = "\r\n",
) -> bytes:
    """Build a Windows HTML Format envelope with offsets from encoded bytes."""
    open_marker = "<!--StartFragment-->" if markers else ""
    close_marker = "<!--EndFragment-->" if markers else ""
    names = ["Version", "StartHTML", "EndHTML", "StartFragment", "EndFragment"]
    if selection is not None:
        names += ["StartSelection", "EndSelection"]
    if source_url is not None:
        names.append("SourceURL")

    def header(values: dict[str, int]) -> bytes:
        lines = []
        for name in names:
            if name == "Version":
                lines.append("Version:0.9")
            elif name == "SourceURL":
                lines.append(f"SourceURL:{source_url}")
            else:
                lines.append(f"{name}:{values.get(name, 0):010d}")
        return (newline.join(lines) + newline).encode("utf-8")

    head_len = len(header({}))
    pre = (before + open_marker).encode("utf-8")
    frag = fragment.encode("utf-8")
    post = (close_marker + after).encode("utf-8")
    values = {
        "StartHTML": head_len,
        "EndHTML": head_len + len(pre) + len(frag) + len(post),
        "StartFragment": head_len + len(pre),
        "EndFragment": head_len + len(pre) + len(frag),
    }
    if selection is True:
        values["StartSelection"] = values["StartFragment"]
        values["EndSelection"] = values["EndFragment"]
    elif selection is False:
        values["StartSelection"] = values["EndSelection"] = -1
    return header(values) + pre + frag + post  # -1 pads as -000000001


def set_header(envelope: bytes, name: str, value: str | None) -> bytes:
    """Rewrite (or drop, with ``None``) one header line, keeping byte length."""
    lines = envelope.split(b"\r\n")
    for i, line in enumerate(lines):
        if line.startswith(name.encode() + b":"):
            old_len = len(line)
            if value is None:
                lines[i] = b"X" * (old_len - 1) + b":"  # unknown header, same length
            else:
                lines[i] = f"{name}:{value}".encode().ljust(old_len)
            return b"\r\n".join(lines)
    raise AssertionError(f"no {name} header")


@dataclass
class FakeClipboard:
    """Offer model with native representations; reads never change it."""

    platform: str = FRAGMENT_PLATFORM
    representations: dict[str, object] = field(default_factory=dict)
    failure: BaseException | None = None
    reads: int = 0

    def reader(self) -> _HtmlOffer | None:
        self.reads += 1
        if self.failure is not None:
            raise self.failure
        if self.platform == WINDOWS:
            envelope = self.representations.get("HTML Format")
            return None if envelope is None else _cf_html_offer(envelope)
        body = self.representations.get("text/html")
        return None if body is None else _fragment_offer(body)

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.representations)


def paste_unchanged(board: FakeClipboard):
    before = board.snapshot()
    try:
        return clipboard.paste_html()
    finally:
        assert board.snapshot() == before


def paste_fails(board: FakeClipboard, match: str) -> clipboard.ClipboardContentError:
    with pytest.raises(clipboard.ClipboardContentError, match=match) as info:
        paste_unchanged(board)
    assert not isinstance(info.value, clipboard.ClipboardImageError)
    return info.value

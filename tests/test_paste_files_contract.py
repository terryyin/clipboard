"""In-memory paste_files Behavior: local decode and ordinary absence.

Observes plan slice 2 / key examples 1–3 without a real clipboard.
"""

from __future__ import annotations

import copy

import pytest
from paste_files_offer import (
    ORDERED_PATHS,
    SPACED_PATH,
    URI_LIST_TWO_LOCAL,
    FakeFilesClipboard,
    install_path_side_effect_spies,
)

import clipboard

# --- Example 1: ordered local paths (Unicode + spaces) ---


def test_ordered_two_file_path_list_unicode_and_spaces(
    restore_files_clipboard_reader, monkeypatch
):
    fake = FakeFilesClipboard(offer=list(ORDERED_PATHS))
    clipboard.set_files_clipboard_reader(fake.reader)
    hits = install_path_side_effect_spies(monkeypatch, ORDERED_PATHS)
    before = copy.deepcopy(fake.offer)

    result = clipboard.paste_files()

    assert result == ORDERED_PATHS
    assert isinstance(result, list)
    assert all(isinstance(p, str) for p in result)
    assert fake.offer == before
    assert hits == []
    assert fake.cut_reissues == []
    # Result is a copy: mutating it must not mutate the fake offer.
    result.append("/tmp/injected")
    assert fake.offer == before


# --- Example 2: file:// uri-list and path-list shaped fakes ---


def test_uri_list_file_uris_decode_to_local_paths(
    restore_files_clipboard_reader, monkeypatch
):
    offer = {
        "kind": "uri-list",
        "uri_list": URI_LIST_TWO_LOCAL,
    }
    fake = FakeFilesClipboard(offer=offer)
    clipboard.set_files_clipboard_reader(fake.reader)
    hits = install_path_side_effect_spies(monkeypatch, ORDERED_PATHS)
    before = copy.deepcopy(fake.offer)

    result = clipboard.paste_files()

    assert result == ORDERED_PATHS
    assert not any(p.startswith("file:") for p in result)
    assert fake.offer == before
    assert hits == []


def test_structured_paths_offer_decodes_like_path_list(
    restore_files_clipboard_reader,
):
    fake = FakeFilesClipboard(
        offer={"kind": "paths", "paths": list(ORDERED_PATHS)},
    )
    clipboard.set_files_clipboard_reader(fake.reader)
    assert clipboard.paste_files() == ORDERED_PATHS


def test_remote_only_uri_list_is_ordinary_absence(
    restore_files_clipboard_reader,
):
    fake = FakeFilesClipboard(
        offer={
            "kind": "uri-list",
            "uri_list": ("https://example.com/a.png\nhttp://example.com/b.txt\n"),
        }
    )
    clipboard.set_files_clipboard_reader(fake.reader)
    assert clipboard.paste_files() is None


def test_mixed_uri_list_keeps_local_skips_remote_without_fetch(
    restore_files_clipboard_reader, monkeypatch
):
    offer = {
        "kind": "uri-list",
        "uri_list": (
            "https://example.com/remote.bin\nfile:///tmp/photos/a%20file.png\n"
        ),
    }
    fake = FakeFilesClipboard(offer=offer)
    clipboard.set_files_clipboard_reader(fake.reader)
    hits = install_path_side_effect_spies(monkeypatch, [SPACED_PATH])

    assert clipboard.paste_files() == [SPACED_PATH]
    assert hits == []


# --- Example 3: path-looking text / empty / image-only / HTML-only → None ---


@pytest.mark.parametrize(
    "offer",
    [
        None,
        {"kind": "empty"},
        {"kind": "text", "text": "/tmp/a file.png\n/tmp/unicodé report.txt"},
        "/tmp/a file.png\n/tmp/unicodé report.txt",
        "file:///tmp/photos/a%20file.png\nfile:///tmp/docs/x.txt\n",
        {"kind": "text/plain", "text": SPACED_PATH},
        {"kind": "image", "label": "raster"},
        {"kind": "html", "html": "<b>hi</b>"},
        {"kind": "text/html", "html": "<a href='/tmp/x'>x</a>"},
        [],
    ],
    ids=[
        "empty-none",
        "empty-kind",
        "path-looking-text-structured",
        "path-looking-bare-string",
        "uri-looking-bare-string-not-file-list",
        "text-plain-kind",
        "image-only",
        "html-only",
        "text-html-kind",
        "empty-path-list",
    ],
)
def test_absence_kinds_return_none(offer, restore_files_clipboard_reader):
    fake = FakeFilesClipboard(offer=offer)
    clipboard.set_files_clipboard_reader(fake.reader)
    before = copy.deepcopy(fake.offer)

    assert clipboard.paste_files() is None
    assert fake.offer == before
    assert fake.cut_reissues == []

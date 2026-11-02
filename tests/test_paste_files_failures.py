"""In-memory paste_files Behavior: cut-ignore, failures, and non-mutation.

Observes plan slice 2 / key examples 4–6 and 8 without a real clipboard.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from paste_files_offer import (
    ORDERED_PATHS,
    SPACED_PATH,
    URI_LIST_TWO_LOCAL,
    FakeFilesClipboard,
    install_path_side_effect_spies,
)

import clipboard

# --- Example 4: cut/move marker beside refs ---


@pytest.mark.parametrize(
    "cut_fields",
    [
        {"cut_marker": "cut"},
        {"PreferredDropEffect": "MOVE"},
        {"x-special/gnome-copied-files": "cut"},
        {"application/x-kde-cutselection": "1"},
        {
            "cut_marker": "cut",
            "PreferredDropEffect": 2,
            "x-special/gnome-copied-files": "cut\nfile:///tmp/x",
        },
    ],
    ids=[
        "generic-cut-marker",
        "PreferredDropEffect",
        "gnome-copied-files",
        "kde-cutselection",
        "combined-markers",
    ],
)
def test_cut_marker_ignored_still_returns_paths(
    cut_fields, restore_files_clipboard_reader, monkeypatch
):
    offer = {
        "kind": "uri-list",
        "uri_list": URI_LIST_TWO_LOCAL,
        **cut_fields,
    }
    fake = FakeFilesClipboard(offer=offer)
    clipboard.set_files_clipboard_reader(fake.reader)
    hits = install_path_side_effect_spies(monkeypatch, ORDERED_PATHS)
    before = copy.deepcopy(fake.offer)

    result = clipboard.paste_files()

    assert result == ORDERED_PATHS
    assert fake.offer == before
    assert fake.cut_reissues == []
    assert fake.writes == []
    assert fake.side_effects == []
    assert hits == []
    # paste_files must never invoke a cut-reissue hook on the fake model.
    clipboard.paste_files()
    assert fake.cut_reissues == []
    assert fake.offer == before


def test_cut_marker_with_path_list_offer(restore_files_clipboard_reader, monkeypatch):
    offer = {
        "kind": "paths",
        "paths": list(ORDERED_PATHS),
        "PreferredDropEffect": "MOVE",
    }
    fake = FakeFilesClipboard(offer=offer)
    clipboard.set_files_clipboard_reader(fake.reader)
    hits = install_path_side_effect_spies(monkeypatch, ORDERED_PATHS)
    before = copy.deepcopy(fake.offer)

    assert clipboard.paste_files() == ORDERED_PATHS
    assert fake.offer == before
    assert hits == []
    assert fake.cut_reissues == []


# --- Example 5: corrupt metadata → ClipboardContentError ---


@pytest.mark.parametrize(
    "offer",
    [
        {"kind": "corrupt", "message": "inconsistent file-list metadata"},
        {"kind": "uri-list", "uri_list": "file:///\x00bad"},
        {"kind": "uri-list", "uri_list": "file://\n"},
        {"kind": "uri-list", "uri_list": 12345},
        {"kind": "paths", "paths": [SPACED_PATH, 12]},
        {"kind": "paths", "paths": "not-a-list"},
        {"kind": "paths", "paths": [SPACED_PATH + "\x00"]},
        {"kind": "mystery-format", "data": "???"},
        object(),
    ],
    ids=[
        "explicit-corrupt-kind",
        "uri-null-byte",
        "uri-empty-path",
        "uri-list-wrong-type",
        "path-list-non-str",
        "path-list-wrong-type",
        "path-null-byte",
        "unrecognized-kind",
        "unrecognized-offer-type",
    ],
)
def test_corrupt_metadata_raises_content_error_not_none_or_paths(
    offer, restore_files_clipboard_reader
):
    fake = FakeFilesClipboard(offer=offer)
    clipboard.set_files_clipboard_reader(fake.reader)
    before = copy.deepcopy(offer) if isinstance(offer, (dict, list)) else offer

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.paste_files()

    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    if isinstance(offer, (dict, list)):
        assert fake.offer == before
    else:
        assert fake.offer is before
    assert fake.cut_reissues == []


# --- Example 6: access / helper failure from fake ---


@pytest.mark.parametrize(
    "failure",
    [
        PermissionError("pasteboard access denied"),
        OSError("wl-paste: text/uri-list helper missing"),
        FileNotFoundError("xclip not found"),
        clipboard.ClipboardContentError("clipboard file-list helper unavailable"),
    ],
    ids=["access-denied", "helper-oserror", "missing-helper", "content-error"],
)
def test_access_and_helper_failures_are_not_absence(
    failure, restore_files_clipboard_reader
):
    fake = FakeFilesClipboard()

    def boom() -> Any:
        fake.reader_calls += 1
        raise failure

    clipboard.set_files_clipboard_reader(boom)
    before_offer = fake.offer

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.paste_files()

    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    assert fake.offer is before_offer
    if not isinstance(failure, clipboard.ClipboardContentError):
        assert "file-list read failed" in str(raised.value).lower()


# --- Non-mutation (examples 1/4/5 shared) ---


def test_read_does_not_mutate_uri_list_offer(
    restore_files_clipboard_reader,
):
    offer = {
        "kind": "uri-list",
        "uri_list": URI_LIST_TWO_LOCAL,
        "PreferredDropEffect": "MOVE",
    }
    fake = FakeFilesClipboard(offer=offer)
    clipboard.set_files_clipboard_reader(fake.reader)
    before = copy.deepcopy(offer)

    first = clipboard.paste_files()
    second = clipboard.paste_files()

    assert first == ORDERED_PATHS
    assert second == ORDERED_PATHS
    assert fake.offer == before
    assert fake.reader_calls == 2
    assert fake.writes == []

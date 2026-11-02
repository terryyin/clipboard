# Source review: SEED-001#read-files

## Launch and input

- Reviewer: fresh general-purpose agent (no conversation inheritance), Cursor Task
- Agent ID: 78308c9b-fd92-49d9-b7c2-f55126331080
- Input: story Goal, Scope (required behavior, supported desktops, required restrictions, scope limits/deferred, rejection constraints), and Key examples 1–8 from `.planning/seeds/SEED-001-clipboard-true-to-its-name.md#read-files` only
- Constraints: use only those inputs; read no other project files; change nothing; return numbered commitments, qualifications, journey examples, and exclusions

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Python desktop tools and automation developers can recover an ordered list of local file references from an independent file manager's clipboard offer through `clipboard`, instead of asking users to transcribe paths or parsing plain text that happens to look like paths. | slice 7 |  |
| 2 | When a native file-list representation offers local files, the call returns those local paths in offer order. | slice 2 | observed: clipboard/_files.py _normalize_files_offer/_paths_from_*; tests/test_paste_files_contract.py::test_ordered_two_file_path_list_unicode_and_spaces |
| 3 | When no local file-list is offered, the call reports ordinary files absence. | slice 2 | observed: clipboard/_files.py absence kinds → None; tests/test_paste_files_contract.py::test_absence_kinds_return_none |
| 4 | Corrupt native file-list metadata or transfer/access failure reports an actionable error. | slice 2 | observed: tests/test_paste_files_failures.py::test_corrupt_metadata_raises_content_error_not_none_or_paths |
| 5 | The read never opens those files. | slice 2 | observed: clipboard/_files.py decode only (no open); tests assert paths without filesystem open |
| 6 | The read never copies those files. | slice 2 | observed: clipboard/_files.py no copy of referenced files; contract suite |
| 7 | The read never moves those files. | slice 2 | observed: tests/test_paste_files_failures.py cut ignore without move |
| 8 | The read never deletes those files. | slice 2 | observed: tests/test_paste_files_failures.py cut ignore without delete |
| 9 | The read never mutates the clipboard. | slice 2 | observed: tests/test_paste_files_failures.py::test_read_does_not_mutate_uri_list_offer |
| 10 | The read never treats a cut/move marker as authority to move or as a move offer to reissue. | slice 2 | observed: tests/test_paste_files_failures.py cut fields ignored; no cut reissue |
| 11 | Add an explicit public read API (proposed spelling `paste_files()`). | slice 1 | observed: clipboard/_files.py paste_files; tests/test_paste_files_seam.py::test_paste_files_public_surface |
| 12 | That API returns an ordered `list[str]` of local filesystem paths when the current clipboard offer includes a native file-list representation that yields at least one local reference. | slice 2 | observed: test_ordered_two_file_path_list_unicode_and_spaces; test_uri_list_file_uris_decode_to_local_paths |
| 13 | That API returns ordinary absence (`None`) when no local file-list is offered. | slice 2 | observed: test_absence_kinds_return_none |
| 14 | Ordinary absence includes empty clipboard. | slice 2 | observed: test_absence_kinds_return_none empty |
| 15 | Ordinary absence includes text-only offers. | slice 2 | observed: test_absence_kinds_return_none text |
| 16 | Ordinary absence includes image-only offers. | slice 2 | observed: test_absence_kinds_return_none image |
| 17 | Ordinary absence includes HTML-only offers. | slice 2 | observed: test_absence_kinds_return_none html |
| 18 | Ordinary absence includes file-list payloads that contain only non-local / remote URIs. | slice 2 | observed: test_remote_only_uri_list_is_ordinary_absence |
| 19 | Failures other than ordinary absence raise `ClipboardContentError` rather than returning `None` or fabricated paths. | slice 2 | observed: tests/test_paste_files_failures.py corrupt + access/helper failures |
| 20 | Those non-absence failures include denied/unavailable access. | slice 2 | observed: tests/test_paste_files_failures.py::test_access_and_helper_failures_are_not_absence |
| 21 | Those non-absence failures include a missing Linux helper required to read the file-list target. | slice 2 | observed: tests/test_paste_files_failures.py::test_access_and_helper_failures_are_not_absence |
| 22 | Those non-absence failures include transfer failure. | slice 2 | observed: tests/test_paste_files_failures.py::test_access_and_helper_failures_are_not_absence |
| 23 | Those non-absence failures include malformed native file-list metadata that cannot yield trustworthy local references. | slice 2 | observed: tests/test_paste_files_failures.py::test_corrupt_metadata_raises_content_error_not_none_or_paths |
| 24 | The read leaves the clipboard unchanged. | slice 2 | observed: tests/test_paste_files_failures.py::test_read_does_not_mutate_uri_list_offer |
| 25 | The read performs no filesystem open on the referenced paths. | slice 2 | observed: clipboard/_files.py path decode only; no Path.open |
| 26 | The read performs no filesystem copy on the referenced paths. | slice 2 | observed: clipboard/_files.py no filesystem copy |
| 27 | The read performs no filesystem move on the referenced paths. | slice 2 | observed: clipboard/_files.py no filesystem move |
| 28 | The read performs no filesystem delete on the referenced paths. | slice 2 | observed: clipboard/_files.py no filesystem delete |
| 29 | The read performs no existence check on the referenced paths. | slice 2 | observed: clipboard/_files.py no existence check |
| 30 | Normalize platform payloads to local path strings. | slice 2 | observed: clipboard/_files.py _local_path_from_file_uri / _paths_from_path_list |
| 31 | Normalization includes decoding `file://` URIs including percent-encoding and Unicode / spaces. | slice 2 | observed: test_uri_list_file_uris_decode_to_local_paths (percent-encoding Unicode spaces) |
| 32 | Normalization includes reading Windows `CF_HDROP` path lists. | slice 6 |  |
| 33 | Normalization includes reading macOS file-URL / filename pasteboard types. | slice 3 |  |
| 34 | Preserve offer order. | slice 2 | observed: test_ordered_two_file_path_list_unicode_and_spaces; uri-list line order preserved |
| 35 | If a cut/move marker is present beside the references, ignore it for all library behavior. | slice 2 | observed: tests/test_paste_files_failures.py::test_cut_marker_ignored_still_returns_paths; cut fields present but unused in clipboard/_files.py normalize |
| 36 | Cut/move markers in scope include `PreferredDropEffect`. | slice 2 | observed: tests/test_paste_files_failures.py PreferredDropEffect cut field ignored via omission in normalize |
| 37 | Cut/move markers in scope include `x-special/gnome-copied-files` “cut”. | slice 2 | observed: tests/test_paste_files_failures.py gnome-copied-files cut field ignored via omission |
| 38 | Cut/move markers in scope include `application/x-kde-cutselection`. | slice 2 | observed: tests/test_paste_files_failures.py kde-cutselection cut field ignored via omission |
| 39 | Cut/move markers in scope include equivalent markers. | slice 2 | observed: tests/test_paste_files_failures.py cut_marker equivalent field ignored via omission |
| 40 | When references are offered with such a marker, still return the local path list. | slice 2 | observed: tests/test_paste_files_failures.py::test_cut_marker_ignored_still_returns_paths |
| 41 | Do not move or delete anything because of such a marker. | slice 2 | observed: tests/test_paste_files_failures.py::test_cut_marker_ignored_still_returns_paths |
| 42 | Do not write or reissue cut/move semantics because of such a marker. | slice 2 | observed: clipboard/_files.py never writes cut; test_cut_marker_* |
| 43 | Never interpret ordinary `paste()` plain text as a file-list success. | slice 2 | observed: clipboard/_files.py bare str → None; test_absence_kinds_return_none path-looking text |
| 44 | Never interpret newline-separated path-looking text as a file-list success. | slice 2 | observed: clipboard/_files.py bare str → None; never parses newline path text as success |
| 45 | Default automated tests stay desktop-free via an injectable read backend. | slice 1 | observed: clipboard/_files.py set_files_clipboard_reader; tests/test_paste_files_seam.py inject/absence/reset cases |
| 46 | Native proof uses an independent file manager. | slice 3 |  |
| 47 | Native proof is not a same-library `copy_files` round-trip alone. | slice 3 |  |
| 48 | Native proof stays explicitly gated. | slice 3 |  |
| 49 | Document Linux helper dependencies for file-list reads (`xclip` / `wl-paste` requesting `text/uri-list` or equivalent). | slice 7 |  |
| 50 | Document supported desktop setup. | slice 7 |  |
| 51 | No `clipboard[images]` requirement for this story. | slice 1 | observed: tests/test_paste_files_seam.py::test_paste_files_importable_without_images_extra |
| 52 | Supported desktop: Windows desktop with Explorer (or equivalent) producing `CF_HDROP`. | slice 6 |  |
| 53 | Supported desktop: macOS Aqua with Finder (or equivalent) producing file-URL / filename pasteboard types. | slice 3 |  |
| 54 | Supported desktop: Linux X11 + helper able to request `text/uri-list` on CLIPBOARD from a named file manager. | slice 4 |  |
| 55 | Supported desktop: Linux Wayland + helper able to request `text/uri-list` (or equivalent) from a named file manager, scoped to the compositor actually proved when one is available. | slice 5 |  |
| 56 | Independent-producer success is an acceptance requirement on each claimed desktop when a session is available. | slice 7 |  |
| 57 | When no usable session exists during execution, record an explicit unverified/unsupported evidence limit for that desktop rather than claiming verified. | slice 7 |  |
| 58 | Never silent success for an unproved desktop. | slice 7 |  |
| 59 | Do not generalize one Wayland compositor’s result to all environments. | slice 5 |  |
| 60 | Do not generalize one Linux file manager’s result to all environments. | slice 4 |  |
| 61 | Do not overload `paste()` to return or accept file lists. | slice 1 | observed: clipboard/__init__.py re-exports pyperclip paste separately from paste_files |
| 62 | Do not overload `copy()` to return or accept file lists. | slice 1 | observed: clipboard/__init__.py re-exports pyperclip copy separately from paste_files |
| 63 | Do not treat ordinary text offers as file-list success. | slice 2 | observed: test_absence_kinds_return_none text |
| 64 | Do not treat HTML offers as file-list success. | slice 2 | observed: test_absence_kinds_return_none html |
| 65 | Do not treat image-only offers as file-list success. | slice 2 | observed: test_absence_kinds_return_none image |
| 66 | Do not bypass OS pasteboard / clipboard authorization. | slice 3 |  |
| 67 | Do not replace clipboard contents as part of the read. | slice 2 | observed: tests/test_paste_files_failures.py::test_read_does_not_mutate_uri_list_offer |
| 68 | Do not clear clipboard contents as part of the read. | slice 2 | observed: tests/test_paste_files_failures.py::test_read_does_not_mutate_uri_list_offer |
| 69 | Do not rewrite clipboard contents as part of the read. | slice 2 | observed: tests/test_paste_files_failures.py::test_read_does_not_mutate_uri_list_offer |
| 70 | Do not open referenced files as part of the read. | slice 2 | observed: clipboard/_files.py no open of referenced paths |
| 71 | Do not hash referenced files as part of the read. | slice 2 | observed: clipboard/_files.py no hash of referenced paths |
| 72 | Do not copy referenced files as part of the read. | slice 2 | observed: clipboard/_files.py no copy of referenced paths |
| 73 | Do not move referenced files as part of the read. | slice 2 | observed: clipboard/_files.py no move of referenced paths |
| 74 | Do not delete referenced files as part of the read. | slice 2 | observed: clipboard/_files.py no delete of referenced paths |
| 75 | Do not promise that returned paths still exist. | slice 7 |  |
| 76 | Do not promise that returned paths are readable. | slice 7 |  |
| 77 | Do not fetch remote / non-`file` URIs. | slice 2 | observed: test_remote_only_uri_list_is_ordinary_absence; test_mixed_uri_list_keeps_local_skips_remote_without_fetch |
| 78 | Do not hang the caller indefinitely waiting on a contended clipboard. | slice 3 |  |
| 79 | Do not silently reissue a cut/move marker as a move offer. | slice 2 | observed: tests/test_paste_files_failures.py no cut reissue |
| 80 | Corrupt or unparseable native file-list metadata must not yield fabricated successful paths. | slice 2 | observed: tests/test_paste_files_failures.py::test_corrupt_metadata_raises_content_error_not_none_or_paths |
| 81 | Plain text that resembles paths must not be treated as a file-list success. | slice 2 | observed: test_absence_kinds_return_none path-looking plain text |
| 82 | A successful read must not mutate the clipboard. | slice 2 | observed: tests/test_paste_files_failures.py::test_read_does_not_mutate_uri_list_offer |
| 83 | A successful read must not perform filesystem side effects on the referenced paths. | slice 2 | observed: contract suite; decode-only _files.py |
| 84 | A cut marker must not cause library-side move/delete. | slice 2 | observed: tests/test_paste_files_failures.py cut ignore no move/delete |
| 85 | A cut marker must not be reissued as move. | slice 2 | observed: tests/test_paste_files_failures.py cut ignore no reissue |
| 86 | Silent success on an unproved desktop is forbidden. | slice 7 |  |
| 87 | The public API spelling is proposed as `paste_files()` (not locked as the only possible name by the story’s own wording). | slice 1 | observed: clipboard/_files.py and __init__ paste_files public name |
| 88 | Ordinary absence is reported as `None`. | slice 2 | observed: test_absence_kinds_return_none returns None |
| 89 | Non-absence failures raise `ClipboardContentError` with actionable messaging (where failure messaging is stated). | slice 2 | observed: tests/test_paste_files_failures.py actionable ClipboardContentError on corrupt/access |
| 90 | Cut/move markers are ignored for library behavior; they are not treated as structured success metadata in this story. | slice 2 | observed: tests/test_paste_files_failures.py cut not structured success metadata |
| 91 | Linux Wayland support is scoped to the compositor actually proved when one is available. | slice 5 |  |
| 92 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. |  | X92 |
| 93 | Evidence for a desktop without a usable session during execution is an explicit unverified/unsupported limit, not a verified claim. | slice 7 |  |
| 94 | Default automated tests remain desktop-free; native proof is gated and uses an independent file manager. | slice 7 |  |
| 95 | This story does not require `clipboard[images]`. | slice 1 | observed: tests/test_paste_files_seam.py::test_paste_files_importable_without_images_extra |
| 96 | Independent file manager (Explorer / Finder / named Linux FM) copies two existing local files, including a Unicode name and spaces → `paste_files()` returns an ordered `list[str]` of the corresponding local paths; a later independent consumer can still obtain the same offer; no file was opened or modified by the read. | slice 3 |  |
| 97 | Same pattern where the native offer is Linux `text/uri-list` of `file://` URIs (percent-encoded spaces / Unicode) or Windows `CF_HDROP` → returned strings are decoded local filesystem paths, not raw URI text and not `paste()` plain text alone. | slice 2 | observed: test_uri_list_file_uris_decode_to_local_paths; test_structured_paths_offer_decodes_like_path_list |
| 98 | Clipboard holds only plain text that looks like paths (or is empty / image-only / HTML-only) → `paste_files()` returns `None` (ordinary files absence); `paste()` / other readers behave as before for their kinds. | slice 2 | observed: test_absence_kinds_return_none |
| 99 | Offer includes a cut/move marker beside local file references → `paste_files()` still returns the local path list; the library does not move, delete, or rewrite the offer as a cut/move. | slice 2 | observed: tests/test_paste_files_failures.py::test_cut_marker_ignored_still_returns_paths |
| 100 | Native file-list metadata is present but corrupt or inconsistent → `ClipboardContentError`; no fabricated paths; clipboard contents remain unchanged. | slice 2 | observed: tests/test_paste_files_failures.py::test_corrupt_metadata_raises_content_error_not_none_or_paths |
| 101 | Missing Linux file-list helper or denied/unavailable clipboard access → `ClipboardContentError` with an actionable message; not silent `None` success. | slice 2 | observed: tests/test_paste_files_failures.py::test_access_and_helper_failures_are_not_absence |
| 102 | Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available → independent file-manager success with floors recorded for the named compositor/helper/file manager; if a session is unavailable during execution, that desktop keeps an explicit evidence limit instead of a verified claim. | slice 7 |  |
| 103 | After this work, in-memory `copy` / `paste` / `paste_image` / `copy_html` / (when present) `paste_html` / `inspect` contract tests still pass; `VERSION` and text-only callers behave as before; `paste_files` does not require `clipboard[images]`. | slice 2 | observed: tests/test_paste_files_failures.py::test_paste_files_contract_without_images_extra + broader in-memory suites |
| 104 | Public exposure of cut vs copy intent / PreferredDropEffect / GNOME–KDE cut verbs as structured return metadata (parse/ignore markers only as needed for the non-move safety rule). |  | X104 |
| 105 | Returning `pathlib.Path` objects or richer reference types. |  | X105 |
| 106 | Remote / non-local URI references. |  | X106 |
| 107 | Virtual or promised files. |  | X107 |
| 108 | Directory-expansion semantics beyond what the native offer already lists. |  | X108 |
| 109 | Outbound file-list write (`SEED-001#copy-files`). |  | X109 |
| 110 | Format inspection (`SEED-001#inspect-formats`). |  | X110 |
| 111 | Bundling GUI toolkits or `win32clipboard` as a required public dependency. |  | X111 |
| 112 | Making default pytest / CI require a real desktop. |  | X112 |
| 113 | Expanding beyond the four-desktop set. |  | X113 |
| 114 | Same-library `copy_files` round-trip as sole native proof. |  | X114 |

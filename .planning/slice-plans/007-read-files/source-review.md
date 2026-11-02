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
| 2 | When a native file-list representation offers local files, the call returns those local paths in offer order. | slice 2 |  |
| 3 | When no local file-list is offered, the call reports ordinary files absence. | slice 2 |  |
| 4 | Corrupt native file-list metadata or transfer/access failure reports an actionable error. | slice 2 |  |
| 5 | The read never opens those files. | slice 2 |  |
| 6 | The read never copies those files. | slice 2 |  |
| 7 | The read never moves those files. | slice 2 |  |
| 8 | The read never deletes those files. | slice 2 |  |
| 9 | The read never mutates the clipboard. | slice 2 |  |
| 10 | The read never treats a cut/move marker as authority to move or as a move offer to reissue. | slice 2 |  |
| 11 | Add an explicit public read API (proposed spelling `paste_files()`). | slice 1 | observed: clipboard/_files.py paste_files; tests/test_paste_files_seam.py::test_paste_files_public_surface |
| 12 | That API returns an ordered `list[str]` of local filesystem paths when the current clipboard offer includes a native file-list representation that yields at least one local reference. | slice 2 |  |
| 13 | That API returns ordinary absence (`None`) when no local file-list is offered. | slice 2 |  |
| 14 | Ordinary absence includes empty clipboard. | slice 2 |  |
| 15 | Ordinary absence includes text-only offers. | slice 2 |  |
| 16 | Ordinary absence includes image-only offers. | slice 2 |  |
| 17 | Ordinary absence includes HTML-only offers. | slice 2 |  |
| 18 | Ordinary absence includes file-list payloads that contain only non-local / remote URIs. | slice 2 |  |
| 19 | Failures other than ordinary absence raise `ClipboardContentError` rather than returning `None` or fabricated paths. | slice 2 |  |
| 20 | Those non-absence failures include denied/unavailable access. | slice 2 |  |
| 21 | Those non-absence failures include a missing Linux helper required to read the file-list target. | slice 2 |  |
| 22 | Those non-absence failures include transfer failure. | slice 2 |  |
| 23 | Those non-absence failures include malformed native file-list metadata that cannot yield trustworthy local references. | slice 2 |  |
| 24 | The read leaves the clipboard unchanged. | slice 2 |  |
| 25 | The read performs no filesystem open on the referenced paths. | slice 2 |  |
| 26 | The read performs no filesystem copy on the referenced paths. | slice 2 |  |
| 27 | The read performs no filesystem move on the referenced paths. | slice 2 |  |
| 28 | The read performs no filesystem delete on the referenced paths. | slice 2 |  |
| 29 | The read performs no existence check on the referenced paths. | slice 2 |  |
| 30 | Normalize platform payloads to local path strings. | slice 2 |  |
| 31 | Normalization includes decoding `file://` URIs including percent-encoding and Unicode / spaces. | slice 2 |  |
| 32 | Normalization includes reading Windows `CF_HDROP` path lists. | slice 6 |  |
| 33 | Normalization includes reading macOS file-URL / filename pasteboard types. | slice 3 |  |
| 34 | Preserve offer order. | slice 2 |  |
| 35 | If a cut/move marker is present beside the references, ignore it for all library behavior. | slice 2 |  |
| 36 | Cut/move markers in scope include `PreferredDropEffect`. | slice 2 |  |
| 37 | Cut/move markers in scope include `x-special/gnome-copied-files` “cut”. | slice 2 |  |
| 38 | Cut/move markers in scope include `application/x-kde-cutselection`. | slice 2 |  |
| 39 | Cut/move markers in scope include equivalent markers. | slice 2 |  |
| 40 | When references are offered with such a marker, still return the local path list. | slice 2 |  |
| 41 | Do not move or delete anything because of such a marker. | slice 2 |  |
| 42 | Do not write or reissue cut/move semantics because of such a marker. | slice 2 |  |
| 43 | Never interpret ordinary `paste()` plain text as a file-list success. | slice 2 |  |
| 44 | Never interpret newline-separated path-looking text as a file-list success. | slice 2 |  |
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
| 63 | Do not treat ordinary text offers as file-list success. | slice 2 |  |
| 64 | Do not treat HTML offers as file-list success. | slice 2 |  |
| 65 | Do not treat image-only offers as file-list success. | slice 2 |  |
| 66 | Do not bypass OS pasteboard / clipboard authorization. | slice 3 |  |
| 67 | Do not replace clipboard contents as part of the read. | slice 2 |  |
| 68 | Do not clear clipboard contents as part of the read. | slice 2 |  |
| 69 | Do not rewrite clipboard contents as part of the read. | slice 2 |  |
| 70 | Do not open referenced files as part of the read. | slice 2 |  |
| 71 | Do not hash referenced files as part of the read. | slice 2 |  |
| 72 | Do not copy referenced files as part of the read. | slice 2 |  |
| 73 | Do not move referenced files as part of the read. | slice 2 |  |
| 74 | Do not delete referenced files as part of the read. | slice 2 |  |
| 75 | Do not promise that returned paths still exist. | slice 7 |  |
| 76 | Do not promise that returned paths are readable. | slice 7 |  |
| 77 | Do not fetch remote / non-`file` URIs. | slice 2 |  |
| 78 | Do not hang the caller indefinitely waiting on a contended clipboard. | slice 3 |  |
| 79 | Do not silently reissue a cut/move marker as a move offer. | slice 2 |  |
| 80 | Corrupt or unparseable native file-list metadata must not yield fabricated successful paths. | slice 2 |  |
| 81 | Plain text that resembles paths must not be treated as a file-list success. | slice 2 |  |
| 82 | A successful read must not mutate the clipboard. | slice 2 |  |
| 83 | A successful read must not perform filesystem side effects on the referenced paths. | slice 2 |  |
| 84 | A cut marker must not cause library-side move/delete. | slice 2 |  |
| 85 | A cut marker must not be reissued as move. | slice 2 |  |
| 86 | Silent success on an unproved desktop is forbidden. | slice 7 |  |
| 87 | The public API spelling is proposed as `paste_files()` (not locked as the only possible name by the story’s own wording). | slice 1 | observed: clipboard/_files.py and __init__ paste_files public name |
| 88 | Ordinary absence is reported as `None`. | slice 2 |  |
| 89 | Non-absence failures raise `ClipboardContentError` with actionable messaging (where failure messaging is stated). | slice 2 |  |
| 90 | Cut/move markers are ignored for library behavior; they are not treated as structured success metadata in this story. | slice 2 |  |
| 91 | Linux Wayland support is scoped to the compositor actually proved when one is available. | slice 5 |  |
| 92 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. |  | X92 |
| 93 | Evidence for a desktop without a usable session during execution is an explicit unverified/unsupported limit, not a verified claim. | slice 7 |  |
| 94 | Default automated tests remain desktop-free; native proof is gated and uses an independent file manager. | slice 7 |  |
| 95 | This story does not require `clipboard[images]`. | slice 1 | observed: tests/test_paste_files_seam.py::test_paste_files_importable_without_images_extra |
| 96 | Independent file manager (Explorer / Finder / named Linux FM) copies two existing local files, including a Unicode name and spaces → `paste_files()` returns an ordered `list[str]` of the corresponding local paths; a later independent consumer can still obtain the same offer; no file was opened or modified by the read. | slice 3 |  |
| 97 | Same pattern where the native offer is Linux `text/uri-list` of `file://` URIs (percent-encoded spaces / Unicode) or Windows `CF_HDROP` → returned strings are decoded local filesystem paths, not raw URI text and not `paste()` plain text alone. | slice 2 |  |
| 98 | Clipboard holds only plain text that looks like paths (or is empty / image-only / HTML-only) → `paste_files()` returns `None` (ordinary files absence); `paste()` / other readers behave as before for their kinds. | slice 2 |  |
| 99 | Offer includes a cut/move marker beside local file references → `paste_files()` still returns the local path list; the library does not move, delete, or rewrite the offer as a cut/move. | slice 2 |  |
| 100 | Native file-list metadata is present but corrupt or inconsistent → `ClipboardContentError`; no fabricated paths; clipboard contents remain unchanged. | slice 2 |  |
| 101 | Missing Linux file-list helper or denied/unavailable clipboard access → `ClipboardContentError` with an actionable message; not silent `None` success. | slice 2 |  |
| 102 | Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available → independent file-manager success with floors recorded for the named compositor/helper/file manager; if a session is unavailable during execution, that desktop keeps an explicit evidence limit instead of a verified claim. | slice 7 |  |
| 103 | After this work, in-memory `copy` / `paste` / `paste_image` / `copy_html` / (when present) `paste_html` / `inspect` contract tests still pass; `VERSION` and text-only callers behave as before; `paste_files` does not require `clipboard[images]`. | slice 2 |  |
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

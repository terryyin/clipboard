# Source review: SEED-001#copy-files

Launch: fresh general-purpose reviewer, no conversation inheritance, 2026-11-02, during execution of slice 1.
Input: only the story's Goal, Scope and Key examples (and the start of Considered alternatives) copied verbatim from `.planning/seeds/SEED-001-clipboard-true-to-its-name.md` section `copy-files`, with no plan, product, proof or human amendment. Instruction: read only that input, change nothing, return numbered commitments, qualifications, examples and exclusions. Reviewer note: examples are illustrations, not rejection rules; 7.6 is conditional.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| G.1 | Python tool and automation developers can hand existing local output files to a desktop file manager through its ordinary copy/paste workflow | slice 7 | |
| G.2 | The user pastes copies wherever they choose, without the tool printing paths or the user handling paths manually | slice 7 | |
| G.3 | `clipboard` is extended from reading file lists (`paste_files`) to offering them | slice 1 | observed: clipboard/_files.py copy_files; tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates |
| G.4 | The capability is tested against file managers, not against the library's own reader | slice 7 | |
| 1 | A new public function `copy_files(paths)` is provided | slice 1 | observed: tests/test_copy_files_contract.py::test_copy_files_public_surface |
| 1.1 | `copy_files` does not require the `clipboard[images]` extra | slice 1 | observed: tests/test_copy_files_contract.py::test_copy_files_works_without_images_extra |
| 2 | `copy_files` accepts an ordered, non-empty iterable of local paths | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates, ::test_generator_input_is_accepted |
| 2.1 | Path items may be `str` | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (relative str) |
| 2.2 | Path items may be `os.PathLike` | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (pathlib.Path) |
| 3 | `copy_files` replaces the current clipboard with one native file-list offer | slice 7 | |
| 3.1 | The offer is marked as copy, not cut | slice 7 | |
| 4 | Relative paths are made absolute against the current directory at call time | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (relative -> cwd-absolute) |
| 4.1 | Symlinks are not resolved | slice 1 | observed: tests/test_copy_files_contract.py::test_symlink_is_kept_not_resolved |
| 4.2 | Path order passes through unchanged | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (order asserted) |
| 4.3 | Duplicate paths pass through (not removed) | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (duplicate kept) |
| 5 | Each named path must exist when `copy_files` is called | slice 1 | observed: tests/test_copy_files_contract.py::test_missing_path_is_named_and_writer_never_called |
| 5.1 | Files are offered | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (file reaches writer) |
| 5.2 | Directories are offered | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (directory reaches writer) |
| 6 | The offer stays pasteable after the writing Python process exits | slice 7 | |
| 7.1 | macOS Aqua native offer: `NSPasteboard` file URLs | slice 3 | |
| 7.2 | Windows native offer: `CF_HDROP` | slice 4 | |
| 7.3 | Windows native offer: `Preferred DropEffect` = copy | slice 4 | |
| 7.4 | Linux X11 native offer: `text/uri-list` | slice 5 | |
| 7.5 | Linux Wayland native offer: `text/uri-list` | slice 6 | |
| 7.6 | Linux X11/Wayland: also the GNOME copied-files convention, where the helper can offer it | slice 6 | |
| 7.7 | The Linux X11/Wayland offer is served by a background owner, as `copy_image` does | slice 6 | |
| 8 | Invalid input raises `ClipboardContentError` naming the problem | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer (message match per case) |
| 8.1 | Invalid input: an empty iterable | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer [], (), iter([]) |
| 8.2 | Invalid input: a bare `str` (which would otherwise iterate characters) | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer bare str |
| 8.3 | Invalid input: a bare `bytes` (which would otherwise iterate characters) | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer bare bytes |
| 8.4 | Invalid input: a non-path item | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer [42], bytes item |
| 8.5 | Invalid input: any path that does not exist | slice 1 | observed: tests/test_copy_files_contract.py::test_missing_path_is_named_and_writer_never_called |
| 8.6 | Invalid-input errors are raised before the current clipboard is replaced (shared fail-before-replace boundary) | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer and ::test_missing_path_leaves_prior_offer_untouched (writer never called) |
| 8.7 | The empty offer is rejected because it would silently clear the clipboard | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer (empty message names clipboard clearing) |
| 8.8 | Clearing the clipboard belongs to SEED-001#clear-clipboard, not this story | slice 1 | observed: clipboard/_files.py _validate_copy_files_paths rejects empty; no clear behavior added |
| 9 | Environment and transfer failures raise `ClipboardContentError` | slice 6 | |
| 9.1 | Failure: missing helper | slice 6 | |
| 9.2 | Failure: unsupported session | slice 6 | |
| 9.3 | Failure: denied access | slice 6 | |
| 9.4 | Failure: transfer failure | slice 6 | |
| 9.5 | Never silent success on such failures | slice 6 | |
| 9.6 | Never a text-only fallback on such failures | slice 6 | |
| 10 | The offer is a reference, not a snapshot | slice 7 | |
| 10.1 | The library does not lock the files | slice 7 | |
| 10.2 | The library does not copy the files | slice 7 | |
| 10.3 | A file manager pasting later copies what exists at paste time | slice 7 | |
| 10.4 | A source removed after `copy_files` returns makes that paste fail or skip, in the file manager's own way | slice 7 | |
| 10.5 | After `copy_files` returns, the library promises nothing more about removed sources and is not involved | slice 7 | |
| 11 | Proof of success: an independent file manager pastes copies into a user-selected destination | slice 7 | |
| 11.1 | Proof: the paste happens after the Python writer exits | slice 7 | |
| 11.2 | Proof: two sources whose names contain Unicode and spaces | slice 7 | |
| 11.3 | Proof: the sources remain unchanged | slice 7 | |
| 11.4 | Proof names the file manager version for each platform | slice 7 | |
| 11.5 | Proof names the OS/compositor version for each platform | slice 7 | |
| 11.6 | Proof names the helper version for each platform | slice 7 | |
| 11.7 | A platform without that observation is recorded as an evidence limit in the README, not a verified claim | slice 7 | |
| 11.8 | Results from one file manager or compositor are not generalized | slice 7 | |
| 11.9 | `paste_files()` returning the same paths is a useful in-memory/native consistency check, not interoperability proof | slice 7 | |
| 12.1 | Deferred, not rejected: a plain-text or name alternative in the same offer | slice 7 | |
| 12.2 | Deferred, not rejected: cut/move semantics | slice 7 | |
| 12.3 | Deferred, not rejected: virtual files | slice 7 | |
| 12.4 | Deferred, not rejected: promised files | slice 7 | |
| 12.5 | Deferred, not rejected: remote URIs | slice 7 | |
| 12.6 | Deferred, not rejected: non-`file:` URIs | slice 7 | |
| 12.7 | Deferred, not rejected: the library itself copying files | slice 7 | |
| 12.8 | Deferred, not rejected: the library itself opening files | slice 7 | |
| 12.9 | Deferred, not rejected: the library itself pasting files | slice 7 | |
| 12.10 | Deferred, not rejected: PRIMARY selection | slice 7 | |
| 12.11 | Deferred, not rejected: WSL as a guaranteed desktop | slice 7 | |
| 12.12 | Deferred, not rejected: SSH as a guaranteed desktop | slice 7 | |
| 12.13 | Deferred, not rejected: containers as guaranteed desktops | slice 7 | |
| 12.14 | Deferred, not rejected: headless CI as a guaranteed desktop | slice 7 | |
| 12.15 | Deferred, not rejected: persistence across logout | slice 7 | |
| 12.16 | Deferred, not rejected: persistence across reboot | slice 7 | |
| E1.a | Setup: `out/report final.pdf` and `out/données é.csv` exist | slice 7 | |
| E1.b | Trigger: `copy_files(["out/report final.pdf", "out/données é.csv"])` | slice 7 | |
| E1.c | Result: the call returns `None` | slice 1 | observed: tests/test_copy_files_contract.py::test_valid_paths_reach_writer_absolute_ordered_with_duplicates (result is None) |
| E1.d | Then the script exits; in the platform's named file manager the user pastes into a chosen folder | slice 7 | |
| E1.e | Result: the user gets copies of both files | slice 7 | |
| E1.f | Result: the originals are unchanged | slice 7 | |
| E2.a | Setup: the clipboard holds text `keep`; `missing.txt` does not exist | slice 1 | observed: tests/test_copy_files_contract.py::test_missing_path_leaves_prior_offer_untouched setup (fake board text keep) |
| E2.b | Trigger: `copy_files(["out/report final.pdf", "missing.txt"])` | slice 1 | observed: tests/test_copy_files_contract.py::test_missing_path_is_named_and_writer_never_called |
| E2.c | Result: raises `ClipboardContentError` naming `missing.txt` | slice 1 | observed: tests/test_copy_files_contract.py::test_missing_path_is_named_and_writer_never_called (names missing.txt) |
| E2.d | Result: `paste()` still returns `keep` | slice 3 | |
| E3.a | Trigger: `copy_files([])` | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer [] |
| E3.b | Trigger: `copy_files("out/report final.pdf")` (bare string) | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer bare str |
| E3.c | Result (for each): raises `ClipboardContentError` | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer |
| E3.d | Result (for each): the previous clipboard is untouched | slice 1 | observed: tests/test_copy_files_contract.py::test_invalid_input_raises_before_writer (writer.calls == []) |
| E4.a | Setup: working directory `/home/u/proj` | slice 1 | observed: tests/test_copy_files_contract.py sources fixture (monkeypatch.chdir tmp cwd) |
| E4.b | Trigger: `copy_files(["out/a.txt"])` | slice 1 | observed: tests/test_copy_files_contract.py::test_round_trip_through_fake_offer_returns_absolute_paths |
| E4.c | Result: `paste_files()` returns `["/home/u/proj/out/a.txt"]` | slice 1 | observed: tests/test_copy_files_contract.py::test_round_trip_through_fake_offer_returns_absolute_paths (paste_files returns cwd-absolute paths) |
| E5.a | Setup: after a successful `copy_files`, the user deletes `out/a.txt` | slice 7 | |
| E5.b | Trigger: the user then pastes in the file manager | slice 7 | |
| E5.c | Result: the file manager reports or skips the missing item | slice 7 | |
| E5.d | Result: nothing is raised in Python | slice 7 | |
| E5.e | Result: no other file is touched | slice 7 | |
| E6.a | Setup: Linux X11 without `xclip` on `PATH` | slice 5 | |
| E6.b | Trigger: `copy_files([...])` | slice 5 | |
| E6.c | Result: raises `ClipboardContentError` with an install hint | slice 5 | |
| E6.d | Result: the previous clipboard is untouched | slice 5 | |
| N.1 | Not scope (rationale): a documented per-platform recipe would leave callers owning formats, copy-versus-cut markers, quoting and lifetime; Windows `Set-Clipboard -Path` treats `[` `]` as wildcards | slice 7 | |

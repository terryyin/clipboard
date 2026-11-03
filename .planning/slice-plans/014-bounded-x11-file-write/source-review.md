# Source review: SEED-001#bounded-x11-file-write

## Launch and input

Fresh general-purpose reviewer (no conversation inheritance). Input was only the
selected story section Goal and Scope from
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#bounded-x11-file-write`
(no Key examples section in that section). Instruction: use only those inputs,
read no other project files, change nothing; return numbered commitments with
qualifications, triggers/journeys, and exclusions.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | On Linux X11, callers of `copy_files(paths)` receive the documented bounded `ClipboardContentError` instead of an indefinite hang (when the X server stalls and the URI list is larger than a pipe buffer) | slice 1 | observed: tests/test_copy_files_x11_writer_stall.py::test_large_uri_list_raises_within_bound_when_owner_never_reads_stdin (ClipboardContentError within shrunk bound; owner killpg) |
| 2 | Every desktop’s native proof covers the directory, duplicate, and relative-path promises that `SEED-001#copy-files` makes | slice 2 |  |
| 3 | Correct `SEED-001#copy-files` so the X11 file-list `xclip` owner is fed without a blocking unbounded pipe write | slice 1 | observed: clipboard/_files_native_x11_writer.py::_start_owner writes body to TemporaryFile stdin (no pipe write) |
| 4a.1 | Keep the background owner | slice 1 | observed: tests/test_copy_files_x11_writer.py::test_body_is_crlf_percent_encoded_file_uris_fed_to_background_xclip |
| 4a.2 | Keep TARGETS plus exact-body read-back | slice 1 | observed: tests/test_copy_files_x11_writer.py::test_returns_only_once_targets_lists_uri_list_with_the_written_body |
| 4a.3 | Keep stderr quoting | slice 1 | observed: tests/test_copy_files_x11_writer.py::test_helper_exit_is_content_error_quoting_stderr |
| 4a.4 | Keep the install hint | slice 1 | observed: tests/test_copy_files_x11_writer.py::test_missing_xclip_has_install_hint_and_launches_nothing |
| 4a.5 | Keep owner cleanup | slice 1 | observed: tests/test_copy_files_x11_writer.py::test_owner_that_never_offers_raises_after_the_bound (_stop_owner/killpg) |
| 5a.1 | Extend the four gated native probes so a directory reaches each native writer and an independent consumer | slice 2 |  |
| 5a.2 | Extend the four gated native probes so a duplicate reaches each native writer and an independent consumer | slice 2 |  |
| 5a.3 | Extend the four gated native probes so a relative path reaches each native writer and an independent consumer | slice 2 |  |

# Source review: SEED-001#bounded-helper-owner-write

Launch: fresh general-purpose reviewer (no conversation inheritance), 2026-11-04, by the execution coordinator.
Input: only the story section `SEED-001#bounded-helper-owner-write` (Goal, Scope, Key examples, Architecture, effort/dependency/safe-stopping lines) copied verbatim from `.planning/seeds/SEED-001-clipboard-true-to-its-name.md` at 1c33eaa, with the story-state JSON removed. No plan, product, proof, or slice scope was supplied; the reviewer read no other file and changed nothing.
Returned commitments are reproduced unchanged below; Slice and Observation columns are the coordinator's allocation.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Goal: Python users calling `copy_image` on a Linux desktop whose display or compositor stalls get a `ClipboardImageError` within one documented bound instead of a hang or a false success, as `copy` and `copy_files` already do. | slice 2 | |
| 2 | Goal: Maintainers keep one rule for handing a background clipboard owner its payload, so the next writer cannot reintroduce the pipe write that hung large text on X11. | slice 2 | |
| 3 | Goal qualification: this finishes the reliability promise of the image and rich-content writes without changing what any write offers. | slice 2 | |
| 4 | Bounded image write on Linux: on Linux X11 and Linux Wayland, each `copy_image` shares one 10 s bound across all of these phases, the same bound `copy` and `copy_files` already use (today Wayland waits up to 30 s and X11 has no bound on the hand-over): | slice 2 | |
| 4.1 | the phase of starting its helper | slice 2 | |
| 4.2 | the phase of handing over the PNG | slice 2 | |
| 4.3 | the phase of confirming the offer | slice 2 | |
| 5 | When the bound passes, `copy_image` raises `ClipboardImageError` that: | slice 2 | |
| 5.1 | names the helper | slice 2 | |
| 5.2 | names the bound | slice 2 | |
| 5.3 | includes the helper's stderr when it wrote any | slice 2 | |
| 6 | When the bound passes, `copy_image` stops the owner it started (its whole session) so no half-started owner lingers. | slice 2 | |
| 7 | The README documents the image bound beside the text bound. | slice 2 | |
| 8 | X11 image write succeeds only when its own owner serves it: `copy_image` on X11 returns only once CLIPBOARD's `image/png` reads back exactly the written PNG bytes, as the text and file-list writers already confirm their own bytes. Reason: waiting only for `image/png` in TARGETS is satisfied by a previous image owner, so a non-reading owner would turn a hang into a silent success (library rule: no silent success on write). | slice 1 | observed: clipboard/_image_write.py _xclip_serves_png exact image/png bytes; tests/test_copy_image_x11_write_stall.py::test_previous_image_owner_does_not_pass_for_the_new_png (fail-first: returned success) |
| 9 | One launcher: every Linux helper-owner clipboard write that hands over a payload starts its helper through one private launcher beside the shared Linux helpers (`clipboard/_desktop`). Listed writers: | slice 2 | |
| 9.1 | X11 `xclip -i` for text | slice 1 | observed: clipboard/_text_native_x11.py _x11_text_clipboard_writer calls _desktop._start_helper_owner; tests/test_text_x11_write_stall.py green |
| 9.2 | X11 `xclip -i` for file list | slice 1 | observed: clipboard/_files_native_x11_writer.py _x11_files_clipboard_writer calls _desktop._start_helper_owner; tests/test_copy_files_x11_writer_stall.py green |
| 9.3 | X11 `xclip -i` for image | slice 1 | observed: clipboard/_image_write.py _write_linux_xclip calls _desktop._start_helper_owner; tests/test_copy_image_x11_write_stall.py |
| 9.4 | Wayland `wl-copy` for text | slice 2 | |
| 9.5 | Wayland `wl-copy` for file list | slice 2 | |
| 9.6 | Wayland `wl-copy` for image | slice 2 | |
| 10 | Launcher hand-over properties: | slice 1 | observed: clipboard/_desktop.py _start_helper_owner; tests/test_helper_owner_launcher.py |
| 10.1 | the payload comes from an unlinked temporary file as `stdin` (never a pipe the caller must drain) | slice 1 | observed: tests/test_helper_owner_launcher.py::test_payload_is_a_file_stdin_in_its_own_session (payload bytes, stdin not PIPE) |
| 10.2 | the helper runs in its own session | slice 1 | observed: tests/test_helper_owner_launcher.py::test_payload_is_a_file_stdin_in_its_own_session (start_new_session) |
| 10.3 | `stdout` is discarded | slice 1 | observed: tests/test_helper_owner_launcher.py::test_payload_is_a_file_stdin_in_its_own_session (stdout DEVNULL) |
| 10.4 | `stderr` goes to the caller's unlinked log | slice 1 | observed: tests/test_helper_owner_launcher.py::test_payload_is_a_file_stdin_in_its_own_session (stderr is caller log) |
| 11 | Each caller keeps its own: | slice 2 | |
| 11.1 | deadline | slice 2 | |
| 11.2 | readiness check | slice 2 | |
| 11.3 | error mapping: `ClipboardContentError` for text and file lists, `ClipboardImageError` for images, with the same install hints | slice 2 | |
| 12 | The Wayland image write gains the detached session and stderr detail the other Wayland writes already have. | slice 2 | |
| 13 | Failures before replacing: each of the following raises the caller's error before any helper starts, so the current clipboard stays as it was: | slice 2 | |
| 13.1 | a missing helper | slice 2 | |
| 13.2 | a temporary file that cannot be written (for example a full temporary directory) | slice 2 | |
| 14 | Preserved unchanged: | slice 2 | |
| 14.1 | session selection | slice 2 | |
| 14.2 | offered formats and types | slice 2 | |
| 14.3 | the writer-exit lifetime | slice 2 | |
| 14.4 | public API | slice 2 | |
| 14.5 | injection seams | slice 2 | |
| 14.6 | existing text and file-list bounds and the meaning of their messages | slice 2 | |
| 14.7 | the existing X11 text and file-list stall tests keep passing through the launcher | slice 1 | observed: tests/test_text_x11_write_stall.py, tests/test_copy_files_x11_writer_stall.py green in make check (killpg fake retargeted to _desktop.os, assertions unchanged) |
| 15 | Proof: desktop-free tests drive a real `sys.executable` owner that never reads its input (the stalled-display stand-in the text/file-list stall tests use) with a PNG above a typical 64 KiB pipe buffer, showing: | slice 2 | |
| 15.1 | X11 `copy_image` raises `ClipboardImageError` within the bound (shortened for the test) and stops the owner's session | slice 1 | observed: tests/test_copy_image_x11_write_stall.py::test_large_png_raises_within_bound_when_owner_never_reads_stdin (_assert_bounded_failure: ClipboardImageError, xclip, 1s bound, killpg owner pid; fail-first blocked past 6s) |
| 15.2 | with a previous owner still listing `image/png`, X11 `copy_image` still raises rather than returning | slice 1 | observed: tests/test_copy_image_x11_write_stall.py::test_previous_image_owner_does_not_pass_for_the_new_png |
| 15.3 | a Wayland `wl-copy` stand-in that never finishes raises within the bound with its stderr | slice 2 | |
| 16 | Proof: every Linux writer's launch goes through the one launcher, checked by the launcher's own tests plus the existing writer suites. | slice 2 | |
| 17 | Proof: the existing gated (`CLIPBOARD_NATIVE_PROBE`) probes keep passing, including writer-exit pasteability: | slice 2 | |
| 17.1 | Xvfb + `xclip` `copy_image` probe | slice 1 | |
| 17.2 | Xvfb + `xclip` text probe | slice 1 | |
| 17.3 | Xvfb + `xclip` `copy_files` probe | slice 1 | |
| 17.4 | Sway + wl-clipboard `copy_image` probe | slice 2 | |
| 17.5 | Sway + wl-clipboard text probe | slice 2 | |
| 17.6 | Sway + wl-clipboard `copy_files` probe | slice 2 | |
| 18 | Evidence limit: a truly stalled X server or compositor is proved by the stand-in only, as for text. | slice 2 | |
| 19 | Key example 1: Linux X11 whose `xclip` never reads its input (stalled display) → `copy_image` of a 480 KB PNG → `ClipboardImageError` naming `xclip` and the 10 s bound about 10 s later; no owner from this call is left running. (Observed 2026-11-04: today the call is still blocked after 12 s, no bound.) | slice 1 | observed: tests/test_copy_image_x11_write_stall.py::test_large_png_raises_within_bound_when_owner_never_reads_stdin; README Bounds paragraph names X11 copy_image 10 s bound |
| 20 | Key example 2: Linux X11, CLIPBOARD already holds an earlier `copy_image` (lists `image/png`), new `xclip` never takes ownership → `copy_image` raises `ClipboardImageError` within the bound rather than returning as if the new image were offered. | slice 1 | observed: tests/test_copy_image_x11_write_stall.py::test_previous_image_owner_does_not_pass_for_the_new_png |
| 21 | Key example 3: Linux X11 working normally → `copy_image(img)` returns once `xclip -o -selection clipboard -t image/png` gives exactly the written PNG; after the Python process exits the image still pastes. | slice 1 | |
| 22 | Key example 4: Linux Wayland whose `wl-copy` never finishes → `copy_image` raises `ClipboardImageError` within 10 s (today 30 s), quoting what `wl-copy` wrote to stderr. | slice 2 | |
| 23 | Key example 5: Linux X11, 200 000 characters of text or a file list above 64 KiB with a non-reading owner → `copy` / `copy_files` raise `ClipboardContentError` within their bound as today, now launched through the shared launcher. | slice 1 | observed: tests/test_text_x11_write_stall.py, tests/test_copy_files_x11_writer_stall.py green; both writers launch via _desktop._start_helper_owner |
| 24 | Key example 6: Linux X11 with no `xclip` on PATH → `copy_image` raises `ClipboardImageError` and `copy_files` raises `ClipboardContentError`, each with its install hint; the clipboard is unchanged. | slice 1 | observed: tests/test_copy_image_failures.py::test_missing_xclip_raises_clipboard_image_error and copy_files missing-xclip tests in tests/test_copy_files_x11_writer.py green |
| 25 | Architecture: no ADR store exists, so no Accepted decision applies; the binding convention is AGENTS.md: shared Linux helper mechanics live in private `clipboard/_desktop` with per-caller failure modes, and content-kind modules must not copy them. | slice 2 | |
| 26 | Architecture: the launcher owns only process start and payload hand-over (temporary-file `stdin`, detached session, discarded `stdout`, caller's `stderr` log). | slice 1 | observed: clipboard/_desktop.py _start_helper_owner (start + hand-over only) |
| 27 | Architecture: the launcher raises launch failures as `OSError` for each caller to map. | slice 1 | observed: tests/test_helper_owner_launcher.py::test_unwritable_temp_file_propagates_before_popen, ::test_missing_helper_propagates_for_the_caller_to_map |
| 28 | Architecture: deadlines, readiness checks, owner stop, and messages stay with the callers. | slice 2 | |
| 29 | Considered and not chosen (alternatives): | slice 2 | |
| 29.1 | copying the temp-file pattern into the image writer only (a third duplicate the story exists to remove) | slice 2 | |
| 29.2 | passing the payload as an `xclip` file argument (`wl-copy` takes none; the named file would have to outlive the call until a stalled owner reads it) | slice 2 | |
| 29.3 | bounding the pipe write with a writer thread (more moving parts; the pipe still ties Python to a reader that may never come) | slice 2 | |
| 30 | Safe stopping point: the launcher with the X11 image write bounded and confirmed is useful by itself; moving the remaining writers onto it can follow. | slice 1 | observed: slice 1 delivered with X11 image write bounded and confirmed independently of Wayland writers |
| 31 | Planning metadata (not a product promise): effort hypothesis M, medium confidence (six call sites, one readiness change); depends on none. | slice 2 | |
| E1 | Exclusion (deferred, not rejected): macOS `osascript` image writes (already bounded, no background owner fed by Python). | slice 2 | |
| E2 | Exclusion (deferred, not rejected): Windows image writes (already bounded, no background owner fed by Python). | slice 2 | |
| E3 | Exclusion (deferred, not rejected): payload-free helper run `wl-copy --clear`. | slice 2 | |
| E4 | Exclusion (deferred, not rejected): payload-free helper run, the X11 clear child. | slice 2 | |
| E5 | Exclusion (deferred, not rejected): readers. | slice 2 | |
| E6 | Exclusion (deferred, not rejected): Wayland read-back confirmation for text or image writes (they keep confirming by `wl-copy`'s foreground exit). | slice 2 | |
| E7 | Exclusion (deferred, not rejected): a configurable bound. | slice 2 | |
| E8 | Exclusion (deferred, not rejected): Linux `copy_html` (no native writer exists). | slice 2 | |

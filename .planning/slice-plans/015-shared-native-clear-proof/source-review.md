# Source review: SEED-001#shared-native-clear-proof

Launch: fresh general-purpose reviewer (no conversation inheritance), 2026-11-04, by the execution coordinator.
Input: only the minimal story (SEED-001 `#shared-native-clear-proof` Goal and Scope) plus this plan's original
correction input (Provenance, Current findings, Preserved promises and constraints, Current decisions), with
slicing, proof table, premises and plan review omitted. The reviewer read only that input and changed nothing;
its numbered return is recorded below verbatim or close.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Maintainers who change what the native `clear()` proof calls "cleared" make that change in one place, not in parallel copies across four probes and four wrappers (so the desktops' proofs cannot drift apart) | slice 4 | observed: scripts/native_clear_support.py cleared_step is the only "cleared" rule; X11/Wayland (linux_native_clear_steps), Windows (probe_windows_native_clear) and macOS (probe_macos_native_clear _cleared) all end in it; single EMPTY_READS |
| 2 | The documentation names `clear()` wherever it lists the operations that pick Wayland on a mixed session | slice 1 | observed: clipboard/_desktop.py _is_linux_wayland docstring and AGENTS.md:36 name clear; README.rst:348 already states mixed-session clear clears Wayland |
| 3 | Scope is limited to correcting SEED-001#clear-clipboard's proof and documentation structure | slice 4 | observed: git diff 13cb7a3..HEAD+worktree touches only scripts/*clear*, tests/test_clear*/test_native_clear_support/test_no_pillow_extra, AGENTS.md, one clipboard/_desktop.py docstring, plan records |
| 3a.1 | One shared "cleared" observation behind the X11 / Wayland / Windows / macOS clear probes | slice 4 | observed: scripts/native_clear_support.py cleared_step is the only "cleared" rule; X11/Wayland (linux_native_clear_steps), Windows (probe_windows_native_clear) and macOS (probe_macos_native_clear _cleared) all end in it; single EMPTY_READS |
| 3a.2 | One Linux step set behind the X11 / Wayland clear probes | slice 2 | observed: scripts/linux_native_clear_steps.py LinuxDesktop + shared steps used by both scripts/probe_linux_{x11,wayland}_native_clear.py (step lists identical to 9eb5a3c) |
| 3a.3 | Wrappers rely on each step's own `ok` | slice 4 | observed: tests/test_clear_native_{linux_x11,linux_wayland,windows,macos}.py assert exit, ok, failed_steps/case list, floors only |
| 3a.4 | Every touched probe file stays within 250 lines | slice 4 | observed: wc -l: every touched scripts/*clear*.py and wrapper <= 250 (max native_clear_support.py 249; X11 probe 141, Wayland 156, Windows 190, macOS 201) |
| 3a.5 | `clear()` is named in the `_is_linux_wayland` docstring (`clipboard/_desktop.py`) | slice 1 | observed: clipboard/_desktop.py _is_linux_wayland docstring: "Used by image write, HTML read, inspect, and clear." |
| 3a.6 | `clear()` is named in the AGENTS.md session sentence ("HTML/inspect/image write select Wayland") | slice 1 | observed: AGENTS.md:36 "HTML/inspect/image write/clear select Wayland" |
| 3a.7 | `tests/test_clear.py` stops restating the no-Pillow scenario | slice 1 | observed: tests/test_clear.py test_clear_is_public_without_images_extra removed; tests/test_no_pillow_extra.py clear scenario asserts "set_clipboard_clearer" in __all__ (make check green) |
| 3a.8 | `tests/test_clear.py` stops asserting private globals (`_clipboard_clearer is _default_clipboard_clearer`) | slice 1 | observed: tests/test_clear.py test_default_clearer_names_platform_and_seam: injected recording clearer, set_clipboard_clearer(None), not-available error and injected_calls == []; fails under keep-injected mutation of clipboard/_clear.py, passes reverted |
| 4 | Changes no product code | slice 4 | observed: git diff --stat 13cb7a3 -- clipboard README.rst docs .github: only clipboard/_desktop.py docstring (1 line) |
| 5 | Changes no public API | slice 4 | observed: git diff --stat 13cb7a3 -- clipboard README.rst docs .github: only clipboard/_desktop.py docstring (1 line) |
| 5a | Changes no error message | slice 4 | observed: git diff --stat 13cb7a3 -- clipboard README.rst docs .github: only clipboard/_desktop.py docstring (1 line) |
| 5b | Changes no README promise; historical promises and README Evidence of SEED-001#clear-clipboard stay as they are | slice 4 | observed: git diff 13cb7a3 -- README.rst empty; README Evidence still matched by CI runs 41741871109/41742684361 and live macOS run |
| 5c | In `clipboard/`, only a docstring in `clipboard/_desktop.py` changes | slice 4 | observed: git diff --stat 13cb7a3 -- clipboard README.rst docs .github: only clipboard/_desktop.py docstring (1 line) |
| 6 | Every probe keeps its step (or macOS case) names | slice 4 | observed: step/case lists identical to base: X11 8, Wayland 9, Windows 8 (CI logs), macOS 6 cases; wrappers assert exact list |
| 6a | Every probe keeps its step numbering | slice 4 | observed: step/case lists identical to base: X11 8, Wayland 9, Windows 8 (CI logs), macOS 6 cases; wrappers assert exact list |
| 6b | Every probe keeps its step order | slice 4 | observed: step/case lists identical to base: X11 8, Wayland 9, Windows 8 (CI logs), macOS 6 cases; wrappers assert exact list |
| 7 | Every probe step keeps its observed evidence | slice 4 | observed: CI logs and live macOS report: each step records listing_after (helper rc/stdout/stderr), child clear records, reads, owner pids/owner_exit |
| 7a.1 | Each step still records the independent helper's own output (exit code, stdout, stderr), where it does today | slice 4 | observed: listing_after holds the independent helper result in every shared step (native_clear_support.cleared_step) |
| 7a.2 | Each step still records the child `clear()` record, where it does today | slice 4 | observed: child_clear / first / second records kept in every step (CI logs, macOS live report) |
| 7a.3 | Each step still records every reader's value, where it does today | slice 4 | observed: reads = read_everything() recorded by cleared_step in every step |
| 7a.4 | Each step still records owner PIDs, where it does today | slice 4 | observed: producer_owner_pids / library_owner_pids recorded on X11 and Wayland (CI run 41741871109) |
| 7a.5 | Each step still records owner exit, where it does today | slice 4 | observed: owner_exit recorded and required in ok (9 owners exited, CI run 41741871109) |
| 8 | Report key names inside a step may become neutral (permission) | slice 4 | observed: keys neutralised to listing_after/classified_empty; grep README.rst docs .github finds none |
| 9a | A wrapper may drop a per-field assertion only when the step's `ok` implies it | slice 4 | observed: per-wrapper removal tables in slice 2-4 returns; each dropped assertion implied by step ok |
| 9b | A wrapper-only condition that matters moves into that step's `ok` (stricter, never looser) | slice 4 | observed: X11 step 2 display_opened/owner_before, file:/// URI, waited_s<=bound_s moved into ok (native_clear_support._owner_exited, linux_native_clear_steps) |
| 10.1 | Wrappers keep exit code 0 | slice 4 | observed: wrappers assert returncode 0, report ok, failed_steps == [] (macOS: every case ok) |
| 10.2 | Wrappers keep `ok` | slice 4 | observed: wrappers assert returncode 0, report ok, failed_steps == [] (macOS: every case ok) |
| 10.3 | Wrappers keep `failed_steps == []` | slice 4 | observed: wrappers assert returncode 0, report ok, failed_steps == [] (macOS: every case ok) |
| 10.4 | Wrappers keep the exact ordered step list | slice 4 | observed: step/case lists identical to base: X11 8, Wayland 9, Windows 8 (CI logs), macOS 6 cases; wrappers assert exact list |
| 10.5 | Wrappers keep environment floors: xclip / Xvfb; Sway / wl-clipboard and `compositor_generalization` false; Windows version / runner image; macOS product / build | slice 4 | observed: wrappers keep xclip/xvfb versions; compositor_generalization False, compositor and wl_clipboard versions; Windows version/runner image; macOS product/build |
| 10.6 | Wrappers keep "fails on an evidence limit, never skips" where it holds today | slice 4 | observed: wrappers still assert exit 0 so an evidence-limit exit 2 fails rather than skips |
| 11a | Default pytest stays desktop-free | slice 4 | observed: nix develop -c make check: 606 passed, 27 skipped on Darwin (no desktop needed) |
| 11b | Probes still exit 2 with `evidence_limit` off their desktop | slice 4 | observed: Darwin: X11, Wayland, Windows probes exit 2 with evidence_limit true |
| 12a | Linux and Windows probes run only in CI jobs `native-linux-x11-clear`, `native-linux-wayland-clear` and `native-windows-clear`, after publication | slice 3 | observed: CI runs 41741871109 (f071961) and 41742684361 (147119b): native-linux-x11-clear, native-linux-wayland-clear, native-windows-clear success after publication |
| 12b | The macOS probe runs locally under `CLIPBOARD_NATIVE_PROBE=1` (replaces the live clipboard; check the screen is unlocked first) | slice 4 | observed: CLIPBOARD_NATIVE_PROBE=1 ... pytest tests/test_clear_native_macos.py -v -rP passed on unlocked session (screen lock checked), six cases ok |
| 13 | If a native run shows a step that held before now fails, stop and return the observation; do not weaken the step or its `ok` | slice 4 | observed: no native step regressed; nothing weakened (slice-2 refactor loosening reverted before publication) |
| 14a | A clear is proven when a child `clear()` returned, the desktop's independent listing classifies as empty, and every public reader reads absence | slice 4 | observed: scripts/native_clear_support.py cleared_step is the only "cleared" rule; X11/Wayland (linux_native_clear_steps), Windows (probe_windows_native_clear) and macOS (probe_macos_native_clear _cleared) all end in it; single EMPTY_READS |
| 14a.1 | Desktops differ only by listing, empty predicate, producer and owner helper | slice 4 | observed: LinuxDesktop/listing+predicate seams: Linux owner/listing/is_empty/produce; Windows consumer_formats/no_formats; macOS independent_listing/no_offer |
| 14a.2 | Platform-only steps stay per desktop: dead `DISPLAY`, missing `wl-copy`, Windows holder bound, macOS `copy("")` contrast, raw early mechanism steps | slice 4 | observed: dead DISPLAY, missing wl-copy, raw early steps, Windows holder steps, macOS copy("") contrast remain per-desktop |
| 14b | The shared producer step requires producer-owner exit on Wayland as on X11 | slice 2 | observed: CI run 41741871109 (f071961) Native Linux Wayland clear (Sway): steps 3,4,8,9 record producer_owner_pids and owner_exit.exited true; failed_steps [] |
| 14c | Shared Linux steps go in a new script module rather than `native_clear_support.py` | slice 2 | observed: new module scripts/linux_native_clear_steps.py; native_clear_support.py holds only the shared cleared_step rule |
| X1 | EXCLUSION: how X11 `clear()` launches its relinquish helper in frozen or zipped applications (separate human decision) | slice 4 | observed: excluded: no change to _x11_relinquish launch, Makefile test-package, text/inspect/copy_files probes or bounded-helper-owner-write |
| X2 | EXCLUSION: a `make test-package` check of the installed `_x11_relinquish.py` | slice 4 | observed: excluded: no change to _x11_relinquish launch, Makefile test-package, text/inspect/copy_files probes or bounded-helper-owner-write |
| X3 | EXCLUSION: probes for other content kinds (text, inspect, copy_files) | slice 4 | observed: excluded: no change to _x11_relinquish launch, Makefile test-package, text/inspect/copy_files probes or bounded-helper-owner-write |
| X4 | EXCLUSION: SEED-001#bounded-helper-owner-write | slice 4 | observed: excluded: no change to _x11_relinquish launch, Makefile test-package, text/inspect/copy_files probes or bounded-helper-owner-write |
| X5 | EXCLUSION: any product behavior change | slice 4 | observed: git diff --stat 13cb7a3 -- clipboard README.rst docs .github: only clipboard/_desktop.py docstring (1 line) |

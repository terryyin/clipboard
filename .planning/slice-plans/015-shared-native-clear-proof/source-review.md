# Source review: SEED-001#shared-native-clear-proof

Launch: fresh general-purpose reviewer (no conversation inheritance), 2026-11-04, by the execution coordinator.
Input: only the minimal story (SEED-001 `#shared-native-clear-proof` Goal and Scope) plus this plan's original
correction input (Provenance, Current findings, Preserved promises and constraints, Current decisions), with
slicing, proof table, premises and plan review omitted. The reviewer read only that input and changed nothing;
its numbered return is recorded below verbatim or close.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Maintainers who change what the native `clear()` proof calls "cleared" make that change in one place, not in parallel copies across four probes and four wrappers (so the desktops' proofs cannot drift apart) | slice 4 | |
| 2 | The documentation names `clear()` wherever it lists the operations that pick Wayland on a mixed session | slice 1 | observed: clipboard/_desktop.py _is_linux_wayland docstring and AGENTS.md:36 name clear; README.rst:348 already states mixed-session clear clears Wayland |
| 3 | Scope is limited to correcting SEED-001#clear-clipboard's proof and documentation structure | slice 4 | |
| 3a.1 | One shared "cleared" observation behind the X11 / Wayland / Windows / macOS clear probes | slice 4 | |
| 3a.2 | One Linux step set behind the X11 / Wayland clear probes | slice 2 | |
| 3a.3 | Wrappers rely on each step's own `ok` | slice 4 | |
| 3a.4 | Every touched probe file stays within 250 lines | slice 4 | |
| 3a.5 | `clear()` is named in the `_is_linux_wayland` docstring (`clipboard/_desktop.py`) | slice 1 | observed: clipboard/_desktop.py _is_linux_wayland docstring: "Used by image write, HTML read, inspect, and clear." |
| 3a.6 | `clear()` is named in the AGENTS.md session sentence ("HTML/inspect/image write select Wayland") | slice 1 | observed: AGENTS.md:36 "HTML/inspect/image write/clear select Wayland" |
| 3a.7 | `tests/test_clear.py` stops restating the no-Pillow scenario | slice 1 | observed: tests/test_clear.py test_clear_is_public_without_images_extra removed; tests/test_no_pillow_extra.py clear scenario asserts "set_clipboard_clearer" in __all__ (make check green) |
| 3a.8 | `tests/test_clear.py` stops asserting private globals (`_clipboard_clearer is _default_clipboard_clearer`) | slice 1 | observed: tests/test_clear.py test_default_clearer_names_platform_and_seam: injected recording clearer, set_clipboard_clearer(None), not-available error and injected_calls == []; fails under keep-injected mutation of clipboard/_clear.py, passes reverted |
| 4 | Changes no product code | slice 4 | |
| 5 | Changes no public API | slice 4 | |
| 5a | Changes no error message | slice 4 | |
| 5b | Changes no README promise; historical promises and README Evidence of SEED-001#clear-clipboard stay as they are | slice 4 | |
| 5c | In `clipboard/`, only a docstring in `clipboard/_desktop.py` changes | slice 4 | |
| 6 | Every probe keeps its step (or macOS case) names | slice 4 | |
| 6a | Every probe keeps its step numbering | slice 4 | |
| 6b | Every probe keeps its step order | slice 4 | |
| 7 | Every probe step keeps its observed evidence | slice 4 | |
| 7a.1 | Each step still records the independent helper's own output (exit code, stdout, stderr), where it does today | slice 4 | |
| 7a.2 | Each step still records the child `clear()` record, where it does today | slice 4 | |
| 7a.3 | Each step still records every reader's value, where it does today | slice 4 | |
| 7a.4 | Each step still records owner PIDs, where it does today | slice 4 | |
| 7a.5 | Each step still records owner exit, where it does today | slice 4 | |
| 8 | Report key names inside a step may become neutral (permission) | slice 4 | |
| 9a | A wrapper may drop a per-field assertion only when the step's `ok` implies it | slice 4 | |
| 9b | A wrapper-only condition that matters moves into that step's `ok` (stricter, never looser) | slice 4 | |
| 10.1 | Wrappers keep exit code 0 | slice 4 | |
| 10.2 | Wrappers keep `ok` | slice 4 | |
| 10.3 | Wrappers keep `failed_steps == []` | slice 4 | |
| 10.4 | Wrappers keep the exact ordered step list | slice 4 | |
| 10.5 | Wrappers keep environment floors: xclip / Xvfb; Sway / wl-clipboard and `compositor_generalization` false; Windows version / runner image; macOS product / build | slice 4 | |
| 10.6 | Wrappers keep "fails on an evidence limit, never skips" where it holds today | slice 4 | |
| 11a | Default pytest stays desktop-free | slice 4 | |
| 11b | Probes still exit 2 with `evidence_limit` off their desktop | slice 4 | |
| 12a | Linux and Windows probes run only in CI jobs `native-linux-x11-clear`, `native-linux-wayland-clear` and `native-windows-clear`, after publication | slice 3 | |
| 12b | The macOS probe runs locally under `CLIPBOARD_NATIVE_PROBE=1` (replaces the live clipboard; check the screen is unlocked first) | slice 4 | |
| 13 | If a native run shows a step that held before now fails, stop and return the observation; do not weaken the step or its `ok` | slice 4 | |
| 14a | A clear is proven when a child `clear()` returned, the desktop's independent listing classifies as empty, and every public reader reads absence | slice 4 | |
| 14a.1 | Desktops differ only by listing, empty predicate, producer and owner helper | slice 4 | |
| 14a.2 | Platform-only steps stay per desktop: dead `DISPLAY`, missing `wl-copy`, Windows holder bound, macOS `copy("")` contrast, raw early mechanism steps | slice 4 | |
| 14b | The shared producer step requires producer-owner exit on Wayland as on X11 | slice 2 | |
| 14c | Shared Linux steps go in a new script module rather than `native_clear_support.py` | slice 2 | |
| X1 | EXCLUSION: how X11 `clear()` launches its relinquish helper in frozen or zipped applications (separate human decision) | slice 4 | |
| X2 | EXCLUSION: a `make test-package` check of the installed `_x11_relinquish.py` | slice 4 | |
| X3 | EXCLUSION: probes for other content kinds (text, inspect, copy_files) | slice 4 | |
| X4 | EXCLUSION: SEED-001#bounded-helper-owner-write | slice 4 | |
| X5 | EXCLUSION: any product behavior change | slice 4 | |

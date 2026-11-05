# Source review: SEED-001#macos-native-wait-evidence

Launch: fresh general-purpose subagent (no conversation inheritance), 2026-11-05,
given only the seed section text (Goal, Scope, Key examples) of
SEED-001#macos-native-wait-evidence; told to read no project files, change
nothing, and return numbered commitments. Returned 22 ids below verbatim.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Automation developers on macOS can rely on `wait_for_kind` and `wait_for_text_change` with the same stated evidence the Linux X11, Linux Wayland and Windows desktops already have | slice 1 | observed: docs/evidence-wait-html-files.rst macOS wait bullet says **verified** with floors, per-step results and evidence limits like the Linux/Windows wait bullet |
| 1.1 | Context: docs/evidence-wait-html-files.rst currently marks the macOS wait Evidence entry "not yet verified" | slice 1 | observed: pre-change docs/evidence-wait-html-files.rst macOS wait bullet (commit abb4de8) said **not yet verified** |
| 1.2 | Context: the gated probe was written with SEED-001#wait-for-content, but every run so far stopped at its evidence limit because the screen was locked | slice 1 | observed: pre-change docs/evidence-wait-html-files.rst macOS wait bullet recorded locked-screen exit 2 runs |
| 2 | On the developer's Mac with an unlocked Aqua console session, run the existing gated probe (`CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked pytest tests/test_wait_native_macos.py -q -rP`, probe `scripts/probe_macos_native_wait.py`) | slice 1 | observed: that exact command run twice on the owner's Mac, both exit 0 (probe run 2026-11-05T14:52Z at abb4de8 (exit 0, ok, verified)) |
| 2.1 | The run requires an unlocked Aqua console session on the developer's Mac | slice 1 | observed: session_state() locked false, on_console true, login_done true, IOConsoleLocked false immediately before; report session same |
| 2.2 | The probe being run is the existing one (`tests/test_wait_native_macos.py` wrapping `scripts/probe_macos_native_wait.py`), not a new probe | slice 1 | observed: no change under scripts/ or tests/ (git diff touches only docs) |
| 3 | The probe's four steps use an independent `pbcopy` producer | slice 1 | observed: report environment producer "pbcopy (independent process, LANG=en_US.UTF-8)"; producer returncode 0 in steps 1, 3, 4 |
| 3.1 | `wait_for_kind("text")` from a cleared pasteboard returns a snapshot listing `"text"` after the copy | slice 1 | observed: report step 1 setup empty, observed kinds [],[],[text], snapshot kinds [text], latency 0.37 s |
| 3.2 | `wait_for_kind("html", timeout=1)` with nothing copied returns `None` at its timeout | slice 1 | observed: report step 2 result None, elapsed 1.008 s |
| 3.3 | `wait_for_text_change` returns the second independently copied text | slice 1 | observed: report step 3 text "wait probe new text", latency 0.012 s |
| 3.4 | Clear followed by an identical recopy leaves `wait_for_text_change` returning `None` | slice 1 | observed: report step 4 observed old,"","",old,old,old; result None at 3.008 s |
| 4 | Replace the macOS wait Evidence entry's "not yet verified" with the observed result, or, if a step fails, with the observed limitation | slice 1 | observed: docs/evidence-wait-html-files.rst macOS wait bullet now **verified** with the observed result |
| 4.1 | The observed result records the macOS version and build | slice 1 | observed: docs/evidence-wait-html-files.rst macOS wait bullet floors macOS 26.6.2 (build 25G83) / Darwin 25.6.0 |
| 4.2 | The observed result records each step's outcome | slice 1 | observed: docs/evidence-wait-html-files.rst macOS wait bullet states each of the four step outcomes |
| 4.3 | The observed result records each step's timing | slice 1 | observed: docs/evidence-wait-html-files.rst macOS wait bullet gives 0.37 s, 1.0 s, 0.01 s, 3.0 s |
| 4.4 | Alternative: if a step fails, the entry records the observed limitation instead | slice 1 | observed: no step failed (failed_steps []), so the alternative does not apply |
| 5 | A failing step is a defect to fix, in the wait or in the probe, before verification is claimed | slice 1 | observed: failed_steps [] on both runs; no defect to fix |
| 6 | No change to the wait API | slice 1 | observed: git diff touches no clipboard/ source |
| 7 | No change to other desktops' evidence | slice 1 | observed: Linux X11/Wayland/Windows wait bullet unchanged in git diff |
| 8 | The probe stays developer-run (it needs the developer's unlocked session) | slice 1 | observed: no workflow change; probe gated by CLIPBOARD_NATIVE_PROBE |
| 8.1 | The probe does not become a CI job | slice 1 | observed: .github/workflows unchanged |
| 9 | Locked-screen or evidence-limit exits leave the Evidence claim unchanged; they do not count as verification | slice 1 | observed: scripts/probe_macos_native_wait.py:69-77 returns 2 with evidence_limit on a locked/off-console session, tests/test_wait_native_macos.py:56 fails on it; docs/evidence-wait-html-files.rst macOS wait bullet says such an exit is not verification |
| 10 | Example: unlocked macOS Aqua session, run the gated probe, it exits 0 with all four steps ok, and the Evidence entry records the observed version and timings | slice 1 | observed: probe run 2026-11-05T14:52Z at abb4de8 (exit 0, ok, verified) and docs/evidence-wait-html-files.rst macOS wait bullet |
| 11 | Example: locked screen, the probe exits 2 with `evidence_limit`, and the Evidence claim stays unchanged | slice 1 | observed: earlier locked runs (pre-change docs/evidence-wait-html-files.rst macOS wait bullet) left the claim "not yet verified"; gate at scripts/probe_macos_native_wait.py:69-77 |

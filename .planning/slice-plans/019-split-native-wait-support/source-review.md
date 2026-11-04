# Source review: SEED-001#split-native-wait-support

Launch: fresh general-purpose reviewer (no plan, return, product, or proof).
Input: story Goal, Scope, key examples, and exclusions only from
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#split-native-wait-support`.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Maintainers of the native wait probes can change either the child wait harness or one probe step without reading a single module that mixes both (today: a 384-line mix in `scripts/native_wait_support.py`). | slice 1 | observed: scripts/native_wait_harness.py (harness+timing only) and scripts/native_wait_support.py (steps+runner+report); neither mixes both |
| 2 | After the split, the wait-support surface is back under the project's 250-line file limit that every other native support module already meets. | slice 1 | observed: wc -l: native_wait_harness.py=243, native_wait_support.py=170, macos_native_wait_support.py=49 (each <=250) |
| 3 | This is a retrospective correction of `SEED-001#wait-for-content` (identity: `SEED-001#split-native-wait-support`). | slice 1 | observed: plan Provenance and findings + identity SEED-001#split-native-wait-support; correction of wait-for-content |
| 4a.1 | One module holds the child wait harness. | slice 1 | observed: scripts/native_wait_harness.py: _CHILD, recording, WaitDesktop, start_kind_child, start_text_change_child, _start, finish_child |
| 4a.2 | That same harness module holds the timing rules. | slice 1 | observed: scripts/native_wait_harness.py: _observation_timing, returned_after_copy, ended_at_timeout |
| 4a.3 | The other module holds the four shared probe steps. | slice 1 | observed: scripts/native_wait_support.py: text_appears_step, nothing_copied_step, text_change_step, clear_then_recopy_step |
| 4a.4 | That steps module holds their runner. | slice 1 | observed: scripts/native_wait_support.py: run_steps |
| 5 | Update imports in the four `scripts/probe_*_native_wait.py` entrypoints to match the split. | slice 1 | observed: probe_linux_x11/wayland/windows import WaitDesktop from native_wait_harness and steps from native_wait_support; probe_macos keeps native_wait_support re-exports + macos_native_wait_support.MACOS |
| 6a.1 | No change to probe step names. | slice 1 | observed: step name strings in native_wait_support.py match wrappers STEPS in tests/test_wait_native_*.py (unchanged) |
| 6a.2 | No change to pass conditions. | slice 1 | observed: pass-condition bodies in the four step functions unchanged vs pre-split (diff only moves them) |
| 6a.3 | No change to report fields. | slice 1 | observed: step()/report() JSON shape unchanged; report still dumps fields |
| 6a.4 | No change to gates. | slice 1 | observed: probe session gates untouched in probe_*_native_wait.py beyond import lines |
| 6a.5 | No change to floors. | slice 1 | observed: environment floors untouched in probes beyond import lines |
| 6a.6 | No change to CI jobs. | slice 1 | observed: git diff names no .github paths; ci.yml wait jobs still present |
| 6a.7 | No change to the wait API. | slice 1 | observed: clipboard/_wait.py and public wait API untouched in this change |
| 7 | No new probe steps. | slice 1 | observed: still exactly four steps in run_steps order; no new step functions |
| 8 | No timing-rule changes. | slice 1 | observed: timing helpers moved verbatim to native_wait_harness.py; constants INTERVAL_S/SLACK_S unchanged |
| 9 | No macOS gated evidence work (remains with `SEED-001#macos-native-wait-evidence`). | slice 1 | observed: no CLIPBOARD_NATIVE_PROBE gated macOS evidence authored; exclusion holds |
| E1 | Maintainer opens the module that runs the child wait to judge timing → that module holds harness + timing rules only, ≤ 250 lines; the four steps, runner, and report live in another module, also ≤ 250 lines. | slice 1 | observed: native_wait_harness.py 243 lines harness+timing only; native_wait_support.py 170 lines steps+runner+report |
| E2 | Branch is pushed → CI jobs `native-linux-x11-wait`, `native-linux-wayland-wait`, and `native-windows-wait` pass with the same four step names as before. | slice 1 | observed: CI run 41932201965 jobs native-linux-x11-wait, native-linux-wayland-wait, native-windows-wait conclusion=success; logs show the four step ids (1_…xclip/wl-copy/Set-Clipboard, 2_…, 3_…, 4_…) unchanged |
| E3 | Any `scripts/probe_*_native_wait.py` run off its desktop (or on a locked macOS session) → exits 2 with `evidence_limit`, as before the split. | slice 1 | observed: probe_linux_x11/wayland/windows exit 2 evidence_limit=true on darwin; macOS locked path unavailable (live Aqua exit 0); gated macOS evidence deferred per exclusion 9 |

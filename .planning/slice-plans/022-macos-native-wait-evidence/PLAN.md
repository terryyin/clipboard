# Plan: Verify the clipboard waits natively on macOS Aqua

**Identity:** SEED-001#macos-native-wait-evidence
**Source:** [Verify the clipboard waits natively on macOS Aqua](../../seeds/SEED-001-clipboard-true-to-its-name.md#macos-native-wait-evidence)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Run the existing gated macOS Aqua wait probe on an unlocked console session
and replace the macOS wait Evidence entry's "not yet verified" with the
observed result (or a failing step's observed limitation). Goal, required
behavior, documentation duty, scope limits, and key examples are in the seed
section; this plan adds none.

**Excluded** (seed scope limits): wait API changes; other desktops' Evidence;
turning the probe into a CI job; treating a locked-screen / evidence-limit
exit as verification.

## Assumptions and direction

- Follows the North Star topic: native claims need an independent producer and
  stated evidence limits. No ADR store exists; no Accepted ADR constrains this
  plan. No new North Star topic is warranted.
- **PFE.** Reuse as-is: `scripts/probe_macos_native_wait.py`,
  `scripts/macos_native_wait_support.py`, shared
  `scripts/native_wait_support.py` / `scripts/native_wait_harness.py`, wrapper
  `tests/test_wait_native_macos.py`, and the Evidence home
  `docs/evidence-wait-html-files.rst`. The four steps already match the other
  desktops' verified wait probes. **Gap:** only the unlocked-session run and
  the Evidence claim remain. No new probe, harness, or wait implementation.
- Local gates (AGENTS.md): `nix develop -c make check` after the Evidence
  edit (docs and planning records only; no Python surface change). No
  workflow change, so `make lint-workflows` is not required. `make
  test-package` is not required (no installed API change).
- The probe **replaces the live clipboard**. Run it only when the developer
  accepts that, on an unlocked Aqua console session.

## Outside-in proof

| Example / promise (seed) | Observable signal | Owning slice |
| --- | --- | --- |
| 1. Unlocked Aqua → gated probe → exit 0, four steps ok; Evidence records version and timings | `CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked pytest tests/test_wait_native_macos.py -q -rP` exits 0; JSON report `ok` true, `evidence_limit` false, `failed_steps` `[]`, steps in wrapper order; `docs/evidence-wait-html-files.rst` macOS wait bullet says **verified** with floors and per-step timings from that report | 1 |
| 2. Locked screen → exit 2 `evidence_limit` → Evidence claim unchanged | Already documented in the current Evidence bullet and probe gate; this story does not re-run a locked session. If the unlock probe instead exits 2, stop: do not claim verification | 1 (stop condition) |
| A failing step (exit 1) before verification | Defect in the wait or the probe; fix it in this story before claiming verification, or stop for a scope decision if the limitation belongs in Evidence instead | 1 |

## Decisive premises

Observed in this preparation workspace on 2026-11-05T14:35Z at `65262a7e8`
(Darwin 25.6.0, macOS 26.6.2 build 25G83, arm64), unless a row says
otherwise.

| Consuming operation | Observation and result | Remainder |
| --- | --- | --- |
| Slice 1 runs the gated probe on a usable Aqua console | `PYTHONPATH=scripts` `session_state()` → `locked: false`, `on_console: true`, `login_done: true`; `ioreg` `IOConsoleLocked` = `No` | Re-check immediately before the probe; a locked or off-console session stops the slice (exit 2 / evidence limit), no Evidence claim |
| The existing probe and wrapper implement the four seed steps | Wrapper `STEPS` and `native_wait_support` step names match examples 1–4 (`1_wait_for_text_…pbcopy` … `4_wait_for_text_change_ignores_clear_then_identical_recopy`); probe docstring and Evidence bullet describe the same independent-`pbcopy` journey | Slice 1's report is the settling observation |
| Evidence home still says "not yet verified" for macOS waits | `docs/evidence-wait-html-files.rst` lines 4–24: macOS Aqua **not yet verified**, prior locked-screen exit 2 on 26.6.2 / 25G83 | Slice 1 replaces that claim from the successful report |
| Desktop-free suite stays green while only Evidence/planning change | Prior trunk desktop-free suite is green; this slice edits Evidence prose and planning records only | `nix develop -c make check` after the Evidence edit |

## Ordered slices

### 1. Verify macOS Aqua waits and record Evidence
Type: Behavior
Status: planned
Proof: Immediately before the probe, confirm `session_state()` is unlocked and
on-console. Run
`CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked pytest
tests/test_wait_native_macos.py -q -rP` (probe
`scripts/probe_macos_native_wait.py`). Accept only exit 0 with `ok` true,
`evidence_limit` false, empty `failed_steps`, and the four ordered steps.
Update the macOS wait bullet in `docs/evidence-wait-html-files.rst` to
**verified** with that run's floors (macOS product/build, Darwin, machine,
Python) and per-step outcomes/timings, in the same style as the Linux/Windows
wait Evidence bullet. Exit 2 → stop, leave Evidence unchanged. Exit 1 → fix
the wait or probe (or stop for a documented limitation decision) before any
verification claim. Then `nix develop -c make check`.

Behavior: unlocked macOS Aqua console with the existing gated wait probe →
run the probe → every step holds and the Evidence entry records the observed
verification (or the run stops at evidence limit / defect without a false
claim).

## Current decisions

- Reuse the existing probe and shared wait steps; do not add a CI job or a
  second macOS wait harness.
- Evidence lives in `docs/evidence-wait-html-files.rst` (README only links
  there). Locked-screen history stays as an evidence-limit note only until a
  successful unlocked run replaces the "not yet verified" claim.

## Plan concern evidence

Slice-plan refinement was not needed: one Behavior owns the probe run and the
Evidence claim, premises are settled or bounded by that run's session gate,
and no independent second outcome remains.

# Plan: Split the native wait probe support along its harness and steps

**Identity:** SEED-001#split-native-wait-support
**Source:** [Split the native wait probe support along its harness and steps](../../seeds/SEED-001-clipboard-true-to-its-name.md#split-native-wait-support)
**Source review:** [source-review.md](source-review.md)

## Provenance and findings

Retrospective correction of SEED-001#wait-for-content (plan
`3477f8f:.planning/slice-plans/018-wait-for-content/PLAN.md`, commits 24938ab, 5d0afdb, bf48f2c, 2f4be58, 0120396).
Finding (2026-11-04, current revision 0120396): `scripts/native_wait_support.py`
is 384 lines, over the post-change refactor check's 250-line limit; every
other `scripts/*_support.py` is ≤ 249 lines. It arrived in bf48f2c (slice 3)
and the slice 3 refactor return reported it as "fine", so the limit was
missed, not waived. It holds two concepts: the child wait harness
(`_CHILD`, `recording`, setup/result templates, `WaitDesktop`,
`start_kind_child`, `start_text_change_child`, `_start`, `finish_child`) with
the timing rules (`_observation_timing`, `returned_after_copy`,
`ended_at_timeout`), and the four probe steps with `step`, `run_steps` and
`report`.

## Preserved promises and constraints

- Probe step names, order, pass conditions, JSON report fields, exit codes,
  gates and floors stay identical on all four desktops; the wrappers'
  `STEPS` lists stay unchanged.
- CI jobs `native-linux-x11-wait`, `native-linux-wayland-wait`,
  `native-windows-wait` and the wait API are untouched.

## Outside-in proof

| Promise | Observable signal | Owning slice |
| --- | --- | --- |
| Each wait support module ≤ 250 lines | `wc -l scripts/*wait_support*.py` | 1 |
| Behaviour unchanged on X11 / Wayland / Windows | branch-push CI run: the three wait jobs pass with the same step names | 1 |
| Behaviour unchanged on macOS | each probe exits 2 with `evidence_limit` on a locked or non-matching host; the gated macOS run belongs to SEED-001#macos-native-wait-evidence | 1 |
| Regression | `nix develop -c make check` green | 1 |

## Ordered slices

### 1. Split the harness from the steps
Type: Structure
Status: done
Proof: `wc -l` on the resulting modules; `nix develop -c make check`; each
`scripts/probe_*_native_wait.py` run directly exits 2 with `evidence_limit`
off its desktop; the branch-push CI run's three wait jobs pass.

Move the harness and timing rules to their own support module (for example
`scripts/native_wait_harness.py`), keep the steps, runner and report in
`scripts/native_wait_support.py`, and update imports in the four probes and
`scripts/macos_native_wait_support.py`. Update the module docstrings and the
probes' docstrings that name `native_wait_support` as the home of the
harness, and the AGENTS.md wait-probe sentence if it should name the new
module.

## Current decisions

- Settled premise (observed 2026-11-04 at 3747d57): the harness and timing
  rules occupy lines 1–253 of the 384-line module, of which nine step-only
  constants (`WAIT_TIMEOUT_S` … `NEW_TEXT`) move with the steps, so the
  harness module lands just under 250 lines and the steps module near 140.
  If the harness module still exceeds 250, put the timing rules
  (`_observation_timing`, `returned_after_copy`, `ended_at_timeout`) in their
  own module rather than trimming docstrings.
- Settled premise: `ci.yml` runs on every branch push and holds the three
  wait jobs, so the branch-push run is the cross-desktop proof.
- Learning (slice 1): harness landed at 243 lines without a third timing
  module; post-change refactor dropped the unused `INTERVAL_S` /
  `WaitDesktop` re-export from `native_wait_support` so probes import those
  from `native_wait_harness` (support 161 lines).
- Accepted proof (slice 1): `wc -l` harness 243 / support 161 / macos 49;
  `nix develop -c make check` 769 passed; off-desktop
  `probe_{linux_x11,linux_wayland,windows}_native_wait.py` exit 2 with
  `evidence_limit`; live macOS Aqua probe exit 0 with the four step names;
  CI run 41932201965 wait jobs
  `native-linux-x11-wait` / `native-linux-wayland-wait` /
  `native-windows-wait` success with the same four step names.

## Execution complete

Product advice: Outcome matches the story — harness and timing live in
`scripts/native_wait_harness.py` (243 lines) and the four steps, runner and
report in `scripts/native_wait_support.py` (161 lines); probe step names,
pass conditions, report fields, gates, floors, CI jobs and the wait API are
unchanged. No product correction or backlog change; macOS gated evidence
remains with `SEED-001#macos-native-wait-evidence`. Residual note: harness
sits at 243/250, so future harness edits still need the size check.

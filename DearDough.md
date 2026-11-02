# DearDough Process Findings

## Retention

- Highest allocated local number: 2

## DD-001 — Optional-extra local proof not mirrored on CI matrix path
When a packaging optional extra is required for new contract tests, updating
Makefile/local `uv run --extra …` alone left the GitHub Actions matrix `tests`
job on bare `uv sync/run --locked`, so published slice work failed on every
OS/Python cell until a CI repair aligned the workflow.

### Occurrences
- Execution: SEED-001#read-images
  - Timestamp: 2026-11-02T10:42:00+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: commit f30e269 (Makefile `--extra images`); CI run https://github.com/terryyin/clipboard/actions/runs/41384361341 attempt 1 failed on `uv run --locked pytest` / missing Pillow; repair commit 48e8266; coordinator transcript 57a69224… noting matrix lacked images extra; repair subagent 7f955186…
  - Observed effect: Story-branch matrix jobs failed after slice 1 publish; WIP stash + dedicated CI repair before continuing slice 2; quality/Nix path had already passed.
  - Inference: Dual local-vs-matrix verification seams need an explicit extras checklist when optional dependencies first enter pytest; Makefile green did not prove the matrix path.

## DD-002 — Settled no-session premise still ran three Behavior deliver cycles
When a plan's decisive premise already settles that the execution checkout cannot
host the remaining desktop sessions, splitting each desktop's authorized
evidence-limit path into its own Behavior slice still incurred a full
implement → obligations/source-review → refactor → publish cycle per desktop
before the consolidation Structure slice, without new native measurement.

### Occurrences
- Execution: SEED-001#read-images-native
  - Timestamp: 2026-11-02T11:43:00+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: PLAN.md Decisive premises (Darwin cannot run Win/Linux probes); slices 1–3 Accepted notes all Darwin/no-session evidence limits; published SHAs d08fb4c, 47e5b9c, 0501e6a (near-identical README evidence-limit increments) then fcd18a0 consolidation; coordinator transcript d2b3e3b5… (three Behavior deliver cycles after settled uname Darwin)
  - Observed effect: Three docs-only Behavior publishes plus refactor agents authorized to fill Accepted notes; no Win/Linux probe scripts delivered; slice 4 rewrote the same Evidence paragraph into one consolidated limit statement.
  - Inference: Once session absence is settled for the executing checkout, one evidence-limit write covering the remaining desktops (or collapsing early-probe Behavior slices) would preserve per-desktop honesty with less deliver/refactor overhead; independent desktop loops remain justified only when a session may still appear.

# Plan for explicit Clipboard CI test-case counts

**Identity:** SEED-006#publish-explicit-ci-test-counts
**Source:** [See Clipboard test case counts in Intent](../../seeds/SEED-006-publish-explicit-ci-test-counts.md#publish-explicit-ci-test-counts)

## Goal and scope

The selected CI attempt's desktop-free pytest evidence shows explicit test-case
counts and outcomes for `tests` and its files in the downloaded summary and
Intent's CI status. Keep the single Ubuntu Python 3.13 representative part,
attempt/revision matching, failure verdict, and release-call exclusion. Native
probes and repeated matrix legs keep their existing evidence boundaries.

Adopt the released schema and collector; do not create file-aggregate outcomes
from case results or count file paths as test-file results. No new dashboard
feature or shared protocol development is included. JUnit timing delivery is
[SEED-005](../../seeds/SEED-005-publish-ci-test-execution-times.md#publish-ci-test-execution-times)'s
outcome. Preserve its supplied timings and breakdown if present at execution;
otherwise case counts and explicit untimed evidence suffice for this story.

## Outside-in proof

| Promise/example | Observable proof | Owner |
| --- | --- | --- |
| Maintainer sees explicit case counts for a completed attempt | Download that run's `ci-proof-summary-attempt-<n>` archive; match repository, revision, run and attempt. The `tests` evidence has `unit: "case"`, the producer's pytest outcomes, and a representative file with matching case counts. Intent shows those figures as test cases. | Slice 1, hosted probe |
| Several cases share a file, including parameterization, failure, error and skip | A real xunit1 pytest fixture exits 1 with five cases in one file: 2 passed, 2 failed, 1 other. Run the project's converter and CLI; suite evidence and its single file each retain those five case outcomes, with no file-unit evidence. The workflow retains the pytest exit status. | Slice 1, local pipeline |
| A fragment is missing, stale or duplicated | Run the same CLI with empty inputs, an earlier-attempt fragment, and duplicate part-1 fragments. Explicit case evidence reports missing/missing/ambiguous respectively, with zero contributed counts; a stale revision is also excluded. | Slice 1, local pipeline |
| Timing and paths survive adoption without invented measurements | Replay timed and untimed inputs through the copied CLI. Timed input retains the sum in milliseconds, including failed cases, at suite/file level; untimed input has no fabricated `durationMs` and records untimed cases. Preserve SEED-005's report conversion when present. | Slice 1, local pipeline |
| Existing CI boundaries still hold | Inspect/replay the producer gate and status handling; lint both workflows. Only Ubuntu/3.13 on a non-release call publishes a fragment. A failed completed pytest run remains failed while producing its evidence; no usable completed report leaves a missing part. | Slice 1, workflow proof |

## Ordered slices

### 1. Publish the representative pytest outcomes as test cases in Intent
Type: Behavior
Status: planned
Proof: Replay the local pipeline below, run `nix develop -c make lint-workflows`,
then observe the first authorized branch CI attempt and Intent display. Retain
the exact run, attempt, revision, artifact and representative-file observations.

Behavior: Given the representative leg's completed pytest report, collecting
that attempt's proof publishes explicit case evidence whose suite and file
counts agree with JUnit, and Intent displays the same test-case outcomes.

Copy these seven released modules unchanged from the installed
`dough-test-optimization/scripts/` into `scripts/`: `ci-proof-summary.mjs`,
`ci-proof-options.mjs`, `ci-proof-contract.mjs`, `ci-proof-evidence.mjs`,
`ci-proof-figures.mjs`, `ci-proof-fragments.mjs`, and `ci-proof-collect.mjs`.
Follow the [installed publisher recipe](../../../.agents/skills/dough-test-optimization/references/ci-proof-summary.md).
In `.github/workflows/desktop-free-tests.yml`, declare `--unit case` and
retain/add `--by-file` on the outcomes fragment command. In `ci.yml`, declare
`--expect tests=1:case`. Preserve any `--times` input and its conversion already
delivered by SEED-005, the workflow's original pytest verdict and report-status
gate, pinned actions, Node 20.19, attempt-named uploads, and revision selection.
The collector must continue running from project-owned scripts, not skill paths.

For local proof in the execution workspace, create disposable real pytest cases
under `tests/`, including the mixed-outcome single file above and a collection
failure. Run `uv run --locked --extra images pytest -o junit_family=xunit1
--junitxml=<report> <fixture>` inside `nix develop`, then the actual
`scripts/junit-outcomes.py` and both copied CLI commands with the workflow's
flags and status gate. Observe the original exit codes alongside the summary.
Exercise empty, stale-attempt, stale-revision and duplicate fragments using
`summarize --expect tests=1:case`. Check schema 2 evidence, `evidence[].files`,
counts, unit and gaps; file count is not an outcome count. Replay representative
timed input through `--times` when testing collector preservation; this does
not require implementing JUnit timing delivery. Remove all disposable cases.
Use a focused maintained publisher regression if needed to retain the changed
contract; do not add a Node requirement to all Python matrix legs.

The first authorized execution publication is also this slice's early hosted
probe. It observes the state-changing boundary that preparation cannot settle:
the producer on Ubuntu/Python 3.13, Node 20.19, artifact upload/download,
collector, and deployed Intent reader/display for this candidate. Use the
recipe's `gh run view`, artifact listing and download commands for that exact
attempt; compare the producer's pytest totals, summary and Intent, including
one file's case count. No release tag or deliberate failing hosted commit is
needed. If the artifact or display disagrees, stop slice acceptance and repair
or revise the plan at that boundary; local JSON or green CI alone is insufficient.

Local gates are proportionate to the change: workflow lint validates the changed
YAML and embedded shell. If the Python converter or its tests change, run focused
pytest proof and `nix develop -c make lint`; run broader `make check` only if the
affected consumer trace warrants it. AGENTS.md defines these Nix entry points.
Normal hosted CI remains owned by execution. Package build and native probes
are not extra local gates for this publisher-only change.

## Current decisions and reuse

- PFE: the current converter already emits one outcomes line per JUnit case;
  the released seven-module collector already handles case/file units, file
  breakdown, optional timing, and attempt gaps. Change the existing publisher
  by adopting that implementation. A bespoke schema or dashboard change would
  duplicate responsibilities already delivered by Open Dough.
- The existing `WRITE_CI_PROOF` selection and `ci-proof` collector own the proof
  journey. Do not rerun or aggregate matrix repetitions as extra cases. Other
  artifacts measure native/installed behavior and serve different purposes.
- Clipboard has no identified CI-proof ADR catalog. Its
  [North Star](../../NORTH-STAR.md) governs clipboard APIs and native evidence;
  this plan changes neither. No new architectural direction is needed.
- SEED-005 and this story overlap in the copied modules, fragment flags and
  converter. Re-read fetched trunk when execution starts; keep the shared released
  collector and merge the flags coherently, preserving the other's delivered
  behavior. Neither outcome requires the other to be implemented first.
- Expected edited files are below the 250-line refactoring threshold: existing
  collector modules 77–207 lines; released replacements/additions 91–249;
  `ci.yml` 241; `desktop-free-tests.yml` 100. Recheck actual execution inputs.

## Decisive premises

Observed on 2026-11-10 in this owned preparation workspace at
`4ff784cc4daadc0ccefa4aa4b5a4bee16a51a6e6`, under `nix develop` with pinned
Python/uv and Node v24.21.0. Scratch collector copies and fixtures were removed
before recording preparation. These are feasibility observations, not delivered
implementation or hosted acceptance.

| Consuming operation | Form/profile and observed result | Unverified remainder |
| --- | --- | --- |
| JUnit converter → current publisher | Real pytest with `-o junit_family=xunit1 --junitxml=<report>` produced five cases in one file, exit 1. `uv run --locked python scripts/junit-outcomes.py <report>` and the current `fragment`/`summarize --expect tests=1` CLI yielded schema 1 `checks`, with no file breakdown. | None for the reported current behavior. |
| Adopted CLI → case evidence and file detail | Temporarily copied the seven installed modules into project `scripts/`. Ran `fragment --outcomes <outcomes> --unit case --by-file --entry tests --part 1 --of 1 --attempt 1 --revision <HEAD> --out <fragments>`, then `summarize --expect tests=1:case` with the same identity. Schema 2 suite and one file each had 2 passed, 2 failed, 1 other cases; five untimed cases and no fabricated duration. A `--times <times>` replay retained the JUnit seconds sum in milliseconds. | Actual hosted producer and Node 20.19 belong to Slice 1's early hosted probe; local Node 24 is not claimed as that profile. |
| Collector → missing or ambiguous evidence | The adopted CLI with an absent directory and an attempt-1 fragment collected for attempt 2 each emitted a missing case part with zero counts. Duplicating the same part emitted ambiguous case evidence and zero contributed counts. | Slice 1 adds stale-revision and implemented workflow/status-gate proof. |
| Summary → released Intent reader | Called installed `checkedSummary` with the produced summary and matching repository/run/attempt/revision; it accepted the five case outcomes. `unitNoun("case", 5)` returned `test cases`. Open Dough's published SEED-281 completion record and installed 0.3.94 recipe confirm the shared supplier is delivered. | This candidate's archive acquisition and deployed Intent display remain Slice 1's early hosted probe. |

## Plan review

Slice-plan refinement was not needed: one common rule counts each reported
JUnit case, and one Behavior owns publisher adoption, gaps, preservation and
end-to-end observation. No independent outcome or preparatory Structure slice
is needed. No remaining slice-specific concern was identified outside the
explicit hosted probe. No pre-Take human decision is required.

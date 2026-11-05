# Plan for publishing Clipboard CI proof

**Identity:** SEED-004#publish-clipboard-ci-proof
**Source:** [Publish Clipboard CI proof for Intent](../../seeds/SEED-004-publish-clipboard-ci-proof.md#publish-clipboard-ci-proof)

## Goal and scope

Show a Clipboard developer the desktop-free pytest totals for `tests` in
**Intent → CI status** for the displayed GitHub Actions attempt. Use the
existing Python 3.13 leg on `ubuntu-latest` as the one expected part. Other
matrix repetitions, native probes, and installed-distribution checks keep
their existing jobs. Per-platform and native proof breakdowns are deferred.

## Outside-in proof

| Example | Observable result | Owning slice |
| --- | --- | --- |
| A normal branch run completes | The exact run's artifact contains only `ci-proof-summary.json`. Its `tests` counts equal the named leg's pytest totals, and Intent displays them as one reported part. | 1 |
| pytest completes with a failing assertion, a case error, and a skip | The real pytest command retains exit 1. A scratch run through the workflow's conversion and collection commands reports the failed assertion and case error as failed, and the skip as other. | 1 |
| Collection aborts or setup leaves no report, or only an earlier attempt has a fragment | The commands for this attempt declare part 1 missing and include zero prior counts. With no summary for the shown attempt, Intent reports proof unavailable. | 1 |

## Ordered slices

### 1. Show the representative pytest run's proof in Intent
Type: Behavior
Status: planned
Proof: Run the local pipeline with actual pytest reports for the three
examples, then `nix develop -c make lint-workflows` and
`nix develop -c make check`. The former checks the changed workflow and
embedded shell. The latter checks the new Python converter with Ruff and
replays the unchanged desktop-free suite. Confirm on the first authorized
branch push and retain the run, artifact and Intent result.

Use the recipe's four unchanged modules in `scripts/` and its
JUnit-to-outcomes conversion. Add xunit1 XML reporting only to the selected
leg's ordinary CI invocation. In the reporting path, use pytest's original
exit status for the step verdict and to distinguish a completed run
(0 or 1, with a usable report) from an interrupted or absent run. Put the
report and derived evidence under runner temp. The remaining legs and
the release caller use their existing pytest command. A setup or conversion
failure leaves no fragment, and a successful upload cannot mask a test
failure. Set up Node only for the proof work.

Declare `tests=1` in the collector. Use same-attempt fragment names and
pattern download, then publish one attempt-named summary with the recipe's
identity fields and PR-head revision rule. Skip this proof path on the
release call identified by its `release-tag` input, keeping proof collection
out of the publishing dependency. Reuse the project's pinned checkout,
upload and download actions, and pin setup-node for a supported Node version.
Use the recipe's one-day fragment and 30-day summary retention.

For focused local proof, run actual pass, fail, skip and fixture-error cases
from a temporary fixture under `tests`, and a separate collection-error
case. Use the same pytest flags, conversion, collector CLI and status
gate as CI. Check that an empty input directory or an earlier attempt's
fragment produces a missing part. Remove scratch cases before delivery.

The first branch run is the early hosted check of the workflow integration,
including the job selection, artifact transfer and deployed Intent read.
Compare the producer's log with the artifact listing and downloaded archive
using the recipe's `gh` commands. Read **Intent → CI status** for that branch
and match the displayed revision, run, attempt, totals and part. Also inspect
the run's native and quality job results. No release tag or special failure
commit is needed. If the first run cannot produce or expose matching proof,
stop slice acceptance at that boundary and repair or revise the plan based
on the failing operation. A green CI verdict or a local JSON file alone
cannot close this slice.

## Current decisions

- Reuse the existing matrix leg and the installed proof contract. The
  package artifact handoff and native probes publish different evidence.
  An independent proof job would rerun pytest, and log scraping would need
  new consumer logic. The installed collector already covers expectations,
  duplicates and attempt identity. [Recipe](../../../.agents/skills/dough-test-optimization/references/ci-proof-summary.md)
- Follow the recipe's GitHub Actions path (steps 3 to 6). Open Dough 0.3.86
  added a CI-adapter path for projects that set `ciAdapter`; Clipboard sets
  none and its judged CI is `ci.yml`, so the adapter `proof` operation and
  `--attempt-id` identity are out of scope. Copy the four modules from the
  0.3.86 install; name the attempt with `--run-id` and `--attempt`.
- Clipboard's planning and repository guidance identify no ADR catalog
  governing CI proof. The existing contract gives report production to
  Clipboard CI and artifact matching to Intent. Native interoperability
  remains independently evidenced under the project's North Star.
  [North Star](../../NORTH-STAR.md)

## Decisive premises

Observations on 2026-11-05 in the preparation worktree at `a545992e9`,
unless the row names a hosted run. At `526acfa23` (Open Dough 0.3.86), the
recipe's GitHub Actions steps 3 to 6 are textually unchanged, and the updated
collector's `summarize --run-id 1 --attempt 2 --expect tests=1` on an empty
directory again reported part 1 missing with zero counts and wrote the
GitHub identity fields `runId` and `runAttempt`.

| Consuming operation | Observation and result | Remainder |
| --- | --- | --- |
| `ci.yml` invokes the desktop-free suite on the representative leg | `gh run view 41951793311 --job 126997205688 --log` shows `uv run --locked --extra images pytest` on Linux, Python 3.13.14, pytest 9.2.0, with 770 passed and 33 skipped. The same workflow run lists the existing distribution and native artifacts. [Run](https://github.com/terryyin/clipboard/actions/runs/41951793311) | Verify the new reporting steps on the first branch run. |
| pytest XML feeds the installed collector without losing failed cases or mistaking collection for a completed report | Under `nix develop`, ran `uv run --locked --extra images pytest -o junit_family=xunit1 --junitxml=<scratch>/report.xml`, then converted the XML file paths and ran the installed `fragment` and `summarize --expect tests=1` commands. The full run gave 770 passed and 33 other, all cases with paths under `tests/`. The separate fixture yielded exit 1 and 1 passed, 2 failed, 1 other. The collection error yielded exit 2 and an XML error with a file path, so a file-existence gate would be insufficient. [pytest exit codes](https://docs.pytest.org/en/stable/reference/exit-codes.html) | The slice proves the implemented gate and checks the hosted Linux producer. |
| The collector and deployed reader select one attempt | The installed collector given an attempt-1 fragment and `summarize --attempt 2 --expect tests=1` excluded the fragment and reported part 1 missing. The deployed dashboard's `/__authenticated-read` returned proof unavailable for Clipboard run 41951793311, attempt 1. The same read for Open Dough run 41951088108, attempt 1, returned a summary with the matching revision and 196 passed checks under `tests`. A query for attempt 2 of that run found no summary. [Existing run with proof](https://github.com/terryyin/open-dough/actions/runs/41951088108) | The first branch run proves Clipboard's new artifact and its display. |
| The collector can summarize an empty attempt | Clipboard's existing download pin takes the pattern branch, filters the listed artifacts and permits zero matches. The installed collector ran against an empty directory with `summarize --attempt 2 --expect tests=1` and reported part 1 missing, with zero counts and no unit. A partial rerun can omit the producer or the collector, so proof remains scoped to the jobs that ran in that attempt. [Pinned download action](https://github.com/actions/download-artifact/blob/9000827ccba6bdab643e8b6fd33ac0654aef8333/src/download-artifact.ts), [GitHub rerun behavior](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs) | The slice exercises the implemented empty-attempt path and checks artifact transfer on GitHub. |

## Plan review

Slice-plan refinement was unnecessary. The existing producer, collector,
and dashboard read form one observable delivery with one proof owner.
No slice-specific concern remains outside that slice's hosted check.

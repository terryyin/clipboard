---
id: SEED-005
status: active
planted: 2026-11-07
scope: story
---

# Publish Clipboard test execution times in Intent

<a id="publish-ci-test-execution-times"></a>

### Publish Clipboard test execution times in Intent

**Identity:** SEED-005#publish-ci-test-execution-times
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/023-publish-ci-test-execution-times/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"368f2c259ac5dbab0813aba1eb09a4cd77615fd7ad66260598d501f5d9e8ec56","plan":"693f67912eefdd168d1aea6e1dc75e64862ef25af65a60dbb2c7c011961e92ef"}}
```

**Beneficiary:** A Clipboard maintainer investigating the runtime of the desktop-free pytest suite.

**Goal:** A Clipboard maintainer can see cumulative test execution time and a
per-file breakdown for the desktop-free tests in the selected CI attempt in
Intent, so they can locate runtime costs before considering test optimization.

**Scope:** Carry each pytest JUnit case's recorded duration and repository-relative
file path through the existing Ubuntu Python 3.13 fragment and attempt summary
into Intent's `tests` location and file views. Sum recorded case durations,
including failures and multiple cases in the same file; execution time means
the JUnit case times (including the phases pytest reports), rather than job
wall time. Convert seconds to milliseconds without inventing timing for cases
whose report supplies none. A recorded zero is measured; absent timing remains
explicit, and a partial sum is visibly incomplete.

Preserve outcome counts and the existing one-part representative-suite coverage,
attempt/revision matching, failure-path publication, missing/ambiguous evidence,
artifact naming and retention, and release-call gating. These protect against
double-counting matrix repetitions or attributing proof to the wrong attempt.
The collector still publishes one `ci-proof-summary-attempt-<n>` artifact.

Follow the [installed CI proof recipe](../../.agents/skills/dough-test-optimization/references/ci-proof-summary.md).

**Scope limits:** No test optimization, new native-probe or matrix coverage,
historical backfill, or Intent product changes. Explicit test-case/test-file
unit adoption remains in
[SEED-006](SEED-006-publish-explicit-ci-test-counts.md#publish-explicit-ci-test-counts);
this story preserves the existing outcome-count meaning while adopting the
collector's timing support.

**Key examples:**

- A completed representative CI attempt reports two cases from one file at
  0.125 and 0.250 seconds, with the second failing. Publishing and selecting
  that attempt shows both outcomes and 375 ms for that file; the failed case
  contributes its recorded time. The `tests` total sums the recorded case
  times across all its files once.
- A file reports one skipped case at zero seconds and another case without a
  duration. The outcomes remain counted, the recorded zero remains measured,
  and Intent exposes the untimed case and incomplete aggregate rather than
  presenting zero as the complete time.
- For an actual completed CI run, downloading its summary and comparing
  Intent's `tests` and representative-file views with that run's JUnit report
  gives the same outcomes and summed durations, allowing for display rounding.
  Another matrix leg or a release workflow call adds no repeated-suite proof;
  a missing report stays a proof gap.

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
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

**Beneficiary:** A Clipboard maintainer investigating the runtime of the desktop-free pytest suite.

**Goal:** Intent shows cumulative execution time and a per-file breakdown for the desktop-free tests in the selected CI attempt.

**Scope:** Carry pytest JUnit durations and repository-relative file paths into the
existing fragment from the Ubuntu Python 3.13 matrix leg. The existing CI
collector publishes one `ci-proof-summary-attempt-<n>` artifact, with that
leg representing the repeated desktop-free suite.

Follow the [installed CI proof recipe](../../.agents/skills/dough-test-optimization/references/ci-proof-summary.md).

**Acceptance:** For a completed run, the downloaded summary and Intent match the pytest
report's counts and timings for `tests` and a representative test file.
A failed case with a recorded duration still contributes evidence, and
missing timing stays explicit.

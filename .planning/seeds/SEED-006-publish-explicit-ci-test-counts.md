---
id: SEED-006
status: active
planted: 2026-11-09
scope: story
---

# See Clipboard test case counts in Intent

<a id="publish-explicit-ci-test-counts"></a>

### See Clipboard test case counts in Intent

**Identity:** SEED-006#publish-explicit-ci-test-counts
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

**Goal.** Clipboard maintainers can tell how many desktop-free pytest cases the
selected CI attempt recorded in Intent.

**Scope.** Adopt the new format in the existing proof publisher for the representative
Ubuntu Python 3.13 desktop-free pytest leg. Preserve the current scope of
CI proof, outcomes, file breakdown, and available timing.

Adopt once Open Dough publishes the explicit test case and test file units
and Intent can read the new format. See the [Open Dough protocol story](https://github.com/terryyin/open-dough/blob/b8fdb3a361899488e12828383afdea02cb545fda/.planning/seeds/SEED-281-distinguish-test-cases-and-files-in-ci-proof.md#distinguish-test-cases-and-files-in-ci-proof).

**Key examples.**

- The downloaded summary and Intent agree with the pytest JUnit report on
  case totals and outcomes for the suite and a representative file.
  Multiple reported cases in one file each count as a test case.

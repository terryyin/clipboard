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
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/023-publish-explicit-ci-test-counts/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"c261d164f6ae02d2eb061b6f559e3127ef5ff0e99522d522dbb2bd858a539212","plan":"1fb8b1500538790bc765e654b395ac717f60753c9744e668c8872624c4d83740"}}
```

**Goal.** Clipboard maintainers can tell how many desktop-free pytest cases the
selected CI attempt recorded in Intent, with counts explicitly labeled as test
cases at suite and file level.

**Scope.** Adopt Open Dough's released explicit-unit proof format in the existing
publisher for the representative Ubuntu Python 3.13 desktop-free pytest leg.
Each JUnit `testcase` contributes one case outcome, including parameterized
cases in the same file. Publish case totals and repository-relative per-file
case counts for the configured `tests` location. Keep passed, failed (including
case errors), other (including skips), and missing or ambiguous evidence visible.
Preserve attempt/revision matching, the pytest verdict, existing publication
gates, and any available timing and file detail.

**Required restriction.** Declare these outcomes as test cases. The number of
paths in a file breakdown is not a measured test-file outcome; publishing it as
one would misrepresent what pytest reported.

**Scope limits.** This increment adds no file-outcome measurement, extra matrix
or native-probe coverage, new Intent UI, or cross-build comparison feature.
Delivering JUnit durations remains with
[test execution times](https://github.com/terryyin/clipboard/blob/203e19d9a05f9ec29af4679ae61f46d9b2884791/.planning/seeds/SEED-005-publish-ci-test-execution-times.md#publish-ci-test-execution-times);
this adoption preserves timing if that work has landed, and leaves unavailable
timing explicit otherwise. Neither story requires the other's delivery.

**Prerequisite.** The shared protocol and Intent reader have shipped in Open
Dough 0.3.94 and are installed here. The
[protocol story](https://github.com/terryyin/open-dough/blob/b8fdb3a361899488e12828383afdea02cb545fda/.planning/seeds/SEED-281-distinguish-test-cases-and-files-in-ci-proof.md#distinguish-test-cases-and-files-in-ci-proof)
and its
[completion record](https://github.com/terryyin/open-dough/blob/main/.planning/done/SEED-281_distinguish-test-cases-and-files-in-ci-proof.json)
establish the supplier outcome. Clipboard owns this publisher migration.

**Key examples.**

- Given a completed representative CI attempt, downloading its summary and
  opening Intent's CI status shows the same suite and representative-file case
  counts and outcomes as that attempt's JUnit report, labeled as test cases.
- Given one file with two passing cases (including parameterization), one
  assertion failure, one case error, and one skip, publishing its completed
  pytest report yields 2 passed, 2 failed, and 1 other test cases for both the
  suite and that file. It does not claim one test-file result.
- Given no usable fragment for the selected attempt, or two fragments claiming
  the same part, the summary declares missing or ambiguous case evidence and
  counts neither stale nor duplicated results. Reporting cannot turn a failed
  pytest verdict into success.
- Given timing already supplied by the publisher, adoption retains it beside
  the same case counts and file paths. With no supplied timing, the summary
  exposes that gap instead of inventing a duration.

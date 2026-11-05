---
id: SEED-004
status: active
planted: 2026-11-05
planted_during: Terry Yin's request to prioritize CI proof adoption
trigger_when: A Clipboard developer reviews pytest outcomes for a CI run
scope: story
---

# SEED-004: Publish Clipboard CI proof for Intent

<a id="publish-clipboard-ci-proof"></a>

### Publish Clipboard CI proof for Intent

**Identity:** SEED-004#publish-clipboard-ci-proof
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/021-publish-clipboard-ci-proof/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"7cd77fbd34984ef62f14637137f88c71f4724b8dcc414a54eb5411c2b224021e","plan":"6d90a17c5344cd3d8293af4f1451032359faec830a3e8467935302cd1b263ee9"}}
```

**Goal**

A Clipboard developer reviewing an ordinary GitHub Actions run can see what
pytest reported for the configured `tests` location in **Intent → CI status**
and tell when the shown attempt has a gap in its evidence.

**Scope**

- Publish one summary for the shown attempt of the judged `ci.yml` workflow.
  Count the desktop-free pytest run from one existing, named matrix leg,
  Python 3.13 on `ubuntu-latest`. This is one repetition of the suite. The
  workflow verdict still reflects the other matrix legs, native probes and
  package checks.
- Count passed and failed test cases, including cases with setup or teardown
  errors, and report skips as other. Preserve pytest's exit status. When
  pytest cannot complete the suite or supply a usable report, show the part
  as missing if the collector runs. A cancelled or partial rerun that never
  runs the collector has no summary for that attempt.
- Defer per-platform, native and installed-distribution proof breakdowns.
  Keep the proof path separate from the release workflow's validation and
  distribution handoff.

**Key examples**

- The representative leg finishes with 770 passes and 33 skips → CI
  publishes one summary for that attempt → Intent shows `tests` with 770
  passed, zero failed, 33 other, and one reported part. These are example
  counts from a real run. [Clipboard CI run](https://github.com/terryyin/clipboard/actions/runs/41951793311)
- The representative leg completes with a failed test and writes a usable
  report → Intent includes the failure count and CI retains the failed
  test step's verdict.
- A setup step prevents pytest from running, or pytest aborts in collection
  → the collector declares the part missing. If a later attempt skips the
  representative leg, that attempt cannot inherit the earlier totals.

**Architecture**

Clipboard owns the report and artifact. Intent owns matching it to the shown
repository, run, attempt and revision, and displaying the result. The strongest
risk is a plausible total from the wrong attempt or from repeated matrix
runs. The collector declares one expected part independently of what arrives.
[Installed CI proof recipe](../../.agents/skills/dough-test-optimization/references/ci-proof-summary.md)

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

**Outcome:** A Clipboard developer can see pytest proof for the configured
`tests` location in the Open Dough dashboard's **Intent → CI status** tab.

Follow the [installed CI proof recipe](../../.agents/skills/dough-test-optimization/references/ci-proof-summary.md)
with [Clipboard's CI workflow](../../.github/workflows/ci.yml). Start with a
named representative matrix leg for the desktop-free pytest suite. The
matrix runs the same tests on multiple Python versions and operating
systems, so the first summary should count one leg rather than add all
repetitions. Keep native desktop probes and package checks running as before.

**Acceptance:** A real GitHub Actions run publishes one summary for its
attempt and the dashboard displays the matching pytest totals. A failed
test still contributes an outcome when the report exists. Missing proof
does not imply that a test passed.

# Source review for SEED-004#publish-clipboard-ci-proof

Launch: fresh general-purpose reviewer with no conversation inheritance;
source-only inputs (Goal, Scope, key examples, Architecture); no plan,
implementation return, product, or proof.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | A Clipboard developer reviewing an ordinary GitHub Actions run can see, in Intent → CI status, what pytest reported for the configured `tests` location. | slice 1 | |
| 2 | A Clipboard developer reviewing that run can tell when the shown attempt has a gap in its evidence. | slice 1 | |
| 3 | CI publishes one summary for the shown attempt of the judged `ci.yml` workflow. | slice 1 | observed: .github/workflows/ci.yml ci-proof job uploads ci-proof-summary-attempt-${{ github.run_attempt }} |
| 4 | That summary counts the desktop-free pytest run from one existing, named matrix leg: Python 3.13 on `ubuntu-latest` (one repetition of the suite). | slice 1 | observed: .github/workflows/ci.yml WRITE_CI_PROOF only when matrix.os==ubuntu-latest && matrix.python==3.13 |
| 5 | The workflow verdict continues to reflect the other matrix legs, native probes, and package checks (they are not collapsed into this summary’s counts). | slice 1 | observed: .github/workflows/ci.yml ci-passed still requires quality, full tests matrix, and native jobs; proof counts only tests=1 |
| 6 | The summary counts passed test cases. | slice 1 | observed: local pipeline under tests/: summarize passed=1 from status cases; scripts/junit-outcomes.py passed path |
| 7 | The summary counts failed test cases, including cases with setup or teardown errors. | slice 1 | observed: local pipeline: fixture error and assertion failure both status failed in outcomes and summary failed=2 |
| 8 | The summary reports skips as other. | slice 1 | observed: local pipeline: skip → other in outcomes and summary other=1 |
| 9 | The summary preserves pytest’s exit status. | slice 1 | observed: .github/workflows/ci.yml pytest step exits with captured status; local STATUS=1 retained through gate |
| 10 | When pytest cannot complete the suite or supply a usable report, and the collector runs, the part is shown as missing. | slice 1 | observed: collection exit 2 gated (no fragment); empty/earlier-attempt summarize → part 1 missing with zero counts |
| 11 | A cancelled or partial rerun that never runs the collector has no summary for that attempt. | slice 1 | observed: .github/workflows/ci.yml ci-proof if !cancelled(); cancelled collector never uploads that attempt summary |
| 12 | Per-platform, native, and installed-distribution proof breakdowns are deferred (out of this story’s scope). |  | G1 |
| 13 | The proof path stays separate from the release workflow’s validation and distribution handoff. | slice 1 | observed: .github/workflows/ci.yml proof steps and ci-proof job skipped when inputs.release-tag != ""; release.yml remains caller only |
| 14 | Clipboard owns the report and artifact. | slice 1 | observed: scripts/ci-proof-*.mjs + junit-outcomes.py and workflow artifact uploads in this repository |
| 15 | Intent owns matching the summary to the shown repository, run, attempt, and revision, and displaying the result. | slice 1 | observed: ci-proof summarize writes repository, runId, runAttempt, revision for Intent matching (Intent displays) |
| 16 | The collector declares one expected part independently of what arrives. | slice 1 | observed: .github/workflows/ci.yml summarize --expect tests=1 declares one part independently of fragments |
| 17 | Native interoperability proof remains independently evidenced under the project’s North Star and is out of this story’s deferred scope. |  | G2 |

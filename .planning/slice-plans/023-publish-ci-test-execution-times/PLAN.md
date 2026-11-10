# Publish Clipboard test execution times in Intent

**Identity:** SEED-005#publish-ci-test-execution-times
**Source:** [Refined story](../../seeds/SEED-005-publish-ci-test-execution-times.md#publish-ci-test-execution-times)

**Source review:** [Independent source commitments](source-review.md)

## Goal and scope

Publish cumulative JUnit case execution time and file breakdowns through the
existing representative desktop-free proof part, so a maintainer can inspect
the selected attempt's suite and file runtime in Intent. Include failed-case
durations, repeated cases in one file, measured zero, and explicit untimed
results. Preserve counts, proof coverage and attempt identity.

No optimization, extra native/matrix proof, historical backfill, Intent code
changes, or explicit case/file unit adoption (SEED-006 owns the latter).
Preparation authorizes no implementation; execution requires its own instruction.

## Existing solution and current decisions

- PFE: `.github/workflows/desktop-free-tests.yml` already produces xunit1
  JUnit on Ubuntu Python 3.13; `scripts/junit-outcomes.py` owns conversion.
  `scripts/ci-proof-*.mjs` own fragments and collection; `ci.yml` owns the
  attempt artifact. Extend this path, rather than add a second publisher.
- Follow the [installed recipe](../../../.agents/skills/dough-test-optimization/references/ci-proof-summary.md).
  Copy its seven collector modules unchanged into `scripts/`. They support
  `--times` and `--by-file`, validate evidence, and retain timing in collection.
  No local fork of their aggregation or schema rules is needed.
- Keep outcomes as legacy results for this story: no `--unit` on fragment
  production and keep `--expect tests=1`. The current collector emits schema 2
  with legacy evidence, which the deployed Intent reader accepts. Adoption
  of the collector is necessary for timing; declaring case/file units is deferred.
- Emit an outcome per reported case and, when measured, a seconds/path timing
  row for that same case. Repeated file paths are intentional. Missing timing
  emits no timing row; never synthesize zero. JUnit's case times are the source
  of truth, including pytest's reported phases, not testsuite or job wall time.
- Preserve repository-relative paths. Retain the existing refusal of reports
  without usable file attribution and the global-error/no-report gap behavior.
  Malformed input must not manufacture complete, successful timing evidence.
- Preserve `!cancelled()` failure-path publication, pytest exit-status handling,
  the single representative part, release-tag gating, revision/attempt keys,
  artifact names, one-day fragments and 30-day summary retention.
- Retain the representative run's source JUnit beside its fragment for the
  existing one-day fragment retention, so hosted proof can compare the report
  with the downloaded summary. The summary artifact still holds only
  `ci-proof-summary.json`; the collector reads fragment JSON, not the XML.
- `.planning/NORTH-STAR.md` concerns public clipboard content APIs and does not
  govern this existing CI reporting path. No new architectural boundary or
  Accepted-ADR decision is implicated; no new direction record is needed.

## Outside-in proof ownership

All promises below belong to slice 1. New fixtures must observe the project's
converter and copied collector through their real command-line boundaries.

| Promise | Observable proof |
| --- | --- |
| Suite and file totals match the selected attempt's JUnit | Fixture XML → converter → `fragment --times --by-file` → `summarize`; hosted JUnit/summary comparison and Intent suite/file observations |
| Multiple cases in one file and failure timing are included | Two same-file cases at 0.125/0.250 seconds, second failed: counts 1 passed/1 failed and 375 ms for file and suite |
| Missing time is explicit; zero is measured | Add a zero-duration skipped case and an untimed case in another file: preserve outcomes, 1 untimed, partial aggregate; all-untimed variant has no invented duration |
| Wrong or missing evidence stays a gap | Focused CLI check for absent report/fragment and wrong attempt or revision; no complete zero-time claim |
| Repeated matrix suite and release calls do not add proof | Workflow gate review plus `make lint-workflows`; actual attempt summary has exactly one representative part |
| Intent reflects the artifact, including incompleteness | Deployed reader replay for deterministic mixed fixture; actual completed run selected in Intent for `tests` and a representative file, allowing display rounding |

## Ordered slices

### 1. Inspect desktop-free suite and file execution time from a CI attempt
Type: Behavior
Status: planned
Proof: All rows above, using the real converter and collector CLI plus a
completed hosted attempt and Intent observations.

Behavior: Given a representative pytest run with JUnit case paths and optional
durations, publishing and selecting its attempt lets the maintainer see the
same outcomes and summed timing for `tests` and individual files, with untimed
results visibly incomplete.

- Refresh the collector copies together. Extend the converter to write the
  matching timing report while retaining its outcome mapping. Update producer
  wiring with `--times` and `--by-file`; retain source XML for the hosted proof.
- Add focused Python converter regression tests, including repeated paths,
  failure/error outcomes, missing duration and measured zero. Exercise the
  complete copied CLI pipeline with deterministic fixtures, rather than only
  testing an imported aggregation helper. Establish a red observation before
  accepting the implementation.
- Keep Node-based pipeline verification in the producer after its existing
  pinned Node setup, or explicitly provision Node if adding such verification
  to another test entry point. Default desktop-free pytest must remain usable
  on every matrix OS; do not add an undeclared Node requirement to it.
- Update `docs/development.rst` and the CI-proof paragraph in `AGENTS.md` with
  the lasting timing meaning, representative leg, source-report location and
  evidence gaps. Leave planning identities out of product code/tests/docs.
- Apply post-change refactoring and affected-consumer tracing before commit.
  The touched converter/workflow/docs and all seven replacement modules are
  currently at most 250 lines; no oversized-file reorganization is needed.
- Local checks use Nix per `AGENTS.md`: focused converter pytest, the real
  fixture-to-summary CLI replay, `nix develop -c make check`, and
  `nix develop -c make lint-workflows`. The broad Python check also covers new
  tests in the default suite. No package build gate is added for CI-only edits.
- Publish under the execution workflow and retain its CI ownership. Download
  the accepted candidate's completed `ci.yml` summary and representative
  fragment/JUnit artifacts with `gh run download`; verify run/attempt/revision,
  one part, total/file outcomes, summed seconds × 1000, untimed counts and
  summary size below Intent's 1 MiB limit. A failure-path fixture proves failed
  cases without deliberately breaking shared CI.
- Perform bounded Intent observation under dough-manual-testing: select that
  exact completed attempt, inspect `tests` and a representative file, and
  compare their displayed timing/outcomes with the downloaded source XML and
  summary. Reuse deterministic reader replay for the partial-time boundary.
  A UI or hosted evidence failure leaves that promise open; diagnose the
  project publication path before proposing any out-of-scope Intent change.

Safe stopping point: the candidate's CI summary and Intent views supply the
promised timing; all required CI and execution closure remain with their
normal owners. Updating collector files alone is not a delivery boundary.

Sizing: one cohesive Behavior and proof loop, M with moderate confidence due
to hosted/UI verification. No numeric slice target or limit is supplied.
Hosted CI is an external wait; it does not justify fragmenting this outcome.

## Decisive premises and observations

Observed 2026-11-10 in the established workspace at `de778d3`, with scratch
files removed before recording preparation. These observations establish the
route and current behavior, not implementation or completed-story proof.

| Premise / consuming operation | Form, profile and result | Unverified remainder |
| --- | --- | --- |
| pytest supplies case seconds and relative file paths | `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py -o junit_family=xunit1 --junitxml=<scratch>/pytest.xml -q`: 27 passed; every case named `tests/test_clipboard.py` and nonnegative seconds. Existing converter CLI produced 27 outcome rows without timing. Pinned pytest's `junitxml.py` uses total phases by default. | Ubuntu's complete suite is checked by slice 1's hosted proof; this macOS sample establishes the pinned runner's report shape, not Linux runtime values. |
| Copied collector accepts this story's legacy flags and preserves timing | Temporary unchanged copies of the seven installed modules: `nix develop -c` Python harness invoked `node <scratch>/ci-proof-summary.mjs fragment --outcomes <rows> --times <seconds-path-rows> --by-file --entry tests --part 1 --of 1 --attempt 1 --revision <40 a characters> --out <fragments>`, then `summarize --fragments <fragments> --expect tests=1 --repository terryyin/clipboard --run-id 1 --attempt 1 --revision <same> --out <summary>`. Real report: 27 passed, 548 ms, 0 untimed. Mixed fixture: 2 passed/1 failed/1 other, 375 ms, 1 untimed; repeated paths aggregate once per case. | Project converter and workflow implementation remain slice 1's work. |
| Current deployed Intent consumes schema 2 legacy timing and file breakdowns | Active port 4173 process identifies deployment `5d31d9fb7d4e-lZlnvn`. From this workspace, the same scratch harness ran `nix develop -c node --experimental-strip-types --input-type=module -e <reader-replay> <summary> <real-or-mixed>` importing that deployment's `ciProofSchema`, `scopeFiguresOf`, `entryTimingOf` and `scopeTimingOf`. Both summaries parsed; suite and each file matched artifact timing; real classified measured, mixed classified partial, timed file measured. | Actual uploaded candidate and rendered UI are final slice proof; this replay does not claim the UI was observed. |
| Authenticated hosted artifact route works and baseline lacks timing | `nix develop -c` Python harness ran `gh run list --repo terryyin/clipboard --workflow ci.yml --status success --limit 1 --json databaseId,headSha,conclusion`, then `gh run download 42729161183 --repo terryyin/clipboard --pattern ci-proof-summary-attempt-* --dir <scratch>`. Attempt 1 at `ece61744bae9073ed4483f6abcaee9645b1f231f` downloaded and matched revision: schema 1, one present part, 776 passed/0 failed/33 other, no timing or files. | The changed candidate needs its own hosted proof. Existing workflow does not retain raw JUnit; slice 1 adds that necessary observation input. |

## Consumer trace and proof boundaries

Search across `scripts/`, `.github/`, `tests/`, docs and planning found one
production converter caller: the desktop-free workflow. Its fragment artifact
feeds the `ci.yml` collector; the summary feeds Intent and installed
dough-test-optimization reads. There are no project reporting regression tests
to reuse. All collector copies must change together, with producer/collector
flags kept compatible and representative failure/report gates preserved.
Default pytest consumers need portable converter tests; Node-only verification
must not make their environment implicitly depend on Node. Clipboard runtime
and native probes do not consume these report formats and need no new native
verification for this story. The execution consumer-trace command owns the
final diff-based trace and dispositions.

## Preparation concern assessment

Slice-plan refinement was not needed: one outcome, one common case-to-file
aggregation rule, one outside-in proof loop, and no independent Structure work.
No remaining blocking concern or human-owned pre-Take decision. Hosted upload
and rendered Intent observations are the slice's final proof, not facts claimed
by preparation. No paid or developer-only premise probe is needed.

## Learnings

The installed timing-capable collector also introduces schema 2's unit
partitioning. Omitting unit declarations preserves legacy count meaning, and
the active Intent deployment accepted that exact profile in the scratch replay.

## Execution context

- Established story-branch execution: Nana-chan, publisher `dashboard-territory.local-clipboard`, checkout `/Users/terryyin/git/clipboard/.worktrees/publish-clipboard-test-execution-times-in-intent`, branch `codex/publish-clipboard-test-execution-times-in-intent`; integration/default checkout `/Users/terryyin/git/clipboard` is a separate role, not an implementation location.
- Authorized remote `origin`, trunk `master`; claim/base `85d7aa880d0b92fbca7d1bb6a789bb6b5974da2a`, starting revision `ee49e04b71036b2c86e8f658bd284fa8ef75e688`. Remote trunk and story branch both confirmed at the claim.
- Setup: `nix develop -c make deps` completed against unchanged `uv.lock`; `nix develop -c make lint` passed (240 formatted Python files). No active Git hooks or selective formatter beyond project Python formatting.
- CI source GitHub Actions `ci.yml` (verified workflow 403397948, name CI), story-branch target. Trunk claim CI is unobserved. Codex observer key `ci-watch-execution:terryyin/clipboard:codex/publish-clipboard-test-execution-times-in-intent:nana-chan-timing`, coordinator `nana-chan-timing`, directory `/tmp/dough-ci-501/watch-iyOdnX`, PID 90699, stream session 69256, yielded cell `g814:9`, selected checkout above.
- Replanning: existing planning authority retained; no numeric slice budget supplied, one M slice. Use existing premise evidence; the hosted and rendered observations remain open. Local Python and fixture checks are bounded ordinary proof; no expensive benchmark or competing owned heavy verification is known.

## Slice 1 local acceptance and progress publication

- Source review and actual CLI assertions inspected. `tests/test_junit_outcomes.py` covers outcome/path mapping, failure/error, repeated paths, measured zero, absent time, malformed time/path, missing report and no partial output for a later global error. Pre-change observation: 16 failed / 3 passed; implementation: 19 passed via `nix develop -c uv run --locked pytest tests/test_junit_outcomes.py -q`.
- `nix develop -c uv run --locked python scripts/check_ci_proof_pipeline.py --out /tmp/clipboard-timing-replay` passed the real XML→converter→fragment→summary chain. Same-file 0.125 passed and 0.250 failed sum to 375 ms; another file carries measured zero and one untimed result. All-untimed has no duration, wrong attempt/revision and missing input stay missing, duplicates stay ambiguous, and retained XML adds no part. Legacy result counts and one representative part remain.
- `nix develop -c node /tmp/clipboard-timing-reader-replay.mjs` passed installed reader/schema/scope/ranking checks including partial wording, zero and refusal of wrong identities. The deployed reader is being rechecked because port 4173 now uses deployment `83fdfec494d8-oDeg04` rather than preparation's deployment.
- `nix develop -c make tests`: 795 passed, 33 gated native skips. `nix develop -c make lint-workflows` and `git diff --check` passed. Guarded preparation will perform selective formatting and the required complete `make check`.
- Consumer trace: `/tmp/clipboard-timing-consumer-trace.md`, generated with `nix develop -c node .agents/skills/dough-execute-plan/scripts/consumer-trace.mjs --checkout /Users/terryyin/git/clipboard/.worktrees/publish-clipboard-test-execution-times-in-intent --base HEAD --term junit-outcomes.py --term durationMs --term ci-proof-summary --term ci-proof-junit.xml --term untimed`. All rows have dispositions. The unchanged production consumer `ci.yml` is exercised by the real collector replay and inspected for one summary, legacy expectation, identity, retention and release gates; hosted acquisition remains G1. Installed read consumers have the reader replay. Guidance/template copies and planning/navigation references do not execute project scripts.
- Independent `/root/refactor_timing` inspected all touched concepts, callers and proof, returned `none — already clean` and `## REFACTOR COMPLETE`; no edits or invalidated proof. Seven collector files byte-match the recipe, all product files <=250 lines.
- Early source-freshness settlement: unchanged at base/trunk `85d7aa880d0b92fbca7d1bb6a789bb6b5974da2a`. Named sibling SEED-006 has no incoming accepted product change at that pinned trunk, so no reconciliation hold.
- Manual mission: up to 15 minutes for exact-attempt suite/file timing/outcomes and artifact comparison, prioritizing suite then representative file, with reserve for evidence gaps. CUA browser discovery returned “browser access host is unavailable”; app inventory succeeded but native Chrome selection timed out after 300 seconds. No rendered observation is claimed. One developer round may be needed once hosted values are known.
- This is progress only: retain `Status: planned`, hosted G1 and rendered G2 before accepting the slice.

## Story obligations

### G1. Hosted attempt and source-report comparison
Reported: slice 1 — "Implementation returned local CLI proof; the published candidate's completed CI artifact and JUnit comparison remain unobserved."
Story clause: "For an actual completed CI run, downloading its summary and comparing Intent's `tests` and representative-file views with that run's JUnit report gives the same outcomes and summed durations, allowing for display rounding."
Disposition: return

### G2. Rendered Intent suite and file views
Reported: slice 1 — "CUA browser access is unavailable and native Chrome selection timed out, so no actual completed attempt has been selected and observed in Intent."
Story clause: "A Clipboard maintainer can see cumulative test execution time and a per-file breakdown for the desktop-free tests in the selected CI attempt in Intent"
Disposition: return

## Deployed-reader remainder

Deployed-reader remainder settled: `nix develop -c node --experimental-strip-types /tmp/clipboard-deployed-intent-reader-replay.mjs` passed against active deployment `83fdfec494d8-oDeg04`. Inspected schema, scope figures and displayed wording assertions: 375 ms suite/file, failed case included, legacy counts, zero measured, untimed partial, no invented all-untimed duration, gap states preserved. G2 still owns actual rendering. Pre-delivery freshness again unchanged at 85d7aa8; sibling SEED-006 remains unlanded, no incoming behavior to reconcile.

Guarded preparation completed selective Ruff formatting, `nix develop -c make check` (lint and desktop-free suite) and `nix develop -c make lint-workflows` successfully before its subsequent record-shape guard refused the trailing paragraph attached to G2. The disposition paragraph is now separated by a proper section heading; product proof remains valid. Earlier formatting attempts stopped on long lines before commit; final string wrapping was mechanical.

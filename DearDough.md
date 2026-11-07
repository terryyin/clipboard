# DearDough Process Findings

## Retention

- Highest allocated local number: 30
- Shared-feedback adoption and compaction recovery (2026-11-07): `e314ecd7b16f1c86970d352d9db043da243ac144:DearDough.md`; shared rows are retained at the linked Open Dough finding owners (`483d3a1e8f0ea24b929675b9a195faca48ac8f47:docs/maintainer/findings/`).
- Shared-feedback adoption and compaction recovery (2026-11-04): `9e36c067e012371aa207d9b469a3fc0a23e3ccdf:DearDough.md`.
- Shared-feedback compaction recovery (2026-11-03): `e2b98b77c9d0b467e610bdc27fe513a4061431ef:DearDough.md`; shared rows are retained at the linked Open Dough finding owners.
- Consolidation (2026-11-03, approved): DD-003, DD-004 and DD-013 are consolidated under ODF-074 with former-code aliases. Recovery: `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`.
- Ownership: project-owned findings (cause in Clipboard's own code, tests, configuration or CI workflow) live in [ProjectFindings.md](ProjectFindings.md); DD-001, DD-005 and DD-010 moved there on 2026-11-03 (recovery: `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`). `DD-NNN` numbering is shared across both files; the highest allocated local number above covers both.

## ODF-414 — Settled no-session premise still ran three Behavior deliver cycles

Former local code: DD-002.

When a plan's decisive premise already settles that the execution checkout cannot
host the remaining desktop sessions, splitting each desktop's authorized
evidence-limit path into its own Behavior slice still incurred a full
implement → obligations/source-review → refactor → publish cycle per desktop
before the consolidation Structure slice, without new native measurement.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-414](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-414.md); source recovery remains in this project’s pre-compaction revision.

## ODF-074 — Native-venue helper and probe premises entered gated CI unverified
Former local code: DD-003.
Former local code: DD-004.
Former local code: DD-013.

Consolidated 2026-11-03 (approved): the three local findings share the ODF-074
problem — native-venue helper, compositor or probe-scaffolding premises were
first observed through published gated-CI runs and repaired through extra CI
round trips. Each keeps its distinct meaning below. Pre-consolidation recovery:
`cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`; full pre-compaction
occurrence rows: `e2b98b77c9d0b467e610bdc27fe513a4061431ef:DearDough.md`.

### Former DD-003 — Linux X11 clipboard ownership learned through gated-CI repair loops
For Linux image write under Xvfb, successive published repairs rediscovered that
`xclip` must stay as CLIPBOARD owner (do not wait for exit), stdin ingest must
not race tempfile deletion, and return must wait until TARGETS lists
`image/png` — knowledge that could have been a decisive early premise before
the gated job was treated as green-or-repair.

### Former DD-004 — Wayland CI compositor chosen without wl-clipboard protocol check
The first Wayland gated job used Weston headless; `wl-copy` failed because
Weston lacks wlr-data-control. Retargeting to Sway (`WLR_BACKENDS=headless`)
fixed proof, after one failed compositor choice.

### Former DD-013 — Native probe scaffolding assumptions failed on the first gated run
New gated probes asserted facts the runner could not supply or used stand-ins
that did not observe the promise: an Xvfb version floor not readable by
`Xvfb -version`, a Windows clipboard holder opened with a NULL window (which
pyperclip's own NULL open shares and closes), and `Get-Clipboard` standing in
for Notepad. Each cost a full CI round trip although the product passed.

Ownership note: local triage called DD-013's relationship to ODF-074 borderline
(probe facts and stand-in consumers asserted before any runner observation), so
its shared-cause claim remains qualified.

### Occurrences
Three distinct executions; DD-003 and DD-004 share one execution, counted once:
- SEED-001#write-images (Cursor, Open Dough 0.3.79) — DD-003 X11 ownership
  repairs (2026-11-02T14:00:07+07:00) and DD-004 Weston→Sway retarget
  (2026-11-02T14:25:25+07:00).
- SEED-001#portable-text (Claude Code, 0.3.82, 2026-11-02T23:37:16+07:00) — DD-013
  Xvfb floor and Windows holder/consumer probe repairs.
- SEED-001#copy-files (Claude Code, 0.3.82, 2026-11-03T08:40:19+07:00) — DD-013
  PowerShell FileDropList reader assumption.
- SEED-001#x11-clear-packaged-apps (Claude Code, claude-opus-5-5, 0.3.82,
  2026-11-04T04:34:03Z) — shared facet of [DD-025](ProjectFindings.md#dd-025):
  plan 016 Decisive premise 3 (`8ffb85613222db6e76068115adf4bae0bd22fdb0:.planning/slice-plans/016-x11-clear-packaged-apps/PLAN.md`)
  predicted CI Linux would classify the installed X11 clear helper as `display`
  after observing only macOS (`libx11`), without exercising the CI job's `nix develop`
  shell (where `libX11` was absent until `9f5e5ff` / `a7c6e5a`, costing a human
  decision stop and three extra commits/CI waits). The repository's Nix dev-shell
  `libX11` configuration stays once in [ProjectFindings.md](ProjectFindings.md#dd-025).

Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-074](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-074.md); source recovery remains in this project’s pre-compaction revision.

## DD-006 — Stop for venue decision when mandatory native proof cannot run locally
When Linux writer-exit probes were story acceptance (issue #5) and the Darwin
checkout could not observe them, execution stopped for an explicit developer
choice (GHA vs skip) instead of inventing an evidence-limit completion or
silently weakening the bar.

### Occurrences
- Execution: SEED-001#write-images
  - Timestamp: 2026-11-02T13:44:00+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: transcript ed9de93f… DEVELOPER ATTENTION on slices 4–5; user reply “skip… or use github actions”; plan Current decisions updated to gated GHA; skip rejected
  - Observed effect: Plan venue revised under approval; Linux acceptance preserved via gated jobs rather than skip or unauthorized limits.
  - Inference: Useful practice — mandatory native proof that the checkout cannot run is a human venue decision, not an agent-chosen evidence-limit substitute.

## ODF-415 — Pre-existing over-limit module surfaced only at the first refactor stop

Former local code: DD-007.

A module already over the refactor file-size limit before the story (470 of
250 lines) was not named as a premise during planning, so the first slice's
post-change refactor stopped for a structural developer decision (package
split) after implementation was done.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-415](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-415.md); source recovery remains in this project’s pre-compaction revision.

## DD-008 — Prior native-venue findings reused; every gated CI probe passed first run
Reusing the project's recorded native venues (Xvfb with an owning xclip,
headless Sway for wl-clipboard) and their findings let three new gated probe
jobs pass on their first published run, with no CI repair cycle.

### Occurrences
- Execution: SEED-001#read-html
  - Timestamp: 2026-11-02T16:41:56+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.79
  - Evidence: slice 4–6 delegation briefs cite the `native-linux-x11-copy-image` / `native-linux-wayland-copy-image` precedent; CI runs 41422813085 (X11), 41424913377 (Wayland), 41427386442 (Windows) succeeded on first attempt; contrast DD-003 / DD-004 repair loops
  - Observed effect: No CI repair commits in this execution; each native slice published a progress increment, then a records-only done commit after observing CI.
  - Inference: Useful practice — carry earlier DearDough helper/compositor findings into native-probe delegation briefs. The `windows-latest` runner also proved to have a usable clipboard session, contrary to an earlier README judgment.
- Execution: SEED-001#desktop-helpers
  - Timestamp: 2026-11-02T21:41:26+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: tip SHA 2b06eb3 CI run https://github.com/terryyin/clipboard/actions/runs/41464367130 success on first attempt including native-windows-paste-html, native-linux-x11/wayland paste_html and copy_image; intermediate published SHAs 1b9ed68, 98daafa, 75d3909 also coverage-success with no repair commits; observer `/tmp/dough-ci-501/watch-Xh83iA`; contrast DD-003 / DD-004
  - Observed effect: Structure relocation of session/listing helpers landed with no CI repair; five-job native confirmation stayed green while later slices continued under observation
  - Inference: Useful practice — reuse the same Xvfb/Sway venues and fail-not-skip native wrapper pattern when relocating desktop helpers; first-run green held for session-selection proof that desktop-free pytest cannot cover
- Execution: SEED-001#clear-clipboard
  - Timestamp: 2026-11-03T14:02:39Z
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: unknown
  - Evidence: slices 3–6 each published a `progress: true` increment (342f12c, 0da29c3, c16d2c1, 8a7368d) then a records-only done commit with observed CI values (81ab56e, f93e1b4, 8184a23, e0c0643); runs 41649816028, 41651498162, 41654014945, 41658893626 had every native clear probe (X11, Sway, windows-latest) pass on its first run; the plan's "early probe at the start of the slice" became the probe's first step in the same increment, because an implementation agent cannot publish
  - Observed effect: No probe or product CI repair in six slices; each CI wait took about 10–15 minutes while the next slice waited
  - Inference: Useful practice holds; plans that schedule a CI-only premise "before" implementation should expect it to run inside the first published increment
- Execution: SEED-001#shared-native-clear-proof
  - Timestamp: 2026-11-03T23:47:15Z
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: slice 2 progress increment f071961 → run 41741871109 (X11, Sway, windows-latest clear) success first run → records-only done 511bef4; slice 3 delegated while that run was queued, published 147119b → run 41742684361 success → done 16260fd; slice 4 macOS live probe ran locally during slice 3's CI
  - Observed effect: Structure refactor of all four native clear probes landed with no CI repair; the next slice's implementation overlapped each CI wait instead of idling 3–4 minutes
  - Inference: Useful practice — when remaining slices touch disjoint files, delegate the next slice while the previous progress increment's native CI runs; each records-only done commit still costs one extra full CI run (~3 min here)
- Execution: SEED-001#bounded-helper-owner-write
  - Timestamp: 2026-11-04T16:17:17+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: slice 1 progress increment 7d55a1b → run 41802978191 (all 26 jobs incl. Native Linux X11 copy_image / text / copy_files) success first run → records-only done 0cd07be; slice 2 progress 1f75f4a → run 41805764901 (Sway copy_image / text / copy_files) success first run → records-only done 16e6241; both plan "early probes" (exact `image/png` read-back, `wl-copy` regular-file stdin) ran inside the first published increment
  - Observed effect: No CI repair; each slice's done status cost a records-only publication and its own full CI run; slice 2 was not overlapped with slice 1's CI because the plan gated slice 2 on the X11 probe outcome
  - Inference: Practice holds; overlap is unavailable when a plan makes the next slice depend on the previous probe's result
- Execution: SEED-001#primary-selection-polish
  - Timestamp: 2026-11-05T05:51:00+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: progress increment `90a8e7b` → run 41928637574 success first attempt including Native Linux Wayland text (Sway PRIMARY) and Native Linux X11 text (Xvfb); records-only done `03a223d`; no native repair commits; observer `/tmp/dough-ci-501/watch-UZnVa9`
  - Observed effect: Renamed Wayland PRIMARY steps and shared `evidence_limit` helpers landed green on the first product publish; no CI repair cycle
  - Inference: Practice holds for a wording/evidence polish that reuses the same Xvfb/Sway text jobs rather than adding new venues

## ODF-258 — Producer-kind gap carried three slices before developer decision

Former local code: DD-009.

The story's "browser or rich editor" producer wording could not be met by the
authorized CI venues; the gap was recorded at slice 4 as an interim obligation
and only put to the developer before slice 7, after Wayland and Windows used
the same helper-producer pattern.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-258](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-258.md); source recovery remains in this project’s pre-compaction revision.

## DD-011 — Stop for authorization before cross-subsystem package split
When the 250-line refactor check required splitting an oversize module into a package that also moved delivered sibling seams, execution stopped for an explicit developer choice instead of splitting without authority or deferring silently.

### Occurrences
- Execution: SEED-001#read-files
  - Timestamp: 2026-11-02T17:02:13+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: coordinator transcript eb2ce85d… DEVELOPER ATTENTION on clipboard.py 517 lines / 250-line gate; user authorized option 1 package split; commit acb5e62 (injectable seam + `clipboard/` package); PLAN.md Learnings slice 1
  - Observed effect: Slice-1 delivery paused until human authorization; authorized split preserved public `import clipboard` / `VERSION` and unblocked later slices
  - Inference: Useful practice — file-size fixes that cross delivered subsystem seams are human-owned packaging decisions, parallel to venue stops for mandatory native proof (DD-006)
- Execution: SEED-001#primary-selection-polish
  - Timestamp: 2026-11-04T22:49:00+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: coordinator DEVELOPER ATTENTION after refactor stop on `README.rst` (1016 / 250); options included packaging split vs defer; user reply `1`; authorized split kept `pyproject.toml` `readme = README.rst` as a short landing and moved Usage / Evidence / Development under `docs/*.rst` (each ≤250)
  - Observed effect: No unauthorized docs packaging change; after authorization the split completed and product delivery resumed
  - Inference: Useful practice holds for a documentation-home split that preserves the packaging entry point while clearing the file-size gate
- Execution: SEED-004#publish-clipboard-ci-proof
  - Timestamp: 2026-11-05T19:23:00+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.86
  - Evidence: coordinator DEVELOPER ATTENTION after refactor stop on `.github/workflows/ci.yml` (593 / 250; already 503 before the slice); options authorized multi-seam split vs defer/exception; user reply `1`; authorized extract of native X11/Windows bodies and desktop-free tests/proof into reusable workflows
  - Observed effect: No unauthorized CI packaging change; after authorization the split completed (`ci.yml` 241 lines) and progress delivery resumed
  - Inference: Useful practice holds for a judged-workflow split that crosses native and desktop-free CI seams while clearing the file-size gate

## ODF-416 — progress:true left mid-plan Behavior slice unfinished until local-proof done commit

Former local code: DD-012.

Publishing the first Behavior increment with `progress: true` kept the slice
`planned` until CI confirmation, which blocked continuing the plan; marking the
slice done on accepted local proof required a second records-only commit and
cancelled the still-running CI for the superseded implementation SHA.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-416](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-416.md); source recovery remains in this project’s pre-compaction revision.

## ODF-289 — Cancelled CI jobs attributed to supersession before checking runner acquisition

Former local code: DD-014.

A failed `CI passed` with cancelled macOS jobs was first reported as
supersession by the next push; the jobs had zero steps and a GitHub annotation
"The job was not acquired by Runner of type hosted", which the coordinator
found only when the same pattern recurred on the next run.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-289](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-289.md); source recovery remains in this project’s pre-compaction revision.

## ODF-141 — Fresh refactor agent for small CI repairs returned no change

Former local code: DD-015.

Delivery required an independent refactor agent before every publication; for
three small repairs or proof-only changes it reported "none — already clean"
after reading the same context again.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-141](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-141.md); source recovery remains in this project’s pre-compaction revision.

## ODF-097 — Source-freshness check chained into delivery ignored a conflict

Former local code: DD-016.

The Story Branch source-freshness check ran in the same shell command as the
guarded delivery, so its `conflict` result was printed but not acted on, and a
plan record contradicting trunk's newer evidence was published.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-097](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-097.md); source recovery remains in this project’s pre-compaction revision.

## ODF-403 — Branch plan notes next to trunk-amended lines kept freshness in conflict

Former local code: DD-017.

Branch-only plan additions placed directly after a trunk-rewritten Learnings
paragraph made the three-way freshness comparison report `overlapping-edit`
even after trunk's text was taken verbatim, twice in one execution.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-403](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-403.md); source recovery remains in this project’s pre-compaction revision.

## ODF-408 — Developer-operated desktop rounds requested while the developer was away

Former local code: DD-018.

Slice 3's Finder paste was planned as a developer-operated round. Three
question rounds were sent; the developer later said they were not at the
computer and asked the agent to proceed itself, and the screen was locked
(`CGSSessionScreenIsLocked: true`), so Finder ignored Apple Events and the
paste could not be observed.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-408](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-408.md); source recovery remains in this project’s pre-compaction revision.

## ODF-259 — CI observer budget expired while the next slice was still open

Former local code: DD-019.

After slice-1 publish, the retained CI observer's budget expired during a long
or interrupted next-slice delegation, so the coordinator continued delivery
without promised monitoring on the prior SHA until the next publish reattached
observation.

Ownership assessment (2026-11-04): shared observer lifecycle. Open Dough
0.3.82's CI notification guidance defines budget expiry as ended coverage.
The execution supplies no evidence of a Clipboard-specific observer override
or failure to follow that contract. [Run 41647699400](https://github.com/terryyin/clipboard/actions/runs/41647699400)
later confirmed the three gated native copy-files jobs and CI passed on
`a73a418`. The shared review also recovered [run 41575770049](https://github.com/terryyin/clipboard/actions/runs/41575770049)
on `d74c178`, which passed the same three gated jobs and CI. This recovers
the intermediate verdict. The observer's coverage still lapsed between
its budget expiry and reattachment.

### Occurrences
- Execution: SEED-001#bounded-x11-file-write
  - Timestamp: unknown
  - Tool: Cursor
  - Open Dough release: 0.3.82
  - Evidence: slice-1 publish d74c178 (2026-11-03T11:02:43+07:00) with observer attached; coordinator transcript after interrupted slice-2 delegation: "CI observation budget expired — continuing without promising monitoring"; slice-2 publish a73a418 (2026-11-03T20:48:37+07:00) reattached observer `/tmp/dough-ci-501/watch-MvPeuG` (coverage state pending for a73a418, run 41647699400)
  - Observed effect: Intermediate gated coverage for d74c178 was not retained as a known green; native X11/Wayland/Windows proof conclusions for the story rest on the later tip's still-pending observation
  - Inference: A long next-slice turn can outlive the prior increment's observation budget; treat mid-story budget expiry as lost coverage (report once, continue) and keep final acceptance conditional on the tip observer, not on an assumed earlier green

## ODF-417 — Plan chose a design already present elsewhere without recording it as existing-solution evidence

Former local code: DD-020.

The plan decided to feed `xclip` from an unlinked temp file and to keep the
correction inside the text subsystem, without citing that the file-list X11
writer already implemented the same owner launch; the post-change refactor
pass then stopped at the subsystem gate on the new duplication.

### Occurrences
- Execution: SEED-001#bounded-x11-text-write
  - Timestamp: unknown
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: `.planning/slice-plans/012-bounded-x11-text-write/PLAN.md` at before-cleanup commit 6d26a2f, Current decisions ("Correction stays inside the text subsystem"; "Feed `xclip` a temp-file `stdin`"); `clipboard/_files_native_x11_writer.py` `_start_owner` from d74c178 (SEED-001#bounded-x11-file-write); slice 1 refactor report ending `## REFACTOR JIDOKA STOP`, coordinator AskUserQuestion, maintainer chose "Defer as follow-up" (queued as SEED-001#bounded-helper-owner-write); plan Learnings slice 1 entry
  - Observed effect: One human interruption and a resumed refactor agent (~62k subagent tokens across both turns) for zero edits; the share-or-defer choice was made mid-execution instead of at planning
  - Inference: A PFE pass during slice planning (the plan names `dough-pfe` for relocating responsibility) would likely have found the sibling launcher and let the plan record share-or-defer up front

## ODF-325 — Coordinator issued a no-op shell call while waiting on background agents

Former local code: DD-021.

While two delegated agents ran, the coordinator ran `echo waiting` solely to
fill the turn, which delegation guidance forbids ("Do not issue no-op calls").

### Occurrences
Two Claude Code / Claude Opus 5.5 executions on Open Dough 0.3.82, both with
unknown event timestamps: SEED-001#bounded-x11-text-write (slice 1
`echo waiting` after delegation) and SEED-003#host-independent-desktop-free-tests
(`fc -ln 0 …; echo skip` before retrying a record-writing script). Each cost
one tool call without affecting work or proof. The existing waiting rule
covers both. Full rows are recoverable from the pre-compaction revision
above and retained at [ODF-325](https://github.com/terryyin/open-dough/blob/main/docs/maintainer/findings/ODF-325.md#odf-325).

## ODF-442 — Refactor pass dropped a step-ok condition the old wrapper asserted

Former local code: DD-024.

A post-change refactor agent, briefed that native probe step `ok` "may only
get stricter", removed the `waited_s <= bound_s` owner-exit check from the
shared "cleared" rule as redundant with `wait_pids_exit`, although the
replaced X11 wrapper had asserted it for the `copy_image` step. It also left a
ruff E501 docstring line while reporting the project formatter had run.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-442](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-442.md); source recovery remains in this project’s pre-compaction revision.

## ODF-418 — CI-owned final-slice proof has no named observation step before the done transition

Former local code: DD-022.

A Behavior slice whose planned proof is a CI matrix observation was published
with `progress: true`; guidance says to mark it done "after accepted
observation" but names no command for that observation, and forbids
`complete-revision` after ordinary slice delivery. The coordinator inferred the
read-only `ci-mailbox.mjs await-revision` and then needed a records-only commit
to flip the status. Related to ODF-416 (same `progress: true` → second
records-only commit), but here the slice was the last one and nothing was
blocked; the gap is the unnamed observation step. Matching uncertain.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-418](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-418.md); source recovery remains in this project’s pre-compaction revision.

## ODF-419 — Probe smoke check ran a destructive child helper on the owner desktop

Former local code: DD-023.

An implementation agent import-checked a new Linux probe support module on the
macOS coordinator host by calling its `child_clear()` helper, which ran the
real `clipboard.clear()` and emptied the developer's live clipboard. The
delegation brief had not said that probe child helpers act on the live
clipboard of whatever host runs them.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-419](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-419.md); source recovery remains in this project’s pre-compaction revision.

## ODF-443 — Refactor return called a 384-line module fine against the 250-line limit

Former local code: DD-027.

A post-change refactor return reported `scripts/native_wait_support.py` at
"about 385 lines … all fine" although the refactor checks require splitting
any checked file over 250 lines; the coordinator accepted `## REFACTOR
COMPLETE` without a size check, and the retrospective found it.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-443](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-443.md); source recovery remains in this project’s pre-compaction revision.

## ODF-444 — Single local premise probe recorded as settled, then contradicted by a rerun

Former local code: DD-028.

A coordinator's one-off local container probe (headless Sway 1.9, wl-clipboard
2.2.1, `primary_selection disabled`) concluded that `wl-copy --primary` exits 0
while the write is dropped, and the plan's Learnings and the slice 2 brief
stated it as settled. The implementation agent's rerun in the same image saw
PRIMARY still served through wlroots data-control v2. The probe output had
shown an unexplained `wl_display_dispatch: Broken pipe` after a compositor
restart in the same container.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-444](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-444.md); source recovery remains in this project’s pre-compaction revision.

## DD-029 — Local Linux containers replaced CI records-only early-probe steps
The plan scheduled records-only CI steps (branch pushes) for both slices'
early premise probes. The coordinator ran them instead in a local Docker
`ubuntu:24.04` container (via colima) with the same `xclip 0.13` and
wl-clipboard 2.2.1 as CI, before delegating; the implementation agents also
ran the new native probes there before returning. CI then confirmed both
probes on its first runs.

### Occurrences
- Execution: SEED-001#primary-selection
  - Timestamp: 2026-11-04T14:13:33+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: plan 017 Learnings "Slice 1 early probe" / "Slice 2 early probe" (Docker ubuntu:24.04); CI runs 41799207621 and 41803370471 passed the X11 and Wayland PRIMARY probes on first publication
  - Observed effect: No probe-only commits or CI round trips; no native CI repair was needed
  - Inference: Useful practice where a container runtime is available; it does not replace CI evidence (Sway 1.9 locally vs 1.11 in CI), so CI remains the native proof owner

<a id="dd-030"></a>

## ODF-445 — Multi-OS matrix bash steps first failed under Windows PowerShell

Former local code: DD-030.

POSIX shell conditionals (`if`, `$?`, `RUNNER_TEMP`) were added to a
`ubuntu`/`macos`/`windows` desktop-free matrix without `shell: bash`. Windows
runners default to PowerShell, so the first hosted run rejected those steps
while the Ubuntu Intent proof fragment and summary already matched the named
leg — one CI repair round-trip to set `shell: bash` on the affected steps.

**Responsibility (2026-11-07):** The shared facet stays here: the
`ci-proof-summary.md` step 3 recipe gives a POSIX shell snippet without noting
`shell: bash` when the producer job is a multi-OS matrix including Windows.
Clipboard's own `.github/workflows/desktop-free-tests.yml` matrix step is the
local facet, repaired in `15d276ba` and kept in
[ProjectFindings.md](ProjectFindings.md#dd-030) (recovery
`434d72b7d720903c3c488edbb3316b99cd2feeb0:DearDough.md#dd-030`).

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-445](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-445.md); source recovery remains in this project’s pre-compaction revision.

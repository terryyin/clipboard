# DearDough Process Findings

## Retention

- Highest allocated local number: 446
- Shared source compaction recovery: `015b3a2b27ca61671723a0b2e8d274c3e3506447:DearDough.md`. Shared occurrences are at the pinned Open Dough records; practice observations keep their distinct executions below.
- Shared-feedback adoption and compaction recovery (2026-11-07): `e314ecd7b16f1c86970d352d9db043da243ac144:DearDough.md`; shared rows are retained at the linked Open Dough finding owners (`483d3a1e8f0ea24b929675b9a195faca48ac8f47:docs/maintainer/findings/`).
- Shared-feedback adoption and compaction recovery (2026-11-04): `9e36c067e012371aa207d9b469a3fc0a23e3ccdf:DearDough.md`.
- Shared-feedback compaction recovery (2026-11-03): `e2b98b77c9d0b467e610bdc27fe513a4061431ef:DearDough.md`; shared rows are retained at the linked Open Dough finding owners.
- Consolidation (2026-11-03, approved): DD-003, DD-004 and DD-013 are consolidated under ODF-074 with former-code aliases. Recovery: `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`.
- Ownership: project-owned findings (cause in Clipboard's own code, tests, configuration or CI workflow) live in [ProjectFindings.md](ProjectFindings.md); DD-001, DD-005 and DD-010 moved there on 2026-11-03 (recovery: `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`). `DD-NNN` numbering is shared across both files; the highest allocated local number above covers both.

## ODF-414 — Settled no-session premise still ran three Behavior deliver cycles

Former local code: DD-002.

A settled no-session premise still triggered three per-desktop Behavior delivery cycles without new native measurement. [ODF-414 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-414.md#odf-414)

## ODF-074 — Native-venue helper and probe premises entered gated CI unverified

Former local code: DD-003.
Former local code: DD-004.
Former local code: DD-013.

Native helper/compositor/probe premises were first observed through published gated runs, adding repair cycles. Three early executions represent the first three aliases, with two aliases from one execution; the packaging run is a fourth execution.

### Former DD-003 — Linux X11 clipboard ownership learned through gated-CI repair loops

`SEED-001#write-images` (Cursor, 0.3.79, 2026-11-02T14:00:07+07:00): X11 image write needed a retained xclip owner, safe stdin lifetime and an image/png TARGETS readiness check.

### Former DD-004 — Wayland CI compositor chosen without wl-clipboard protocol check

Same execution at 2026-11-02T14:25:25+07:00. Weston lacked wlr-data-control. Headless Sway fixed proof after one failed venue choice.

### Former DD-013 — Native probe scaffolding assumptions failed on the first gated run

`SEED-001#portable-text` (Claude Code, 0.3.82, 2026-11-02T23:37:16+07:00) repaired the Xvfb floor and Windows holder/consumer probes. `SEED-001#copy-files` (same host/release, 2026-11-03T08:40:19+07:00) repaired the PowerShell FileDropList premise. The common cause remains qualified: some checks used stand-ins that did not observe the promise.

`SEED-001#x11-clear-packaged-apps` (Claude Code Opus 5.5, 0.3.82, 2026-11-04T04:34:03Z) predicted CI Linux `display` from macOS `libx11` without observing CI's Nix shell. Three commits and a human decision followed. Its local facet, DD-025, is retired in [ProjectFindings.md](ProjectFindings.md) (recovery `cf2018106f4338a7a1789e7c5dd1fec2e397a171:ProjectFindings.md#dd-025`). [ODF-074 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-074.md#odf-074)

## DD-006 — Stop for venue decision when mandatory native proof cannot run locally

A required native proof unavailable in the Darwin checkout led to an explicit venue decision. `SEED-001#write-images` (2026-11-02T13:44:00+07:00, Cursor, 0.3.79; transcript `ed9de93f…`, slices 4–5) adopted gated GitHub Actions and preserved the Linux acceptance promise.

## ODF-415 — Pre-existing over-limit module surfaced only at the first refactor stop

Former local code: DD-007.

Planning omitted an already 470-line module against a 250-line limit. The first refactor pass stopped after implementation for a package-split decision. [ODF-415 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-415.md#odf-415)

## DD-008 — Prior native-venue findings reused; every gated CI probe passed first run

Reusing Xvfb with an owning xclip, headless Sway and prior Windows native proof avoided repeated CI repairs. Distinct executions:

- `SEED-001#read-html` (2026-11-02T16:41:56+07:00, Claude Code, 0.3.79): first-run X11, Wayland and Windows proof on runs 41422813085, 41424913377 and 41427386442. Windows had a usable clipboard session.
- `SEED-001#desktop-helpers` (2026-11-02T21:41:26+07:00, Cursor auto, 0.3.82): five native jobs passed on `2b06eb3` in 41464367130 without CI repair, including before tip (observer `watch-Xh83iA`).
- `SEED-001#clear-clipboard` (2026-11-03T14:02:39Z, Claude Code Opus 5.5, release unknown): runs 41649816028, 41651498162, 41654014945 and 41658893626 passed first native proof. The first published increment carried the early probe; waits still took about 10–15 minutes.
- `SEED-001#shared-native-clear-proof` (2026-11-03T23:47:15Z, Claude Code Opus 5.5, 0.3.82): runs 41741871109 and 41742684361 passed. Overlapping disjoint next work avoided idle waits; each done commit still started another ~3-minute run.
- `SEED-001#bounded-helper-owner-write` (2026-11-04T16:17:17+07:00, Claude Code Opus 5.5, 0.3.82): runs 41802978191 and 41805764901 passed with early probes in their first increments. Slice 2 could not overlap its X11 prerequisite.
- `SEED-001#primary-selection-polish` (2026-11-05T05:51:00+07:00, Cursor auto, 0.3.82): run 41928637574 passed native Wayland/X11 on `90a8e7b`; done at `03a223d`, no repair (observer `watch-UZnVa9`).

## ODF-258 — Producer-kind gap carried three slices before developer decision

Former local code: DD-009.

The producer-kind mismatch was noted at slice 4 and reached the developer before slice 7, after other slices followed the same helper-producer pattern. [ODF-258 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-258.md#odf-258)

## DD-011 — Stop for authorization before cross-subsystem package split

Human decisions preceded cross-subsystem splits required by the 250-line refactor limit.

- `SEED-001#read-files` (2026-11-02T17:02:13+07:00, Cursor auto, 0.3.82): developer authorized splitting 517-line `clipboard.py`; `acb5e62` preserved the import and VERSION (transcript `eb2ce85d…`).
- `SEED-001#primary-selection-polish` (2026-11-04T22:49:00+07:00, Cursor auto, 0.3.82): authorized splitting a 1,016-line README, retaining the pyproject entry and moving usage, evidence and development to short documents.
- `SEED-004#publish-clipboard-ci-proof` (2026-11-05T19:23:00+07:00, Cursor auto, 0.3.86): authorized a 593-line CI workflow split across native and desktop-free seams. Reusable workflows reduced the entry to 241 lines and progress resumed.

## ODF-416 — progress:true left mid-plan Behavior slice unfinished until local-proof done commit

Former local code: DD-012.

The first mid-plan progress increment kept the slice planned even though local proof was sufficient. A records-only done publication cancelled the running implementation CI. [ODF-416 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-416.md#odf-416)

## ODF-289 — Cancelled CI jobs attributed to supersession before checking runner acquisition

Former local code: DD-014.

The initial diagnosis blamed supersession for cancelled macOS jobs. They had zero steps and no runner assignment. [ODF-289 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-289.md#odf-289)

## ODF-141 — Fresh refactor agent for small CI repairs returned no change

Former local code: DD-015.

Fresh refactor passes on small CI repairs returned without edits. Later reports include a refactor bypass as counterevidence, with earlier evidence preserved. [ODF-141 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-141.md#odf-141)

## ODF-097 — Source-freshness check chained into delivery ignored a conflict

Former local code: DD-016.

A chained delivery ignored the visible source-freshness conflict and proceeded to publication. [ODF-097 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-097.md#odf-097)

## ODF-403 — Branch plan notes next to trunk-amended lines kept freshness in conflict

Former local code: DD-017.

Adjacent plan notes conflicted with trunk-amended lines after the source-freshness check. [ODF-403 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-403.md#odf-403)

## ODF-408 — Developer-operated desktop rounds requested while the developer was away

Former local code: DD-018.

Developer-operated desktop rounds were requested while the developer was away. Keep genuinely human-operated proof separate from what the agent can observe. [ODF-408 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-408.md#odf-408)

## ODF-259 — CI observer budget expired while the next slice was still open

Former local code: DD-019.

The observer budget expired while the next slice was interrupted. The next publish started a new observer after the coverage gap. The retained follow-through distinguishes incomplete and later CI receipts. [ODF-259 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-259.md#odf-259)

## ODF-417 — Plan chose a design already present elsewhere without recording it as existing-solution evidence

Former local code: DD-020.

The text-writer plan chose an unlinked temp-file stdin without citing the sibling X11 file-writer launcher. Refactor surfaced the duplication after implementation and required a human share-or-defer choice (~62k agent-reported tokens, no edits). [ODF-417 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-417.md#odf-417)

## ODF-325 — Coordinator issued a no-op shell call while waiting on background agents

Former local code: DD-021.

Two 0.3.82 Claude Code Opus 5.5 executions (event times unknown) spent one no-op call each: the text-writer slice 1 and the host-independent desktop-free tests record retry. Existing guidance covered both. [ODF-325 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-325.md#odf-325)

## ODF-442 — Refactor pass dropped a step-ok condition the old wrapper asserted

Former local code: DD-024.

The refactor removed the X11 owner-exit deadline from the shared clear step and left a Ruff E501 line despite claiming the formatter ran. [ODF-442 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-442.md#odf-442)

## ODF-418 — CI-owned final-slice proof has no named observation step before the done transition

Former local code: DD-022.

A final CI-owned Behavior slice needed a separate done commit. The coordinator inferred the read-only mailbox command because the workflow named no observation step. Relation to ODF-416 remains uncertain. [ODF-418 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-418.md#odf-418)

## ODF-419 — Probe smoke check ran a destructive child helper on the owner desktop

Former local code: DD-023.

A Linux probe smoke check called the real child clear helper on the macOS coordinator and emptied the developer’s live clipboard. [ODF-419 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-419.md#odf-419)

## ODF-443 — Refactor return called a 384-line module fine against the 250-line limit

Former local code: DD-027.

A refactor return called a 384-line module acceptable under the 250-line rule. The retrospective found the missed acceptance check. [ODF-443 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-443.md#odf-443)

## ODF-444 — Single local premise probe recorded as settled, then contradicted by a rerun

Former local code: DD-028.

The plan treated a single headless Sway 1.9/clipboard 2.2.1 run as decisive despite a broken pipe after compositor restart. A rerun in the same image still served PRIMARY through wlroots data-control v2. [ODF-444 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-444.md#odf-444)

## DD-029 — Local Linux containers replaced CI records-only early-probe steps

Local Ubuntu 24.04 Docker replaced two planned probe-only commits in `SEED-001#primary-selection` (2026-11-04T14:13:33+07:00, Claude Code Opus 5.5, 0.3.82). Plan 017 early probes used xclip 0.13 and wl-clipboard 2.2.1 before delegation. CI 41799207621 and 41803370471 confirmed X11 and Wayland PRIMARY first try. Sway differed (1.9 local, 1.11 CI), so CI remained the native proof owner.

<a id="dd-030"></a>

## ODF-445 — Multi-OS matrix bash steps first failed under Windows PowerShell

Former local code: DD-030.

The shared CI-proof recipe used POSIX syntax without noting the shell requirement for Windows matrix jobs. The repaired workflow was the DD-030 local facet, now retired in [ProjectFindings.md](ProjectFindings.md) (recovery `cf2018106f4338a7a1789e7c5dd1fec2e397a171:ProjectFindings.md#dd-030`). [ODF-445 evidence](https://github.com/terryyin/open-dough/blob/483d3a1e8f0ea24b929675b9a195faca48ac8f47/docs/maintainer/findings/ODF-445.md#odf-445)

## DD-446 — Guarded preparation withheld publication on mechanical and record failures

The fresh-delivery guard kept formatter and obligation-record failures local rather than publishing an older or partially prepared candidate. This is an observed practice; it does not establish a defect in the guidance. Sequence the formatter before lint, and keep execution narrative outside an obligation's field paragraph.

### Occurrences
- Execution: `SEED-005#publish-ci-test-execution-times`; first implementation `7619b4f636ba13b1cd40f3122dcff90b64c0bdd6`
  - Timestamp: unknown; observed during 2026-11-10 execution before implementation publication
  - Tool: Codex
  - Open Dough release: 0.3.94 (installed before the established start; guidance unchanged during execution)
  - Evidence: this execution conversation's guarded `fresh` results for `/tmp/clipboard-timing-progress-preparation.json`: first `operation: formatting` refused Ruff E501 before formatting; the next formatted three files but retained one long string; after mechanical wrapping, `operation: story obligations` refused G2's trailing narrative as `no-disposition`. Every refusal reported `commit: null`, `publication: pending`. Corrected preparation subsequently accepted `7619b4f`.
  - Observed effect: no failed preparation committed or published; local proof remained reusable after mechanical fixes. The three retries arose from coordinator command/record construction, not demonstrated product defects.
  - Inference: retain the guard and improve caller construction; the record does not measure a general time saving or justify another approval gate.

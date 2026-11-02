# DearDough Process Findings

## Retention

- Highest allocated local number: 9

## DD-001 — Optional-extra local proof not mirrored on CI matrix path
When a packaging optional extra is required for new contract tests, updating
Makefile/local `uv run --extra …` alone left the GitHub Actions matrix `tests`
job on bare `uv sync/run --locked`, so published slice work failed on every
OS/Python cell until a CI repair aligned the workflow.

### Occurrences
- Execution: SEED-001#read-images
  - Timestamp: 2026-11-02T10:42:00+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: commit f30e269 (Makefile `--extra images`); CI run https://github.com/terryyin/clipboard/actions/runs/41384361341 attempt 1 failed on `uv run --locked pytest` / missing Pillow; repair commit 48e8266; coordinator transcript 57a69224… noting matrix lacked images extra; repair subagent 7f955186…
  - Observed effect: Story-branch matrix jobs failed after slice 1 publish; WIP stash + dedicated CI repair before continuing slice 2; quality/Nix path had already passed.
  - Inference: Dual local-vs-matrix verification seams need an explicit extras checklist when optional dependencies first enter pytest; Makefile green did not prove the matrix path.

## DD-002 — Settled no-session premise still ran three Behavior deliver cycles
When a plan's decisive premise already settles that the execution checkout cannot
host the remaining desktop sessions, splitting each desktop's authorized
evidence-limit path into its own Behavior slice still incurred a full
implement → obligations/source-review → refactor → publish cycle per desktop
before the consolidation Structure slice, without new native measurement.

### Occurrences
- Execution: SEED-001#read-images-native
  - Timestamp: 2026-11-02T11:43:00+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: PLAN.md Decisive premises (Darwin cannot run Win/Linux probes); slices 1–3 Accepted notes all Darwin/no-session evidence limits; published SHAs d08fb4c, 47e5b9c, 0501e6a (near-identical README evidence-limit increments) then fcd18a0 consolidation; coordinator transcript d2b3e3b5… (three Behavior deliver cycles after settled uname Darwin)
  - Observed effect: Three docs-only Behavior publishes plus refactor agents authorized to fill Accepted notes; no Win/Linux probe scripts delivered; slice 4 rewrote the same Evidence paragraph into one consolidated limit statement.
  - Inference: Once session absence is settled for the executing checkout, one evidence-limit write covering the remaining desktops (or collapsing early-probe Behavior slices) would preserve per-desktop honesty with less deliver/refactor overhead; independent desktop loops remain justified only when a session may still appear.
- Execution: SEED-001#inspect-formats
  - Timestamp: 2026-11-02T16:52:28+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: PLAN.md Decisive premises (Darwin; xclip/wl-paste absent — Win/Linux cannot probe here); coordinator 8888689d… after slice 3: “Slices 4–6 are evidence-limit paths on this Darwin host”; published 629513f (X11), ee446c2 (Wayland), 0c9741a (Windows) each with full deliver→source-review→refactor→publish; README/probe `evidence_limit` paths only for those desktops
  - Observed effect: Three more Behavior publish cycles after session absence was settled; unlike the read-images-native occurrence, each slice also wired a real enumerator + desktop-free tests (not docs-only), but native verification remained predetermined evidence-limit with no new desktop measurement on this host.
  - Inference: Settled no-session still does not justify three early-probe Behavior cycles for the verification claim; enumerator wiring for remaining desktops can share one Structure/Behavior slice with a single honest multi-desktop evidence-limit write.

## DD-003 — Linux X11 clipboard ownership learned through gated-CI repair loops
For Linux image write under Xvfb, successive published repairs rediscovered that
`xclip` must stay as CLIPBOARD owner (do not wait for exit), stdin ingest must
not race tempfile deletion, and return must wait until TARGETS lists
`image/png` — knowledge that could have been a decisive early premise before
the gated job was treated as green-or-repair.

### Occurrences
- Execution: SEED-001#write-images
  - Timestamp: 2026-11-02T14:00:07+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: commits 3b4149e (`-quiet`), 7fb288b (pipe hang), c6f6585 (leave owner running), 8d842c6 (stdin/`-quiet` regression), a2f4a99 (restore fire-and-forget), 833bbd3 (TARGETS wait); coordinator transcript ed9de93f… lines noting X11 hang → pipe hang → ownership → opaque race; before-cleanup a922455:.planning/slice-plans/003-write-images/PLAN.md Learnings on Xvfb xclip
  - Observed effect: Multiple story-branch CI repair cycles on slices 4–5 before both native jobs stayed green; interim “done” floors were rewritten after later ownership fixes.
  - Inference: When gated CI is the authorized native venue, helper lifetime/ownership premises belong in an early local or throwaway probe before counting the job as the acceptance loop.

## DD-004 — Wayland CI compositor chosen without wl-clipboard protocol check
The first Wayland gated job used Weston headless; `wl-copy` failed because
Weston lacks wlr-data-control. Retargeting to Sway (`WLR_BACKENDS=headless`)
fixed proof, after one failed compositor choice.

### Occurrences
- Execution: SEED-001#write-images
  - Timestamp: 2026-11-02T14:25:25+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: commit 8d842c6 (Weston job), a2f4a99 (Sway retarget; commit message: Weston lacks wlr-data-control); before-cleanup a922455:.planning/slice-plans/003-write-images/PLAN.md Accepted proof / Learnings; transcript ed9de93f… “Weston lacks… switching… to Sway”
  - Observed effect: Wayland acceptance waited on a compositor swap and a second gated-CI cycle after X11 work was already in flight.
  - Inference: Named Wayland CI compositors need a protocol/helper compatibility check (wlr-data-control / wl-clipboard) before the first published probe job.

## DD-005 — Platform stub wording change broke Windows-only assertion
Editing the shared default `NotImplementedError` message for honesty on
unimplemented platforms invalidated a substring assertion that only runs off
Darwin/Linux, so the Windows matrix failed after the evidence-limit commit
until a follow-up assertion fix.

### Occurrences
- Execution: SEED-001#write-images
  - Timestamp: 2026-11-02T14:37:42+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: d408685 (message → “not implemented for this platform”); Windows matrix failure noted in transcript ed9de93f…; repair c5e10c3 (assertion → matching substring)
  - Observed effect: Extra CI cycle between slice-6 evidence-limit publish and tip green; docs slice absorbed the assertion repair.
  - Inference: Platform-gated message assertions are coupled to shared stub wording; change both in one publish or assert on exception type only.

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

## DD-007 — Pre-existing over-limit module surfaced only at the first refactor stop
A module already over the refactor file-size limit before the story (470 of
250 lines) was not named as a premise during planning, so the first slice's
post-change refactor stopped for a structural developer decision (package
split) after implementation was done.

### Occurrences
- Execution: SEED-001#read-html
  - Timestamp: unknown
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.79
  - Evidence: 2026-11-02, before commit 0d3e238 (16:11:50+07:00); `9d3ceda:.planning/slice-plans/005-read-html/PLAN.md` Decisive premises name no file-size premise; slice 1 refactor return `## REFACTOR JIDOKA STOP` (clipboard.py 510 lines); developer answer "Split now"; same PLAN.md Current decisions "Developer decision (2026-11-02, slice 1 refactor stop)"
  - Observed effect: One extra refactor round (about 20 minutes reported by the refactor agent) and a mid-slice human question; the split landed with slice 1.
  - Inference: Planning could check the line counts of files the plan will edit and settle split-or-exception before the first slice; impact was modest because the split was cheap.

- Execution: SEED-002#linux-file-offers-ci
  - Timestamp: unknown
  - Tool: Codex
  - Open Dough release: 0.3.82
  - Evidence: 2026-11-02 before cc6d541; baseline `7a908cc:.github/workflows/ci.yml` has 275 lines, initial Thunar-job addition reached 318; independent refactor return reports the 250-line gate and about four minutes of work; cc6d541 extracts the unchanged Wayland jobs into `native-wayland-copy-image.yml` and `native-wayland-paste-html.yml`.
  - Observed effect: The bounded file-manager experiment acquired two additional reusable workflow files during post-change refactoring; their command behavior stayed unchanged and required workflow lint and hosted validation.
  - Inference: The same late discovery as the earlier module occurrence: planning could recognize an already over-limit workflow and include the required cohesive split before implementation. This occurrence needed no cross-subsystem human decision.

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

## DD-009 — Producer-kind gap carried three slices before developer decision
The story's "browser or rich editor" producer wording could not be met by the
authorized CI venues; the gap was recorded at slice 4 as an interim obligation
and only put to the developer before slice 7, after Wayland and Windows used
the same helper-producer pattern.

### Occurrences
- Execution: SEED-001#read-html
  - Timestamp: unknown
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.79
  - Evidence: 2026-11-02, between commits 8659430 (17:18:38+07:00) and 1a5b92d (17:36:04+07:00); `9d3ceda:.planning/slice-plans/005-read-html/PLAN.md` Story obligations G4 (reported slice 4, interim until slices 5, 6, 7, then owner changed); developer answer "Verified, helper-labelled"; `9d3ceda:.planning/seeds/SEED-001-clipboard-true-to-its-name.md` "Developer amendment (2026-11-02, during execution)"; `9d3ceda:.planning/slice-plans/005-read-html/source-review.md` replaced after the amendment
  - Observed effect: Slices 5–6 proceeded on an unresolved acceptance question; the amendment then required a fresh source review and re-allocation of 77 commitment ids.
  - Inference: Asking at the first occurrence (slice 4) would have settled README wording earlier and avoided carrying the interim; the late ask still preceded any false claim.

## DD-010 — Desktop-free unavailable-path test asserted host OS
A desktop-free test for the Windows unavailable stub used `assert sys.platform != "win32"` so the path was only exercised off Windows; the windows-latest matrix failed until the assertion was replaced with a platform monkeypatch.

### Occurrences
- Execution: SEED-001#read-files
  - Timestamp: 2026-11-02T17:45:49+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: CI failures on 23ff505 (run https://github.com/terryyin/clipboard/actions/runs/41430900179, Python 3.10/3.14 windows-latest); repair commit b00d9ab (`monkeypatch…platform` to `"darwin"`); observer `/tmp/dough-ci-501/watch-8h3joP` events 1–3; coordinator transcript eb2ce85d… stash slice-7 docs then CI repair
  - Observed effect: Extra story-branch CI repair between slice-6 Windows evidence-limit publish and tip green; desktop-free suite had encoded a Darwin/non-Windows host assumption
  - Inference: Unavailable-stub / platform-branch tests must force the non-target platform via monkeypatch (or assert exception type only), never require the CI host OS; distinct from stub-message substring coupling (DD-005)

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

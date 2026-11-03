# DearDough Process Findings

## Retention

- Highest allocated local number: 19

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
- Execution: SEED-001#desktop-helpers
  - Timestamp: 2026-11-02T21:41:26+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: tip SHA 2b06eb3 CI run https://github.com/terryyin/clipboard/actions/runs/41464367130 success on first attempt including native-windows-paste-html, native-linux-x11/wayland paste_html and copy_image; intermediate published SHAs 1b9ed68, 98daafa, 75d3909 also coverage-success with no repair commits; observer `/tmp/dough-ci-501/watch-Xh83iA`; contrast DD-003 / DD-004
  - Observed effect: Structure relocation of session/listing helpers landed with no CI repair; five-job native confirmation stayed green while later slices continued under observation
  - Inference: Useful practice — reuse the same Xvfb/Sway venues and fail-not-skip native wrapper pattern when relocating desktop helpers; first-run green held for session-selection proof that desktop-free pytest cannot cover

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

- Execution: SEED-001#portable-text
  - Timestamp: 2026-11-02T22:40:30+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: run https://github.com/terryyin/clipboard/actions/runs/41471306541 Python 3.10/3.14 windows-latest `tests\test_text_x11.py:31: AttributeError: module 'os' has no attribute 'killpg'` (fixture `monkeypatch.setattr(os, "killpg", …)` without `raising=False`); repair commit c086e20 (fixture `raising=False`, product `_stop_owner` falls back to `proc.kill()`)
  - Observed effect: One extra story-branch CI repair cycle on slice 4; the product helper would also have raised AttributeError where `os.killpg` is absent
  - Inference: Same root as the earlier row — a desktop-free test encoded a POSIX host capability; the next slice's delegation brief carried the warning and slice 5 / 6 unit tests had no such failure

- Execution: SEED-001#copy-files
  - Timestamp: 2026-11-03T08:20:26+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: runs 41558761684 (5787804: 12 setup errors `OSError: [Errno 22] Invalid argument` for the fixture file named with `"` and `\` on windows-latest) and 41559117116 (5df300b: 8 failures `No module named '_scproxy'` because the darwin_helper fixture patched the shared `sys.platform` to darwin on Windows, sending `Path.as_uri` into urllib's macOS branch); repairs 5df300b and 152faa2
  - Observed effect: Two consecutive story-branch CI repair cycles right after slice 3 (about 5 minutes of CI wait each); product code unchanged
  - Inference: Same root as the earlier rows: desktop-free tests encoded a POSIX host (file-name characters, platform faking on the shared `sys`); after the slice 4–6 briefs warned about it, the X11 and Wayland writer tests faked only a module-local `sys` and passed on every matrix OS first time

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

## DD-012 — progress:true left mid-plan Behavior slice unfinished until local-proof done commit
Publishing the first Behavior increment with `progress: true` kept the slice
`planned` until CI confirmation, which blocked continuing the plan; marking the
slice done on accepted local proof required a second records-only commit and
cancelled the still-running CI for the superseded implementation SHA.

### Occurrences
- Execution: SEED-001#desktop-helpers
  - Timestamp: 2026-11-02T21:10:11+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: commits 237e23d (implementation) then 1b9ed68 (mark slice 1 done); coordinator transcript 0fc04e77… “Slice 1 stayed `planned` under `progress: true`… marking it done while CI keeps observing”; observer event CI_INCOMPLETE cancelled on 237e23d (run 41459230661); coverage success later on 1b9ed68 (run 41459401185)
  - Observed effect: Extra records-only publish before slice 2; cancelled CI on the implementation SHA; ~1 minute between the two commits; later Structure slices proceeded under observation without waiting for tip green
  - Inference: When local proof is the authorized done floor and CI is observation/repair only, publishing Behavior with `progress: true` creates avoidable mid-plan friction; mark done on local proof in the same publish, or treat progress as non-blocking for the next slice without a second commit

## DD-013 — Native probe scaffolding assumptions failed on the first gated run
New gated probes asserted facts the runner could not supply or used stand-ins
that did not observe the promise: an Xvfb version floor not readable by
`Xvfb -version`, a Windows clipboard holder opened with a NULL window (which
pyperclip's own NULL open shares and closes), and `Get-Clipboard` standing in
for Notepad. Each cost a full CI round trip although the product passed.

### Occurrences
- Execution: SEED-001#portable-text
  - Timestamp: 2026-11-02T23:37:16+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: run 41471306541 (X11 probe all steps ok, wrapper failed `assert env[floor]` on `xvfb_version: null`; repair c086e20 adds `dpkg-query`); run 41483294562 (Windows step 5 `close_ok: false`, held `paste()`/`copy()` succeeded; step 2 both PowerShells report one line; repair 450f786 adds own-window holder with `GetOpenClipboardWindow` evidence and a Notepad `EM_GETLINECOUNT` consumer); run 41484980894 green on both
  - Observed effect: Slices 4 and 6 each needed one probe-only repair cycle (about 15–25 minutes of CI wait each) before native acceptance; no product code changed for these
  - Inference: Before the first gated run, check that each asserted floor has a runner-available source (package manager first) and that each stand-in consumer or holder observes the story's own example (here, Notepad and a real ownership hold); slice 4's lesson was carried into slices 5–6 briefs, which then failed only on the Windows-specific holder semantics

- Execution: SEED-001#copy-files
  - Timestamp: 2026-11-03T08:40:19+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: run 41560847952 job native-windows-copy-files: Explorer `Shell.Application` paste copies matched, drop effect 01-00-00-00, `GetFileDropList` exact, but `independent_paths_equal` failed because `Get-Clipboard -Format FileDropList | ForEach-Object { $_.FullName }` in PowerShell 5.1 yielded one space-joined string; probe-only repair ab913cf; run 41561268655 green
  - Observed effect: One probe-only CI round trip (about 5 minutes) before slice 4's native acceptance; product passed on the first run
  - Inference: A second independent reader added for robustness carried an unverified PowerShell collection assumption; the slice 5 and 6 probes passed on their first gated run

## DD-014 — Cancelled CI jobs attributed to supersession before checking runner acquisition
A failed `CI passed` with cancelled macOS jobs was first reported as
supersession by the next push; the jobs had zero steps and a GitHub annotation
"The job was not acquired by Runner of type hosted", which the coordinator
found only when the same pattern recurred on the next run.

### Occurrences
- Execution: SEED-001#portable-text
  - Timestamp: 2026-11-02T23:08:46+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: run 41475927301 (ca8917b, both macOS jobs cancelled, 0 steps, annotation above) first reported as superseded by the 823dcce push; run 41478592764 attempt 1 macOS 3.14 same annotation, rerun with `gh run rerun --failed` → attempt 2 green; correction stated to the developer
  - Observed effect: One wrong cause stated in a progress report and corrected later; no wrong action followed because the superseded revision changed only planning files
  - Inference: Classify a cancelled job by its steps / runner / annotations before naming supersession; a zero-step job with that annotation is infrastructure and warrants a rerun of the failed jobs for coverage

## DD-015 — Fresh refactor agent for small CI repairs returned no change
Delivery required an independent refactor agent before every publication; for
three small repairs or proof-only changes it reported "none — already clean"
after reading the same context again.

### Occurrences
- Execution: SEED-001#portable-text
  - Timestamp: 2026-11-03T00:07:26+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: refactor agents for slice 3 (60.8k subagent tokens, no edits), slice 4 CI repair c086e20 (47.8k, no edits), bound-clamp repair 43ee728 (50.4k, no edits); agent usage lines in the coordinator transcript
  - Observed effect: About 160k subagent tokens and several minutes per publication for no code change; other refactor passes in the same execution did make useful edits (owner→function map, shared Linux helper log, docs contradiction)
  - Inference: A proportionality rule (e.g. coordinator may record "no refactor candidates" for a repair whose diff is a few lines inside one function, or reuse the slice's refactor pass when the repair stays within already-reviewed code) could save cost without losing the passes that found real residue; timestamp is the last occurrence's repair commit 43ee728

- Execution: SEED-001#copy-files
  - Timestamp: 2026-11-03T08:40:19+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: coordinator delivered CI repairs 5df300b, 152faa2 and ab913cf (each a few lines in one test file or probe script) and the plan-only slice 2 commits without the required fresh refactor agent; every slice implementation increment did get one (slices 1, 3–7)
  - Observed effect: The delivery contract's refactor step was skipped for small repairs, a compliance deviation rather than an authorized rule; no residue from those repairs has been reported
  - Inference: The coordinator applied the proportionality this finding proposes without an authorizing rule; adopting the rule or keeping the step would stop silent skips

## DD-016 — Source-freshness check chained into delivery ignored a conflict
The Story Branch source-freshness check ran in the same shell command as the
guarded delivery, so its `conflict` result was printed but not acted on, and a
plan record contradicting trunk's newer evidence was published.

### Occurrences
- Execution: SEED-001#copy-files
  - Timestamp: 2026-11-02T21:33:33+07:00
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: one coordinator Bash call ran `source-freshness.mjs check … | cut -c1-40` (printed `{"result":"conflict"`), then story-obligations and `execution-increment-delivery.mjs fresh`; published d503c8e recorded "no Linux desktop, X11 file-manager evidence limit" while trunk cc86951 had completed slice 2 with real Thunar evidence; correction 085b6d9 after a developer decision
  - Observed effect: One wrong published plan record, one extra correction commit and one developer question; no product code affected
  - Inference: Run the freshness check as its own gating call and branch on its result before any delivery command, as the coordinator did for every later delivery (`[ "$r" = unchanged ] || exit 1`)

## DD-017 — Branch plan notes next to trunk-amended lines kept freshness in conflict
Branch-only plan additions placed directly after a trunk-rewritten Learnings
paragraph made the three-way freshness comparison report `overlapping-edit`
even after trunk's text was taken verbatim, twice in one execution.

### Occurrences
- Execution: SEED-001#copy-files
  - Timestamp: unknown
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: between commits 085b6d9 (2026-11-02T21:36:14+07:00) and 5787804 (2026-11-03T08:17:17+07:00): after taking trunk's plan text, `source-freshness.mjs check` still reported plan `conflict` until the branch's slice 1 learning bullet adjacent to trunk's Learnings paragraph was dropped; later the slice 3 learning in the same position again forced `conflict` and was moved to a separate `## Execution learnings` section, after which the result was `amended` and `absorb` succeeded
  - Observed effect: Two diagnosis detours reading `source-freshness.mjs` and its comparison module, and one dropped plan learning
  - Inference: Keep branch-only plan notes in sections trunk is unlikely to rewrite, or separated from trunk-edited hunks by unchanged lines; the containment search treats adjacent additions as overlapping

## DD-018 — Developer-operated desktop rounds requested while the developer was away
Slice 3's Finder paste was planned as a developer-operated round. Three
question rounds were sent; the developer later said they were not at the
computer and asked the agent to proceed itself, and the screen was locked
(`CGSSessionScreenIsLocked: true`), so Finder ignored Apple Events and the
paste could not be observed.

### Occurrences
- Execution: SEED-001#copy-files
  - Timestamp: unknown
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: between commits 085b6d9 (2026-11-02T21:36:14+07:00) and 5787804 (2026-11-03T08:17:17+07:00): Finder rounds 1–2 answered "Only one / none" (round 1 overwritten by a PNG; round 2 pasteboard types empty at an unchanged changeCount); round 3 rejected with "I am not on the computer right now … Please proceed this without me"; the coordinator then found the session locked, `screencapture` "could not create image from display", and Finder Apple Events timing out; a slice 3 rework agent (about 150k subagent tokens) could not reproduce a vanish
  - Observed effect: The macOS file-manager claim ended as an evidence limit (G2) after one rework delegation and several investigation turns on a pasteboard hypothesis that the lock state may explain
  - Inference: Before asking for a developer-operated desktop round, check the session lock state and try host automation first; treat answers to remote prompts as possibly not observed at the machine (the developer's preference is now in agent memory)

## DD-019 — CI observer budget expired while the next slice was still open
After slice-1 publish, the retained CI observer's budget expired during a long
or interrupted next-slice delegation, so the coordinator continued delivery
without promised monitoring on the prior SHA until the next publish reattached
observation.

### Occurrences
- Execution: SEED-001#bounded-x11-file-write
  - Timestamp: unknown
  - Tool: Cursor
  - Open Dough release: 0.3.82
  - Evidence: slice-1 publish d74c178 (2026-11-03T11:02:43+07:00) with observer attached; coordinator transcript after interrupted slice-2 delegation: "CI observation budget expired — continuing without promising monitoring"; slice-2 publish a73a418 (2026-11-03T20:48:37+07:00) reattached observer `/tmp/dough-ci-501/watch-MvPeuG` (coverage state pending for a73a418, run 41647699400)
  - Observed effect: Intermediate gated coverage for d74c178 was not retained as a known green; native X11/Wayland/Windows proof conclusions for the story rest on the later tip's still-pending observation
  - Inference: A long next-slice turn can outlive the prior increment's observation budget; treat mid-story budget expiry as lost coverage (report once, continue) and keep final acceptance conditional on the tip observer, not on an assumed earlier green

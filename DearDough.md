# DearDough Process Findings

## Retention

- Highest allocated local number: 8

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

- Execution: SEED-001#read-files
  - Timestamp: 2026-11-02T17:29:32+07:00
  - Tool: Cursor
  - Model: auto
  - Open Dough release: 0.3.82
  - Evidence: PLAN.md Decisive premises (Darwin cannot run Win/Linux probes; settled before slices 4–6); Learnings slices 4–6 evidence limits + thin readers; published SHAs fd62820 (X11), 60d4c8d (Wayland), 23ff505 (Windows); coordinator transcript eb2ce85d… sequential deliver of slices 4 then 5 then 6 after settled uname Darwin / missing helpers
  - Observed effect: Three full Behavior deliver cycles (implement → obligations/source-review → refactor → publish) after the no-session premise was already settled; each added evidence-limit probe/docs plus a thin platform reader (xclip / wl-paste / ctypes CF_HDROP), not native measurement on this host
  - Inference: Recurrence of the settled-no-session multi-slice pattern; thin readers could share one Structure (or early Behavior) with a single multi-desktop evidence-limit write, preserving honesty without three deliver loops once session absence is settled

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
## DD-007 — Desktop-free unavailable-path test asserted host OS
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
## DD-008 — Stop for authorization before cross-subsystem package split
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

# DearDough Process Findings

## Retention

- Highest allocated local number: 5

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

## DD-002 — Linux X11 clipboard ownership learned through gated-CI repair loops
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

## DD-003 — Wayland CI compositor chosen without wl-clipboard protocol check
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

## DD-004 — Platform stub wording change broke Windows-only assertion
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

## DD-005 — Stop for venue decision when mandatory native proof cannot run locally
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

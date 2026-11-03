# DearDough Process Findings

## Retention

- Highest allocated local number: 19
- Shared-feedback compaction recovery (2026-11-03): `e2b98b77c9d0b467e610bdc27fe513a4061431ef:DearDough.md`; shared rows are retained at the linked Open Dough finding owners. DD-003, DD-004 and DD-013 all map to ODF-074 and keep their local codes until a consolidation decision. DD-019 awaits local triage.

## DD-001 — Optional-extra local proof not mirrored on CI matrix path
When a packaging optional extra is required for new contract tests, updating
Makefile/local `uv run --extra …` alone left the GitHub Actions matrix `tests`
job on bare `uv sync/run --locked`, so published slice work failed on every
OS/Python cell until a CI repair aligned the workflow.

Responsibility (triage 2026-11-03): project — Clipboard's `Makefile` and
`.github/workflows/ci.yml` matrix carry separate `uv` invocations; no project findings record is defined in this project's guidance, so it stays here.
Current assessment: repair 48e8266 is adopted (matrix `tests` uses
`--extra images`), but the two command seams remain independent. Keep open
until the next new optional extra enters pytest; no story selected for one
occurrence.

### Occurrences
- Execution: SEED-001#read-images
  - Timestamp: 2026-11-02T10:42:00+07:00
  - Tool: Cursor
  - Open Dough release: 0.3.79
  - Evidence: commit f30e269 (Makefile `--extra images`); CI run https://github.com/terryyin/clipboard/actions/runs/41384361341 attempt 1 failed on `uv run --locked pytest` / missing Pillow; repair commit 48e8266; coordinator transcript 57a69224… noting matrix lacked images extra; repair subagent 7f955186…
  - Observed effect: Story-branch matrix jobs failed after slice 1 publish; WIP stash + dedicated CI repair before continuing slice 2; quality/Nix path had already passed.
  - Inference: Dual local-vs-matrix verification seams need an explicit extras checklist when optional dependencies first enter pytest; Makefile green did not prove the matrix path.

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

## DD-003 — Linux X11 clipboard ownership learned through gated-CI repair loops
For Linux image write under Xvfb, successive published repairs rediscovered that
`xclip` must stay as CLIPBOARD owner (do not wait for exit), stdin ingest must
not race tempfile deletion, and return must wait until TARGETS lists
`image/png` — knowledge that could have been a decisive early premise before
the gated job was treated as green-or-repair.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-074](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-074.md); source recovery remains in this project’s pre-compaction revision.

## DD-004 — Wayland CI compositor chosen without wl-clipboard protocol check
The first Wayland gated job used Weston headless; `wl-copy` failed because
Weston lacks wlr-data-control. Retargeting to Sway (`WLR_BACKENDS=headless`)
fixed proof, after one failed compositor choice.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-074](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-074.md); source recovery remains in this project’s pre-compaction revision.

## DD-005 — Platform stub wording change broke Windows-only assertion
Editing the shared default `NotImplementedError` message for honesty on
unimplemented platforms invalidated a substring assertion that only runs off
Darwin/Linux, so the Windows matrix failed after the evidence-limit commit
until a follow-up assertion fix.

Responsibility (triage 2026-11-03): project — a Clipboard test coupled to
copied stub wording; no project findings record is defined in this project's guidance, so it stays here. Repaired for that test by c5e10c3; the general
rule is in scope of queued
[SEED-003#host-independent-desktop-free-tests](.planning/seeds/SEED-003-host-independent-tests.md#host-independent-desktop-free-tests)
(queued, not resolved). Related to DD-010, distinct cause.

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

## ODF-415 — Pre-existing over-limit module surfaced only at the first refactor stop

Former local code: DD-007.

A module already over the refactor file-size limit before the story (470 of
250 lines) was not named as a premise during planning, so the first slice's
post-change refactor stopped for a structural developer decision (package
split) after implementation was done.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-415](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-415.md); source recovery remains in this project’s pre-compaction revision.

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

## ODF-258 — Producer-kind gap carried three slices before developer decision

Former local code: DD-009.

The story's "browser or rich editor" producer wording could not be met by the
authorized CI venues; the gap was recorded at slice 4 as an interim obligation
and only put to the developer before slice 7, after Wayland and Windows used
the same helper-producer pattern.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-258](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-258.md); source recovery remains in this project’s pre-compaction revision.

## DD-010 — Desktop-free unavailable-path test asserted host OS
A desktop-free test for the Windows unavailable stub used `assert sys.platform != "win32"` so the path was only exercised off Windows; the windows-latest matrix failed until the assertion was replaced with a platform monkeypatch.

Responsibility (triage 2026-11-03): project — Clipboard's desktop-free tests
and fixtures encode host assumptions (the shared `text_session` fixture in
`tests/conftest.py` still patches the global `sys.platform`); no project findings record is defined in this project's guidance, so it stays here. Response:
queued
[SEED-003#host-independent-desktop-free-tests](.planning/seeds/SEED-003-host-independent-tests.md#host-independent-desktop-free-tests)
(queued, not resolved).

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

## ODF-416 — progress:true left mid-plan Behavior slice unfinished until local-proof done commit

Former local code: DD-012.

Publishing the first Behavior increment with `progress: true` kept the slice
`planned` until CI confirmation, which blocked continuing the plan; marking the
slice done on accepted local proof required a second records-only commit and
cancelled the still-running CI for the superseded implementation SHA.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-416](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-416.md); source recovery remains in this project’s pre-compaction revision.

## DD-013 — Native probe scaffolding assumptions failed on the first gated run
New gated probes asserted facts the runner could not supply or used stand-ins
that did not observe the promise: an Xvfb version floor not readable by
`Xvfb -version`, a Windows clipboard holder opened with a NULL window (which
pyperclip's own NULL open shares and closes), and `Get-Clipboard` standing in
for Notepad. Each cost a full CI round trip although the product passed.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-074](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-074.md); source recovery remains in this project’s pre-compaction revision.

## ODF-289 — Cancelled CI jobs attributed to supersession before checking runner acquisition

Former local code: DD-014.

A failed `CI passed` with cancelled macOS jobs was first reported as
supersession by the next push; the jobs had zero steps and a GitHub annotation
"The job was not acquired by Runner of type hosted", which the coordinator
found only when the same pattern recurred on the next run.

### Occurrences
Distinct executions, original provenance, observations and qualified inferences are
[retained at ODF-289](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-289.md); source recovery remains in this project’s pre-compaction revision.

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
[retained at ODF-408](https://github.com/terryyin/open-dough/blob/a29f625255a3368eb721249c01df96e0f98edfd4/docs/maintainer/findings/ODF-408.md); source recovery remains in this project’s pre-compaction revision.

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

# Clipboard Project Findings

Project-owned retrospective follow-ups: findings whose cause lies in Clipboard's own code, tests, configuration or CI workflow rather than in published Open Dough guidance. An occurrence in this repository alone does not make its cause project-specific. General execution lessons and defects in published Open Dough skills or their release payload remain in [DearDough.md](DearDough.md). Original finding codes and occurrence evidence are retained; shared local-number allocation (`DD-NNN` codes are numbered across both files) and removed-finding recovery references remain in DearDough.md.

Maintenance assessment, 2026-11-03: DD-001, DD-005 and DD-010 moved here from DearDough.md as project-owned records, with their occurrence rows, responsibility assessments and response links unchanged. Exact source recovery: `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`.

## DD-001 — Optional-extra local proof not mirrored on CI matrix path
When a packaging optional extra is required for new contract tests, updating
Makefile/local `uv run --extra …` alone left the GitHub Actions matrix `tests`
job on bare `uv sync/run --locked`, so published slice work failed on every
OS/Python cell until a CI repair aligned the workflow.

Responsibility (triage 2026-11-03): project — Clipboard's `Makefile` and
`.github/workflows/ci.yml` matrix carry separate `uv` invocations.
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

## DD-005 — Platform stub wording change broke Windows-only assertion
Editing the shared default `NotImplementedError` message for honesty on
unimplemented platforms invalidated a substring assertion that only runs off
Darwin/Linux, so the Windows matrix failed after the evidence-limit commit
until a follow-up assertion fix.

Responsibility (triage 2026-11-03): project — a Clipboard test coupled to
copied stub wording. Repaired for that test by c5e10c3; the general
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

## DD-010 — Desktop-free unavailable-path test asserted host OS
A desktop-free test for the Windows unavailable stub used `assert sys.platform != "win32"` so the path was only exercised off Windows; the windows-latest matrix failed until the assertion was replaced with a platform monkeypatch.

Responsibility (triage 2026-11-03): project — Clipboard's desktop-free tests
and fixtures encode host assumptions (the shared `text_session` fixture in
`tests/conftest.py` still patches the global `sys.platform`). Response:
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

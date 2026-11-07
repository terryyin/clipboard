# Clipboard Project Findings

Project-owned retrospective follow-ups: findings whose cause lies in Clipboard's own code, tests, configuration or CI workflow rather than in published Open Dough guidance. An occurrence in this repository alone does not make its cause project-specific. General execution lessons and defects in published Open Dough skills or their release payload remain in [DearDough.md](DearDough.md). Original finding codes and occurrence evidence are retained; shared local-number allocation (`DD-NNN` codes are numbered across both files) and removed-finding recovery references remain in DearDough.md.

Maintenance assessment, 2026-11-03: DD-001, DD-005 and DD-010 moved here from DearDough.md as project-owned records, with their occurrence rows, responsibility assessments and response links unchanged. Exact source recovery: `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`.

DD-005 retired on 2026-11-04. The Windows-only image-write stub assertion that
broke after a wording edit was corrected by `c5e10c3`; the adopted
`SEED-003#host-independent-desktop-free-tests` response (`5380548`, recorded at
`663dca6`) exercises that stub on every host through `fake_platform` and
asserts the error and its cause types. [CI run 41656910713](https://github.com/terryyin/clipboard/actions/runs/41656910713)
passed all desktop-free matrix jobs on that revision. Full finding and
original occurrence recovery: `2c4149d49df4a08fac54932eef1d72ef67a774f4:ProjectFindings.md`.

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

## DD-010 — Desktop-free unavailable-path test asserted host OS
A desktop-free test for the Windows unavailable stub used `assert sys.platform != "win32"` so the path was only exercised off Windows; the windows-latest matrix failed until the assertion was replaced with a platform monkeypatch.

Responsibility (triage 2026-11-03): project — Clipboard's desktop-free tests
and fixtures encoded host assumptions, including global `sys.platform`
patching in `text_session`. The adopted
`SEED-003#host-independent-desktop-free-tests` response (`05d2e02`, `5380548`;
completion at `066dae4`) replaces the global patch with `fake_platform` and
guards against future global fakes. [CI run 41656910713](https://github.com/terryyin/clipboard/actions/runs/41656910713)
passed all desktop-free matrix jobs, including the pretend-Darwin writer and
X11 owner-shutdown tests on Windows. Keep the wider host-independence finding
open through the next newly added platform-branch test that exercises the
adopted guard and the desktop-free matrix.

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

<a id="dd-025"></a>

## DD-025 — Plan premise predicted a CI classification without observing the CI environment
A decisive planning premise stated the CI package job would classify the
installed X11 clear helper as `display`, but it was observed only on macOS
(`libx11`). The CI job runs inside the Nix dev shell, whose Python saw no
libX11, so the story's key example failed after publication and needed a
developer decision and two more CI cycles.

Responsibility (triage 2026-11-07): mixed — the repository's Nix dev-shell
`libX11` packaging configuration in CI is local (repaired in `9f5e5ff` and
`a7c6e5a`, paired with DD-026 below); the shared premise-observation facet
(observing only on macOS rather than in the consuming `nix develop` Linux
environment) is cross-referenced in [DearDough.md](DearDough.md#odf-074)
with this execution counted once. No new local story.

### Occurrences
- Execution: SEED-001#x11-clear-packaged-apps
  - Timestamp: 2026-11-04T04:34:03Z
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: plan 016 "Decisive premises" 3 (`8ffb85613222db6e76068115adf4bae0bd22fdb0:.planning/slice-plans/016-x11-clear-packaged-apps/PLAN.md`) ("on CI Linux the classification is expected to be `display`"); CI run https://github.com/terryyin/clipboard/actions/runs/41773836492 (e600e48) "Lint and package (Nix)" printed `failure libx11`; obligation O1; developer chose option 1; fixes 9f5e5ff, a7c6e5a; CI run https://github.com/terryyin/clipboard/actions/runs/41776839169 printed `failure display`
  - Observed effect: Execution stopped for a human decision after slice 2 publication; three extra commits and CI waits (about 2–5 minutes each)
  - Inference: A premise about this project's CI environment should be checked against that job's actual shell (here `nix develop` on ubuntu-latest, not the system Python) before it backs a key example; the source-only review's separate E5a commitment is what exposed the mismatch, since the rule R4.8 alone accepted either value

<a id="dd-026"></a>

## DD-026 — Nix shell variable merged onto the mkShell result, so CI never saw it
`pkgs.mkShell { … } // optionalAttrs isLinux { VAR = …; }` attaches `VAR` to
the derivation value, not to `mkShell`'s arguments, so it is not exported to
the shell. The check treated an absent variable as "libX11 not supplied" and
accepted `libx11`, so CI went green without the intended `display` proof.

### Occurrences
- Execution: SEED-001#x11-clear-packaged-apps
  - Timestamp: 2026-11-04T05:00:30Z
  - Tool: Claude Code
  - Model: claude-opus-5-5
  - Open Dough release: 0.3.82
  - Evidence: 9f5e5ff `flake.nix`; local proof `nix eval … devShells.x86_64-linux.default.CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR` (derivation attribute, not `drvAttrs`); CI run https://github.com/terryyin/clipboard/actions/runs/41776343130 green with `failure libx11`; fix a7c6e5a `mkShell ({ … } // …)` with `drvAttrs ? CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR` true on x86_64-linux
  - Observed effect: One misleading green CI run and one extra fix cycle (about 5 minutes)
  - Inference: Prove a dev-shell variable through `drvAttrs` or by printing it inside that platform's shell; a check whose strictness depends on a variable being present should be paired with proof that the variable arrives

<a id="dd-030"></a>

## DD-030 — Multi-OS matrix bash steps first failed under Windows PowerShell (local facet)
`.github/workflows/desktop-free-tests.yml` runs across `ubuntu`/`macos`/`windows`, where Windows runners default to PowerShell. Adding POSIX shell conditionals (`if`, `$?`, `RUNNER_TEMP`) to that matrix without `shell: bash` failed the Windows jobs on `30f503ec` (run 42027483878) until `15d276ba` declared `shell: bash` on the pytest and fragment steps (green run 42028715651).

Responsibility (triage 2026-11-07): local workflow facet repaired at `15d276ba`; the shared `ci-proof-summary.md` recipe facet remains in [DearDough.md](DearDough.md#dd-030) with the single `SEED-004#publish-clipboard-ci-proof` execution counted once (recovery `434d72b7d720903c3c488edbb3316b99cd2feeb0:DearDough.md#dd-030`). No new local story.

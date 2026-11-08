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

Local evidence compaction recovery: `6db9e349c080b403ffc88352d61df5ddb3e5945c:ProjectFindings.md` preserves the original occurrence rows.

## DD-001 — Optional-extra local proof not mirrored on CI matrix path

The desktop-free matrix used bare `uv sync/run --locked` while Makefile proof included Pillow. `SEED-001#read-images` (2026-11-02T10:42:00+07:00, Cursor, 0.3.79) passed local Nix quality but failed every OS/Python cell at slice 1 ([CI 41384361341](https://github.com/terryyin/clipboard/actions/runs/41384361341), `f30e269`, transcripts `57a69224…`/`7f955186…`). Repair `48e8266` aligned the matrix with `--extra images` after stashing slice 2 work. Both commands remain project-owned and separate. Observe the next optional extra entering pytest before closing.

## DD-010 — Desktop-free unavailable-path test asserted host OS

Desktop-free tests encoded platform features of the runner. [SEED-003#host-independent-desktop-free-tests](https://github.com/terryyin/clipboard/blob/066dae4c79d0d9a9dbecf37c4f8c189960fea1f8/.planning/seeds/SEED-003-host-independent-tests.md#host-independent-desktop-free-tests) (`05d2e02`, `5380548`, completion `066dae4`) adopted `fake_platform` and a guard against global patching. [CI 41656910713](https://github.com/terryyin/clipboard/actions/runs/41656910713) passed the desktop-free matrix, including pretend-Darwin and X11 owner-shutdown tests on Windows. Keep the wider finding open until a newly added platform-branch test exercises the adopted guard on the matrix.

- `SEED-001#read-files` (2026-11-02T17:45:49+07:00, Cursor auto, 0.3.82): an unavailable-stub test asserted the host was non-Windows. Run [41430900179](https://github.com/terryyin/clipboard/actions/runs/41430900179) failed on Python 3.10/3.14 Windows; `b00d9ab` forced Darwin. See transcript `eb2ce85d…` and observer `watch-8h3joP`. One CI repair, distinct from DD-005 wording coupling.
- `SEED-001#portable-text` (2026-11-02T22:40:30+07:00, Claude Code Opus 5.5, 0.3.82): fixture assumed `os.killpg` exists. [Run 41471306541](https://github.com/terryyin/clipboard/actions/runs/41471306541) failed on Windows; `c086e20` fixed the fixture and added the product fallback. Later slices briefed the assumption and passed.
- `SEED-001#copy-files` (2026-11-03T08:20:26+07:00, Claude Code Opus 5.5, 0.3.82): POSIX-only fixture names and a global Darwin patch caused two Windows repair cycles (~5 minutes each) without product edits ([41558761684](https://github.com/terryyin/clipboard/actions/runs/41558761684), [41559117116](https://github.com/terryyin/clipboard/actions/runs/41559117116), repairs `5df300b`/`152faa2`). Later writers faked module-local `sys` and passed on all matrix hosts.

<a id="dd-025"></a>

## DD-025 — Plan premise predicted a CI classification without observing the CI environment

`SEED-001#x11-clear-packaged-apps` (2026-11-04T04:34:03Z, Claude Code Opus 5.5, 0.3.82) expected `display` in plan 016 premise 3 at `8ffb856`, after observing `libx11` on macOS. CI's Linux Nix shell lacked libX11 ([41773836492](https://github.com/terryyin/clipboard/actions/runs/41773836492), `e600e48`), stopping execution for the developer and three commits/CI waits (~2–5 minutes each). E5a in the source-only review exposed the gap; rule R4.8 accepted either outcome.

The shared [ODF-074 premise facet](DearDough.md#odf-074--native-venue-helper-and-probe-premises-entered-gated-ci-unverified) and local DD-026 export mistake below occurred in the same execution. `9f5e5ff` and `a7c6e5a` corrected the local configuration and [CI 41776839169](https://github.com/terryyin/clipboard/actions/runs/41776839169) observed `failure display`. The CI-environment proof now reaches the original example. No new local story.

<a id="dd-026"></a>

## DD-026 — Nix shell variable merged onto the mkShell result, so CI never saw it

In the DD-025 execution (2026-11-04T05:00:30Z, Claude Code Opus 5.5, 0.3.82), `9f5e5ff` put the Linux-only `CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR` on the derivation result instead of passing it to `mkShell`. `nix eval` showed the attribute but [CI 41776343130](https://github.com/terryyin/clipboard/actions/runs/41776343130) went green with `failure libx11`, one misleading result and an extra ~5-minute repair cycle. `a7c6e5a` merges into the arguments. Check `drvAttrs` or print the value inside the actual shell; [CI 41776839169](https://github.com/terryyin/clipboard/actions/runs/41776839169) then saw `failure display`.

<a id="dd-030"></a>

## DD-030 — Multi-OS matrix bash steps first failed under Windows PowerShell (local facet)
`.github/workflows/desktop-free-tests.yml` runs across `ubuntu`/`macos`/`windows`, where Windows runners default to PowerShell. Adding POSIX shell conditionals (`if`, `$?`, `RUNNER_TEMP`) to that matrix without `shell: bash` failed the Windows jobs on `30f503ec` (run 42027483878) until `15d276ba` declared `shell: bash` on the pytest and fragment steps (green run 42028715651).

Responsibility (triage 2026-11-07): local workflow facet repaired at `15d276ba`; the shared `ci-proof-summary.md` recipe facet remains in [DearDough.md](DearDough.md#dd-030) with the single `SEED-004#publish-clipboard-ci-proof` execution counted once (recovery `434d72b7d720903c3c488edbb3316b99cd2feeb0:DearDough.md#dd-030`). No new local story.

# Clipboard Project Findings


Clipboard owns findings in its code, tests and CI. [DearDough.md](DearDough.md) owns shared guidance findings and DD numbering across both records. The 2026-11-03 move of DD-001/005/010 is recoverable at `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`. Original occurrence rows are also available at `6db9e349c080b403ffc88352d61df5ddb3e5945c:ProjectFindings.md`.

- **DD-005 retired 2026-11-04.** `c5e10c3` corrected the Windows image-write stub. SEED-003 adopted `fake_platform` (`5380548`, recorded at `663dca6)) and CI 41656910713 passed the desktop-free matrix. Recovery: `2c4149d49df4a08fac54932eef1d72ef67a774f4:ProjectFindings.md`.
- **DD-010 retired 2026-11-10.** Guard `066dae4` and new platform variants including `24938ab` were exercised by CI 41829466322 on Windows Python 3.10/3.14. No host-assumption repair followed through `cf20181`; run 42027483878 was DD-030's distinct shell failure.
- **DD-025/026 retired 2026-11-10.** `9f5e5ff`/`a7c6e5a` corrected Nix and CI 41776839169 showed the expected failure display. Shared facet: [ODF-074](DearDough.md#odf-074--native-venue-helper-and-probe-premises-entered-gated-ci-unverified).
- **DD-030 retired 2026-11-10.** `15d276b` declared Bash for the matrix. CI 42028715651 and later desktop-free jobs through `cf20181` passed. Shared facet: [ODF-445](DearDough.md#odf-445--multi-os-matrix-bash-steps-first-failed-under-windows-powershell).

DD-010/025/026/030 recovery: `cf2018106f4338a7a1789e7c5dd1fec2e397a171:ProjectFindings.md`.

## DD-001 — Optional-extra local proof not mirrored on CI matrix path

The desktop-free matrix used bare `uv sync/run --locked` while Makefile proof included Pillow. `SEED-001#read-images` (2026-11-02T10:42:00+07:00, Cursor, 0.3.79) passed local Nix quality but failed every OS/Python cell at slice 1 ([CI 41384361341](https://github.com/terryyin/clipboard/actions/runs/41384361341), `f30e269`, transcripts `57a69224…`/`7f955186…`). Repair `48e8266` aligned the matrix with `--extra images` after stashing slice 2 work. Both commands remain project-owned and separate. Observe the next optional extra entering pytest before closing.

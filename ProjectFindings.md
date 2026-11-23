# Clipboard Project Findings

Clipboard owns findings in its code, tests and CI. [DearDough.md](DearDough.md) owns shared guidance findings and DD numbering across both records. The 2026-11-03 move of DD-001/005/010 is recoverable at `cc46e7d94343869b7a704e20a1dca77723b066aa:DearDough.md`. Original occurrence rows are also available at `6db9e349c080b403ffc88352d61df5ddb3e5945c:ProjectFindings.md`.

[Retirement proofs and recovery for DD-005/010/025/026/030](https://github.com/terryyin/clipboard/blob/99121548d349c718975f46ea91f2d3f296b8fc90/ProjectFindings.md#clipboard-project-findings).

## DD-001 — Optional-extra local proof not mirrored on CI matrix path

The desktop-free matrix used bare `uv sync/run --locked` while Makefile proof included Pillow. `SEED-001#read-images` (2026-11-02T10:42:00+07:00, Cursor, 0.3.79) passed local Nix quality but failed every OS/Python cell at slice 1 ([CI 41384361341](https://github.com/terryyin/clipboard/actions/runs/41384361341), `f30e269`, transcripts `57a69224…`/`7f955186…`). Repair `48e8266` aligned the matrix with `--extra images` after stashing slice 2 work. Both commands remain project-owned and separate. Observe the next optional extra entering pytest before closing.

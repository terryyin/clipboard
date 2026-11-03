# Plan: Bound the X11 file-list write and prove directories and duplicates natively

**Identity:** SEED-001#bounded-x11-file-write
**Source:** [Bound the X11 file-list write and prove directories and duplicates natively](../../seeds/SEED-001-clipboard-true-to-its-name.md#bounded-x11-file-write)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Provenance

Retrospective correction of SEED-001#copy-files (story and plan
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#copy-files` and
`.planning/slice-plans/008-copy-files/PLAN.md`, recoverable from branch
`claude/copy-local-file-references-into-file-managers` at c30ff90; first-parent
commits fbafe60..c30ff90, excluding trunk merge a580bb1; net diff
`git diff 93ab158 c30ff90`). The X11 writer came from slice 5 (6562a75,
44086d0); the probes from slices 3–6.

## Current findings

1. **Unbounded X11 file-list write (defect).**
   `clipboard/_files_native_x11_writer.py` `_start_owner` does
   `proc.stdin.write(body); proc.stdin.close()` on a pipe with no deadline;
   the 10 s bound only covers the later TARGETS/read-back loop. On a stalled
   X server a `text/uri-list` body larger than the pipe buffer (about 64 KiB,
   roughly 1,000 long paths) blocks `copy_files` indefinitely, contradicting
   the module docstring and the story's bounded-failure promise ("Missing
   helper, unsupported session, denied access, or transfer failure raises
   `ClipboardContentError`; never silent success"). Same root as
   SEED-001#bounded-x11-text-write finding 1, in a different subsystem.
   `tests/fake_xclip_files.py` owners never block, so tests miss it.
2. **Native proof misses directories, duplicates and relative paths (proof
   gap).** All four `scripts/probe_*_native_copy_files.py` pass two absolute
   file paths only; directories (story: "files and directories alike are
   offered"), duplicates ("order and duplicates pass through") and relative
   paths (key example 4, native `paste_files()`) are proven only against the
   in-memory fake (`tests/test_copy_files_contract.py`). Concrete risk: the
   macOS writer's directory trailing-slash branch and its read-back
   ("kept N of M") are unobserved for a duplicate or a directory.

## Preserved promises and constraints

- `copy_files` validation, error types and messages (install hints,
  "exited with status", bound wording), the `text/uri-list` CRLF body, the
  background-owner lifetime, TARGETS plus exact-body read-back, the session
  rule, and every non-X11 writer stay as they are.
- If a native probe shows a platform cannot offer a duplicate or a directory
  as promised, stop and return that observation as a story decision; do not
  weaken the promise or the probe.
- Excluded: the text and image writers' identical pipe-write pattern
  (SEED-001#bounded-x11-text-write owns the text one), extracting a shared
  Linux owner helper, and file-manager evidence limits.

## Outside-in proof

| Finding | Observable signal | Owning slice |
| --- | --- | --- |
| 1 | Desktop-free test with a real fake owner process (a Python script via `sys.executable`, so it runs on every CI OS) that never reads stdin: `copy_files` over a URI list larger than 64 KiB raises `ClipboardContentError` within a shrunk bound plus margin; fails before the fix | 1 |
| 1 | `tests/test_copy_files_x11_writer.py` green; gated `native-linux-x11-copy-files` green | 1 |
| 2 | Each gated probe also offers a directory, a duplicate and a relative path (relative to the probe's cwd) and its independent consumer reads them as absolute paths in order; `paste_files()` agrees; X11/Wayland/Windows jobs green; macOS probe run recorded with floors | 2 |
| Regression | `nix develop -c make check`; full CI green | 1, 2 |

## Ordered slices

### 1. Bounded X11 file-list owner input
Type: Behavior
Status: planned
Proof: rows 1–2 above. Candidate fix: write the body to an unlinked
temporary file, seek to 0 and pass it as the owner's stdin (no pipe), or
otherwise bound the write by the shared deadline; choose and justify, and
align with SEED-001#bounded-x11-text-write's choice when it has landed.

### 2. Native proof for directories, duplicates and relative paths
Type: Behavior
Status: planned
Proof: row 3 above.

## Current decisions

- Correction stays inside the file-list subsystem.

## Learnings

_(none yet)_

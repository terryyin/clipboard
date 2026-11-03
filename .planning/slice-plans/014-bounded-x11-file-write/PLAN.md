# Plan: Bound the X11 file-list write and prove directories and duplicates natively

**Identity:** SEED-001#bounded-x11-file-write
**Source:** [Bound the X11 file-list write and prove directories and duplicates natively](../../seeds/SEED-001-clipboard-true-to-its-name.md#bounded-x11-file-write)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Provenance

Retrospective correction of SEED-001#copy-files (story and plan recoverable
at before-cleanup commit d86f90d:
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#copy-files` and
`.planning/slice-plans/008-copy-files/PLAN.md`; first-parent commits
fbafe60..6ddb51d, excluding trunk merge a580bb1; net diff
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
Status: done
Proof: rows 1–2 above.

Behavior: Linux X11 session with `xclip` on `PATH` whose owner never reads
its input (stalled display) → `copy_files(paths)` whose `text/uri-list` body
is larger than a pipe buffer → `ClipboardContentError` within the 10 s write
bound, the owner's process group signalled, as for a short list today.

`_start_owner` writes the body to an unlinked `tempfile.TemporaryFile()`,
seeks to 0 and passes it as the owner's `stdin` (closed once the owner has
it); Python never writes to a pipe, so the `BrokenPipeError` handling and
`FakeUriListOwner`'s broken-pipe mode go away, and an early exit is still
reported from status and the stderr log. `FakeX11Files.popen` reads the body
from the stdin file instead of asserting `subprocess.PIPE`. The new
real-process test stubs `os.killpg` with `raising=False`, as the existing
writer fixture does, so it terminates its own child on Windows CI too.

### 2. Native proof for directories, duplicates and relative paths
Type: Behavior
Status: done
Proof: row 3 above.

Behavior: each desktop's gated `copy_files` probe → a further offer-level
round copies `[<relative file>, <directory>, <same file again>]` from a
child Python process whose cwd is the probe's source folder, and exits → the
platform's existing independent consumer (`xclip -o`, `wl-paste`,
PowerShell 5.1 `-STA` CF_HDROP reader, `osascript` `public.file-url` items)
reads three absolute paths in that order, directory included, and
`paste_files()` agrees.

The existing two-file round, including its Thunar / Explorer paste, stays as
it is: a duplicate entry would collide in a file-manager paste, and
file-manager evidence is excluded. If a consumer shows a platform drops or
merges the duplicate or the directory, stop under the preserved-promise rule
above.

## Decisive premises

Observed in this workspace (Darwin, `nix develop -c uv run`), scratch edits
reverted:

- **Symptom (finding 1).** `_x11_files_clipboard_writer` with
  `_XCLIP_URI_LIST_WRITE_CMD` pointed at a `sys.executable` script that only
  sleeps, TARGETS stubbed empty, write bound 1 s, 6 s thread watchdog:
  10 paths (1,100-byte body) → `ClipboardContentError after 1.0s`;
  2,000 paths (220,000-byte body) → `STILL BLOCKED at 6s watchdog`.
- **Fix (slice 1).** Same harness with the temp-file `stdin` applied:
  2,000 paths → `ClipboardContentError after 1.0s`. With that edit in
  `clipboard/_files_native_x11_writer.py`,
  `uv run --all-extras pytest -q tests` → 9 failed, 519 passed, 24 skipped
  (baseline 528 passed), all in `tests/test_copy_files_x11_writer.py` through
  `FakeX11Files.popen` / `FakeUriListOwner`: those are the consumers slice 1
  adapts.
- **macOS duplicate and directory (slice 2's riskiest platform).** From a cwd
  holding `report final.pdf` and `a dir/`, default-writer
  `copy_files(["report final.pdf", "a dir", "report final.pdf"])` succeeded
  (no "kept N of M"); an independent `osascript` AppKit read returned three
  `public.file-url` items in order (`…/report%20final.pdf`,
  `…/a%20dir/`, `…/report%20final.pdf`) and `paste_files()` returned the
  three absolute paths. The prior text clipboard was restored afterwards.
  X11, Wayland and Windows consumers are proved by their gated CI jobs.

## Current decisions

- Correction stays inside the file-list subsystem.
- Feed `xclip` a temp-file `stdin` rather than a bounded pipe-writer thread,
  matching SEED-001#bounded-x11-text-write's recorded decision (no
  partial-write or `BrokenPipeError` handling; the owner's input is complete
  before it starts). Neither correction extracts a shared helper.
- The directory/duplicate/relative proof is a separate offer-level round in
  each probe; file-manager pastes keep the two-file round.

## Plan review

Slice-plan refinement not needed: two independent findings map to two
slices with their own proof, slice 1's consumers and slice 2's riskiest
native premise were observed, and no boundary, design, proof or sizing
concern remains. No remaining slice-specific concerns were identified.

## Learnings

- Temp-file stdin means FakeX11Files must read the body at `popen` time; the
  old pipe `write`/`close` / broken-pipe protocol is gone.
- The real-process stall proof needs a `killpg` stub with `raising=False` that
  still terminates the child (Windows CI has no `os.killpg`).
- File-size gate: keep the stall case in
  `tests/test_copy_files_x11_writer_stall.py` beside the FakeX11Files suite.
- Relative-round expected paths must `Path.resolve()`; macOS writers publish
  `/private/tmp` while `abspath` keeps `/tmp`.
- Shared relative-round helpers live in
  `scripts/copy_files_native_probe_support.py` so probes stay under the
  file-size gate.

## Accepted proof (slice 1)

- `nix develop -c uv run --locked --extra images pytest -q tests/test_copy_files_x11_writer.py tests/test_copy_files_x11_writer_stall.py` → 12 passed
- Product: `_start_owner` feeds an unlinked `TemporaryFile` as stdin (no pipe write)
- Gated `native-linux-x11-copy-files` left to CI after publish

## Accepted proof (slice 2)

- `nix develop -c uv run --locked --extra images pytest -q tests/test_copy_files_native_*.py` → 29 passed, 4 skipped
- Live macOS: `CLIPBOARD_NATIVE_PROBE=1 … scripts/probe_macos_native_copy_files.py` → ok, three absolute paths (directory + duplicate + relative) agree
- Expected paths use `Path.resolve()` so `/tmp` vs `/private/tmp` matches writers
- Gated X11/Wayland/Windows native jobs left to CI after publish

## Execution complete

Product advice: no-change

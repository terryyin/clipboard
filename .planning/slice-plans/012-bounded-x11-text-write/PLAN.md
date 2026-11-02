# Plan: Bound the X11 text write for large text on a stalled display

**Identity:** SEED-001#bounded-x11-text-write
**Source:** [Bound the X11 text write for large text on a stalled display](../../seeds/SEED-001-clipboard-true-to-its-name.md#bounded-x11-text-write)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Provenance

Retrospective correction of SEED-001#portable-text (plan
`slice-plans/010-portable-text/PLAN.md`, commits 9c55992..0402674 on branch
`claude/use-the-text-clipboard-reliably-and-diagnose-una`, excluding trunk
merge 42c0a6f). The X11 writer came from slice 4 (8a816be, c086e20,
43ee728); the Wayland wrapper from slice 5 (823dcce).

## Current findings

1. **Unbounded X11 write (defect).** `clipboard/_text_native_x11.py`
   `_start_owner` does `proc.stdin.write(data); proc.stdin.close()` on a pipe
   with no deadline; the 10 s bound only covers the later read-back loop.
   `xclip` opens the display before reading stdin, so on a stalled X server a
   text larger than the pipe buffer (about 64 KiB) blocks `copy()`
   indefinitely. Reproduced read-only: fake `xclip` (`exec sleep 40`) on
   `PATH`, 1,000 chars → `ClipboardContentError` at 10.0 s; 200,000 chars →
   still blocked at a 20 s watchdog. Contradicts the story's "Failure arrives
   within a documented bound of seconds" / "never an indefinite wait", the
   README Usage bound ("each `copy()` shares one 10 s bound"), and the module
   docstring. Existing tests miss it because `tests/fake_xclip_text.py`
   `FakeOwner.write` never blocks.
2. **Test-only production branch (residue).** `_stop_owner`
   (`clipboard/_text_native_x11.py` ~119–122) falls back to `proc.kill()`
   when `os.killpg` is missing, but the X11 owner is only selected on Linux,
   where `os.killpg` exists; only
   `test_owner_is_killed_directly_where_process_groups_do_not_exist` and
   `FakeOwner.kill` reach it. The Windows unit-test problem it answered is
   already solved by the fixture's `raising=False`.
3. **Wayland wrapper skips on an evidence limit (doc/test inconsistency).**
   `tests/test_text_native_linux_wayland.py` `pytestmark` skips when
   `WAYLAND_DISPLAY`, `wl-copy` or `wl-paste` is missing although its
   docstring and README ("each wrapper … fails rather than skips on an
   evidence limit") say it fails; CI's workflow checks mask this, a local
   gated run does not.

## Preserved promises and constraints

- X11 `copy()` leaves a background `xclip` owner that outlives Python, returns
  only once that owner serves exactly the written bytes as `UTF8_STRING`,
  quotes `xclip`'s stderr on early exit, kills the owner's process group on
  timeout, and raises `ClipboardContentError` within the 10 s bound.
- No change to the public API, macOS, Wayland or Windows paths, session
  selection, messages, or README promises (finding 1's fix makes the existing
  bound statement true).
- Excluded: the same pipe-write pattern in `clipboard/_image_write.py`
  (image subsystem; needs its own authorization) and the per-call
  `pyperclip.is_available()` delegation rule (a separate product decision).

## Outside-in proof

| Finding | Observable signal | Owning slice |
| --- | --- | --- |
| 1 | Desktop-free test running a real fake owner process (a Python script via `sys.executable`, so it runs on every CI OS) that never reads stdin: `copy("a" * 200_000)` raises `ClipboardContentError` within a shrunk write bound plus margin; fails before the fix | 1 |
| 1 | Existing `tests/test_text_x11.py` writer tests still pass (fake adapted to the new stdin) | 1 |
| 1 | Gated CI `native-linux-x11-text` stays green (owner start path changed) | 1 |
| 2 | Fallback, its test and `FakeOwner.kill` removed; `tests/test_text_x11.py` green on all CI OSes | 2 |
| 3 | Wayland wrapper skips only off Linux or without `CLIPBOARD_NATIVE_PROBE=1`; a desktop-free test shows it fails on a missing session/helper report; CI `native-linux-wayland-text` green | 2 |
| Regression | `nix develop -c make check`; full CI green | 1, 2 |

## Ordered slices

### 1. Bounded X11 owner input
Type: Behavior
Status: planned
Proof: as rows 1–3 above. Candidate fix: write the UTF-8 bytes to an unlinked
temporary file, seek to 0 and pass it as the owner's stdin (no pipe, no
`BrokenPipeError` handling), or otherwise bound the write by the shared
deadline; choose and justify.

### 2. Remove test-only fallback and make the Wayland wrapper fail-not-skip
Type: Structure
Status: planned
Proof: as rows 4–5 above.

## Current decisions

- Correction stays inside the text subsystem.

## Learnings

_(none yet)_

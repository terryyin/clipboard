# Plan: Bound the X11 text write for large text on a stalled display

**Identity:** SEED-001#bounded-x11-text-write
**Source:** [Bound the X11 text write for large text on a stalled display](../../seeds/SEED-001-clipboard-true-to-its-name.md#bounded-x11-text-write)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Provenance

Retrospective correction of SEED-001#portable-text (story and plan recoverable
at before-cleanup commit ae8e7a2:
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#portable-text` and
`.planning/slice-plans/010-portable-text/PLAN.md`; commits 9c55992..0402674 on branch
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
  `pyperclip.is_available()` delegation rule. The maintainer accepted explicit
  delegation on 2026-11-03; that compatibility change belongs to the separate
  [SEED-001#explicit-text-delegation story](../../seeds/SEED-001-clipboard-true-to-its-name.md#explicit-text-delegation),
  queued after this correction.

## Outside-in proof

| Finding | Observable signal | Owning slice |
| --- | --- | --- |
| 1 | New desktop-free test running a real fake owner process (a Python script via `sys.executable`, so it runs on every CI OS) that never reads stdin: `copy("a" * 200_000)` on the X11 path raises `ClipboardContentError` within a shrunk write bound plus margin. A thread watchdog makes the pre-fix run fail instead of hanging the suite | 1 |
| 1 | Existing `tests/test_text_x11.py` and `tests/test_text_native_linux_bound.py` writer tests pass with `FakeX11.popen` reading the owner's stdin file | 1 |
| 1 | Gated CI `native-linux-x11-text` stays green (real `xclip` reading a file stdin) | 1 |
| 2 | Fallback, `test_owner_is_killed_directly_where_process_groups_do_not_exist` and `FakeOwner.kill` removed; `tests/test_text_x11.py` green on all CI OSes | 2 |
| 3 | Wayland wrapper skips only off Linux or without `CLIPBOARD_NATIVE_PROBE=1`; CI `native-linux-wayland-text` green | 3 |
| Regression | `nix develop -c make check` (AGENTS.md "Check Python"); full CI green | 1, 2, 3 |

## Ordered slices

### 1. Bounded X11 owner input
Type: Behavior
Status: planned
Proof: rows 1–3 above.

Behavior: Linux X11 session with `xclip` on `PATH` whose owner never reads
its input (stalled display) → `copy()` of text larger than a pipe buffer →
`ClipboardContentError` within the 10 s write bound, the owner's process
group signalled, as for small text today.

`_start_owner` writes the UTF-8 bytes to an unlinked
`tempfile.TemporaryFile()`, seeks to 0 and passes it as the owner's `stdin`;
Python never writes to a pipe, so `BrokenPipeError` handling and the
`FakeOwner` broken-pipe mode go away (an early exit is still reported from
status and the stderr log). The new real-process test stubs
`os.killpg` with `raising=False` to terminate its own child, because
Windows has no `os.killpg` and slice 2 removes the fallback.

### 2. Remove the test-only process-group fallback
Type: Structure
Status: planned
Proof: row 4 above.

Correction: `_stop_owner` calls `os.killpg` directly; the `proc.kill()`
branch, its test and `FakeOwner.kill` go. Removes a production branch only
tests reach (the owner is selected only on Linux). Preserved behavior:
`test_owner_that_never_offers_raises_after_the_bound` still observes the
group kill.

### 3. Wayland text wrapper fails rather than skips on an evidence limit
Type: Structure
Status: planned
Proof: row 5 above.

Correction: drop the `WAYLAND_DISPLAY` / `wl-copy` / `wl-paste` `skipif`
from `tests/test_text_native_linux_wayland.py` so the probe's evidence-limit
report (exit 2) fails the wrapper, as its docstring, the README and the X11
wrapper already do; update the now-stale "The probe wrapper skips without
these" comment in `.github/workflows/native-wayland-text.yml`.

## Decisive premises

Observed in this workspace (Darwin, `nix develop -c uv run`), scratch edits
reverted:

- **Symptom (finding 1).** `_x11_text_clipboard_writer` with
  `_XCLIP_WRITE_CMD` pointed at a `sys.executable` script that only sleeps,
  write bound 1 s, 6 s thread watchdog: 1,000 chars →
  `ClipboardContentError after 1.0s`; 200,000 chars →
  `STILL BLOCKED at 6s watchdog`.
- **Fix (slice 1).** Same harness with the temp-file `stdin` applied:
  200,000 chars → `ClipboardContentError after 1.0s`. With that edit,
  `pytest tests/test_text_x11.py tests/test_text_native_linux_bound.py`
  → 8 failed, 18 passed, all through `FakeX11.popen` asserting
  `stdin is subprocess.PIPE`: those writer tests are the consumers slice 1
  adapts. `scripts/linux_x11_native_text_support.py` has its own small
  probe-producer pipe write and is not a consumer.
- **Fallback consumers (slice 2).** `_stop_owner` reduced to a direct
  `os.killpg`: `uv run --all-extras pytest -q tests` → 1 failed
  (`test_owner_is_killed_directly_where_process_groups_do_not_exist`),
  431 passed, 20 skipped. Without `os.killpg` the call surfaces as a
  `ClipboardContentError`, hence slice 1's test stub.
- **Wrapper discrimination (slice 3).** With the wrapper's `pytestmark`
  emptied, `CLIPBOARD_NATIVE_PROBE=1 pytest
  tests/test_text_native_linux_wayland.py` → failed on
  `assert result.returncode == 0` (`assert 2 == 0`, report
  `"evidence_limit": true`). Real `xclip` and Sway behavior are proved by the
  gated CI jobs.

## Current decisions

- Correction stays inside the text subsystem.
- Feed `xclip` a temp-file `stdin` rather than adding a bounded pipe-writer
  thread: no partial-write or `BrokenPipeError` handling, and the owner's
  input is complete before it starts.
- Excluded with the image writer: `tests/test_paste_html_native_linux_wayland.py`
  keeps its `WAYLAND_DISPLAY` skip (HTML subsystem).

## Plan review

Slice-plan refinement not needed: the former slice 2's two independent proof
loops were split into slices 2 and 3 while planning, and no other boundary,
design, proof or sizing concern remains. No remaining slice-specific concerns
were identified.

## Learnings

_(none yet)_

# Plan: Bound every helper-owner clipboard write behind one launcher

**Identity:** SEED-001#bounded-helper-owner-write
**Source:** [Bound every helper-owner clipboard write behind one launcher](../../seeds/SEED-001-clipboard-true-to-its-name.md#bounded-helper-owner-write)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

`copy_image` on Linux X11 and Wayland fails with `ClipboardImageError`
within one documented 10 s bound instead of hanging (X11) or waiting 30 s
(Wayland), and an X11 image write succeeds only when its own `xclip` serves
exactly the written PNG. Every Linux helper-owner write that hands over a
payload (X11 `xclip -i` for text, file list, image; Wayland `wl-copy` for
text, file list, image) starts its helper through one private launcher in
`clipboard/_desktop`. Scope, the required readiness change and its reason,
and key examples 1–6 are in the seed section; this plan adds none.

**Excluded** (seed scope limits): macOS `osascript` and Windows writes,
payload-free runs (`wl-copy --clear`, the X11 clear child), readers, a
Wayland read-back confirmation, a configurable bound, Linux `copy_html`.

## Assumptions and direction

- Follows the North Star topic: same failure model (helper failures raise,
  never silent success), fakes in default CI, native claims only with
  independent consumers and stated evidence limits. No revision needed.
  No ADR store exists; no Accepted ADR constrains this plan. AGENTS.md
  binds: shared Linux helper mechanics live in `clipboard/_desktop` and
  content-kind modules must not copy them.
- **PFE.** Reuse: the unlinked-temp-file launcher already exists twice
  (`_text_native_x11._start_owner`, `_files_native_x11_writer._start_owner`)
  and the owner stop once (`_text_native_x11._stop_owner`, imported by the
  file-list writer); the bounded readiness loops (poll + exact read-back)
  exist in both X11 writers, and `_remaining` / `_helper_log_suffix` in
  `clipboard/_text_native_linux`. **Gap:** no shared launcher; the image
  writers bypass both. One new concept: a launcher
  `_start_helper_owner(cmd, payload, log) -> Popen` in `clipboard/_desktop`
  (payload into an unlinked `tempfile.TemporaryFile` as `stdin`,
  `start_new_session=True`, `stdout=DEVNULL`, `stderr=log`; `OSError` from
  `Popen` or the temp-file write propagates for the caller to map) and the
  owner-session stop beside it. Callers keep deadlines, readiness, and
  messages. No generic "write framework": the readiness loops stay per
  caller because each confirms a different offer.
- Bound: `copy_image` on Linux reuses `_LINUX_TEXT_TIMEOUT_S` (10 s), the
  value `copy` / `copy_files` document, rather than a new constant; the
  X11 TARGETS-only `_wait_xclip_image_png_offer` is replaced by an exact
  `image/png` read-back (each read bounded by the remaining time, a 2 s
  read cap as the text writer uses).
- Desktop-free stall tests follow `tests/test_text_x11_write_stall.py`: a
  real `sys.executable` owner that never reads, monkeypatched command and
  bound, `os.killpg` faked (`raising=False`, POSIX-only), watchdog thread,
  assert error type plus the named helper and bound, not copied wording
  (AGENTS.md). They must pass on every matrix OS.
- Preparation checkout: Darwin 25.6.0, this workspace. Linux X11 and
  Wayland native proof runs in GitHub Actions after a branch push (Native
  Linux X11 copy_image / text / copy_files under Xvfb, Native Linux
  Wayland copy_image / text / copy_files under Sway).
- Local gate (AGENTS.md): `nix develop -c make check` every slice. No
  packaging, `__all__`, or workflow change, so `make test-package` and
  `make lint-workflows` are not required locally (CI still runs them).

## Outside-in proof

| Example / promise (seed) | Observable signal | Owning slice |
| --- | --- | --- |
| 1. X11, non-reading `xclip`, PNG above 64 KiB → `ClipboardImageError` within the bound, owner session stopped | New desktop-free stall test through public `clipboard.copy_image` with `_write_linux_xclip` installed: real non-reading owner, bound monkeypatched to 1 s, raises `ClipboardImageError` naming `xclip` and the bound within bound + margin; faked `killpg` received the owner's pid. Fails today (watchdog: still blocked) | 1 |
| 2. X11, previous owner lists `image/png`, new owner never serves → raises, not success | Desktop-free: same stand-in with a small PNG and TARGETS / read-back stubbed to the previous owner's offer (`image/png` listed, different bytes) → `ClipboardImageError` within the bound. Fails today (returns in 0.03 s) | 1 |
| 3. X11 normal write returns after exact read-back; pastes after writer exit | Gated `tests/test_copy_image_native_linux_x11.py` (Xvfb job): independent `xclip -o -t image/png` consumer and writer-exit check stay green | 1 |
| 4. Wayland `wl-copy` never finishes → `ClipboardImageError` within 10 s with its stderr | Desktop-free: `_write_linux_wl_copy` with a stand-in that writes a line to stderr and sleeps without exiting, bound monkeypatched → raises within bound + margin, message carries the stderr line; owner started in its own session (launch kwargs observed) | 2 |
| 5. Large text / file list with a non-reading owner still raise within bound, through the launcher | Existing `tests/test_text_x11_write_stall.py`, `tests/test_copy_files_x11_writer_stall.py` unchanged and green; the per-writer `_start_owner` copies are gone (each X11 / Wayland writer calls `_desktop._start_helper_owner`) | 1 (X11), 2 (Wayland) |
| 6. Missing helper → caller's error with install hint; clipboard unchanged | Existing `tests/test_copy_image_failures.py` missing-`xclip` / missing-`wl-copy` tests and the text / file-list missing-helper tests stay green | 1, 2 |
| Temp file cannot be written → caller's error before any helper starts | Desktop-free: launcher test with `tempfile.TemporaryFile` raising `OSError` → `OSError` propagates, `Popen` never called; one writer-level test maps it to its error type | 1 |
| Wayland writes keep working through a temp-file `stdin` | Gated Sway jobs: Native Linux Wayland copy_image, text copy/paste, copy_files stay green | 2 |
| Documentation | README Bounds paragraph names the Linux `copy_image` 10 s bound; Linux image-write installation text names the background owner and the bound; Evidence notes the stalled owner is proved by desktop-free stand-ins only | 1 (X11), 2 (Wayland) |
| Regression | `nix develop -c make check` green; all native Linux jobs green after push | every slice |

## Decisive premises

Observed in this workspace (Darwin 25.6.0, branch
`claude/bound-every-helper-owner-clipboard-write-behind` at 1749a14, plus
the uncommitted seed refinement):

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| The local gate runs in this checkout | Every slice's `make check` | `nix develop -c make check` → `612 passed, 27 skipped in 20.25s` | Settled |
| Native Linux jobs are green at the start | Regression baseline for slices 1–2 | `gh run view 41786189679` (head 1749a14): Native Linux X11 copy_image / text / copy_files and Native Linux Wayland copy_image / text / copy_files all `success` | Settled for CI |
| The X11 image write blocks without bound on a non-reading owner | Example 1; slice 1's stall test must fail first | Scratch probe (job tmp, not committed): fake `xclip` = `exec sleep 3600` on `PATH`, `_image_write._write_linux_xclip` with a 480 622-byte PNG in a watchdog thread → still blocked after 12 s | Settled (symptom reproduced) |
| The X11 TARGETS-only readiness reports success for a stale `image/png` offer | Example 2; slice 1's readiness change | Scratch probe: same fake `xclip`, `_xclip_targets_lenient` returning `TARGETS\nimage/png\n`, 8×8 PNG → `_write_linux_xclip` returned success after 0.028 s | Settled (false success reproduced) |
| The Wayland image write is bounded today, at 30 s | Example 4 baseline (10 s is a shortening, not a new bound) | Scratch probe: fake `wl-copy` = `exec sleep 3600`, 480 909-byte PNG → `OSError: wl-copy clipboard write timed out` after 30.07 s | Settled |
| `xclip -o -t image/png` returns exactly the bytes `xclip -t image/png -i` read | Slice 1's exact read-back (example 3 success path) | The X11 native probe compares decoded samples, not bytes; the text writer's exact UTF8_STRING read-back is the same xclip mechanism and is green in CI, but image bytes are not yet observed | **Early probe** in slice 1: the branch push runs the Xvfb copy_image job; a timeout there stops slice 1 and changes the readiness rule (decode-and-compare) before slice 2 |
| `wl-copy` serves a payload read from a regular-file `stdin` as it does from a pipe | Slice 2's launcher use on Wayland | Not observable on this Mac | **Early probe** at the start of slice 2: the branch push runs the three Sway write jobs; a failure stops slice 2 and the Wayland writers keep their bounded pipe (scope decision for the developer) |

## Ordered slices

### 1. Bounded, self-confirmed X11 image write through one launcher
Type: Behavior
Status: done
Proof: new desktop-free tests through public `clipboard.copy_image` (examples
1, 2, temp-file failure) fail first, then pass; existing X11 text and
file-list stall tests and `tests/test_copy_image_failures.py` stay green;
`nix develop -c make check`; after push, Native Linux X11 copy_image, text
and copy_files jobs green (early probe for exact `image/png` read-back).

Behavior: Linux X11 session whose `xclip` never reads, or never takes
ownership while a previous owner still lists `image/png` → `copy_image` →
`ClipboardImageError` naming `xclip` and the 10 s bound, owner session
stopped; a working `xclip` → returns once `image/png` reads back the exact
PNG. Adds `_start_helper_owner` and the owner stop to `clipboard/_desktop`,
moves the X11 text and file-list writers onto them (deleting their
`_start_owner` copies), and documents the Linux X11 `copy_image` bound.

Accepted local proof (2026-11-04, Darwin): `tests/test_copy_image_x11_write_stall.py`
(examples 1, 2 and the writer-level temp-file test; all three failed first: blocked
past 6 s / returned success / `Popen` with `stdin=PIPE`) and
`tests/test_helper_owner_launcher.py` pass; `nix develop -c make check` →
621 passed, 27 skipped. The four existing X11 text / file-list fixtures now fake
`os.killpg` via `_desktop.os` (one line each; assertions unchanged). Refactor:
`_X11_FILES_WRITE_TIMEOUT_S` reuses `_LINUX_TEXT_TIMEOUT_S`; the full-temp-dir
stand-in lives in `tests/fake_full_temp_dir.py`. Native proof: GHA run
41802978191 on 7d55a1b — Native Linux X11 copy_image / text / copy_files (and
all Wayland jobs) success; the exact `image/png` read-back early probe holds,
so the readiness rule stays byte-exact.
Learning for slice 2: faking `subprocess.Popen` to substitute the stall command
while stubbing `subprocess.run` makes one test fail first on the old pipe code and
pass on the launcher; reuse it for the Wayland stand-in.

### 2. Wayland owner writes through the launcher, image bound at 10 s
Type: Behavior
Status: planned
Proof: early probe first (push, Sway write jobs green with temp-file
`stdin`); new desktop-free test for example 4 fails first (30 s bound, no
stderr detail) then passes; existing Wayland text / file-list / image
suites green; `nix develop -c make check`; Native Linux Wayland copy_image,
text and copy_files jobs green.

Behavior: Linux Wayland session whose `wl-copy` never finishes →
`copy_image` → `ClipboardImageError` within 10 s quoting `wl-copy`'s
stderr, helper started in its own session. Moves the Wayland text,
file-list and image writers' `wl-copy` start onto `_start_helper_owner`
(foreground-exit wait stays per caller, bounded by the remaining time;
`wl-copy --clear` keeps its payload-free run) and completes the README
bound text for Wayland.

Accepted local proof (2026-11-04, Darwin): `tests/test_copy_image_wayland_write_stall.py`
(example 4 failed first: blocked past 7 s on the old 30 s bound; temp-file test
failed first: `Popen` with `stdin=PIPE`), Wayland text / file-list temp-file tests
(`tests/test_text_wayland_writer.py`, `tests/test_copy_files_wayland_writer.py`,
failed first against the base writers); `nix develop -c make check` → 625
passed, 27 skipped. Refactor: Linux PNG owners moved to
`clipboard/_image_write_linux.py` (shared launch-error / exit-status helpers);
Wayland writer tests split into `tests/test_text_wayland_writer.py`. Wayland text
and file-list timeouts keep `proc.kill()` of the foreground helper (the story's
session stop is a `copy_image` promise). Pending: Native Linux Wayland copy_image /
text / copy_files (Sway) on the pushed revision — the temp-file `stdin` early
probe (commitments 17.4–17.6).

## Plan concern evidence

Slice-plan refinement was not needed: the launcher is introduced with its
first consumer and the two X11 writers that already duplicate it (one X11
proof loop on the Xvfb jobs), and slice 2 is the independent Wayland proof
loop on the Sway jobs; one common launch rule, with readiness kept per
caller because each confirms a different offer. Each slice's one
unobserved native premise is bounded by its early probe. This review
identified no remaining slice-specific concern.

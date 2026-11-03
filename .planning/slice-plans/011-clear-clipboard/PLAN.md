# Plan: Clear every representation from the current clipboard

**Identity:** SEED-001#clear-clipboard
**Source:** [Clear every representation from the current clipboard](../../seeds/SEED-001-clipboard-true-to-its-name.md#clear-clipboard)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

A new public `clear()` (no `clipboard[images]` extra) leaves the current
CLIPBOARD with no offer at all on macOS Aqua, Windows desktop, Linux X11, and
Linux Wayland (named compositor). Afterwards `paste()` is `""`,
`paste_html()` / `paste_image()` / `paste_files()` are `None`, and
`inspect()` is empty. Independent native consumers see no types. `clear()`
returns `None`. Calling it on an empty clipboard, or twice in a row,
succeeds. Clearing ends this library's own Linux background owner. No session, a
missing helper, a Windows clipboard held past the bound, denied access, and
helper or native failure raise `ClipboardContentError` within a bound. Linux
`inspect()` reports an empty snapshot, not an error, when CLIPBOARD has no
owner or nothing is copied.

**Excluded:** PRIMARY, the macOS Find pasteboard and other named pasteboards;
clearing one kind only; snapshot / restore; history, clipboard-manager, cloud,
or Universal Clipboard erasure; checking afterwards that the clipboard stays
empty; WSL / SSH / containers / headless CI as guaranteed desktops; any change
to `copy("")` or the text path (owned by SEED-001#portable-text).

## Assumptions

- PFE: **reuse** the `osascript` / AppKit subprocess stack of
  `clipboard/_html_native_macos.py` and `clipboard/_offer_macos.py` (bounded
  `subprocess.run`, `_helper_failure_detail`); the user32 loader and bounded
  `OpenClipboard` retry in `clipboard/_offer_windows.py` (`_load_user32`,
  `_open_clipboard_bounded`, 15 s); private `clipboard/_desktop` for
  `_is_linux_wayland`, helper-failure detail, and the no-owner /
  nothing-copied markers (`_XCLIP_NO_TARGETS`, `_WL_PASTE_NOTHING_COPIED`);
  the `set_html_clipboard_writer` injection pattern and
  `_call_content_backend` from `clipboard/_errors.py`; the gated
  `CLIPBOARD_NATIVE_PROBE` probes, `scripts/native_probe_*` helpers,
  `scripts/windows_powershell_producers.py`,
  `scripts/windows_clipboard_consumer.py`, `tests/win32_clipboard_fake.py`, and
  the `ci.yml` Xvfb / Sway / `windows-latest` jobs. **Change:**
  `_open_clipboard_bounded`'s message names the operation instead of always
  saying "enumerating formats"; the Linux inspect listings in `_desktop` treat
  no-owner / nothing-copied as an empty list. **Gap:** no clear operation, no
  X11 relinquish mechanism (`xclip` has none). PyClip's clear was considered
  and not reused (extra dependency, unverified native behavior).
- X11 mechanism: `XSetSelectionOwner(display, CLIPBOARD, None, CurrentTime)`
  through libX11 with `ctypes` (libX11 is already installed wherever `xclip`
  runs, so users install nothing new). If slice 5's early probe shows that a
  non-owner cannot empty CLIPBOARD this way, fall back to
  `xsel --clipboard --clear`. That adds `xsel` as an install requirement for
  `clear()` on X11, and the README and errors must name it.
- Linux session selection uses `_desktop._is_linux_wayland` (the writer rule
  of image write, HTML, and inspect). With both `DISPLAY` and
  `WAYLAND_DISPLAY`, Wayland is cleared. The compositor carries that to
  XWayland clients.
- No ADR store exists in this repository; no Accepted ADR constrains this
  plan. The North Star topic above governs the shape: an explicit new API
  beside `copy` / `paste`, the same absence / value / failure model, fakes in
  default CI, and native claims only with independent consumers and stated
  evidence limits. This plan follows it without revision.
- SEED-001#portable-text is Taken and in progress. It edits `_desktop.py`,
  `ci.yml`, the README, and `clipboard/__init__.py`. Expect textual merges at
  those files. This plan neither changes nor depends on the text path; it
  reads text only through public `paste()`.
- This preparation checkout is Darwin 25.6.0 (macOS 26.6.2 / 25G83, arm64)
  with no `xclip`, `xsel`, `wl-copy`, or X server. The macOS probe runs here
  under `CLIPBOARD_NATIVE_PROBE=1` and **replaces the developer's live
  clipboard**, as the existing macOS probes do. Linux and Windows proof runs
  in the gated GitHub Actions jobs.
- Local gate: `nix develop -c make check` (AGENTS.md). Add
  `nix develop -c make lint-workflows` whenever `.github/workflows` changes.
  `nix develop -c make test-package` runs once in slice 1, because the public
  `__all__` grows.

## Outside-in proof

| Example (seed) | Observable signal | Owning slice |
| --- | --- | --- |
| 1. HTML + text from another app → `clear()` → readers absent, `inspect()` empty, independent consumer empty | Fake seam: clearer called once, `None` returned. Native: independent producer of HTML + text, `clear()` in a child process, independent type listing empty, plus `paste()` `""`, `paste_html()` `None`, `inspect()` empty | 1, 2, 4, 5, 6 |
| 2. Image from another app → `clear()` → `paste_image()` `None` | Native image producer, then `clear()`, then an independent consumer and `paste_image()` | 2, 4, 5, 6 |
| 3. Already empty, and twice in a row → `None` | Fake seam: two calls succeed. Native: `clear()` twice on a cleared clipboard, no error | 1, 2, 4, 5, 6 |
| 4. `copy("")` versus `clear()` on macOS | Probe: after `copy("")` the type list holds `public.utf8-plain-text`; after `clear()` the type list is empty | 2 |
| 5. Library-owned Linux background owner ends | `copy_image` (X11 `xclip`, Wayland `wl-copy`) owner PID alive, then `clear()`, then that PID exits within a bound and no owner / nothing copied is reported | 4, 5 |
| 6. Linux empty offer → `inspect()` empty, not an error | Desktop-free tests with the observed helper wording; native: fresh Xvfb (no owner) and fresh Sway (nothing copied) → `inspect()` empty | 3 |
| 7. No session → error; Wayland without `wl-copy` → `wl-clipboard` hint | Desktop-free dispatch tests; native Sway job with `PATH` lacking `wl-copy` | 4 (and the X11 counterpart in 5) |
| 8. Windows clipboard held past the bound → error, prior content intact; released in time → success | Fake user32 (`OpenClipboard` failing until a deadline / until released); native: a second process holding `OpenClipboard` | 6 |
| 9. Manager re-offer is outside the promise | README evidence-limit text naming clipboard managers (Klipper, compositor persistence); no mechanism, no test | 2 (README section), kept current by 4–6 |
| Regression | Existing suites green; `import clipboard` without Pillow exposes `clear`; `make test-package` sees `clear` | 1, every slice |

`clear()` and a read in the same process are only a consistency check. Native
claims need an independent producer and consumer in other processes.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| Default pytest is desktop-free and green at the starting revision | Slice 1 regression baseline | `nix develop -c make check` in this worktree at 4dbb488 → `302 passed, 16 skipped` | Settled |
| Linux `inspect()` raises today on no-owner / nothing-copied | Slice 3 changes it | `_linux_x11_clipboard_inspector()` with `DISPLAY=:0` and a fake `subprocess.run` returning exit 1 / `Error: target TARGETS not available` → `ClipboardContentError … enumeration failed: Error: target TARGETS not available`; `_linux_wayland_clipboard_inspector()` with exit 1 / `Nothing is copied` → `ClipboardContentError … MIME-list enumeration failed: Nothing is copied` | Settled |
| Real `xclip` no-owner wording on CI is the `_XCLIP_NO_TARGETS` marker | Slice 3 classification; slices 5's proof | CI run 41649816028: xclip 0.13 on ubuntu-26.04 Xvfb → exit 1, `Error: target TARGETS not available`; newer wording `There is no owner for the` also recognized | Settled |
| macOS `clearContents` removes every type and repeats cleanly | Slice 2 clearer | macOS 26.6.2, private named pasteboard via `osascript` / AppKit: `public.html`, `Apple HTML pasteboard type`, `public.utf8-plain-text`, `NSStringPboardType` → `clearContents` → 0 types; second `clearContents` → 0 types; change count 1 → 2 → 3; `stringForType` nil | Settled for the call; general pasteboard and any privacy prompt in slice 2's gated probe |
| `copy("")` leaves an empty text offer on macOS and X11 and truly clears on Windows / Wayland | Example 4 contrast, README wording | pyperclip 1.11.0 source: Windows `EmptyClipboard` without data (418–440), Wayland `wl-copy --clear` (210–230), X11 pipes `""` to `xclip` (157–167); macOS empty `pbcopy` leaves `public.utf8-plain-text` (SEED-001#portable-text observation) | Settled |
| `wl-copy --clear` empties the selection on Sway and ends a `wl-copy` owner | Slice 4 clearer | Needs Sway | **Early probe** at the start of slice 4 |
| A non-owner `XSetSelectionOwner(CLIPBOARD, None)` empties CLIPBOARD under Xvfb and makes an `xclip` owner exit; libX11 loads by `ctypes` on `ubuntu-latest` | Slice 5 mechanism | Needs Xvfb | **Early probe** at the start of slice 5; false → `xsel --clear` fallback per Assumptions |
| `OpenClipboard(NULL)` + `EmptyClipboard` removes every format for an independent consumer on `windows-latest` | Slice 6 clearer | Needs a Windows session | **Early probe** at the start of slice 6 |
| CI hosts Xvfb + `xclip`, Sway + `wl-clipboard`, and a `windows-latest` clipboard session | Slices 3–6 venues | `ci.yml` jobs `native-linux-x11-*`, `native-linux-wayland-*`, `native-windows-paste-html` | Settled for venues |
| The macOS probe route runs in this checkout | Slice 2 proof route | `osascript` AppKit script ran here (premise above) | Settled for the route; it changes the live clipboard, so it runs only at slice 2 execution |

## Ordered slices

### 1. `clear()` contract behind an explicit seam
Type: Behavior
Status: done
Proof: desktop-free tests through public `clipboard.clear` with a fake
clearer injected by new `clipboard.set_clipboard_clearer`. The fake is
called once per call and `clear()` returns `None`. Two calls in a row both
succeed. A fake raising `ClipboardContentError` passes it through. A fake
raising `OSError` / `RuntimeError` becomes `ClipboardContentError` with the
original as `__cause__`. `set_clipboard_clearer(None)` restores the default.
On a platform with no native clearer yet, the default raises
`ClipboardContentError` naming the platform and the seam. The no-Pillow
import test sees `clear`. `nix develop -c make check` and
`nix develop -c make test-package` pass.

Behavior: Pre-condition: there is no clear operation. Trigger: callers use
`clear()` against a fake seam. Postcondition: seed examples 1 and 3 hold at
the contract boundary. Interim behavior: the default clearer raises "not
available" on every platform until slices 2, 4, 5, and 6 fill it, and the
README says so for each platform not yet delivered.

### 2. macOS Aqua clear
Type: Behavior
Status: done
Proof: desktop-free tests with a fake `subprocess.run`. Darwin dispatch
reaches the `osascript` clearer, which runs with a timeout. A non-zero exit,
a timeout, or `OSError` raises `ClipboardContentError` with the helper detail.
Gated probe `tests/test_clear_native_macos.py`
(`CLIPBOARD_NATIVE_PROBE=1`, this checkout) does the following. An
independent `osascript` producer writes `public.html` + `public.utf8-plain-text`.
A child Python process calls `clear()` and exits. An independent `osascript`
type listing is empty, `pbpaste` prints nothing, and the parent's
`paste_html()` is `None` and `inspect()` is empty. The same runs with a PNG
producer, and then `paste_image()` is `None`. `clear()` twice on the cleared
pasteboard succeeds. `copy("")`, then a type listing, shows
`public.utf8-plain-text`, then `clear()`, and the type listing is empty. The
probe records whether any privacy prompt appeared. The README gains the
`clear()` section, the macOS verified claim with the OS version, and the
evidence-limit text for clipboard managers / history / Universal Clipboard.

Behavior: Pre-condition: slice 1. Trigger: `clear()` on macOS Aqua.
Postcondition: seed examples 1–4 hold with independent consumers. Example
9's boundary is documented.

### 3. Empty Linux clipboard reads as an empty snapshot
Type: Behavior
Status: done
Proof: first, the early probe. On a fresh Xvfb in the X11 job, record
`xclip -selection clipboard -o -t TARGETS` exit code and stderr. On a fresh
Sway, record `wl-paste -l` exit code and stderr. Then desktop-free tests in
`tests/test_inspect_x11.py` / `tests/test_inspect_wayland.py` with the
observed wording, and with the existing `_XCLIP_NO_TARGETS` /
`_WL_PASTE_NOTHING_COPIED` markers, return
`ClipboardOfferSnapshot(frozenset(), ())`. Other non-zero exits still raise.
Native: the X11 and Sway jobs assert that `inspect()` on the fresh session is
empty and `paste_html()` / `paste_files()` are `None`. If either reader
raises there, this slice fixes it the same way, keeping the marker in
`_desktop`. `nix develop -c make check` and
`nix develop -c make lint-workflows` pass.

Behavior: Pre-condition: Linux `inspect()` raises on an unowned / empty
clipboard. Trigger: `inspect()` and the readers on an empty Linux CLIPBOARD.
Postcondition: seed example 6 holds; the empty state that slices 4–5 create
is observable through the library.

### 4. Linux Wayland clear (Sway)
Type: Behavior
Status: planned
Proof: first, the early probe in the Sway job. A `wl-copy` owner of
`text/html`, then `wl-copy --clear`, then `wl-paste -l` reports nothing
copied and the owner PID exits. Then desktop-free tests: Wayland dispatch
(`_is_linux_wayland`) runs `wl-copy --clear` with stdin closed and a
timeout. Missing `wl-copy` raises `ClipboardContentError` naming
`wl-clipboard`. Neither `DISPLAY` nor `WAYLAND_DISPLAY` raises "no desktop
session is visible". A non-zero exit carries the helper detail. Native
(Sway job, gated): an independent `wl-copy` producer of `text/html`, then a
child `clear()`, then `wl-paste -l` nothing copied, `inspect()` empty,
`paste_html()` `None`. A `copy_image` owner, then `clear()`, then the owner
exits and `paste_image()` is `None`. `clear()` twice succeeds. `PATH` without
`wl-copy` gives the hint. The README records Sway and `wl-clipboard`
versions; other compositors are evidence limits.

Behavior: Pre-condition: slices 1 and 3. Trigger: `clear()` on a Wayland
session. Postcondition: seed examples 1, 2, 3, 5, and 7 hold on Sway.

### 5. Linux X11 clear (Xvfb)
Type: Behavior
Status: planned
Proof: first, the early probe in the X11 job. An `xclip` owner of
`text/html`. A separate Python process loads libX11 via `ctypes`, opens
`DISPLAY`, interns `CLIPBOARD`, calls
`XSetSelectionOwner(..., None, CurrentTime)`, and `XFlush` /
`XCloseDisplay`. Then `xclip -o -t TARGETS` reports no owner and the `xclip`
PID exits. If this fails, switch to `xsel --clipboard --clear` (installed in
the job) and update the seed's install wording. Then desktop-free tests: X11
dispatch calls the clearer. A missing libX11 (or `xsel`) and an unopenable
display raise `ClipboardContentError` naming `DISPLAY` / the requirement.
Native (Xvfb job, gated): an independent `xclip -t text/html` producer, then
a child `clear()`, then no owner, `inspect()` empty, and `paste_html()` /
`paste_files()` `None`. A `copy_image` owner, then `clear()`, then the owner
exits and `paste_image()` is `None`. `clear()` twice succeeds. The README
records the Xvfb / `xclip` versions and names desktops with clipboard
managers as evidence limits.

Behavior: Pre-condition: slices 1 and 3. Trigger: `clear()` on an X11
session. Postcondition: seed examples 1, 2, 3, 5, and the X11 counterpart of
7 hold under Xvfb.

### 6. Windows desktop clear
Type: Behavior
Status: planned
Proof: first, the early probe in a gated `windows-latest` job. A PowerShell
producer (`scripts/windows_powershell_producers.py`) offers HTML + text, then
`OpenClipboard(NULL)` / `EmptyClipboard` / `CloseClipboard`, then an
independent consumer process (`scripts/windows_clipboard_consumer.py`)
enumerates no formats. Then desktop-free tests with
`tests/win32_clipboard_fake.py`: win32 dispatch opens through the shared
bounded `_open_clipboard_bounded` (message now names the operation), calls
`EmptyClipboard`, and always closes. `EmptyClipboard` failure raises with
`last_error`. An open that fails until the deadline raises "held by another
process". An open that is released before the deadline succeeds. Native
(gated job): HTML + text producer and image producer, each followed by a
child `clear()`, then the consumer lists no formats and `inspect()` is
empty. `clear()` twice succeeds. A helper process holding `OpenClipboard`
past the bound makes `clear()` raise and the prior formats remain. The job
fails, without skipping, on an evidence limit, as AGENTS.md requires for the
Windows proof. `nix develop -c make lint-workflows` passes. The README
records the runner image.

Behavior: Pre-condition: slice 1. Trigger: `clear()` on Windows desktop.
Postcondition: seed examples 1, 2, 3, and 8 hold on `windows-latest`. The
README notes that Win+V history and cloud clipboard are not erased.

## Current decisions

- `clear()` means no offer at all; an empty placeholder does not count (seed
  decision, reviewable before Take).
- The Linux inspect empty-offer change belongs to this story (slice 3).
- A re-offer after clear is not detected; the README names it (example 9).
- X11 uses libX11 via `ctypes` unless slice 5's probe disproves it; then
  `xsel`.
- Public names: `clear` and `set_clipboard_clearer`, added to `__all__`.

## Story obligations

### G1. Default clearer raises "not available" on every platform
Reported: slice 1 — "No native clearer is implemented. When slices 2, 4, 5 and 6 add a native clearer, each must drop its platform from that parametrize list."
Story clause: "with one call whose result is the same on every supported desktop"
Disposition: interim until slices 2, 4, 5, 6

### G2. macOS privacy prompt on clear() is unobserved
Reported: slice 2 — "Privacy prompt: not observable, so it is recorded as an evidence limit"
Story clause: "within a bound of seconds, never a silent success"
Disposition: no user cost "A failed clear is reported, so the user never believes content is gone when it is not": clearContents reads nothing; every child clear() in the native probe returned in under 0.5 s with types emptied, so no prompt blocked or failed the call; the README Evidence records the limit.

## Learnings

- Slice 1 (accepted 2026-11-03): `clipboard/_clear.py` holds the seam;
  `_default_clipboard_clearer` is the one place later slices add
  `sys.platform` dispatch before the fallback raise. Each native slice drops
  its platform from `tests/test_clear.py::test_default_clearer_names_platform_and_seam`.
  Accepted proof: `nix develop -c uv run --locked --extra images pytest
  tests/test_clear.py tests/test_no_pillow_extra.py -q` (19 passed),
  `nix develop -c make check` (544 passed, 24 skipped; the 302 baseline
  in Decisive premises predates later merges), `nix develop -c make
  test-package` (asserts `clear` / `set_clipboard_clearer` callable).
- Slice 2 (accepted 2026-11-03): `clipboard/_clear_macos.py` clears the
  general pasteboard via `osascript` AppKit `clearContents` (15 s bound).
  Native probe `scripts/probe_macos_native_clear.py` (support
  `scripts/macos_native_clear_support.py`, wrapper
  `tests/test_clear_native_macos.py`) passed twice on macOS 26.6.2 / 25G83:
  HTML+text and PNG producers emptied to `[]`, `pbpaste` empty, all readers
  absent; `copy("")` left `public.utf8-plain-text`. On-screen privacy prompts
  are not observable from agent sessions (`screencapture` has no display
  access); recorded as G2. A PNG offer is listed with system-added TIFF types,
  so producer checks test inclusion. AGENTS.md now names `clear`.
- Slice 3 (accepted 2026-11-03; native proof CI run 41649816028 on 342f12c,
  ubuntu-26.04: xclip 0.13 says `Error: target TARGETS not available` exit 1;
  Sway 1.11 + wl-clipboard 2.2.1 says `Nothing is copied` exit 1; every reader
  read absence on both): `_desktop._xclip_reports_no_owner` /
  `_wl_paste_reports_nothing_copied` are now the one home for empty-clipboard
  wording (both xclip wordings, both wl-paste wordings), used by inspect,
  HTML, file-list, and text readers. New CI jobs `native-linux-x11-clear` and
  `native-linux-wayland-clear` (`native-wayland-clear.yml`) record the fresh
  session's raw helper wording, then run `scripts/probe_linux_{x11,wayland}_native_clear.py`
  step 1; slices 4–5 append clear steps to each probe's `_probe`.
- Slice 4 (desktop-free proof accepted 2026-11-03; native proof pending the
  published revision's CI): `clipboard/_clear_wayland.py` runs `wl-copy
  --clear` (stdin closed, stderr to a temp file, 10 s bound); `_clear.py`
  Linux dispatch: Wayland via `_is_linux_wayland`, no session raises,
  X11-only still "not available". Probe steps 2–7 in
  `scripts/probe_linux_wayland_native_clear.py`; slice 5 should reuse
  `linux_native_clear_support.helper_pids` / `wait_pids_exit` / `child_clear`
  and revisit `_desktop._linux_desktop_session_visible` once X11 dispatches.
- The per-module osascript runners (`_offer_macos`, `_html_native_macos`,
  `_clear_macos`) keep separate failure messages and bounds; consolidating
  them is a cross-module refactor outside this story.

## Concern evidence

Slice-plan refinement was not needed. Each slice is one Behavior with one
proof loop, and the per-platform slices share one rule (remove every offer)
through one seam, not special cases. The only Structure touch (operation
name in `_open_clipboard_bounded`) stays inside the Behavior it serves. This
review found no remaining slice-specific concern. The unobserved native
premises (slices 3–6) are each bounded by an early probe at the start of
their slice, and their failure stops that slice and changes this plan. The
interim "not available" default from slice 1 is an accepted trade-off, which
slices 2, 4, 5, and 6 replace.

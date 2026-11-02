# Plan: Use the text clipboard reliably and diagnose unavailable access

**Identity:** SEED-001#portable-text
**Source:** [Use the text clipboard reliably and diagnose unavailable access](../../seeds/SEED-001-clipboard-true-to-its-name.md#portable-text)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Existing users of `copy(text)` / `paste()` get exact Unicode text exchange
with independent applications on Windows desktop, macOS Aqua, Linux X11, and
Linux Wayland (named compositor), and a bounded `ClipboardContentError`
naming the cause instead of a silent `""` or no-op when the desktop clipboard
cannot be reached. `copy` / `paste` keep their names, signatures, `str`
results, pyperclip's non-`str` coercion, and untranslated native line
endings; `paste()` returns `""` for ordinary absence and never `None`; a
`str` with `\x00` or an unencodable code point is refused before the
clipboard is replaced; text written stays pasteable after the writer exits.
The four default paths are owned by this package; WSL, a mechanism the caller
already resolved in pyperclip, and X11 desktops without `xclip` (xsel,
Klipper, Qt) keep working through pyperclip with failure translation only.

**Excluded:** newline normalization; rejecting `bytes` / `None`; PRIMARY;
clearing other representations; waits; RTF; a pyobjc text path; verified
support for xsel / Klipper / Qt / Cygwin / SSH / containers / headless CI;
persistence across logout or reboot; changing any other public API.

## Assumptions

- PFE: **reuse** pyperclip 1.11.0 for WSL (`clip.exe` / PowerShell bridge),
  for its bounded Windows `CF_UNICODETEXT` backend (`OpenClipboard` retried
  about 0.5 s, then `PyperclipWindowsException`), and as the delegate for
  every environment this story does not own; **reuse** this package's
  bounded helper pattern (`subprocess.run(..., timeout=...)`, stderr
  classification such as `_XCLIP_NO_TARGETS` in `_html_native_linux.py`,
  `_exit_detail`), the `xclip` background-owner lifetime with `TARGETS`
  polling and `wl-copy` forking from `_image_write.py`, `ClipboardContentError`
  with `_call_content_backend`, the `set_*_clipboard_reader` / `_writer`
  injection pattern of `_html.py`, gated `CLIPBOARD_NATIVE_PROBE` probes with
  `scripts/native_probe_*` helpers and `ci.yml` Xvfb / Sway / `windows-latest`
  jobs, and README evidence-limit wording. **Change:** text stops being a bare
  pyperclip re-export; `ClipboardContentError`'s docstring widens from "rich
  content" to clipboard content. **Gap:** no owned text module, no text
  seam, no native text proof.
- Session selection for text follows pyperclip's order (WSL; then
  `WAYLAND_DISPLAY` with `wl-copy` and `wl-paste` on `PATH`; then `DISPLAY`)
  so no working user changes mechanism. If SEED-001#desktop-helpers has
  landed when a Linux slice starts, its private desktop module hosts this
  predicate and the helper-failure formatting; otherwise place them in the
  text module along the same layout rather than copying another module's.
  Unifying the Wayland rules stays the product decision desktop-helpers
  recorded.
- No ADR store exists in this repository; no Accepted ADR constrains this
  plan. The North Star topic above governs the explicit-API shape; this plan
  follows it (text keeps its two names and gains the same absence / value /
  failure model) and the topic records that text's default paths move into
  the package.
- This preparation checkout is Darwin 25.6.0 (macOS 26.6.2 / 25G83, arm64)
  with `pbcopy` / `pbpaste` and no `xclip`, `xsel`, `wl-copy`, or `wl-paste`.
  macOS proof runs here under `CLIPBOARD_NATIVE_PROBE=1`; Linux and Windows
  proof runs in gated GitHub Actions jobs.
- Local gate: `nix develop -c make check` (AGENTS.md); add
  `nix develop -c make lint-workflows` whenever `.github/workflows` changes.

## Outside-in proof

| Example (seed) | Observable signal | Owning slice |
| --- | --- | --- |
| 1. Exact round trip with an independent app after writer exit | Independent producer → `paste()` exact; child `copy()` exits → independent consumer exact (Unicode, emoji, leading/trailing spaces, newline) | 3 (macOS), 4 (X11), 5 (Sway), 6 (Windows) |
| 2. macOS process without locale variables keeps Unicode exact | Child with empty environment: `copy()` then independent `pbpaste` in UTF-8 shell exact; `paste()` exact | 3 |
| 3. `copy("")` → `paste()` is `""` | Fake seam round trip; each native job / probe | 1, 3–6 |
| 4. NUL or lone surrogate refused before replacing | `ClipboardContentError` naming the problem, writer never called; native: prior text still read by an independent consumer | 1, plus one native check in 3 |
| 5. Dead `DISPLAY` / stale `WAYLAND_DISPLAY` → error, not `""`, within bound | `ClipboardContentError` quoting the helper's display failure for `paste()` and `copy()`; measured under the bound | 4, 5 |
| 6. No session → "no desktop session" error; `DISPLAY` without `xclip` → install hint | Desktop-free dispatch tests; native job with `PATH` lacking `xclip` | 2, 4 |
| 7. Stalled owner / held clipboard → error after bound | Fake `subprocess` timeout → `ClipboardContentError` (X11 unit); Windows held `OpenClipboard` → translated error, released → success | 4 (unit), 6 |
| 8. Image-only → `""`, no exception | Fake reader returning no text; native image-only / cleared case on macOS and Windows | 1, 3, 6 |
| 9. Windows CRLF untranslated | PowerShell `Set-Clipboard` of two lines → `paste()` is `"line 1\r\nline 2"`; `copy("line 1\nline 2")` → `Get-Clipboard` shows two lines | 6 |
| 10. WSL and other delegated paths raise `ClipboardContentError` | Dispatch test with a fake pyperclip raising `PyperclipException` / `FileNotFoundError` / returning `None` | 1, 2 |
| Writer-exit lifetime | Writer process exits before the independent consumer reads | 3–6 |
| Regression | Existing suites green; `make test-package` still imports and calls `copy` / `paste`; `import clipboard` resolves no pyperclip mechanism | 1, every slice |

A `paste()` after `copy()` in the same process is a consistency check; native
claims need an independent producer or consumer in another process.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| pyperclip's Linux backends turn helper failure into `""` / silent no-op | Slices 4–5 own the helper calls | Darwin, fake `xclip` on `PATH` printing `Error: Can't open display: :99` and exiting 1, `DISPLAY=:99`: `pyperclip.init_xclip_clipboard()` → `copy("hello")` returned `None` in 0.38 s, `paste()` returned `''`; source has no `returncode` check or `timeout` (lines 158–236) | Settled |
| `pbcopy` / `pbpaste` corrupt non-ASCII without a UTF-8 locale and a forced UTF-8 locale restores exact bytes | Slice 3 forces the child locale | macOS 26.6.2, Find pasteboard (`-pboard find`): `env -i pbpaste` → `h\x8ello ?? ???`; `env -i pbcopy` stored `h√©llo üëã`; `env -i LC_ALL=en_US.UTF-8` (also `LANG=en_US.UTF-8`, `LC_CTYPE=UTF-8`, `C.UTF-8`) → exact bytes both ways; `LC_ALL` wins over `LC_CTYPE`, and `LC_ALL=UTF-8` or an unknown locale falls back to C | Settled: set `LC_ALL=en_US.UTF-8` on the helper's environment |
| `pbcopy` / `pbpaste` pass NUL, CRLF, LF, leading/trailing whitespace; empty input leaves an empty `public.utf8-plain-text`; cleared pasteboard reads `""` with exit 0 | Slice 3 absence and value rules | Same Find-pasteboard session, `xxd` and a JXA `NSPasteboard` type listing | Settled |
| `pyperclip.is_available()` is `False` until a mechanism is resolved | Slice 2 delegation rule | `python -I -c` printed `False` before any `copy` / `paste`; source line 647 | Settled |
| Default pytest is desktop-free and green at the starting revision | Slice 1 regression baseline | `nix develop -c make deps check` in this worktree at 59f8d81 → `309 passed, 15 skipped`, `All checks passed!` | Settled |
| Text tests today stub `pyperclip.determine_clipboard` in a subprocess; `make test-package` asserts only callable `copy` / `paste` and `VERSION` | Slice 1 replaces the stub with the seam | `tests/test_clipboard.py`, `Makefile` `test-package` | Settled |
| desktop-helpers' private desktop module is not on trunk yet | Slices 2, 4, 5 placement rule | `git ls-tree origin/master clipboard/` at 59f8d81 lists no `_desktop*.py` | Settled now; recheck at each Linux slice start |
| CI hosts Xvfb + `xclip` 0.13, Sway 1.11 + `wl-clipboard` 2.2.1, and a `windows-latest` clipboard session | Slices 4–6 venues | `ci.yml` gated jobs; README Windows `paste_html` evidence (`windows-latest`, PowerShell producer) | Settled for venues |
| `xclip` / `wl-paste` stderr for a dead display and for an absent text target is classifiable; `UTF8_STRING` then `STRING` fallback behaves as ICCCM says | Slices 4–5 classification | Needs the Linux jobs; Darwin here | **Early probe** inside slices 4 and 5 (first CI run; unknown wording defaults to failure) |
| Windows applications deliver `\r\n`; LF-only writes paste as lines; a held `OpenClipboard` makes pyperclip raise within its retry | Slice 6 proof | Needs a Windows session | **Early probe** inside slice 6 |
| `wl-copy` with empty input serves an empty text offer (or must `--clear`, as pyperclip does) | Slice 5 `copy("")` | Needs Sway | **Early probe** inside slice 5; keep `--clear` until observed |

## Ordered slices

### 1. Owned text contract behind an explicit seam
Type: Behavior
Status: done
Proof: desktop-free tests through public `clipboard.copy` / `clipboard.paste`
with a fake writer and reader injected by new `clipboard.set_text_clipboard_writer`
/ `clipboard.set_text_clipboard_reader`: Unicode, emoji, whitespace,
multiline and `""` round-trip through the fakes; `42` reaches the writer as
`"42"`; `"a\x00b"` and `"\ud800"` raise `ClipboardContentError` naming the
problem with the writer never called; a reader returning `None` yields `""`;
`PyperclipException`, `FileNotFoundError`, and other reader / writer
exceptions become `ClipboardContentError` with the original as `__cause__`;
`set_*(None)` restores the default; `import clipboard` in a subprocess leaves
`pyperclip.is_available()` `False`; the old subprocess stub test is replaced;
`nix develop -c make check` and `make test-package` pass.

Behavior: Pre-condition: `copy` / `paste` are bare pyperclip re-exports.
Trigger: callers use them against a fake seam, or the default backend, which
in this slice delegates to pyperclip with failure translation. Postcondition:
seed examples 3, 4, 8, and 10 hold at the contract boundary on every platform,
with no change to which mechanism pyperclip picks until slices 2–5.

### 2. Session dispatch and no-session diagnosis
Type: Behavior
Status: done
Proof: desktop-free tests patching platform, environment, `shutil.which`, and
a fake pyperclip: WSL (`/proc/version` containing `microsoft`) and an already
resolved pyperclip delegate; Windows uses pyperclip's Windows backend; Linux
with `WAYLAND_DISPLAY` plus both `wl-copy` and `wl-paste` selects the owned
Wayland path, `DISPLAY` plus `xclip` the owned X11 path, `DISPLAY` with only
`xsel` / `klipper` / Qt delegates to pyperclip, `DISPLAY` with no helper at
all raises `ClipboardContentError` naming `xclip` and `wl-clipboard` with
install hints, and neither variable raises one saying no desktop session is
visible; the owned paths are placeholders raising `ClipboardContentError`
until slices 3–5 fill them; `nix develop -c make check` passes.

Behavior: Pre-condition: slice 1. Trigger: `copy` / `paste` on each session
shape. Postcondition: seed example 6 holds desktop-free, example 10 keeps WSL
on its bridge, and each desktop has a named owner for slices 3–5.

### 3. macOS Aqua owned path and local probe
Type: Behavior
Status: done
Proof: default Darwin reader / writer run `pbpaste` / `pbcopy` with
`LC_ALL=en_US.UTF-8` on the child environment and a bounded timeout (reader
15 s as `_offer_macos`), classify a non-zero exit or timeout as
`ClipboardContentError`; gated probe `scripts/probe_macos_native_text.py`
(`CLIPBOARD_NATIVE_PROBE=1`, wrapper `tests/test_text_native_macos.py`, fails
rather than skips on an evidence limit): an independent `osascript` producer
sets `"  héllo 👋 ﾃｽﾄ\nline 2 "` → `paste()` exact; a child Python with an
empty environment runs `copy()` of the same text and exits → an independent
`pbpaste` under the user's UTF-8 locale and an `osascript` `the clipboard`
consumer read it exactly; the child's `paste()` under an empty environment is
exact; `copy("")` → `paste()` is `""`; `copy("a\x00b")` leaves the prior
text readable by the independent consumer; a cleared pasteboard and, when the
host offers one, an image-only pasteboard read `""`. Floors recorded (macOS,
build, Darwin, arch, Python). Unobserved steps → macOS evidence limit.

Behavior: Pre-condition: slices 1–2. Trigger: `copy` / `paste` on Aqua,
including from a process without locale variables. Postcondition: seed
examples 1, 2, 3, 4, 8 verified on macOS or limited.

### 4. Linux X11 owned path and gated Xvfb job
Type: Behavior
Status: planned
Proof: owned X11 reader runs `xclip -selection clipboard -o -t UTF8_STRING`
(10 s bound), falls back to `-t STRING` decoded as Latin-1 when the owner
offers no `UTF8_STRING`, returns `""` when there is no owner or no text
target, and raises `ClipboardContentError` quoting stderr for any other
failure, a timeout, or a missing `xclip`; the writer feeds UTF-8 to a
background `xclip -selection clipboard -i` owner (`start_new_session`, as
`_image_write`) and waits until `TARGETS` lists `UTF8_STRING`, raising with
the helper's stderr on early exit or on the bound; desktop-free tests with a
fake `subprocess` cover the classification and the timeout (example 7);
gated job `native-linux-x11-text` (Xvfb + `xclip`; `make lint-workflows`
passes): independent `xclip -i` producer → `paste()` exact; child `copy()`
exits → independent `xclip -o` exact; `copy("")` → `paste()` `""`;
`DISPLAY=:99` → both operations raise within the bound quoting the display
failure; `PATH` without `xclip` → install hint. First run settles the stderr
wording premise; unexpected wording is recorded in Learnings and still fails
closed.

Behavior: Pre-condition: slices 1–2. Trigger: `copy` / `paste` on X11 with
`xclip`. Postcondition: seed examples 1, 3, 5, 6, 7 on X11.

### 5. Linux Wayland owned path and gated Sway job
Type: Behavior
Status: planned
Proof: owned Wayland reader lists `wl-paste --list-types`, picks the first
text type (`text/plain;charset=utf-8`, `text/plain`, `UTF8_STRING`, `TEXT`,
`STRING`) and reads it with `wl-paste -n -t <type>` (10 s bound), returns `""`
for "Nothing is copied" or no text type, and raises `ClipboardContentError`
for a connection failure, timeout, or missing helper; the writer pipes UTF-8
to `wl-copy` (which forks its background owner) and keeps `wl-copy --clear`
for `""` until the early probe observes an empty offer; gated job
`native-linux-wayland-text` on Sway: independent `wl-copy` producer →
`paste()` exact; child `copy()` exits → independent `wl-paste` exact;
`copy("")` → `""`; `WAYLAND_DISPLAY=wayland-9` (no such socket) → both
operations raise within the bound; `PATH` without `wl-paste` → install hint.
Claims scoped to Sway 1.11 / wl-clipboard 2.2.1.

Behavior: Pre-condition: slices 1–2 (4's helper classification reused).
Trigger: `copy` / `paste` on a Wayland session with wl-clipboard.
Postcondition: seed examples 1, 3, 5, 6 on Sway.

### 6. Windows text proof through pyperclip's backend
Type: Behavior
Status: planned
Proof: gated job `native-windows-text` on `windows-latest`
(`tests/test_text_native_windows.py`, fails rather than skips): independent
PowerShell `Set-Clipboard` producer of `"line 1\r\nline 2"` with Unicode and
surrounding spaces → `paste()` exact including `\r\n`; child `copy("héllo 👋\nline 2")`
exits → `Get-Clipboard -Raw` exact and shows two lines; `copy("")` →
`Get-Clipboard` empty and `paste()` `""`; image-only (PowerShell
`[Windows.Forms.Clipboard]::SetImage`) → `""`; a PowerShell holder keeping
`OpenClipboard` for 3 s → `paste()` raises `ClipboardContentError` whose
cause is `PyperclipWindowsException`, and after release `paste()` succeeds.
Any step the runner cannot perform is recorded in Learnings and becomes a
named README evidence limit, not a skip.

Behavior: Pre-condition: slices 1–2. Trigger: `copy` / `paste` on a Windows
desktop. Postcondition: seed examples 1, 3, 7, 8, 9 on Windows.

### 7. Document the text contract and its evidence
Type: Behavior
Status: planned
Proof: README Usage states the text contract (exact text, `""` absence,
never `None`, untranslated line endings with `splitlines()`, NUL and
unencodable refusal before replacing, `ClipboardContentError` with bounds and
install hints, pyperclip coercion kept, delegated environments and the WSL
bridge, that `pyperclip.PyperclipException` no longer surfaces); Installation
lists the Linux text helpers; Evidence lists per-desktop floors or limits from
slices 3–6, including the unobserved macOS "Paste from Other Apps" denial and
SSH-into-macOS cases; `ClipboardContentError` docstring, module docstrings,
AGENTS.md's package summary, and the North Star evidence line agree;
`nix develop -c make check` passes.

Behavior: Pre-condition: slices 3–6 results. Trigger: documentation update.
Postcondition: callers know exactly what is promised and verified where.

## Current decisions

- Text failures raise `ClipboardContentError` with the pyperclip or helper
  error as `__cause__`; no new exception class.
- Validation and `None` → `""` normalization sit above the seam so every
  backend shares fail-before-replace and the `str` result.
- Delegation to pyperclip happens when pyperclip is already resolved at first
  text use, under WSL, and for X11 sessions without `xclip`; delegated paths
  promise translation only.
- Line endings are never translated; `copy("")` promises only that `paste()`
  returns `""`.
- The macOS helper environment sets `LC_ALL=en_US.UTF-8`; Linux reads use a
  10 s bound and macOS reads 15 s, matching the existing readers.

## Learnings

- Slice 1: pyperclip 1.11.0 coerces every argument with plain `str()` and
  never rejects a type (older allowed versions did), so `clipboard/_text.py`
  owns `str()` coercion above the seam; the default backend reads
  `pyperclip.copy` / `pyperclip.paste` at call time because pyperclip swaps
  those globals on first use. A reader returning a non-`str` (e.g. `bytes`)
  raises `ClipboardContentError`.
- Slice 1 accepted proof: `tests/test_clipboard.py` seam, coercion,
  fail-before-write, `None` → `""`, `__cause__` translation, restore, and
  lazy-pyperclip subprocess tests; `nix develop -c make check` 335 passed /
  16 skipped; `nix develop -c make test-package` pass. README line 5 and
  AGENTS.md still say text re-exports pyperclip (slice 7).
- Slice 2: trunk (with SEED-001#desktop-helpers' `clipboard/_desktop.py`)
  was merged into the story branch first. pyperclip 1.11.0
  `determine_clipboard` (lines 497–565) tries Cygwin, Windows, WSL, macOS
  (pyobjc, else pbcopy), Wayland (`WAYLAND_DISPLAY` + `wl-copy` + `wl-paste`),
  then under `DISPLAY` xclip before xsel, klipper+qdbus, qtpy, PyQt5. The text
  rule lives in `clipboard/_desktop_text.py` (`_text_session_owner`), a
  sibling of `_desktop.py` kept separate for the file-size limit;
  `clipboard/_text.py` `_select_text_backend` prefers an already resolved
  pyperclip and is evaluated per call. Owned paths raise via
  `_owned_text_path_pending` until slices 3–5 (G1); the story branch must not
  land before then. Proof: `tests/test_text_session.py`,
  `tests/test_text_dispatch.py`; `make check` 355 passed / 16 skipped.
- Slice 3: `clipboard/_text_native_macos.py` owns macOS text (pbcopy /
  pbpaste, child env plus `LC_ALL=en_US.UTF-8`, 15 s bounds, strict UTF-8
  decode). `scripts/probe_macos_native_text.py` (wrapper
  `tests/test_text_native_macos.py`) passed on macOS 26.6.2 / 25G83 / Darwin
  25.6.0 / arm64 / Python 3.13.17 with no evidence limits; removing `LC_ALL`
  made the no-locale steps fail. Probe learnings: AppleScript `the clipboard`
  coerces LF to CR, so exactness is judged on `the clipboard as «class
  utf8»`; Python's PEP 538 injects `LC_CTYPE=C.UTF-8` into a child started
  with `env={}`, so a no-locale probe must drop `LANG` / `LC_*` before
  importing `clipboard`. The macOS denial and SSH cases stay unobserved.
  `make check` 368 passed / 17 skipped.
- Slice 4 (in progress, awaiting `native-linux-x11-text`):
  `clipboard/_text_native_x11.py` reads `TARGETS` first so absence never
  depends on stderr wording; the writer waits until the background owner
  serves exactly the written bytes, because the previous owner usually
  lists `UTF8_STRING` too (the TARGETS-only wait in `_image_write` shares
  that latent race). `xvfb-run -a` allocates from `:99`, so the probe picks
  a free display from `:90` as the dead display. Shared Linux runner:
  `clipboard/_text_native_linux.py`. Local: `make check` 389 passed / 18
  skipped.

## Story obligations

### G1. Owned macOS, X11 and Wayland text paths are placeholders
Reported: slice 2 — "with the placeholders, default `copy` / `paste` raise `ClipboardContentError` on real macOS, on Linux X11 with xclip, and on Linux Wayland with wl-clipboard. This must not reach trunk until slices 3–5 fill those paths."
Story clause: "`copy(text)` replaces the clipboard with exactly `text`, and `paste()` returns exactly the text the clipboard offers"
Disposition: interim until slices 3, 4, 5

### G2. macOS pyobjc users move from pyperclip's AppKit path to the owned pbcopy path
Reported: slice 2 — "pyperclip prefers pyobjc there (lines 524–530), but the owned macOS path (plan: pbcopy, no pyobjc text path) will change their mechanism."
Story clause: "Session selection for text keeps pyperclip's order so no working user changes mechanism"
Disposition: excluded "a macOS AppKit (`pyobjc`) text path"

## Plan review

Refinement not needed: each slice owns one outcome and proof loop; the
contract precedes dispatch, dispatch precedes the three owned desktop paths,
and documentation closes on their evidence. The per-desktop slices are
justified because each desktop has a live session (local macOS, CI Linux and
Windows) that can still produce new measurement.

Remaining concerns: none beyond the early probes inside slices 4–6, which
bound the unobserved native premises above and fail closed.

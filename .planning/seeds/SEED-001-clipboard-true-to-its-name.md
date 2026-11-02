---
id: SEED-001
status: active
planted: 2026-11-02
planted_during: Terry Yin's request to make clipboard true to its name
trigger_when: Selecting the next clipboard library improvement
scope: 11 candidate stories; 4 L, 6 M, 1 S effort hypotheses
---

# SEED-001: Make clipboard true to its name

## Why This Matters

For Python application and automation developers, assembling separate tools
and platform-specific recipes for ordinary clipboard content should change to
dependable exchange with desktop applications through `clipboard`, while
preserving existing text callers and respecting native access restrictions.

The present public surface is text-only. Historical requests for
[image reading](https://github.com/terryyin/clipboard/issues/2) and
[Linux image writing](https://github.com/terryyin/clipboard/issues/5) provide
specific demand. The maintainer explicitly asked for domain research,
decomposition, and queueing, with the near-future direction of making the
project true to its name. When offered text-first ordering, Terry chose
**images and rich content first**. Terry also approved the
[initial planning conventions](../README.md).

The named beneficiary and the initial desktop scope are the proposed framing
retained from that exchange. The value hypothesis is less consumer glue and
more predictable cross-application behavior. The highest-learning hypothesis
is that an image copied by an independent desktop application can be consumed
through one understandable Python contract across the supported desktop set.
User prioritization does not establish the technical feasibility of that
hypothesis.

## Alternatives and Decision

- **Do nothing or defer:** preserves a tiny wrapper but leaves the image
  requests and the maintainer's stated direction unanswered.
- **Smaller change:** improve text documentation and expose more upstream
  helpers. Useful for text users, but it does not deliver images or HTML.
- **Strongest existing-tool alternative:** recommend pyperclip plus Pillow
  and native clipboard recipes. This may be enough for one expert's task,
  but consumers still own inconsistent results, native format mapping,
  installation, and lifetime behavior.
- **Recommended direction:** keep the simple text entry points and add
  explicit, dependable content operations. Reuse existing solutions when they
  satisfy the behavior; choose implementations during refinement/planning.

The alternatives and learning hypotheses above are research recommendations,
not a maintainer-approved backend design. See the
[domain research](../research/2026-11-02-clipboard-domain.md) for evidence,
platform distinctions, reuse candidates, and uncertainty.

## Shared Boundaries

- New desktop content support targets Windows, macOS, Linux X11, and Linux
  Wayland. Each story's refinement must name supported OS/desktop/compositor
  and helper versions, permission behavior, and the proof available for each.
  Do not generalize one compositor's result to all Wayland environments.
- Preserve `copy`, `paste`, and `VERSION` and the supported Python range.
  Keep existing text call sites working; add explicit content operations
  rather than changing `paste()` to return an image, bytes, or filenames.
- Each story owns the smallest end-to-end native integration, installation
  instructions, actionable errors, and tests needed for its own outcome.
  Missing access, denied permission, contention, timeout, absent format, and
  malformed data must not all collapse into an empty result. Respect native
  authorization; do not bypass it through a fallback backend.
- Read operations leave the clipboard unchanged. Invalid write input is
  rejected before replacing current content. Report native transfer failures
  truthfully; do not promise rollback or atomicity across platforms without
  proof. Ordinary clipboard contents are untrusted data, not commands.
- Successful writes must have a documented, tested lifetime, including
  pasting after the writing Python process exits in supported desktop
  sessions. Ownership transfer and serving resources belong to the writer's
  story. Do not require the consuming user to keep an incidental GUI window
  open. No persistence across logout/reboot, history, or cloud-sync guarantee.
- Support is established through independent native producers/consumers,
  appropriate automated checks, and explicit evidence limits. In-memory tests
  remain useful but cannot establish native interoperability. Native manual
  observations are performed only when explicitly requested or required by
  an authorized plan slice.
- No automatic history collection, clipboard payload logging, cloud service,
  keystroke injection, mobile API, or remote clipboard bridge is in scope.

## Story Decomposition

<a id="copy-files"></a>

### Copy local file references into file managers

**Identity:** SEED-001#copy-files
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/008-copy-files/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"be7e65190bf6bcbc8fb4a3225a3f3ec02fc5ae7c07e6dfce9a69c5e43eac4480","plan":"c89e2108e3fc09c37959d25078326ff0624a58ec107c9c22eb5b96aa556db431"}}
```

**Goal:** Python tool and automation developers can hand existing local
output files to a desktop file manager through its ordinary copy/paste
workflow, so the user pastes copies wherever they choose without the tool
printing paths or the user handling them manually. This extends `clipboard`
from reading file lists (`paste_files`) to offering them, tested against file
managers rather than against the library's own reader.

**Scope:**

- *Required behavior.* A new `copy_files(paths)` (no `clipboard[images]`
  extra) takes an ordered, non-empty iterable of `str` / `os.PathLike` local
  paths and replaces the current clipboard with one native file-list offer
  marked as **copy**, not cut. Relative paths are made absolute against the
  current directory at call time (symlinks are not resolved); order and
  duplicates pass through. Each named path must exist when `copy_files` is
  called; files and directories alike are offered. The offer stays pasteable
  after the writing Python process exits. Native offers: macOS Aqua
  `NSPasteboard` file URLs; Windows `CF_HDROP` plus `Preferred DropEffect` =
  copy; Linux X11 / Wayland a `text/uri-list` (and the GNOME copied-files
  convention where the helper can offer it) served by a background owner, as
  `copy_image` does.
- *Required restrictions.* Invalid input — empty iterable, a bare `str` /
  `bytes` (which would otherwise iterate characters), a non-path item, or any
  path that does not exist — raises `ClipboardContentError` naming the problem
  **before** the current clipboard is replaced (shared fail-before-replace
  boundary). An empty offer is rejected because it would silently clear the
  clipboard, which belongs to SEED-001#clear-clipboard. Missing helper,
  unsupported session, denied access, or transfer failure raises
  `ClipboardContentError`; never silent success or a text-only fallback.
- *Removed or changed sources.* The offer is a reference, not a snapshot: the
  library neither locks nor copies the files. A file manager pasting later
  copies what exists at paste time; a source removed after `copy_files`
  returns makes that paste fail or skip in the file manager's own way, and the
  library promises nothing further and is not involved.
- *Proof.* Success means an independent file manager pastes copies into a
  user-selected destination after the Python writer exits, with two sources
  whose names contain Unicode and spaces, and the sources remain unchanged.
  Name the file manager, OS/compositor and helper versions per platform; a
  platform without that observation is an evidence limit in the README, not a
  verified claim, and one file manager or compositor is not generalized.
  `paste_files()` returning the same paths is a useful in-memory/native
  consistency check, not interoperability proof.
- *Scope limits (deferred, not rejected).* A plain-text or name alternative in
  the same offer; cut/move semantics; virtual or promised files; remote or
  non-`file:` URIs; copying, opening, or pasting files by the library itself;
  PRIMARY selection; WSL, SSH, containers, and headless CI as guaranteed
  desktops; persistence across logout or reboot.
- *Plan:* [008-copy-files](../slice-plans/008-copy-files/PLAN.md).

**Key examples:**

1. `out/report final.pdf` and `out/données é.csv` exist →
   `copy_files(["out/report final.pdf", "out/données é.csv"])` returns `None`
   and the script exits → in the platform's named file manager the user pastes
   into a chosen folder and gets copies of both; the originals are unchanged.
2. The clipboard holds text `keep`; `missing.txt` does not exist →
   `copy_files(["out/report final.pdf", "missing.txt"])` raises
   `ClipboardContentError` naming `missing.txt` → `paste()` still returns
   `keep`.
3. `copy_files([])` or `copy_files("out/report final.pdf")` → raises
   `ClipboardContentError`; the previous clipboard is untouched.
4. Working directory `/home/u/proj`, `copy_files(["out/a.txt"])` →
   `paste_files()` returns `["/home/u/proj/out/a.txt"]`.
5. After a successful `copy_files`, the user deletes `out/a.txt` and then
   pastes in the file manager → the file manager reports or skips the missing
   item; nothing is raised in Python and no other file is touched.
6. Linux X11 without `xclip` on `PATH` → `copy_files([...])` raises
   `ClipboardContentError` with an install hint; the previous clipboard is
   untouched.

**Considered alternatives.** A documented per-platform recipe
(`Set-Clipboard -Path`, `osascript`, `xclip -t text/uri-list`) leaves callers
owning formats, copy-versus-cut markers, quoting and lifetime; Windows
PowerShell `Set-Clipboard -Path` treats `[` `]` as wildcards and remains only a
possible implementation aid. Revealing the files in the file manager
(`open -R`, `explorer /select,`) skips the clipboard and would change the
story's copy/paste goal, so it is not pursued here. The recommended direction
reuses the existing file-list format knowledge and the helper and
writer-lifetime patterns of `paste_files`, `copy_image`, and `copy_html`.

**Architecture.** Adds the first outbound file-list writer: per-platform
writers beside the existing `_files_native_*` readers, with a
`set_files_clipboard_writer` injection seam mirroring the HTML and image
writers so default tests stay in-memory. Validation lives above the writer so
every platform shares fail-before-replace. Linux session detection and helper
failure reporting reuse private `clipboard/_desktop` (including the
file-list reader's distinct Wayland rule) rather than adding another copy.
Linux writer lifetime relies on a background helper owner (`xclip` /
`wl-copy`), as `copy_image` does; Windows and macOS hand the data to the
system clipboard, which keeps it after exit. No ADR store exists in this
repository, so no Accepted decision was checked.

**Open risk for planning.** `xclip` and `wl-copy` offer one MIME type per
owner process. Whether named Linux file managers (GNOME Files, Dolphin,
Thunar) paste a lone `text/uri-list` or need `x-special/gnome-copied-files`
is unobserved here (Darwin checkout). Planning should settle it with an early
probe before building the Linux writers; if no single-type offer serves a
named file manager, the Linux coverage becomes a scope decision for the
maintainer instead of a silent reduction.

<a id="portable-text"></a>

### Use the text clipboard reliably and diagnose unavailable access

**Identity:** SEED-001#portable-text
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/010-portable-text/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"909f1a736c15214db0489b88ccfe923c709b1caf7ccd2cecd56ca682e0aa82ff","plan":"9ad1b77d74cd6abde7a6c87a114a57a43fa871ba46bbdbeee52a1590494180fd"}}
```

**Goal:** Existing Python users of `copy(text)` / `paste()` get exact Unicode
text exchange with independent desktop applications on the supported
desktops, and a bounded, named failure instead of a silent empty string or
no-op when the desktop clipboard cannot be reached, so they can trust the
package's simplest API and recover from session problems without guessing.
This is the baseline behind the package name; the richer APIs already sit
beside it.

**Scope:**

- *Required behavior.* `copy(text)` replaces the clipboard with exactly
  `text`, and `paste()` returns exactly the text the clipboard offers, as a
  `str`: Unicode and emoji, multiline strings, leading/trailing whitespace,
  and the empty string survive unchanged in both directions, including when
  the Python process has no UTF-8 locale (launchd, cron, IDE-spawned). Text
  written stays pasteable after the Python process exits. `paste()` returns
  `""` for ordinary absence (empty clipboard, or a clipboard with no text
  representation such as image-only); it never returns `None`. Native line
  endings pass through untranslated: text copied by a Windows application
  comes back with `\r\n`, and `paste().splitlines()` is the portable way to
  split lines.
- *Diagnosable failure.* Missing helper, no visible desktop session, a
  display or compositor that no longer answers, denied access, a stalled
  clipboard owner, and helper or transfer failure raise
  `ClipboardContentError` naming the cause and the fix where one is known
  (install hint naming `xclip` / `wl-clipboard`; "no `DISPLAY` or
  `WAYLAND_DISPLAY`"; the failing helper's message), within a documented
  bound of seconds, never an indefinite wait, a fabricated `""`, or a silent
  no-op write. Linux helper exit status and stderr are read, not discarded.
  Native text the helper returns in a non-UTF-8 declared encoding is decoded
  by that declaration (X11 `STRING` is Latin-1) or reported as
  `ClipboardContentError`; `UnicodeDecodeError` never escapes `paste()`.
- *Required restrictions.* A `str` containing `\x00` raises
  `ClipboardContentError` **before** the clipboard is replaced: Windows
  `CF_UNICODETEXT` is NUL-terminated, so the text would be silently
  truncated (data loss, the shared no-silent-truncation boundary). A `str`
  that cannot be UTF-8 encoded (lone surrogate) fails the same way before
  replacing. There is no in-memory fallback presented as the system
  clipboard; the injection seam used by tests is explicit.
- *Compatibility preserved.* `copy` / `paste` keep their names, positional
  signatures, and `str` results; `pyperclip` stays a dependency. Working
  text access that this story does not own keeps working through pyperclip
  with only failure translation: WSL (`clip.exe` / PowerShell bridge), a
  mechanism the caller selected with `pyperclip.set_clipboard`, and X11
  desktops with only `xsel`, Klipper, or Qt. Those paths carry no new
  bounded-failure or lifetime promise and are documented as unverified.
  Non-`str` arguments keep pyperclip's `str()` coercion (`copy(42)` copies
  `"42"`), as today; see Decisions.
- *Platform set and selection.* Owned default paths: Windows desktop
  (`CF_UNICODETEXT`), macOS Aqua (`pbcopy` / `pbpaste` run with a UTF-8
  locale), Linux X11 (`xclip`, `UTF8_STRING` first), Linux Wayland
  (`wl-copy` / `wl-paste`, background owner for lifetime, named compositor
  only). Session selection for text keeps pyperclip's order so no working
  user changes mechanism: WSL first; then Wayland when `WAYLAND_DISPLAY` is
  set and both `wl-copy` and `wl-paste` are on `PATH`; otherwise X11 when
  `DISPLAY` is set.
- *Proof.* Independent producers and consumers per desktop: X11 and Wayland
  under the existing gated Xvfb + `xclip` and Sway + `wl-clipboard` jobs
  (round trip after writer exit, dead `DISPLAY` / stale `WAYLAND_DISPLAY`,
  helper off `PATH`); Windows under a gated `windows-latest` job with
  PowerShell `Set-Clipboard` / `Get-Clipboard` (round trip, CRLF, held
  clipboard); macOS with an owner-desktop probe
  (`CLIPBOARD_NATIVE_PROBE=1`) using independent `osascript` / `pbpaste`,
  including a no-locale subprocess. A desktop without that observation is a
  README evidence limit, not a verified claim. Default pytest stays
  desktop-free through an explicit text seam.
- *Scope limits (deferred, not rejected).* Newline normalization on write
  or read; rejecting `bytes` / `None` / other non-`str` input; PRIMARY
  selection (SEED-001#primary-selection); clearing other representations
  (SEED-001#clear-clipboard); waiting for text (SEED-001#wait-for-content);
  RTF; a macOS AppKit (`pyobjc`) text path; verified support for `xsel`,
  Klipper, Qt, Cygwin, SSH, containers, headless CI, or remote desktops;
  persistence across logout or reboot.

**Key examples:**

1. Clipboard holds anything → `copy("  héllo 👋\nline 2 ")` and the script
   exits → an independent consumer on that desktop (`xclip -o`, `wl-paste`,
   `Get-Clipboard -Raw`, `pbpaste` in a UTF-8 shell) shows exactly those
   characters, spaces and newline included; the reverse, an independent
   producer copying the same text, makes `paste()` return it exactly.
2. macOS, Python started with no locale variables (as launchd does) →
   `copy("héllo 👋")` → `pbpaste` in a user terminal shows `héllo 👋`, not
   `h√©llo üëã`; `paste()` in that process returns `héllo 👋`, not
   `h?llo ??`.
3. `copy("")` → `paste()` returns `""` on every supported desktop. Whether
   other representations remain is platform behavior this story does not
   promise (Windows and `wl-copy` clear the clipboard; macOS and `xclip`
   leave an empty text offer).
4. Clipboard holds `keep` → `copy("a\x00b")` raises `ClipboardContentError`
   naming the NUL → `paste()` still returns `keep`. Same for `"\ud800"`.
5. Linux, `DISPLAY=:99` with no server there, `xclip` installed → `paste()`
   raises `ClipboardContentError` quoting xclip's display failure within the
   bound, instead of `""`; `copy("x")` raises instead of returning as if
   written. Same with `WAYLAND_DISPLAY` naming a socket whose compositor is
   gone.
6. SSH into Linux with neither `DISPLAY` nor `WAYLAND_DISPLAY` → `paste()`
   raises `ClipboardContentError` saying no desktop session is visible;
   with `DISPLAY` set and no `xclip` on `PATH` → the error names `xclip` and
   its install hint. Neither case returns `""`.
7. X11 CLIPBOARD owner that never answers → `paste()` raises after the
   documented bound. Windows clipboard held open by another process past
   the bound → raises; released within the bound → succeeds as before.
8. Image-only clipboard → `paste()` returns `""`; `inspect()` reports the
   image kind. No exception, because text is simply absent.
9. Windows Notepad copies two lines → `paste()` returns
   `"line 1\r\nline 2"`; `copy("line 1\nline 2")` pastes into Notepad as
   two lines.
10. WSL → `copy` / `paste` keep using the existing Windows bridge; a failing
    `powershell.exe` raises `ClipboardContentError` rather than returning
    `""`.

**Investigation (facts, with sources).** pyperclip 1.11.0 (installed; pin
`>=1.8.2,<2`) runs `xclip` / `xsel` / `wl-copy` / `wl-paste` and discards
their exit status and stderr, with no timeout, so a dead display yields
`paste() == ""` and a silent no-op `copy` (source lines 158–236). Its
Windows path retries `OpenClipboard` for 0.5 s then raises, writes
`wcslen` characters (truncating at NUL), and `copy("")` empties every
format (395–462). Its pyobjc path returns `None` for a text-less pasteboard
(123–126). Observed on this host (macOS 26.6.2 / 25G83, Find pasteboard so
the live clipboard stayed untouched): with `LC_ALL=C` or an empty
environment, `pbpaste` turns `héllo 👋 ﾃｽﾄ` into `h\x8ello ?? ???` and
`pbcopy` stores `h√©llo üëã`; any UTF-8 `LC_ALL`, `LC_CTYPE`, or `LANG`
restores exact bytes both ways; `pbcopy`/`pbpaste` pass NUL, CRLF, leading
and trailing whitespace through; an empty `pbcopy` leaves an empty
`public.utf8-plain-text` offer; a cleared pasteboard reads `""` with exit 0.
Project tests cover text only through a stubbed `determine_clipboard`; no
native text proof exists, while the CI already hosts Xvfb + `xclip`,
Sway + `wl-clipboard`, and a `windows-latest` clipboard session.
*Hypotheses for planning:* Windows applications deliver `\r\n` and accept
LF-only writes (settle in the Windows job); `xclip` 0.13 and `wl-paste`
2.2.1 stderr wording for a dead display is classifiable (settle in the
Linux jobs); a macOS "Paste from Other Apps" denial may make `pbpaste`
return `""` with exit 0 (settle only by denying the terminal's permission
on a macOS 15.4+ desktop; not done here, so denial stays an evidence limit
if undetectable); `pbcopy` / `pbpaste` behavior in an SSH session without
WindowServer access is unobserved.

**Considered alternatives.** (a) Keep the bare re-export and document its
limits: no code risk, but false empties and the macOS locale corruption
remain, so the purpose fails. (b) Wrap pyperclip only (validate input,
translate exceptions, check session variables first): fixes NUL, error
type, and the no-session message, but cannot see helper failure or a dead
display because pyperclip discards them, and cannot fix the locale without
mutating process environment. (c) Add `copy_text` / `paste_text` with the
strong contract beside unchanged `copy` / `paste`: no compatibility risk,
two text APIs, and the simple API stays untrustworthy. (d) Upstream fixes to
pyperclip and raise the pin: welcome in parallel, not under this project's
control. **Recommended:** own the four default text paths in this package,
reusing its bounded-helper patterns, and delegate everything else to
pyperclip with failure translation. The decisive challenge is that only this
option reaches the story's purpose on Linux; its risk, changing mechanism
for working users, is contained by keeping pyperclip's selection order and
the delegate fallback. Borrowed mechanism: a stale NFS mount reports
`ESTALE` rather than an empty directory because the error travels on a
separate channel from the data; here the helper's exit status and stderr
are that channel, so empty text and failed access never share the value
`""`. The analogy breaks where `xclip` exits 1 for both "no owner" and
"can't open display": classification must read version-dependent stderr
wording, and unknown wording defaults to failure, not to `""`.

**Architecture.** Text leaves the `__init__` re-export for an owned text
module with per-platform native modules and an explicit injection seam
(mirroring `set_html_clipboard_reader`) so default tests stay in-memory;
the subprocess-stub test is replaced. `ClipboardContentError` grows from
"rich content" to clipboard content including text; text failures raise it
with the pyperclip or helper error as `__cause__`, which changes what a
caller catching `pyperclip.PyperclipException` sees (noted in the README).
Linux session detection and helper-failure formatting reuse the single
private desktop module that SEED-001#desktop-helpers introduces when it has
landed; until then follow its target layout rather than adding a copy. The
text selection predicate (pyperclip's order) is a third Wayland rule beside
`paste_html`'s and `paste_files`'; unifying them stays the product decision
desktop-helpers recorded, not this story's. Writer lifetime on Linux relies
on the helper's background owner as `copy_image` does; Windows and macOS
hand data to the system. No ADR store exists in this repository, so no
Accepted decision was checked.

**Decisions recorded here, reviewable before Take.** Text failures use
`ClipboardContentError` rather than a new class (one failure type for all
non-image content, and `copy_html` already raises it for invalid text).
Non-`str` arguments keep pyperclip's coercion because rejecting them would
break working call sites; rejecting `bytes` / `None` is a deferred proposal.
No newline translation on either side. `copy("")` promises only that
`paste()` then returns `""`.

<a id="clear-clipboard"></a>

### Clear every representation from the current clipboard

**Identity:** SEED-001#clear-clipboard
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/011-clear-clipboard/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"0bd330ead961dec862bca590971b7c89b5638bc5b94bf0586512e3d91f30c304","plan":"37530da5855f8770fa813d8a4751b85bdb626639d3f5824acf2578eb206dbbf9"}}
```

**Goal:** Python users and automation developers can deliberately empty the
current clipboard, removing every representation another application or this
library offered (text, HTML, image, file list, unknown types), with one call
whose result is the same on every supported desktop, instead of relying on
`copy("")`, which empties the clipboard on Windows and `wl-copy` but leaves
an empty text offer on macOS and `xclip`. A failed clear is reported, so the
user never believes content is gone when it is not. This adds the ordinary
clipboard "clear" action beside the read and write operations, and keeps
its meaning as more content kinds are added.

**Scope:**

- *Required behavior.* A new `clear()` (no `clipboard[images]` extra) leaves
  the current CLIPBOARD with **no offer at all**: no old representation is
  readable, and no empty placeholder (such as an empty text type) is left in
  its place. Afterwards the library's readers report ordinary absence:
  `paste()` returns `""`, `paste_html()`, `paste_image()`, and
  `paste_files()` return `None`, and `inspect()` returns empty `kinds` and
  `formats`. Independent native
  consumers see an empty clipboard too. `clear()` returns `None`, and
  calling it on an already empty clipboard, or twice in a row, succeeds
  with no error. When this library's own Linux background owner (from
  `copy_image`, or later writers) is serving the old offer, clearing ends
  that offer, so no helper process keeps serving it.
- *Native paths.* macOS Aqua: `NSPasteboard` general pasteboard
  `clearContents`. Windows desktop: `OpenClipboard` / `EmptyClipboard` /
  `CloseClipboard` through user32, retrying the open within a documented
  bound while another process holds the clipboard. Linux X11: give up
  CLIPBOARD ownership so no owner remains (`xclip` has no clear operation;
  planning chooses the mechanism, see Architecture). Linux Wayland:
  `wl-copy --clear`. Session selection uses the existing writer rule
  (Wayland when `WAYLAND_DISPLAY` or the session type says so), as image
  write, HTML, and inspect do.
- *Empty Linux offer reads as empty (included).* Today `inspect()` on Linux
  raises when CLIPBOARD has no owner (`xclip` "target TARGETS not
  available") or nothing is copied (`wl-paste` "Nothing is copied" /
  "No selection"), even though its contract says an empty offer gives an
  empty snapshot. This story makes those two cases return an empty
  snapshot, because otherwise the state `clear()` creates cannot be
  observed through the library's own contract. Other non-zero helper exits
  still raise.
- *Failure reporting.* No visible desktop session, missing helper
  (`wl-clipboard` install hint on Wayland; whatever the X11 mechanism needs
  on X11), a Windows clipboard held past the bound, denied access, and a
  helper or native call that fails raise `ClipboardContentError` naming the
  cause, within a bound of seconds, never a silent success. A failed clear
  promises nothing about what is on the clipboard afterwards beyond what the
  platform did.
- *Boundary of the promise.* Clearing acts on the current CLIPBOARD once.
  Something that offers content **after** the clear is a newer copy, not a
  failed clear: another application copying, a clipboard manager that
  immediately offers its saved entry again (for example, KDE Klipper's
  "prevent empty clipboard" or a compositor's built-in clipboard
  persistence), or a sync service. `clear()` does not check the clipboard
  again afterwards and does not report such a re-offer. It does not erase
  OS clipboard history (Windows Win+V, managers' saved entries), cloud or
  Universal Clipboard copies, or remote devices, and it claims no secure
  deletion.
- *Proof.* An independent producer puts HTML + text, and separately an
  image, on the clipboard; after `clear()` an independent consumer sees no
  types: macOS through a gated owner-desktop probe
  (`CLIPBOARD_NATIVE_PROBE=1`, `osascript` producer, pasteboard type list
  and `pbpaste` consumers); Windows in a gated `windows-latest` job
  (PowerShell `Set-Clipboard` producer, format enumeration /
  `Get-Clipboard` consumer); X11 under the existing Xvfb + `xclip` job (no
  clipboard manager); Wayland under the existing Sway + `wl-clipboard` job.
  The README names those sessions and helper versions. GNOME, KDE, and any
  desktop with a clipboard manager are evidence limits, not verified
  claims. Default pytest stays desktop-free through an explicit injection
  seam.
- *Scope limits (deferred, not rejected).* Clearing PRIMARY
  (SEED-001#primary-selection), the macOS Find pasteboard, or other named
  pasteboards; clearing only one kind while keeping others; snapshot and
  restore; erasing history, managers, or synced copies; checking that the
  clipboard stays empty afterwards; WSL, SSH, containers, and headless CI as
  guaranteed desktops. Changing what `copy("")` does belongs to
  SEED-001#portable-text, not to this story.
- *Plan:* [011-clear-clipboard](../slice-plans/011-clear-clipboard/PLAN.md).

**Key examples:**

1. Another application copies a formatted paragraph (HTML + text) →
   `clear()` returns `None` → `paste()` returns `""`, `paste_html()` returns
   `None`, `inspect()` returns empty `kinds` and `formats`; pasting into an
   independent application inserts nothing.
2. Another application copies an image → `clear()` → `paste_image()` returns
   `None` and no independent consumer can read the image.
3. The clipboard is already empty → `clear()` returns `None`; calling it
   again also returns `None`.
4. Contrast with text: on macOS today `copy("")` leaves `inspect().kinds ==
   {"text"}` with an empty value; `clear()` leaves `inspect().formats == ()`
   on every supported desktop.
5. Linux X11: `copy_image(img)` returned and its background `xclip` owner is
   serving the image → `clear()` → that owner stops serving and exits;
   `xclip -o -t TARGETS` reports no owner.
6. Linux X11 with nothing owning CLIPBOARD (for example, right after
   `clear()`) → `inspect()` returns an empty snapshot instead of raising;
   the same on Wayland when `wl-paste` says nothing is copied.
7. Linux with neither `DISPLAY` nor `WAYLAND_DISPLAY` → `clear()` raises
   `ClipboardContentError` saying no desktop session is visible; Wayland
   without `wl-copy` on `PATH` → the error names `wl-clipboard`.
8. Windows, another process holds the clipboard open past the bound →
   `clear()` raises `ClipboardContentError` naming the held clipboard; the
   previous content is still there. Released within the bound → `clear()`
   succeeds.
9. KDE with Klipper set to prevent an empty clipboard → `clear()` returns
   `None`, then Klipper offers its last entry again; `inspect()` shows that
   entry. This is a newer offer outside the promise; the README names it.

**Investigation (facts, with sources).** Observed on this host (macOS 26.6.2
/ 25G83, `osascript` / AppKit, on a private named pasteboard so the live
clipboard stayed untouched): after writing `public.html` and
`public.utf8-plain-text`, `clearContents` left zero types, a second
`clearContents` on the empty pasteboard succeeded, the change count rose on
each call, and `stringForType` returned nil. pyperclip 1.11.0 (installed)
handles `copy("")` by calling `EmptyClipboard` with no data on Windows
(`__init__.py` 418–440) and `wl-copy --clear` on Wayland (210–230), but
pipes empty input to `xclip -selection c` on X11 (157–167) and `pbcopy` on
macOS, which leave an empty text offer (the macOS result is recorded under
SEED-001#portable-text). In the code, the Linux inspect listings
`_xclip_targets_inspect` / `_wl_paste_list_types_inspect` in
`clipboard/_desktop.py` raise on any non-zero exit, while the HTML read
listings in the same module already treat "target TARGETS not available"
and "Nothing is copied" / "No selection" as absence. No test covers inspect
on an empty Linux clipboard. *Hypotheses for planning:* a non-owner client
setting the X11 CLIPBOARD owner to `None` empties it under Xvfb and makes
an `xclip` background owner exit (settle in the X11 job before building
on it); `wl-copy --clear` empties the selection on Sway (settle in the
Wayland job); `EmptyClipboard` after `OpenClipboard(NULL)` removes every
format for PowerShell consumers (settle in the Windows job); clearing the
macOS general pasteboard triggers no paste-privacy prompt (settle with the
owner-desktop probe); `paste_html()`, `paste_files()`, and `paste_image()`
already return `None` on an unowned X11 / nothing-copied Wayland clipboard
(their code treats "not available" / "Nothing is copied" as absence; settle
in the Linux jobs, and any reader that raises there is fixed here like
`inspect()`); the clipboard-manager re-offer behavior in example 9
is from upstream descriptions and is not observed here.

**Considered alternatives.** (a) Document `copy("")` as the clear: no code,
but it leaves an empty text offer on macOS and X11, and SEED-001#portable-text
explicitly does not promise more than `paste() == ""`, so the user still has
to guess. (b) Offer an explicit empty placeholder (take ownership and serve
zero types): it is not empty on X11 (an owner still answers), keeps a
helper process alive, and differs from what Windows, macOS, and `wl-copy`
do. (c) Clear, then inspect again and raise if anything is offered: it
cannot tell a manager's re-offer from a legitimate new copy made in the same
moment, so it would report false failures; rejected in favor of the stated
boundary. (d) Reuse PyClip's clear: an extra dependency for four short
native calls, and its native behavior is not verified. **Recommended:**
native clear per platform behind one `clear()`. *Borrowed mechanism:* HTTP
`DELETE` versus `PUT` with an empty body on a resource with several
negotiated representations. `copy("")` is the empty `PUT`: the resource
still exists with one empty text variant. `clear()` is the `DELETE`: every
variant is gone, and repeating it is idempotent and still succeeds.
Clipboard managers and history play the role of caches, which the library
does not purge. The analogy breaks on X11 and Wayland, where there is no
server storage to delete from; "deleting" is giving up ownership, and a
manager can become the new owner at once, which is a new `PUT` by someone
else, not stale data. So success means the clear was performed, not that
the clipboard stays empty. *Strongest doubt (challenge):* on desktops with
an always-on clipboard manager, `clear()` can succeed and old content can
still be pasteable a moment later. That meets the wording but not the
purpose for those users. It does not change what this story can promise,
because a re-offer cannot be told apart from a new copy. It is handled by
the boundary above, example 9, and README evidence limits, not by more
mechanism.

**Architecture.** Adds one public operation, `clear()`, with an injection
seam `set_clipboard_clearer` (mirroring `set_html_clipboard_writer`) so
default tests stay in-memory, in a new content module with per-platform
native clearers, raising `ClipboardContentError`. macOS reuses the
`osascript` / AppKit stack of `copy_html` and `inspect`. Windows reuses the
bounded `OpenClipboard` retry approach of `clipboard/_offer_windows.py`
rather than another copy with a different bound. Linux session detection,
helper-failure detail, and the no-owner / nothing-copied markers come from
private `clipboard/_desktop`; the inspect empty-offer change lives in its
listing functions, so content-kind modules do not copy those helpers. X11
has no clear in `xclip`, so planning chooses between calling
`XSetSelectionOwner(CLIPBOARD, None)` through libX11 with `ctypes`
(recommended: libX11 is already present wherever `xclip` runs, so there is
no new install) and requiring `xsel --clipboard --clear` (a second X11
helper users must install). SEED-001#portable-text is in progress and owns
the text path and `copy("")`; this story leaves both unchanged and only
reads text through the existing `paste()`. No ADR store exists in this
repository, so no Accepted decision was checked.

**Decisions recorded here, reviewable before Take.** `clear()` means "no
offer at all", not "no old content" (an empty placeholder does not count),
because the title promises every representation and `copy("")` already
gives the weaker result on two platforms. The Linux inspect empty-offer
change is included in this story. A clipboard manager's re-offer after the
clear is outside the promise and is not detected.

<a id="wait-for-content"></a>

### Wait for clipboard content with bounded cancellation and timeouts

**Identity:** SEED-001#wait-for-content
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Automation developers can wait for a user to copy supported
  content without writing their own unbounded polling loops.
- **Evaluation:** Starting without the requested supported kind, a wait returns
  when another application supplies it; a changed-value wait returns when the
  observed value changes. A deadline or cancellation ends the wait predictably;
  unavailable or denied access fails distinctly from timeout.
- **Value / learning:** Makes interactive automation practical and tests which
  monitoring semantics can be honest across native event and polling models.
- **Boundary:** One bounded wait, scoped to an explicitly supported content
  kind. Specify initial-value behavior, zero/invalid timeout, cancellation,
  clearing, and observation interval during refinement. Changed value does not
  mean every copy event: identical recopy and changes between observations may
  be missed. No global audit log, background watcher by default, or promise of
  lossless event delivery. Permission denial must not cause repeated prompts.
- **Effort hypothesis:** **M**, medium confidence; assumes a bounded observation
  contract is acceptable where native notification support is unavailable.
- **Depends on:** None. The story must include the supported read behavior it
  needs, reusing already delivered content operations when available. Do not
  wait for a hypothetical universal event backend.
- **Safe stopping point:** Callers gain predictable waiting without hidden
  history, payload logging, busy spinning, or stranded monitoring resources.

<a id="primary-selection"></a>

### Use the Linux primary selection explicitly

**Identity:** SEED-001#primary-selection
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python users on Linux can participate in the select-and-middle-
  click text workflow without unexpectedly changing the ordinary clipboard.
- **Evaluation:** With different text in CLIPBOARD and PRIMARY, an explicit
  PRIMARY read/write uses only PRIMARY; default text calls keep using CLIPBOARD.
  Unsupported selection access produces a clear unsupported outcome.
- **Value / learning:** Respects an established Linux clipboard behavior and
  tests X11/Wayland selection differences without pretending macOS/Windows
  expose the same facility.
- **Boundary:** Explicit text selection operations on supported X11 and
  Wayland sessions. No automatic synchronization, macOS Find buffer, SECONDARY,
  multi-seat routing, or rich data on PRIMARY in this story.
- **Effort hypothesis:** **M**, medium confidence; assumes native helpers or
  protocols expose PRIMARY where advertised. Wayland support is conditional
  on the compositor and protocol, not inferred from X11.
- **Depends on:** None. Selection semantics are independently evaluable.
- **Safe stopping point:** Opt-in Linux behavior is useful by itself and
  unsupported selections never silently fall back to CLIPBOARD.

## Ordering and Scope Reduction

The global queue follows the maintainer's images/rich-content priority: image
reading, image writing, HTML writing, then HTML reading. Image reading has
direct user demand and a strong reuse candidate, so it tests useful scope
early. HTML writing precedes reading because its paired rich/plain offer
tests the more consequential multi-format assumption. Inspection follows
those concrete workflows; it is not a prerequisite framework project.

File input/output expands to another everyday content type. Text reliability,
clear, waits, and explicit PRIMARY finish the selected ordinary desktop
behaviors. All first seven stories retain their own text compatibility,
failure semantics, native lifetime, and installation obligations; their order
does not postpone those requirements. Priority is not a dependency chain.
No genuine blocking dependency has been identified, so none is recorded.

Effort distribution: **4 L, 6 M, 1 S**, with confidence stated per story. Each
read or write is independently useful; combining both would hide distinct
consumers and proof. These are decomposition hypotheses, not ready execution
plans. Refine one selected story before execution planning, splitting further
if native evidence makes its outcome too large.

If scope must shrink, drop PRIMARY first, then waits, then outbound files,
then inbound files. Stop after any delivered content workflow with its
compatibility and safety obligations complete. Preserve the image/HTML core
unless the maintainer revises the direction; native evidence that invalidates
it requires a scope decision rather than silently reducing platform coverage.

## Open Decisions

No remaining parent-level selection or order decision blocks this decomposition.
The research recommendations and effort hypotheses remain reviewable. Story
refinement must settle concrete supported platform combinations, image value
shapes, HTML context exposure, absence/error results, dependency installation,
and native proof. Those are not implementation decisions made by this seed.

RTF, arbitrary typed binary transfer, snapshot/restore, sensitive-data hints,
a CLI, async streams, history, cloud synchronization, and mobile are unqueued
extension possibilities in the research, not additional selected promises.

## When to Surface

Now, when selecting the first improvement that makes `clipboard` more than a
text wrapper; revisit the ordering after the first independent native image
interoperability evidence.

## Breadcrumbs

- Terry Yin's 2026-11-02 request to research the domain, decompose stories,
  queue them, and set the initial near-future direction.
- Terry's explicit replies: prioritize images/rich content; use the proposed
  planning conventions and comparative S/M/L bands.
- [Domain research and linked primary sources](../research/2026-11-02-clipboard-domain.md).
- [Product backlog](../PRODUCT-BACKLOG.md).
- [Repository contribution constraints](../../AGENTS.md).

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

<a id="bounded-x11-file-write"></a>

### Bound the X11 file-list write and prove directories and duplicates natively

**Identity:** SEED-001#bounded-x11-file-write
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/014-bounded-x11-file-write/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"c9ca8b031d954198d2a4ceb0eae584c183fca25bc125263e51d4c84da703be1f","plan":"80bbb2521ea44bc1fac0f838ddb3e8eed770167a4dd9bce045eec7aceb169fd0"}}
```

**Goal:** Callers of `copy_files(paths)` on Linux X11 get the documented
bounded `ClipboardContentError` instead of an indefinite hang when the X
server stalls and the URI list is larger than a pipe buffer, and every
desktop's native proof covers the directory, duplicate and relative-path
promises SEED-001#copy-files makes.

**Scope:** Correction of SEED-001#copy-files: feed the X11 file-list
`xclip` owner without a blocking unbounded pipe write, keeping the background
owner, TARGETS plus exact-body read-back, stderr quoting, install hint and
owner cleanup; extend the four gated native probes so a directory, a
duplicate and a relative path reach each native writer and an independent
consumer. Excludes the same pattern in the text writer (owned by
SEED-001#bounded-x11-text-write) and `copy_image`, a shared Linux owner
helper (a structure decision for the maintainer), and file-manager paste
evidence limits.
[Plan](../slice-plans/014-bounded-x11-file-write/PLAN.md)

<a id="bounded-x11-text-write"></a>

### Bound the X11 text write for large text on a stalled display

**Identity:** SEED-001#bounded-x11-text-write
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/012-bounded-x11-text-write/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"49c53cff5acac2714373807928aa4b62d600b74bef85fa96a4a9d0ceba954949","plan":"8d26bef174c6eed0b88d31dd7bac3ba67fae7f39b5aad6797a599bae6167feb2"}}
```

**Goal:** Callers of `copy(text)` on Linux X11 get the documented bounded
`ClipboardContentError` instead of an indefinite hang when the X server stalls
and the text is larger than a pipe buffer, so SEED-001#portable-text's "never
an indefinite wait" holds for every text size.

**Scope:** Correction of SEED-001#portable-text's owned X11 writer only: feed
`xclip` its input without a blocking unbounded pipe write, keeping the
background owner, exact-bytes read-back, stderr quoting and owner cleanup;
remove the test-only `os.killpg` fallback; make the gated Wayland text wrapper
fail rather than skip on a missing session or helper. Excludes the same
pattern in `copy_image` and any change to selection rules.
[Plan](../slice-plans/012-bounded-x11-text-write/PLAN.md)

The maintainer accepted keeping this correction first in the queue on
2026-11-03.

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

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

<a id="wait-for-content"></a>

### Wait for clipboard content with bounded cancellation and timeouts

**Identity:** SEED-001#wait-for-content
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/018-wait-for-content/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"43b8af3b29c58c0897efc418c2e41e03e86ddc7b6790ace4b99fe26742786d80","plan":"beae2ac3d900293b2f4b01a98c778551d7a7768162f2da825f907981542a01a0"}}
```

**Goal:** Automation developers can wait, in one bounded call, for the user
(or another application) to copy content their script needs, instead of
writing their own polling loops around `inspect` / `paste` with ad hoc
sleeps, deadlines and error handling. A wait returns as soon as the content
is observed, ends predictably at its deadline or on cancellation, and never
hides an access failure as "nothing copied yet". This makes interactive
automation ("copy the image you want to process") practical with the content
operations already delivered, and records honestly what a polling observer
can and cannot see.

**Scope:**

- *Required behavior: wait for a kind.* A new public function
  `wait_for_kind(kind, *, timeout, interval=0.5, cancel=None)` observes the
  current offer through `inspect` and returns the first
  `ClipboardOfferSnapshot` whose `kinds` contain `kind` (one of
  `"text"`, `"image"`, `"html"`, `"files"`). It is a state wait: when the
  kind is already offered at the first observation it returns at once (a
  caller who needs *new* content uses the text-change wait, or clears first).
  It reads no payload, so it needs no images extra, and it leaves the
  clipboard unchanged.
- *Required behavior: wait for changed text.* A new public function
  `wait_for_text_change(*, timeout, interval=0.5, cancel=None)` reads the
  text through `paste` once as its baseline, then returns the first later
  observed text that is non-empty and differs from that baseline. Clearing,
  or an offer with no text, is not a change: the wait continues. "Changed"
  compares observed values, not copy events: an identical recopy, and values
  that come and go between two observations, are missed (documented, not a
  defect).
- *Required behavior: deadline and cancellation.* `timeout` is required and
  is a non-negative finite number of seconds measured on a monotonic clock;
  there is no unbounded wait. `timeout=0` makes exactly one observation
  (for the text-change wait, only the baseline). When the deadline passes, or
  when `cancel` (a `threading.Event`, or any object with `is_set()` and
  `wait(seconds)`) is set, the wait returns `None` without another
  observation. Between observations the wait sleeps on `cancel.wait(...)` (or
  an equivalent sleep), so setting `cancel` from another thread ends it
  without waiting out the interval, and no time is spent busy spinning. No
  new observation starts after the deadline; an observation already in
  flight finishes within its own existing helper bound, so a wait returns no
  later than `timeout` plus one observation. `KeyboardInterrupt` propagates.
- *Required behavior: failures end the wait.* Any `ClipboardContentError`
  from an observation (no desktop session, missing helper, denied access,
  enumeration or helper failure or helper timeout, "not available" on the
  platform) is raised at once and is never retried, so a refused permission
  cannot be asked for again by the wait itself. An empty clipboard is
  absence, not failure: `inspect` yields no kinds and `paste` yields `""`,
  and the wait keeps observing. A timeout or cancellation returns `None`,
  so it can never be mistaken for a failure.
- *Required behavior: invalid input.* An unknown `kind`, a negative, NaN,
  infinite, boolean or non-numeric `timeout`, an `interval` that is not a
  positive finite number, or a `cancel` without `is_set` / `wait` raises
  `ClipboardContentError` before any observation, following the library's
  invalid-input rule. Required restriction: `interval` must be positive
  because a zero interval busy-spins helper processes against the desktop;
  `timeout` must be finite because the story's promise is a bounded wait.
- *Platforms.* The waits run wherever their observation operation runs, with
  that operation's session selection and errors: `wait_for_kind` through
  `inspect` (macOS Aqua, Windows desktop, Linux X11 TARGETS, Linux Wayland
  MIME list; elsewhere `inspect`'s "not available" error is raised at the
  first observation), `wait_for_text_change` through `paste` (all `paste`
  backends, including pyperclip delegation). Injected seams
  (`set_clipboard_inspector`, `set_text_clipboard_reader`) are honoured, so
  desktop-free tests need no new seam.
- *Resources and privacy.* The wait runs in the calling thread, starts no
  background watcher, thread or long-lived helper, keeps no history beyond the
  one baseline text it compares against, and logs no payload. Every helper it
  starts is the bounded helper of the observation operation, finished before
  the wait returns or raises.
- *Proof.* Desktop-free default tests (in-memory inspector and reader, fake
  clock and cancel) cover immediate return, appearance after several
  observations, deadline, `timeout=0`, cancellation from another thread,
  failure propagation without retry, clearing during a change wait, and the
  invalid inputs. Gated native probes (`CLIPBOARD_NATIVE_PROBE`) on macOS,
  Windows, Linux X11 (Xvfb + `xclip`) and Linux Wayland (Sway +
  wl-clipboard) start a wait, then copy with an independent producer
  (`pbcopy`, PowerShell `Set-Clipboard`, `xclip`, `wl-copy`) and check that
  `wait_for_kind("text")` from an empty clipboard and
  `wait_for_text_change` both return within the deadline, and that a wait
  with nothing copied returns `None` after its timeout. The README documents
  the two functions, the observation limits, and the observed sessions;
  other kinds and other compositors rely on `inspect`'s existing native
  proof and are evidence limits for the wait itself.
- *Scope limits (deferred, not rejected).* Native change notification
  (macOS `changeCount`, Windows clipboard sequence number or format
  listener, X11 XFixes, `wl-paste --watch`) as an optimization; changed-value
  waits for images, HTML or files; waiting on PRIMARY
  (SEED-001#primary-selection); async/awaitable waits; callbacks or
  iterators over successive changes; a background watcher; any promise of
  lossless or per-event delivery.
- *Plan:* [018-wait-for-content](../slice-plans/018-wait-for-content/PLAN.md).

**Key examples:**

1. Empty clipboard → `wait_for_kind("image", timeout=30)` → the user copies a
   screenshot in another app 3 s later → returns a snapshot whose `kinds`
   contain `"image"` within about one interval of the copy.
2. Clipboard already offers text → `wait_for_kind("text", timeout=5)` →
   returns at once after one observation.
3. Clipboard holds `"old"` → `wait_for_text_change(timeout=30)` → another app
   copies `"new"` → returns `"new"`.
4. Clipboard holds `"old"` → `wait_for_text_change(timeout=30)` → the
   clipboard is cleared, then `"old"` is copied again → the wait keeps
   observing and returns `None` at 30 s (clearing and identical recopy are
   not changes).
5. Nothing copied → `wait_for_kind("html", timeout=2)` → returns `None` about
   2 s later, with no observation started after the deadline.
6. A wait with `cancel=event` and `timeout=60` → another thread sets `event`
   after 1 s → the wait returns `None` without waiting out the interval or
   the timeout.
7. Linux with no desktop session → `wait_for_kind("text", timeout=10)` →
   raises `ClipboardContentError` ("no desktop session") at once, not after
   10 s and not `None`.
8. `wait_for_kind("rtf", timeout=1)`, `wait_for_text_change(timeout=-1)`,
   `wait_for_kind("text", timeout=float("inf"))`, or
   `wait_for_kind("text", timeout=1, interval=0)` → `ClipboardContentError`
   before the clipboard is observed.
9. `wait_for_text_change(timeout=0)` → reads the baseline once and returns
   `None`.

<a id="primary-selection"></a>

### Use the Linux primary selection explicitly

**Identity:** SEED-001#primary-selection
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/017-primary-selection/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"ebba7de01ba4eea61a1390381a7f7eee3282670efa9789c83cbb7067199d3ab6","plan":"39909e95269bb078edb151bdb9d7b88ce77cc7d174def566539db191f2c47159"}}
```

**Goal:** Python users and automation developers on a Linux desktop can take
part in the select-and-middle-click text workflow: read the text the user has
just selected, or offer text for a middle-click paste, without changing what
the ordinary clipboard holds. Today `copy` / `paste` reach only CLIPBOARD, so
such a user has to call `xclip -selection primary` or `wl-paste --primary`
themselves. This adds Linux's second everyday text exchange beside the
ordinary clipboard, and never pretends macOS or Windows have one.

**Scope:**

- *Required behavior.* Two new public functions beside `copy` / `paste`:
  `copy_primary(text)` replaces the PRIMARY selection with `text`, and
  `paste_primary()` returns PRIMARY's text as `str`. Both act on PRIMARY
  only: `copy_primary` leaves CLIPBOARD as it was, and `copy` / `paste` keep
  acting on CLIPBOARD only and leave PRIMARY as it was. `copy_primary`
  applies the same input rules as `copy` (non-`str` values through `str()`;
  text containing `"\x00"` or not UTF-8 encodable is rejected with
  `ClipboardContentError` before PRIMARY is replaced). `paste_primary`
  returns `""` when nothing is selected or the owner offers no text, never
  `None`, with line endings untranslated, as `paste` does. Text written with
  `copy_primary` stays pasteable by middle-click after the Python process
  exits, as `copy` text does.
- *Native paths.* Linux X11 through `xclip -selection primary`; Linux
  Wayland through wl-clipboard's `--primary` (`wl-copy --primary`,
  `wl-paste --primary`), which works only where the compositor offers a
  primary-selection protocol to wl-clipboard. Session choice follows the
  text rule `copy` / `paste` already use (`_text_session_owner`: Wayland
  when `WAYLAND_DISPLAY` is set and both wl-clipboard helpers are on PATH,
  otherwise X11 with `DISPLAY`), so on one session PRIMARY and CLIPBOARD
  text are reached through the same desktop. Reads and writes use the
  10 s bound the Linux text helpers already share.
- *Unsupported never falls back to CLIPBOARD (required restriction).* Every
  case where PRIMARY cannot be reached raises `ClipboardContentError` naming
  the reason, and never reads or writes CLIPBOARD instead: macOS, Windows,
  WSL and other non-Linux platforms ("not available" on that platform); Linux
  with no desktop session; a Wayland compositor whose wl-clipboard reports
  that primary selection is not supported (distinct from "nothing
  selected", which reads `""`); and a session without the owned helper
  (X11 without `xclip`, even where pyperclip could still reach CLIPBOARD
  through `xsel` or Qt; Wayland without wl-clipboard), with an install hint.
  Other helper failures and timeouts raise as `paste` / `copy` do. Reason:
  the story's promise is that the ordinary clipboard is never changed or read
  by mistake; a silent fallback would overwrite what the user copied.
- *Injected text seams do not apply.* `set_text_clipboard_writer` /
  `set_text_clipboard_reader` keep governing `copy` / `paste` only; an
  injected CLIPBOARD writer or reader never receives PRIMARY traffic.
- *Proof.* Gated native probes (`CLIPBOARD_NATIVE_PROBE`) under the existing
  Xvfb + `xclip` and Sway + wl-clipboard CI jobs, with independent
  producers and consumers (`xclip -selection primary|clipboard`,
  `wl-copy` / `wl-paste` with and without `--primary`) and the writer-exit
  lifetime check. Desktop-free default tests cover dispatch, validation,
  absence, the unsupported cases and the no-fallback rule with fake helpers.
  The README names the observed sessions and helper versions. GNOME, KDE,
  other compositors, XWayland bridging of PRIMARY between X11 and Wayland
  clients, and a native compositor without primary-selection support are
  evidence limits unless observed.
- *Scope limits (deferred, not rejected).* Rich data (HTML, images, files)
  on PRIMARY; `inspect` and `clear` of PRIMARY; SECONDARY; the macOS Find
  pasteboard; automatic or optional synchronization between PRIMARY and
  CLIPBOARD; multi-seat routing; waiting for a selection change
  (SEED-001#wait-for-content); a public injection seam for PRIMARY
  (desktop-free tests fake the helpers). A clipboard manager or desktop
  setting that copies PRIMARY into CLIPBOARD (or back) on its own is a
  newer offer by that program, outside this promise; the README names it.
- *Plan:* [017-primary-selection](../slice-plans/017-primary-selection/PLAN.md).

**Key examples:**

1. Linux X11, CLIPBOARD holds `"copied"` and the user has selected
   `"selected"` in a terminal → `paste_primary()` returns `"selected"`;
   `paste()` still returns `"copied"`.
2. Same session → `copy_primary("for middle click")` → an independent
   `xclip -selection primary -o` (or a middle-click) gives
   `"for middle click"`, and `xclip -selection clipboard -o` still gives
   `"copied"`. The same holds after the Python process that wrote it exits.
3. Same session → `copy("new copy")` → `paste()` gives `"new copy"` and
   `paste_primary()` still gives `"selected"`.
4. Linux X11 with nothing owning PRIMARY → `paste_primary()` returns `""`.
5. Linux Wayland on Sway → examples 1–3 hold through `wl-copy --primary` /
   `wl-paste --primary` and their non-primary counterparts.
6. Linux Wayland compositor where wl-clipboard reports primary selection is
   unsupported → `paste_primary()` and `copy_primary("x")` raise
   `ClipboardContentError` saying so; CLIPBOARD is neither read nor
   changed.
7. macOS or Windows → `copy_primary("x")` raises `ClipboardContentError`
   saying PRIMARY is not available on that platform; the clipboard is
   unchanged.
8. Linux X11 session with `xsel` but no `xclip` → `paste()` still works
   through pyperclip, but `paste_primary()` raises naming the missing
   `xclip` with an install hint.
9. `copy_primary("a\x00b")` → `ClipboardContentError` before PRIMARY is
   replaced; the earlier selection is still readable.

<a id="primary-selection-polish"></a>

### Correct PRIMARY wording and probe evidence left by the primary-selection execution

**Identity:** SEED-001#primary-selection-polish
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/020-primary-selection-polish/PLAN.md"}
```

**Goal:** Python users calling `copy_primary` / `paste_primary` get error
messages that always name the primary selection (never "clipboard"), and
maintainers get native PRIMARY evidence whose step names, run ids and test
documentation match the story examples, correcting residue from the
SEED-001#primary-selection execution.

**Scope:** `copy_primary` input-rejection wording; the X11-without-xclip
message in a session that also sets `WAYLAND_DISPLAY`; the Wayland PRIMARY
probe step names; the Wayland PRIMARY README Evidence run id; the
disabled-Sway wording in PRIMARY test documentation; the duplicated
evidence-limit reason chains in the PRIMARY probes. No behavior other than
error text changes. Plan:
[020-primary-selection-polish](../slice-plans/020-primary-selection-polish/PLAN.md).

<a id="bounded-helper-owner-write"></a>

### Bound every helper-owner clipboard write behind one launcher

**Identity:** SEED-001#bounded-helper-owner-write
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/019-bounded-helper-owner-write/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"c8426762bfc0a46ae83bdf00966d0b20a518d6321fc9faf4198d01e7b7075e7b","plan":"9354dc3daa75f7e5a66dd4bf49d3b20fc2bf6041702a9ec8e91c3cd31b804d7d"}}
```

**Goal:** Python users calling `copy_image` on a Linux desktop whose display
or compositor stalls get a `ClipboardImageError` within one documented bound
instead of a hang or a false success, as `copy` and `copy_files` already
do. Maintainers keep one rule for handing a background clipboard owner its
payload, so the next writer cannot reintroduce the pipe write that hung
large text on X11. This finishes the reliability promise of the image and
rich-content writes without changing what any write offers.

**Scope:**

- *Required behavior: bounded image write on Linux.* On Linux X11 and
  Linux Wayland, each `copy_image` shares one 10 s bound across starting
  its helper, handing over the PNG, and confirming the offer, the bound
  `copy` and `copy_files` already use (today the Wayland path waits up to
  30 s and the X11 path has no bound on the hand-over). When the bound
  passes it raises `ClipboardImageError` naming the helper and the bound,
  with the helper's stderr when it wrote any, and stops the owner it
  started (its whole session) so no half-started owner lingers. The README
  documents the bound beside the text bound.
- *Required behavior: an X11 image write succeeds only when its own owner
  serves it.* `copy_image` on X11 returns only once CLIPBOARD's `image/png`
  reads back exactly the written PNG bytes, as the text and file-list
  writers already confirm their own bytes. Reason: the current check only
  waits for `image/png` in TARGETS, which a previous image owner already
  lists, so with the hand-over bounded a non-reading owner would otherwise
  turn a hang into a silent success (the library rule is no silent success
  on write).
- *Required behavior: one launcher.* Every Linux helper-owner clipboard
  write that hands over a payload (X11 `xclip -i` for text, file list and
  image; Wayland `wl-copy` for text, file list and image) starts its helper
  through one private launcher beside the shared Linux helpers
  (`clipboard/_desktop`): the payload comes from an unlinked temporary file
  as `stdin` (never a pipe the caller must drain), the helper runs in its
  own session with `stdout` discarded and `stderr` in the caller's unlinked
  log. Each caller keeps its own deadline, readiness check and error mapping
  (`ClipboardContentError` for text and file lists, `ClipboardImageError`
  for images, with the same install hints). The Wayland image write gains
  the detached session and stderr detail the other Wayland writes already
  have.
- *Required behavior: failures before replacing.* A missing helper, or a
  temporary file that cannot be written (for example a full temporary
  directory), raises the caller's error before any helper starts, so the
  current clipboard stays as it was.
- *Preserved.* Session selection, offered formats and types, the
  writer-exit lifetime, public API, injection seams, and the existing text
  and file-list bounds and messages' meaning stay as they are; the existing
  X11 text and file-list stall tests keep passing through the launcher.
- *Proof.* Desktop-free tests drive a real `sys.executable` owner that
  never reads its input (the stalled-display stand-in the text and
  file-list stall tests use) with a PNG above a typical 64 KiB pipe buffer:
  X11 `copy_image` raises `ClipboardImageError` within the bound (shortened for the test)
  and stops the owner's session; with a previous owner still listing
  `image/png`, it still raises rather than returning; a Wayland `wl-copy`
  stand-in that never finishes raises within the bound with its stderr.
  Every Linux writer's launch goes through the one launcher (checked by the
  launcher's own tests plus the existing writer suites). The existing gated
  Xvfb + `xclip` and Sway + wl-clipboard `copy_image`, text and
  `copy_files` probes (`CLIPBOARD_NATIVE_PROBE`) keep passing, including
  writer-exit pasteability. A truly stalled X server or compositor is an
  evidence limit: proved by the stand-in only, as for text.
- *Scope limits (deferred, not rejected).* macOS `osascript` and Windows
  image writes (already bounded, no background owner fed by Python);
  payload-free helper runs (`wl-copy --clear`, the X11 clear child);
  readers; a Wayland read-back confirmation for text or image writes (they
  keep confirming by `wl-copy`'s foreground exit); a configurable bound;
  Linux `copy_html` (no native writer exists).

**Key examples:**

1. Linux X11 whose `xclip` never reads its input (stalled display) →
   `copy_image` of a 480 KB PNG → `ClipboardImageError` naming `xclip` and
   the 10 s bound about 10 s later; no owner from this call is left running.
   (Observed 2026-11-04 with a non-reading fake `xclip`: today the call is
   still blocked after 12 s, with no bound.)
2. Linux X11, CLIPBOARD already holds an earlier `copy_image` (it lists
   `image/png`), and the new `xclip` never takes ownership → `copy_image`
   raises `ClipboardImageError` within the bound rather than returning as if
   the new image were offered.
3. Linux X11 working normally → `copy_image(img)` returns once
   `xclip -o -selection clipboard -t image/png` gives exactly the written
   PNG; after the Python process exits the image still pastes.
4. Linux Wayland whose `wl-copy` never finishes → `copy_image` raises
   `ClipboardImageError` within 10 s (today 30 s), quoting what `wl-copy`
   wrote to stderr.
5. Linux X11, 200 000 characters of text or a file list above 64 KiB with
   a non-reading owner → `copy` / `copy_files` raise `ClipboardContentError`
   within their bound as today, now launched through the shared launcher.
6. Linux X11 with no `xclip` on PATH → `copy_image` raises
   `ClipboardImageError` and `copy_files` raises `ClipboardContentError`,
   each with its install hint; the clipboard is unchanged.

**Architecture:** No ADR store exists in this repository, so no Accepted
decision applies. The binding convention is AGENTS.md: shared Linux helper
mechanics live in private `clipboard/_desktop` with per-caller failure
modes, and content-kind modules must not copy them. The launcher therefore
owns only process start and payload hand-over (temporary-file `stdin`,
detached session, discarded `stdout`, caller's `stderr` log) and raises
launch failures as `OSError` for each caller to map; deadlines, readiness
checks, owner stop, and messages stay with the callers. Considered and not
chosen: copying the temp-file pattern into the image writer only (a third
duplicate the story exists to remove); passing the payload as an `xclip`
file argument (`wl-copy` takes none, and the named file would have to
outlive the call until a stalled owner reads it); bounding the pipe write
with a writer thread (more moving parts, and the pipe still ties Python to
a reader that may never come).

- **Effort hypothesis:** **M**, medium confidence (six call sites and one
  readiness change, all with existing desktop-free suites and native
  probes).
- **Depends on:** None.
- **Safe stopping point:** The launcher with the X11 image write bounded and
  confirmed is useful by itself; moving the remaining writers onto it can
  follow.

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

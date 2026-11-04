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

<a id="macos-native-wait-evidence"></a>

### Verify the clipboard waits natively on macOS Aqua

**Identity:** SEED-001#macos-native-wait-evidence
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planless"}
```

**Goal:** Automation developers on macOS can rely on `wait_for_kind` and
`wait_for_text_change` with the same stated evidence the Linux X11, Linux
Wayland and Windows desktops already have. Today the README marks the macOS
wait Evidence entry "not yet verified": the gated probe was written with
SEED-001#wait-for-content, but every run so far stopped at its evidence
limit because the screen was locked.

**Scope:**

- *Required behavior.* On the developer's Mac with an unlocked Aqua console
  session, run the existing gated probe
  (`CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked pytest
  tests/test_wait_native_macos.py -q -rP`, probe
  `scripts/probe_macos_native_wait.py`). Its four steps use an independent
  `pbcopy` producer: `wait_for_kind("text")` from a cleared pasteboard
  returns a snapshot listing `"text"` after the copy; `wait_for_kind("html",
  timeout=1)` with nothing copied returns `None` at its timeout;
  `wait_for_text_change` returns the second independently copied text; and
  clear-then-identical-recopy leaves it returning `None`.
- *Documentation.* Replace the README macOS wait Evidence entry's "not yet
  verified" with the observed result (macOS version and build, per-step
  outcome and timing) or, if a step fails, the observed limitation; a failing
  step is a defect to fix in the wait or the probe before claiming
  verification.
- *Scope limits.* No change to the wait API or other desktops' evidence.
  The probe is developer-run (it needs the developer's unlocked session); it
  does not become a CI job.

**Key examples:**

1. Unlocked macOS Aqua session → the gated probe → exit 0, four steps ok,
   README macOS wait Evidence entry records the observed version and timings.
2. Locked screen → the probe exits 2 with `evidence_limit` → no README claim
   changes.

<a id="split-native-wait-support"></a>

### Split the native wait probe support along its harness and steps

**Identity:** SEED-001#split-native-wait-support
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/019-split-native-wait-support/PLAN.md"}
```

**Goal:** Maintainers of the native wait probes can change the child wait
harness or one probe step without reading a 384-line module that mixes both,
bringing `scripts/native_wait_support.py` back under the project's 250-line
file limit that every other native support module meets. Retrospective
correction of SEED-001#wait-for-content.

**Scope:**

- Split `scripts/native_wait_support.py` along its cohesive seam (the child
  wait harness and timing rules versus the four shared probe steps and their
  runner) so each module is at most 250 lines; update the four
  `scripts/probe_*_native_wait.py` imports.
- No change to probe step names, pass conditions, report fields, gates,
  floors, CI jobs or the wait API.
- *Plan:* [019-split-native-wait-support](../slice-plans/019-split-native-wait-support/PLAN.md).

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

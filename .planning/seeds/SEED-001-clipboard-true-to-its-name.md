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

<a id="bounded-x11-text-write"></a>

### Bound the X11 text write for large text on a stalled display

**Identity:** SEED-001#bounded-x11-text-write

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

<a id="clear-clipboard"></a>

### Clear every representation from the current clipboard

**Identity:** SEED-001#clear-clipboard
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python users can deliberately remove the current copied
  content, including images and rich representations, without guessing whether
  copying an empty string cleared the offer.
- **Evaluation:** After another application offers both HTML and text or an
  image, a clear operation leaves no old representation readable from the
  current clipboard. Repeating it on an already empty clipboard succeeds.
- **Value / learning:** Supplies an ordinary clipboard action whose meaning
  remains useful as content types expand.
- **Boundary:** Clear the current target only. Report unavailable/denied
  clearing separately from success. No promise to erase OS history, a manager's
  cache, a remote device, or a newer copy another application makes afterward.
- **Effort hypothesis:** **S**, medium confidence; assumes native clear/release
  operations are available. Reassess if ownership proof reveals more breadth.
- **Depends on:** None. External producers provide the data to clear.
- **Safe stopping point:** Current clipboard clearing works without a history
  service and never claims secure deletion beyond the current offer.

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

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


<a id="desktop-helpers"></a>

### Keep native HTML-read proof strict and desktop helper knowledge single-homed

**Identity:** SEED-001#desktop-helpers
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/006-desktop-helpers/PLAN.md"}
```

**Goal:** Python developers relying on the README's verified desktop claims
keep a CI signal that fails when a verified native HTML-read probe stops
proving anything, and maintainers of the remaining SEED-001 stories reuse one
home for desktop session detection and helper handling instead of copying it
per content kind (correction of SEED-001#read-html; story recoverable at
`9d3ceda:.planning/seeds/SEED-001-clipboard-true-to-its-name.md#read-html`).

**Scope:** Make the gated Windows `paste_html` probe fail rather than skip when
it cannot verify; move Linux session detection, helper-failure detail
formatting, and the xclip `TARGETS` listing out of the image/HTML content-kind
modules into one private desktop module with each caller's current semantics;
leave `_html_native.py` as dispatch only; fold duplicated seam and structural
`paste_html` tests into the behavioral contract. Public API, results, error
messages, and install hints stay unchanged. Plan:
[006-desktop-helpers](../slice-plans/006-desktop-helpers/PLAN.md).

<a id="read-files"></a>

### Read file references copied by file managers

**Identity:** SEED-001#read-files
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/007-read-files/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"19533af6bdae4591160a23bd2d1b30b430d77c0f388076b74fa62c403755a527","plan":"7c3faccd4ece9b575a4b37088fcca2b0db8df7a431e1f71bb3f3e9e09b60dfa7"}}
```

**Goal:** Python desktop tools and automation developers can recover an
**ordered list of local file references** from an independent file manager's
clipboard offer through `clipboard`, instead of asking users to transcribe
paths or parsing plain text that happens to look like paths: when a native
file-list representation offers local files, the call returns those local
paths in offer order; when no local file-list is offered, the call reports
ordinary files absence; corrupt native file-list metadata or transfer/access
failure reports an actionable error — and the read never opens, copies, moves,
or deletes those files, never mutates the clipboard, and never treats a
cut/move marker as authority to move or as a move offer to reissue.

**Scope:**

- **Required behavior:** Add an explicit public read API (proposed spelling
  `paste_files()`) that returns an ordered `list[str]` of **local filesystem
  paths** when the current clipboard offer includes a native file-list
  representation that yields at least one local reference, or ordinary
  absence (`None`) when no local file-list is offered (including empty
  clipboard, text-only, image-only, HTML-only, and file-list payloads that
  contain only non-local / remote URIs). Failures other than ordinary absence
  (denied/unavailable access, missing Linux helper required to read the
  file-list target, transfer failure, malformed native file-list metadata that
  cannot yield trustworthy local references) raise `ClipboardContentError`
  rather than returning `None` or fabricated paths. The read leaves the
  clipboard unchanged and performs **no** filesystem open, copy, move, delete,
  or existence check on the referenced paths. Normalize platform payloads to
  local path strings (decode `file://` URIs including percent-encoding and
  Unicode / spaces; read Windows `CF_HDROP` path lists; read macOS file-URL /
  filename pasteboard types). Preserve offer order. If a cut/move marker is
  present beside the references (`PreferredDropEffect`,
  `x-special/gnome-copied-files` “cut”, `application/x-kde-cutselection`, or
  equivalent), **ignore it for all library behavior**: still return the local
  path list when references are offered, do not move or delete anything, and
  do not write or reissue cut/move semantics. Never interpret ordinary
  `paste()` plain text (or newline-separated path-looking text) as a file-list
  success. Default automated tests stay desktop-free via an injectable read
  backend; native proof uses an **independent file manager** (not a
  same-library `copy_files` round-trip alone) and stays explicitly gated.
  Document Linux helper dependencies for file-list reads (`xclip` /
  `wl-paste` requesting `text/uri-list` or equivalent) and supported desktop
  setup. No `clipboard[images]` requirement for this story.
- **Supported desktops (this story):** Windows desktop with Explorer (or
  equivalent) producing `CF_HDROP`; macOS Aqua with Finder (or equivalent)
  producing file-URL / filename pasteboard types; Linux X11 + helper able to
  request `text/uri-list` on CLIPBOARD from a named file manager; Linux
  Wayland + helper able to request `text/uri-list` (or equivalent) from a
  named file manager, scoped to the compositor actually proved when one is
  available. WSL, SSH, containers, and headless CI are not additional
  guaranteed desktops. Independent-producer success is an acceptance
  requirement on each claimed desktop when a session is available; when no
  usable session exists during execution, record an explicit
  unverified/unsupported evidence limit for that desktop rather than claiming
  verified — never silent success. Do not generalize one Wayland compositor's
  or one Linux file manager's result to all environments.
- **Required restrictions:** Do not overload `paste()` / `copy()` to return or
  accept file lists. Do not treat ordinary text, HTML, or image-only offers as
  file-list success. Do not bypass OS pasteboard / clipboard authorization.
  Do not replace, clear, or rewrite clipboard contents as part of the read.
  Do not open, hash, copy, move, or delete referenced files as part of the
  read. Do not promise that returned paths still exist or are readable. Do not
  fetch remote / non-`file` URIs. Do not hang the caller indefinitely waiting
  on a contended clipboard. Do not silently reissue a cut/move marker as a
  move offer.
- **Scope limits / deferred:** Public exposure of cut vs copy intent /
  PreferredDropEffect / GNOME–KDE cut verbs as structured return metadata
  (parse/ignore markers only as needed for the non-move safety rule);
  returning `pathlib.Path` objects or richer reference types; remote /
  non-local URI references; virtual or promised files; directory-expansion
  semantics beyond what the native offer already lists; outbound file-list
  write (`SEED-001#copy-files`); format inspection (`SEED-001#inspect-formats`);
  bundling GUI toolkits or `win32clipboard` as a required public dependency;
  making default pytest / CI require a real desktop; expanding beyond the
  four-desktop set; same-library `copy_files` round-trip as sole native proof.
- **Rejection constraints:** Corrupt or unparseable native file-list metadata
  must not yield fabricated successful paths (independent need: Shared
  Boundaries malformed-data honesty). Plain text that resembles paths must not
  be treated as a file-list success. A successful read must not mutate the
  clipboard or perform filesystem side effects on the referenced paths. A cut
  marker must not cause library-side move/delete or be reissued as move.
  Silent success on an unproved desktop is forbidden.

**Key examples:**

1. Independent file manager (Explorer / Finder / named Linux FM) copies two
   existing local files, including a Unicode name and spaces → `paste_files()`
   returns an ordered `list[str]` of the corresponding local paths; a later
   independent consumer can still obtain the same offer; no file was opened or
   modified by the read.
2. Same pattern where the native offer is Linux `text/uri-list` of `file://`
   URIs (percent-encoded spaces / Unicode) or Windows `CF_HDROP` → returned
   strings are decoded local filesystem paths, not raw URI text and not
   `paste()` plain text alone.
3. Clipboard holds only plain text that looks like paths (or is empty /
   image-only / HTML-only) → `paste_files()` returns `None` (ordinary files
   absence); `paste()` / other readers behave as before for their kinds.
4. Offer includes a cut/move marker beside local file references →
   `paste_files()` still returns the local path list; the library does not
   move, delete, or rewrite the offer as a cut/move.
5. Native file-list metadata is present but corrupt or inconsistent →
   `ClipboardContentError`; no fabricated paths; clipboard contents remain
   unchanged.
6. Missing Linux file-list helper or denied/unavailable clipboard access →
   `ClipboardContentError` with an actionable message; not silent `None`
   success.
7. Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available →
   independent file-manager success with floors recorded for the named
   compositor/helper/file manager; if a session is unavailable during
   execution, that desktop keeps an explicit evidence limit instead of a
   verified claim.
8. After this work, in-memory `copy` / `paste` / `paste_image` / `copy_html` /
   (when present) `paste_html` / `inspect` contract tests still pass; `VERSION`
   and text-only callers behave as before; `paste_files` does not require
   `clipboard[images]`.

**Direction (explored):** Compare credible ways to reach the goal against
Shared Boundaries, North Star, and delivered image / HTML shapes.

1. **Explicit `paste_files()` → `list[str] | None` with `ClipboardContentError`
   on failure (recommended).** Mirror delivered `paste_image` /
   planned `paste_html` absence/value/failure: thin public contract,
   injectable reader for CI, platform readers that decode native file-list
   offers to ordered local path strings, document helpers rather than bundling
   them. Ignore cut/move markers for library behavior. No Pillow /
   `clipboard[images]` requirement unless evidence forces a shared stack.
2. **Docs-only recipes (`wl-paste -t text/uri-list`, `xclip -t text/uri-list`,
   Windows `CF_HDROP` / `DragQueryFile`, macOS pasteboard file URLs).**
   Strongest smaller / existing-tool path; leaves each consumer owning
   URI decoding, plain-text vs file-list distinction, cut-marker safety, and
   absence vs error — insufficient for the cohesive library promise.
3. **Structured public return (`paths`, optional `operation: copy|cut`).**
   Useful later for honest cut-aware UIs, but expands the minimal
   reference-ingest outcome; defer public cut/copy metadata and keep
   marker handling internal (ignore for side effects).
4. **Reuse Pillow `ImageGrab.grabclipboard()` filename-list branch on Windows
   plus ad-hoc helpers elsewhere.** May accelerate Windows reads, but couples
   file reading to the images extra and still needs a uniform
   absence/failure model and macOS/Linux readers — acceptable as an internal
   Windows tactic only if it does not force `clipboard[images]` on this story;
   not the default public stack.
5. **Parse `paste()` plain text / newline path lists.** Meets a narrow “get
   paths” wording but violates the story’s plain-text boundary and Shared
   Boundaries content-kind honesty — rejected.

Borrowed mechanism: **URI / bookmark references without retrieving the
resource body** (as with `Content-Location` or a link list). Roles map as:
native file-list offer → reference list; `file://` / `CF_HDROP` / pasteboard
filenames → local reference identifiers; HTTP GET / open of the body →
filesystem open of the file (forbidden here); cache that returns locations
without downloading → non-mutating clipboard read of references only;
`Content-Disposition` / method override that would delete the origin →
cut/move markers that must not become library-side moves. Adapt by making the
public success meaning an ordered local path list decoded from native
file-list formats, with no open/existence check and with cut markers ignored
for side effects. Limit of the analogy: unlike HTTP, clipboard references have
no validators — a successful read does not promise the paths still exist, and
platforms disagree on cut markers and URI encoding; document per-desktop
floors rather than inventing freshness or move semantics.

Challenge: the purpose is **accepting a user’s copied local files as
structured references** with honest absence/failure and zero filesystem side
effects — not a path-from-text parser, not a cut/move agent, and not a remote
URI fetcher. Meeting the wording by scanning `paste()` text, opening paths to
“verify” them, or reissuing cut as move misses that purpose. Strongest
consequential doubt: “local file reference” spans divergent native shapes
(Windows `CF_HDROP`, macOS file URLs / filename arrays, Linux `text/uri-list`
plus optional GNOME/KDE cut companions), so interoperability floors and
evidence limits are required — accepted as an execution risk bounded by early
native probes and documented decoding rules, not a rewrite of the
local-reference-read goal. Deferring public cut/copy metadata does not shrink
the purpose: callers still get ordered local paths, and the library still
refuses move side effects.

**Architecture:** ADR store is undefined in this repository; no Accepted ADR
constrains this story (architecture check: store missing — no Accepted-ADR
citation completed). North Star
[Rich clipboard content beside text re-exports](../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)
already directs explicit APIs beside `copy`/`paste`, thin normalization, and
in-memory vs native proof — follow it for file-list read. Consequential system
effects: (1) add a rich-read responsibility for **file references** beside
delivered `paste_image` / `copy_html` (and planned `paste_html` / `inspect`)
without overloading text entry points; (2) platform readers must own native
file-list decoding (Windows `CF_HDROP`; macOS file-URL / filename types;
Linux `text/uri-list`) and map them to one absence / path-list /
`ClipboardContentError` model — qualities pyperclip `paste` does not provide;
(3) non-mutation of the clipboard, refusal to parse plain text as files, and
refusal to honor cut markers as moves are part of the public contract;
(4) reuse `ClipboardContentError` for file-list read failures — do not
overload `ClipboardImageError`; (5) do not require the `clipboard[images]`
extra for this story even if an internal Windows tactic reuses a
filename-list helper. No new North Star topic is required unless execution
evidence overturns the explicit path-list API shape.

- **Effort hypothesis:** **M**, medium-low confidence; assumes a bounded set of
  native file-manager conventions rather than every desktop's custom format.
- **Depends on:** None. The source is an independent file manager.
- **Safe stopping point:** Users can select inputs by copying files; merely
  reading the clipboard never opens, copies, moves, or deletes those files.

<a id="copy-files"></a>

### Copy local file references into file managers

**Identity:** SEED-001#copy-files
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python tools can hand existing output files to a file manager
  through its normal copy/paste workflow.
- **Evaluation:** Python offers two existing local file references with Unicode
  and spaces; a supported independent file manager recognizes a copy offer and
  can paste copies to a user-selected destination after the Python writer exits.
- **Value / learning:** Eliminates manual path handling and tests outbound
  file-list interoperability independently of image content.
- **Boundary:** Copy semantics for existing local files. No cut/move, deletion,
  virtual/promised files, remote transfers, or automatic filesystem paste by
  the library. Invalid input fails before current content is replaced. Spell
  out behavior if a source is later removed.
- **Effort hypothesis:** **L**, low confidence; native file-list conventions
  and file-manager interpretation differ across platforms.
- **Depends on:** None. File-manager behavior, not the library's file reader,
  establishes success.
- **Safe stopping point:** Files can be exported through familiar desktop
  interaction; the library itself does not modify them or issue move semantics.

<a id="portable-text"></a>

### Use the text clipboard reliably and diagnose unavailable access

**Identity:** SEED-001#portable-text
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Existing Python users can trust the simple text API and
  recover from desktop/session problems without guessing at empty results.
- **Evaluation:** Existing `copy(text)`/`paste()` calls exchange Unicode,
  emoji, multiline strings, leading/trailing whitespace, and empty text with
  an independent app on supported desktops. Missing tools, denied access,
  stale display connections, and persistent contention yield bounded,
  actionable failure rather than false success or an indefinite hang.
- **Value / learning:** Establishes the smallest dependable baseline behind
  the package name while preserving users of the original interface.
- **Boundary:** Specify Python text/newline behavior and native conversion
  limits. Embedded NUL and unsupported input must not silently truncate or
  erase current data. Preserve working WSL text access; do not extend the new
  rich-content promise to WSL, SSH, containers, or arbitrary remote desktops.
  No fake in-memory fallback presented as the system clipboard.
- **Effort hypothesis:** **M**, medium confidence; assumes upstream text
  behavior can be reused, with targeted corrections where native evidence
  contradicts the contract. Earlier stories still own their own failures.
- **Depends on:** None. This is not permission for previous stories to defer
  compatibility, failures, or installation information here.
- **Safe stopping point:** Existing callers retain a documented working text
  workflow and useful failure recovery even if optional later stories stop.

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

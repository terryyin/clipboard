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


<a id="read-html"></a>

### Read HTML fragments copied by desktop applications

**Identity:** SEED-001#read-html
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/005-read-html/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"a961d0e82c6382c70eefaff3b758472644803173e04576677a5962a7c9052355","plan":"f685ddd8248a73814e24d402b889103fb72a6c3e8ef9e550a93b1239452c8db3"}}
```

**Goal:** Python document and automation developers can recover the Unicode
HTML **fragment** of a selection copied by an independent browser or rich
editor through `clipboard`, instead of receiving only plain text: when HTML is
offered, the returned markup matches the selected fragment (native
fragment/context envelopes decoded correctly); when only text or no HTML is
offered, the call reports ordinary HTML absence; corrupt native HTML metadata
or transfer/access failure reports an actionable error — and the read never
changes what remains available for another consumer.

**Scope:**

- **Required behavior:** Add an explicit public read API (proposed spelling
  `paste_html()`) that returns a Unicode HTML fragment string when the current
  clipboard offer includes an HTML representation, or ordinary absence
  (`None`) when no HTML is offered (including text-only and empty clipboard).
  Failures other than ordinary absence (denied/unavailable access, missing
  Linux helper, transfer failure, malformed native HTML envelope/metadata that
  cannot yield a trustworthy fragment) raise `ClipboardContentError` rather
  than returning `None` or a fabricated fragment. The read leaves the clipboard
  unchanged. Extract the **fragment** from platform envelopes that wrap
  selection plus context (notably Windows `HTML Format` UTF-8 byte offsets);
  do not return the raw envelope headers as if they were the fragment. Never
  execute markup, fetch linked resources, open local paths found in markup, or
  synthesize HTML from plain text / RTF. Default automated tests stay
  desktop-free via an injectable read backend; native proof uses an
  **independent producer** (browser or rich editor — not a same-library
  `copy_html` round-trip alone) and stays explicitly gated. Document Linux
  helper dependencies for HTML reads (`xclip` on X11; `wl-paste` on Wayland)
  and supported desktop setup. No `clipboard[images]` requirement for this
  story.
- **Supported desktops (this story):** Windows desktop; macOS Aqua; Linux X11
  + `xclip` (or equivalent) able to request `text/html` on CLIPBOARD; Linux
  Wayland + `wl-paste` (or equivalent) scoped to the compositor actually
  proved when one is available. WSL, SSH, containers, and headless CI are not
  additional guaranteed desktops. Independent-producer success is an
  acceptance requirement on each claimed desktop when a session is available;
  when no usable session exists during execution, record an explicit
  unverified/unsupported evidence limit for that desktop rather than claiming
  verified — never silent success. Do not generalize one Wayland compositor's
  result to all Wayland environments.
- **Required restrictions:** Do not overload `paste()` / `copy()` to return or
  accept HTML. Do not treat ordinary text, file-list, or image-only offers as
  HTML success. Do not bypass OS pasteboard / clipboard authorization. Do not
  replace, clear, or rewrite clipboard contents as part of the read. Do not
  present envelope headers, full surrounding context HTML, or a synthesized
  document as the fragment result. Do not hang the caller indefinitely waiting
  on a contended clipboard.
- **Scope limits / deferred:** Public exposure of surrounding context HTML,
  source URL, or other producer metadata as a structured return type (parse
  envelopes internally as needed for correct fragment extraction only);
  RTF / attributed-string conversion; full-document import as a distinct
  contract; arbitrary MIME / typed-binary read; format inspection
  (`SEED-001#inspect-formats`); bundling GUI toolkits or `win32clipboard` as a
  required public dependency; making default pytest / CI require a real
  desktop; expanding beyond the four-desktop set; same-library `copy_html`
  round-trip as sole native proof.
- **Rejection constraints:** Corrupt or unparseable native HTML metadata must
  not yield a bogus successful fragment (independent need: Shared Boundaries
  malformed-data honesty). Text-only content must not be turned into HTML by
  synthesis. A successful read must not mutate the clipboard offer. Silent
  success on an unproved desktop is forbidden.

**Key examples:**

1. Independent browser or rich editor copies a Unicode HTML selection (styled
   link or small table) on a supported desktop → `paste_html()` returns the
   fragment markup for that selection (not only `paste()` plain text); a later
   independent consumer can still obtain the same offer.
2. Same pattern where the native offer uses Windows `HTML Format` with
   fragment/context byte offsets (including non-ASCII) → returned string is the
   fragment between the offsets, not the Version/StartHTML header block or the
   unselected surrounding context alone.
3. Clipboard holds only plain text (or is empty / image-only / file-list) →
   `paste_html()` returns `None` (ordinary HTML absence); `paste()` / other
   readers behave as before for their kinds.
4. Native HTML metadata is present but corrupt or inconsistent (e.g. invalid
   Windows fragment offsets) → `ClipboardContentError`; no fabricated fragment;
   clipboard contents remain unchanged.
5. Missing Linux HTML helper or denied/unavailable clipboard access →
   `ClipboardContentError` with an actionable message; not silent `None`
   success.
6. Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available →
   independent-producer success with floors recorded for the named
   compositor/helper; if a session is unavailable during execution, that
   desktop keeps an explicit evidence limit instead of a verified claim.
7. After this work, in-memory `copy` / `paste` / `paste_image` / `copy_html`
   contract tests still pass; `VERSION` and text-only callers behave as before;
   `paste_html` does not require `clipboard[images]`.

**Direction (explored):** Compare credible ways to reach the goal against
Shared Boundaries, North Star, and delivered HTML write / image read shapes.

1. **Explicit `paste_html()` → `str | None` with `ClipboardContentError` on
   failure (recommended).** Mirror delivered `paste_image` absence/value/failure
   and `copy_html`'s content-error type: thin public contract, injectable
   reader for CI, platform readers that decode interoperable HTML envelopes to
   a fragment string, document helpers rather than bundling them. No Pillow /
   `clipboard[images]` requirement unless evidence forces a shared stack.
2. **Docs-only recipes (`wl-paste -t text/html`, `xclip -t text/html`, Windows
   CF_HTML snippets).** Strongest smaller / existing-tool path; leaves each
   consumer owning fragment-vs-context extraction, absence vs error, and
   platform differences — insufficient for the cohesive library promise.
3. **Structured public return (`fragment`, optional `context`, `source_url`).**
   Useful later and matches research's "document whether context is exposed,"
   but expands the minimal fragment-ingest outcome; defer public metadata and
   keep envelope parsing internal.
4. **Depend on Qt `QMimeData` / PyClip / a GUI toolkit for HTML MIME.** May
   move bytes sooner, but adds heavy or divergent dependencies and still needs
   independent-producer proof and this project's absence/failure model —
   deferred as default stack.
5. **Return raw platform HTML bytes/string without fragment extraction.** Meets
   a narrow "read HTML" wording but misses fragment/context boundary handling
   (especially Windows) — rejected for this story's goal.

Borrowed mechanism: **HTTP Content-Range / byte-range extraction** over a
larger resource. Roles map as: full resource → native HTML envelope or
document-with-context; `Content-Range` / range markers → Windows
`StartFragment`/`EndFragment` (and analogous selection bounds); ranged body →
the fragment string callers need; cache/proxy that serves the range without
mutating the origin → a non-mutating clipboard read. Adapt by making correct
range extraction part of the public success meaning on envelopes that use it,
while platforms that already offer fragment-only `text/html` return that body
directly. Limit of the analogy: unlike HTTP, some producers omit reliable
range markers or ship fragment-only HTML; inventing a mandatory Windows-style
envelope on macOS/Linux would create false failures — document per-desktop
envelope behavior and fail only when present metadata is unusable.

Challenge: the purpose is **selected-fragment markup** with honest
absence/failure — not an HTML-named function that returns any HTML-ish payload.
Meeting the wording with raw CF_HTML headers, full context HTML, plain-text
synthesis, or same-library round-trips alone misses that purpose. Strongest
consequential doubt: independent producers disagree on whether `text/html` /
pasteboard HTML is fragment-only or document-with-selection, so "correct
fragment" may need per-desktop floors and evidence limits — accepted as an
execution risk bounded by early native probes and documented extraction rules,
not a rewrite of the fragment-read goal during refinement. Deferring public
context/source fields does not shrink the purpose: callers still get the
fragment the selection intended.

**Architecture:** ADR store is undefined in this repository; no Accepted ADR
constrains this story (architecture check: store missing — no Accepted-ADR
citation completed). North Star
[Rich clipboard content beside text re-exports](../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)
already directs explicit APIs beside `copy`/`paste`, thin normalization, and
in-memory vs native proof — follow it for HTML read. Consequential system
effects: (1) add a rich-read responsibility beside delivered `copy_html` /
`paste_image` without overloading text entry points; (2) platform readers must
own native HTML envelope decoding (Windows fragment offsets; macOS HTML
pasteboard type; Linux `text/html` MIME) and map them to one
absence / fragment / `ClipboardContentError` model — qualities pyperclip
`paste` does not provide; (3) non-mutation of the clipboard and refusal to
synthesize HTML from text are part of the public contract; (4) reuse
`ClipboardContentError` for HTML read failures — do not overload
`ClipboardImageError`. No new North Star topic is required unless execution
evidence overturns the explicit fragment-string API shape. HTML read does not
require the `clipboard[images]` extra.

- **Effort hypothesis:** **M**, medium-low confidence; assumes bounded native
  fragment parsing and a small agreed set of external producers across the
  four-desktop set.
- **Depends on:** None. HTML comes from another application; delivered
  `copy_html` is not a scheduling prerequisite (reuse for regression / local
  fakes only). Independent producers prove this story.
- **Safe stopping point:** Developers can ingest rich selections even without
  later file or inspection features; malformed metadata cannot cause a bogus
  successful fragment or a clipboard write; text and image callers remain
  compatible.

<a id="read-files"></a>

### Read file references copied by file managers

**Identity:** SEED-001#read-files
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python desktop tools can accept a user's copied local files
  as structured references rather than ask them to transcribe paths.
- **Evaluation:** A file manager copies two local files, including a Unicode
  name and spaces; Python retrieves the corresponding file references in
  order. Plain text that resembles paths is not interpreted as file content.
- **Value / learning:** Adds a common non-text clipboard workflow and reveals
  Windows, macOS, and Linux file-list conventions.
- **Boundary:** Existing local file references, with representation and
  supported file managers named in refinement. A cut marker, if present, must
  not trigger moving/deleting anything or be silently reissued as a move.
  No file reading, existence guarantee, remote URI fetching, or promised files.
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

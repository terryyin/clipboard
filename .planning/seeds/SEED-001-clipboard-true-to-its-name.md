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

<a id="read-images"></a>

### Read images copied by desktop applications

**Identity:** SEED-001#read-images
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/001-read-images/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"414c9b90f9c00a00eab8c4f7852624359254d75ec8947813b00add9af722e63c","plan":"8d9b2e591d60a88b8b4ddd4a18317c202a9c19a20f79ad18767c8d5f1aac2152"}}
```

**Plan:** [slice-plans/001-read-images/PLAN.md](../slice-plans/001-read-images/PLAN.md)

**Goal:** Python automation developers can retrieve a static raster image
copied by an ordinary desktop application through one explicit `clipboard`
operation, without writing platform-specific clipboard code, while
`copy` / `paste` / `VERSION` and existing text callers stay unchanged.

**Scope:**

- **Required behavior:** An explicit image-read operation returns a Pillow
  `Image.Image` with usable raster pixels (dimensions, colors, and alpha
  when the native offer carries it) for one static image placed on the
  clipboard by an independent producer. The optional `clipboard[images]`
  extra installs Pillow; Linux install docs name `xclip` (X11) or
  `wl-paste` (Wayland). Native encodings (PNG, DIB/DIBV5, macOS image
  types, Linux image MIME) convert behind that contract. The read leaves
  clipboard contents unchanged. Text-only or empty clipboard is ordinary
  absence (`None`). A file-reference / filename-list offer alone is absence
  of image (not opened or decoded from disk). Malformed image bytes are a
  distinguishable failure. Access denied, unavailable desktop, missing
  required helper, contention, or transfer failure are distinguishable from
  absence and must not collapse to an empty success.
- **Supported desktops:** Windows desktop; macOS pasteboard sessions that
  grant access; Linux X11 with `xclip`; Linux Wayland with `wl-paste` where
  the compositor exposes clipboard data. Exact helper/OS floors are
  evidence-backed during planning and proof. WSL, SSH, containers, and
  headless CI are not additional guaranteed desktops. Wayland support is
  not inferred from one compositor.
- **Required restrictions:** Do not change `paste()` to return images.
  Do not bypass OS pasteboard authorization. Do not treat URL-only or
  file-reference offers as images.
- **Scope limits / deferred:** Animation, screenshot capture, image
  writing, automatic URL fetch, opening file-manager references, RTF,
  arbitrary typed bytes, history, cloud sync, PNG-bytes-only APIs, and
  library-owned non-Pillow buffers. Narrowing first delivery to a subset
  of the supported desktops is out of scope for this story.
- **Rejection constraints:** File-reference-only → no image (independent
  need: do not perform filesystem reads from clipboard offers). Access /
  helper / malformed failures → not absence (independent need: actionable
  diagnosis per Shared Boundaries).

**Key examples:**

1. Independent screenshot app has copied a static PNG-capable raster →
   caller runs the image-read API → receives a Pillow `Image` with matching
   width, height, and expected opaque colors; clipboard still offers that
   image.
2. Desktop app copied an image with alpha → image-read → alpha preserved
   when the native offer includes it; when a supported desktop drops alpha,
   docs/tests state that limit rather than inventing opacity.
3. Clipboard holds only Unicode text → image-read → `None`; `paste()` still
   returns the text; clipboard unchanged.
4. Windows (or other) clipboard holds only a filename / file-list offer →
   image-read → `None` (no file open); not an image success.
5. Clipboard holds corrupted image bytes under an image type → image-read →
   distinguishable failure, not absence and not a partial fake image.
6. No usable desktop clipboard / denied pasteboard access / required Linux
   helper missing → image-read → actionable failure distinct from absence.

**Architecture:**

- This repository defines no ADR store, index, status fields, or
  architecture-area map in project guidance (`AGENTS.md`, `.planning/`,
  `docs/`). Accepted-ADR examination was unavailable; no ADR check completed.
- Image read is a new responsibility beside the existing pyperclip text
  re-export: a contract layer that normalizes platform offers into one
  absence / Pillow image / failure model. Qualities at stake: cross-desktop
  semantic uniformity, preservative reads, dependency honesty (Pillow /
  helpers as declared install needs), and proof that in-memory fakes cannot
  alone establish native interoperability.
- Preferred reuse direction: wrap/normalize Pillow
  `ImageGrab.grabclipboard()` (which on Windows may return a filename list)
  rather than requiring a GUI toolkit or owning every native decoder in
  this story. Exact module layout and API spelling are planning concerns.

**Settled decisions (2026-11-02, Terry):** Pillow `Image` via
`clipboard[images]`; keep the four-desktop promise with helper docs and
evidence limits.

- **For / why:** Python automation developers can consume a screenshot or
  copied image without platform-specific clipboard code.
- **Evaluation:** On each supported desktop, an independent screenshot or
  image application copies a static raster image; Python retrieves a Pillow
  image with the expected dimensions, colors, and supported alpha. A copied
  image file reference alone is reported as no image, not opened implicitly.
- **Value / learning:** Answers the existing image-reading request
  ([issue #2](https://github.com/terryyin/clipboard/issues/2)) and tests
  whether native image differences can fit one useful contract.
- **Boundary:** One static raster item. No animation, screenshot capture,
  automatic URL fetching, or image writing. Malformed image data has a
  distinguishable failure; text-only content is an ordinary absence case.
- **Effort hypothesis:** **L**, medium-low confidence; assumes reusable image
  decoding, with native image types and desktop access still to verify.
- **Depends on:** None. No earlier new story is required to consume an image
  supplied by another application.
- **Safe stopping point:** Image ingestion works even if every later story is
  cancelled; reads preserve content and text callers remain compatible.

<a id="read-images-native"></a>

### Native image-read verification on Windows and Linux

**Identity:** SEED-001#read-images-native
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Close the SEED-001#read-images four-desktop promise with
  independent-producer native proof (or updated evidence limits) on Windows,
  Linux X11+`xclip`, and Linux Wayland+`wl-paste`, including helper/OS floors,
  alpha behavior, and native Windows CF_HDROP filename-list absence.
- **Evaluation:** On each remaining desktop, either record a matching native
  probe like the macOS Aqua result, or keep an explicit unverified/unsupported
  note — never silent success. Do not generalize one Wayland compositor.
- **Value / learning:** Turns documented evidence limits into verified floors
  before image writing expands the same desktop set.
- **Boundary:** Native verification and docs/floors for image **read** only.
  No image writing. Reuse `paste_image` / `clipboard[images]` as delivered.
- **Effort hypothesis:** **M**, medium confidence; depends on available
  desktop sessions and compositor coverage.
- **Depends on:** None for scheduling; builds on delivered `paste_image`.
- **Safe stopping point:** Each desktop has either native proof or an honest
  evidence limit; text and macOS image-read callers remain compatible.

<a id="write-images"></a>

### Copy Python images into desktop applications

**Identity:** SEED-001#write-images
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python report and image-tool authors can hand a generated
  image to an ordinary desktop application without saving and importing a
  temporary file manually.
- **Evaluation:** Python copies a static raster image; an independent image
  or document application pastes recognizable pixels with correct dimensions
  and supported transparency, including after the Python writer exits.
- **Addresses:** [Issue #5: I want to add image to clipboard](https://github.com/terryyin/clipboard/issues/5).
  The reporter needs image copying on Linux without depending on the
  Windows-only `win32clipboard` module.
- **Required issue example:** On each supported Linux X11 and Wayland path,
  a Python script uses `clipboard` to copy a raster image; after that script
  exits, a user pastes the image into an independent desktop image or document
  application. Document the Linux dependencies and supported desktop setup.
  Windows-only success or image-reading support does not fulfill issue #5.
- **Value / learning:** Delivers the Linux image-writing outcome requested in
  issue #5 and tests native image compatibility and writer lifetime.
- **Boundary:** One raster image, with supported input forms and conversion
  limits settled in refinement. Reject invalid images before replacement;
  replace an old offer without leaving stale representations. This is image
  content, not a file-manager copy or screenshot command.
- **Effort hypothesis:** **L**, low confidence; Windows image conventions,
  macOS representation choice, and Linux ownership all need native proof.
- **Depends on:** None. An independent desktop consumer proves this story;
  the library's image reader is not a prerequisite.
- **Safe stopping point:** Image export remains useful without any richer
  content work; serving resources end when superseded and writing does not hang
  the caller indefinitely.

<a id="copy-html"></a>

### Copy HTML with a matching plain-text alternative

**Identity:** SEED-001#copy-html
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python report authors can paste formatted snippets into rich
  applications while text-only destinations receive readable text.
- **Evaluation:** Given a Unicode HTML fragment with a styled link or small
  table and its explicit matching text alternative, one Python copy permits a
  rich editor to paste formatting and a text editor to paste the alternative.
  Repeat after writer exit; neither representation overwrites the other.
- **Value / learning:** Establishes rich-content exchange and simultaneous
  representations, especially on Wayland where one-type helpers may be
  insufficient for this promise.
- **Boundary:** HTML fragment plus caller-supplied plain text, published as one
  logical offer. No HTML renderer, general HTML-to-text conversion, embedded
  remote-resource fetching, RTF generation, or pixel-identical layout promise.
  The Windows case includes non-ASCII fragment/context boundaries.
- **Effort hypothesis:** **L**, low confidence; assumes interoperable rich
  targets can be named and multi-representation ownership is feasible.
- **Depends on:** None. Include the representation handling this outcome
  needs; do not invent a separate generic-backend prerequisite.
- **Safe stopping point:** One coherent rich-copy workflow works independently;
  unsupported rich access fails explicitly instead of silently claiming that
  two sequential text writes delivered both formats.

<a id="read-html"></a>

### Read HTML fragments copied by desktop applications

**Identity:** SEED-001#read-html
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python document and automation developers can preserve the
  markup of a selected browser/editor fragment rather than receive only text.
- **Evaluation:** A browser or rich editor copies a Unicode selection; Python
  reads its HTML fragment, with fragment/context boundaries handled correctly.
  Text-only content reports HTML absence, while corrupt native metadata reports
  an error. Clipboard content remains available to another consumer.
- **Value / learning:** Completes inbound HTML use without requiring a renderer
  and exposes native fragment-envelope differences.
- **Boundary:** Read the supplied HTML representation; document whether context
  and source metadata are exposed. Never execute markup, fetch resources, or
  synthesize HTML from plain text. No RTF conversion or full document import.
- **Effort hypothesis:** **M**, medium-low confidence; assumes bounded native
  fragment parsing and a small agreed set of external producers.
- **Depends on:** None. HTML comes from another application, so HTML writing
  in this library is not required first.
- **Safe stopping point:** Developers can ingest rich selections even without
  later file or inspection features; malformed metadata cannot cause a bogus
  successful fragment or a clipboard write.

<a id="inspect-formats"></a>

### Inspect clipboard content kinds and offered formats

**Identity:** SEED-001#inspect-formats
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Application developers can decide whether to enable text,
  image, rich-content, or file paste without trying to interpret an empty string.
- **Evaluation:** An external application offers HTML and text; Python reports
  both kinds and their native format identifiers without replacing the offer.
  Image-only, empty, and unavailable/denied access produce distinguishable
  outcomes where the native platform permits that distinction.
- **Value / learning:** Makes mixed clipboard content understandable and avoids
  conflating content availability with a broken environment.
- **Boundary:** Non-mutating inspection of the current offer, including offered
  types the library cannot decode. Separate platform capability from current
  content. Document snapshots and races; do not claim that inspection reserves
  data or that every format can be read. No arbitrary-format read/write API.
- **Effort hypothesis:** **M**, medium confidence; assumes native enumeration
  is accessible, with permission and empty-state differences to settle.
- **Depends on:** None. Inspect external offers without requiring new content
  writers or a generic binary exchange feature.
- **Safe stopping point:** Paste UIs gain useful decisions and diagnostics;
  inspection avoids unnecessary payload retrieval and preserves native access
  prompts and restrictions.

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

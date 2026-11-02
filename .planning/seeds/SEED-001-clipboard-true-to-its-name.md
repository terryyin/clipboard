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

<a id="write-images"></a>

### Copy Python images into desktop applications

**Identity:** SEED-001#write-images
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/003-write-images/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"bd98eb984b16e3111349481f4dd1263dc3e6acebb6aaeb488945b4038ddcac49","plan":"8a44c33d66ee150e06589c56b7bae41817051a609060b0b37b06d061b834f546"}}
```

**Plan:** [slice-plans/003-write-images/PLAN.md](../slice-plans/003-write-images/PLAN.md)

**Goal:** Python report and image-tool authors can hand a generated static
raster to an ordinary desktop application through `clipboard` without saving
and re-importing a temporary file: after the writing Python process exits, an
independent image or document application pastes recognizable pixels with
correct dimensions and supported transparency on each supported desktop that
this story claims, while text callers and delivered `paste_image` stay
compatible.

**Scope:**

- **Required behavior:** Add an explicit public write API (proposed spelling
  `copy_image`) that accepts a Pillow `Image`, requires the existing optional
  `clipboard[images]` extra, and publishes one static raster offer the desktop
  can paste. Invalid or unloadable input is rejected with
  `ClipboardImageError` **before** replacing the current clipboard contents.
  A successful write replaces prior text and image representations so a later
  paste does not see a stale offer of the other kind. Failures other than
  successful publication (missing helper, denied access, transfer failure,
  unsupported session) raise `ClipboardImageError` rather than silent no-op.
  Document Linux helper dependencies (`xclip` on X11; `wl-copy` on Wayland)
  and supported desktop setup. Default automated tests stay desktop-free via
  an injectable write backend; native proof uses an **independent consumer**
  (not a same-library `paste_image` round-trip alone) and stays explicitly
  gated. Successful writes remain pasteable after the writing process exits on
  each claimed desktop. Opaque rasters are required; when the native offer
  carries alpha, preserve it or document a platform drop. Convert non-RGB(A)
  modes to a transferable RGB/RGBA raster before offering; document conversion
  limits. Calling without the images extra raises `ImportError` consistent
  with `paste_image`.
- **Supported desktops (this story):** Windows desktop; macOS Aqua; Linux X11
  + `xclip`; Linux Wayland + `wl-copy` scoped to the compositor actually
  proved when one is available. WSL, SSH, containers, and headless CI are not
  additional guaranteed desktops. **Linux X11 and Wayland writer-exit success
  are acceptance requirements** (issue #5); they are not substitutable by an
  evidence-limit note. Windows and macOS require the same independent-consumer
  + writer-exit proof when a session is available; when no usable session
  exists during execution, record an explicit unverified/unsupported evidence
  limit for that desktop rather than claiming verified — never silent success.
- **Required restrictions:** Do not overload `copy()` / `paste()` to accept or
  return images. Do not bypass OS pasteboard / clipboard authorization. Do not
  treat a file-path / file-list / URL offer as fulfilling this image-content
  story. Do not leave a superseded text or image representation readable after
  a successful image write. Do not hang the caller indefinitely waiting to
  serve clipboard data. Do not generalize one Wayland compositor's result to
  all Wayland environments.
- **Scope limits / deferred:** Path/bytes overloads (callers open to `Image`
  first); animated / multi-frame / screenshot APIs; file-manager copy offers;
  HTML / rich / multi-item pasteboards; bundling GUI toolkits or
  `win32clipboard` as a required public dependency; making default pytest / CI
  require a real desktop; expanding beyond the four-desktop set; inventing
  rollback/atomicity guarantees beyond fail-before-replace. Using
  `paste_image` alone as native proof remains deferred (insufficient).
  Splitting Linux-first vs Win/macOS into separate stories is deferred unless
  execution evidence forces a resplit — this story keeps the four-desktop
  outcome with the Linux acceptance floor above.
- **Rejection constraints:** Invalid image input must not replace current
  content (independent need: Shared Boundaries fail-before-replace). Silent
  success on an unproved desktop is forbidden (honest four-desktop promise).
  Windows-only delivery is forbidden as story completion (issue #5). Wayland
  compositor generalization is forbidden.

**Key examples:**

1. Pillow RGB image in hand on a supported Linux X11 session with `xclip` →
   `copy_image(image)` returns successfully → writing process exits →
   independent image/document app pastes matching width, height, and opaque
   colors; Linux deps and floors are documented.
2. Same pattern on a supported Linux Wayland session with `wl-copy` on a named
   compositor → independent consumer pastes after writer exit; success is
   documented for that compositor only.
3. Pillow RGBA image whose native offer preserves alpha → independent consumer
   pastes with transparent pixels matching the source (or docs record an
   explicit alpha drop for that desktop).
4. Clipboard currently holds text (or a prior image) → `copy_image` succeeds →
   a subsequent text paste / image paste from another app does not recover the
   superseded representation.
5. Corrupt or empty Image (cannot produce a transferable raster) →
   `ClipboardImageError` before any clipboard replacement; prior offer remains.
6. Missing Linux helper or denied/unavailable clipboard access →
   `ClipboardImageError` with an actionable message; no silent empty success.
7. Windows desktop and/or macOS Aqua session available → same independent-
   consumer + writer-exit success with floors recorded; if a session is
   unavailable during execution, that desktop keeps an explicit evidence limit
   instead of a verified claim.
8. After this work, in-memory `copy` / `paste` / `paste_image` contract tests
   still pass; `VERSION` and text-only callers behave as before; calling
   `copy_image` without `clipboard[images]` raises `ImportError`.

**Direction (explored):** Compare credible ways to reach the goal against
Shared Boundaries, North Star, and issue #5.

1. **Explicit `copy_image(Image)` with platform-native offers + Linux helpers
   (recommended).** Mirror the delivered `paste_image` / `clipboard[images]`
   shape: thin public contract, injectable backend for CI, native writers that
   publish interoperable formats (not arbitrary labeled bytes), document
   helpers rather than bundling them. Pillow `ImageGrab` is read-only — write
   must be implemented (or carefully reused from a focused helper), not assumed
   from ImageGrab.
2. **Docs-only recipes (`xclip` / `wl-copy` / platform snippets).** Strongest
   smaller / existing-tool path; leaves each consumer owning format choice,
   lifetime, and errors — insufficient for the cohesive library promise and
   issue #5.
3. **Depend on an external image-clipboard package (e.g. pyperclipimg) or Qt.**
   May move pixels sooner, but adds heavy or divergent dependencies
   (pywin32 / pyobjc / GUI toolkit) and still needs independent-consumer proof
   and this project's absence/failure model — deferred as default stack.
4. **Linux-only story now; Win/macOS later.** Would satisfy issue #5 earlier,
   but splits the Shared Boundaries four-desktop write outcome; deferred unless
   execution forces a resplit.

Borrowed mechanism: **clipboard-manager / deferred-delivery handoff** (like a
post office holding a parcel after the sender leaves, or X11 SAVE_TARGETS /
`wl-copy` background serving). Roles map as: sender → writing Python process;
parcel → raster bytes in a native image type; post office → clipboard manager
or helper that keeps serving after exit; recipient → independent desktop app.
Adapt by making post-exit paste a required proof on each claimed desktop, not
an optional nicety. Limit of the analogy: unlike a durable post office, some
sessions have no manager/compositor support — those must fail explicitly or
stay evidence-limited (Win/macOS) / block acceptance (Linux), not pretend the
parcel remains.

Challenge: the purpose is handing pixels to another app without a temp-file
workflow, including after the writer exits — especially on Linux. `copy_image`
existing is only one way to reach that purpose. Meeting the wording with a
Windows-only or round-trip-only implementation misses the purpose (issue #5 and
independent-consumer proof). Strongest consequential doubt: four-desktop
post-exit lifetime is hard and may force a later Linux-first resplit — accepted
as an execution risk bounded by early native probes, not a rewrite of the goal
during refinement.

**Architecture:** ADR store is undefined in this repository; no Accepted ADR
constrains this story (architecture check: store missing — no Accepted-ADR
citation completed). North Star
[Rich clipboard content beside text re-exports](../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)
already directs explicit APIs beside `copy`/`paste`, optional `clipboard[images]`,
thin normalization, and in-memory vs native proof — follow it for write.
Consequential system effects: (1) add a write responsibility beside
`paste_image` without overloading text entry points; (2) platform writers must
own native format choice and post-exit serving/ownership, qualities ImageGrab
does not provide on write; (3) fail-before-replace and stale-representation
clearing are part of the public contract, not backend accidents. No new North
Star topic is required unless execution evidence overturns the explicit-API
shape.

- **Effort hypothesis:** **L**, low confidence; Windows DIB/PNG conventions,
  macOS pasteboard representation, and Linux ownership/lifetime all need
  native proof; Linux acceptance cannot fall back to evidence limits alone.
- **Depends on:** None. An independent desktop consumer proves this story;
  delivered `paste_image` is not a scheduling prerequisite (reuse for
  regression only).
- **Safe stopping point:** Image export remains useful without HTML/files work;
  serving resources end when superseded; writing does not hang the caller
  indefinitely; text and `paste_image` callers remain compatible.

<a id="copy-html"></a>

### Copy HTML with a matching plain-text alternative

**Identity:** SEED-001#copy-html
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/004-copy-html/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"7d455e2d985e8f3975afdd7aca89554e321a6ad2513afb45e9b7c081fe1b5118","plan":"79ac17ba9c74003898dd839d3916358ae9c1c8d1cb1ae2ccf452475880312564"}}
```

**Plan:** [slice-plans/004-copy-html/PLAN.md](../slice-plans/004-copy-html/PLAN.md)

**Goal:** Python report authors can hand a Unicode HTML fragment and an
explicit matching plain-text alternative to ordinary desktop applications
through `clipboard` in one logical offer: after the writing Python process
exits, a rich editor pastes recognizable formatting from the fragment and a
text-only destination pastes the alternative, on each supported desktop this
story claims, while existing text callers and delivered image APIs stay
compatible.

**Scope:**

- **Required behavior:** Add an explicit public write API (proposed spelling
  `copy_html(html, text)`) that accepts a Unicode HTML fragment string and a
  caller-supplied Unicode plain-text alternative and publishes **both** as one
  clipboard update. A successful write leaves neither representation
  overwriting the other: a rich consumer can obtain HTML and a text consumer
  can obtain the alternative from that same offer. Invalid input (wrong types,
  or empty HTML with no usable fragment when the contract requires one) is
  rejected **before** replacing current clipboard contents. Failures other than
  successful dual publication (missing helper, denied access, transfer
  failure, unsupported session, inability to offer both representations
  together) raise an actionable clipboard content error rather than silent
  no-op or a text-only write claiming success. Document platform HTML
  envelopes and Linux helper dependencies as needed (`xclip` on X11; Wayland
  helpers that can offer multiple MIME types — not a one-type-only path that
  drops the alternative). Default automated tests stay desktop-free via an
  injectable write backend; native proof uses **independent** rich and
  plain-text consumers (not a same-library round-trip alone) and stays
  explicitly gated. Successful dual offers remain pasteable after the writing
  process exits on each claimed desktop. On Windows, publish interoperable
  `HTML Format` with correct UTF-8 fragment/context byte offsets for
  non-ASCII content. Do not synthesize the plain-text alternative from HTML
  inside this story.
- **Supported desktops (this story):** Windows desktop; macOS Aqua; Linux X11
  + a multi-type-capable helper; Linux Wayland + a multi-type-capable helper
  scoped to the compositor actually proved when one is available. WSL, SSH,
  containers, and headless CI are not additional guaranteed desktops. Dual
  publication and writer-exit success are acceptance requirements on each
  claimed desktop when a session is available; when no usable session exists
  during execution, record an explicit unverified/unsupported evidence limit
  for that desktop rather than claiming verified — never silent success. Do
  not generalize one Wayland compositor's result to all Wayland environments.
- **Required restrictions:** Do not overload `copy()` / `paste()` to accept or
  return HTML. Do not treat two sequential text (or text-then-HTML) writes as
  fulfilling this story. Do not bypass OS pasteboard / clipboard
  authorization. Do not leave only one of the two promised representations
  after claiming success. Do not hang the caller indefinitely waiting to serve
  clipboard data. Do not execute markup, fetch remote resources, or promise
  pixel-identical layout across applications.
- **Scope limits / deferred:** Automatic HTML-to-text conversion; reading HTML
  (`SEED-001#read-html`); RTF or other rich formats; full HTML documents as a
  distinct contract from fragments; embedded resource packaging; bundling GUI
  toolkits or `win32clipboard` as a required public dependency; making default
  pytest / CI require a real desktop; expanding beyond the four-desktop set;
  inventing rollback/atomicity guarantees beyond fail-before-replace; same-
  library HTML round-trip as sole native proof.
- **Rejection constraints:** A call that cannot publish HTML and plain text
  together must not replace current content with a partial offer presented as
  success (independent need: simultaneous dual-representation promise and
  Shared Boundaries fail-before-replace). Silent success on an unproved
  desktop is forbidden. Sequential single-format writes claiming dual success
  are forbidden.

**Key examples:**

1. Unicode HTML fragment with a styled link (or small table) and an explicit
   matching plain-text alternative → `copy_html(html, text)` succeeds →
   writing process exits → independent rich editor pastes formatting; text
   editor pastes the alternative; neither representation alone replaced the
   other.
2. Same pattern including non-ASCII characters in fragment and/or surrounding
   Windows `HTML Format` context → rich consumer pastes the correct fragment
   (offsets/encoding hold); text consumer pastes the Unicode alternative.
3. Clipboard currently holds ordinary text (or a prior image) → `copy_html`
   succeeds → subsequent independent pastes see the new HTML and text
   alternatives, not the superseded offer as the sole content.
4. Empty or non-string HTML / text arguments that violate the public contract
   → actionable error before any clipboard replacement; prior offer remains.
5. Session or helper cannot offer HTML and plain text together (e.g. one-type-
   only helper path) → actionable failure; no silent text-only "success".
6. Missing Linux helper or denied/unavailable clipboard access → actionable
   error; no silent empty success.
7. Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available →
   same dual-consumer + writer-exit success with floors recorded for the named
   compositor/helper; if a session is unavailable during execution, that
   desktop keeps an explicit evidence limit instead of a verified claim.
8. After this work, in-memory `copy` / `paste` / `paste_image` contract tests
   still pass; `VERSION` and text-only callers behave as before; image APIs
   remain unchanged.

**Direction (explored):** Compare credible ways to reach the goal against
Shared Boundaries, North Star, and the dual-representation promise.

1. **Explicit `copy_html(html, text)` with one multi-representation native
   offer (recommended).** Mirror the delivered explicit-API shape beside
   `copy`/`paste`: thin public contract, injectable backend for CI, platform
   writers that publish interoperable HTML envelopes plus plain text together,
   document helpers rather than bundling them. No Pillow / `clipboard[images]`
   requirement for this story unless evidence forces a shared helper stack.
2. **Docs-only recipes or two sequential `copy` / helper writes.** Strongest
   smaller / existing-tool path; cannot keep both representations as one offer
   (especially on Wayland) and invites false "success" — insufficient for the
   library promise.
3. **Depend on Qt `QMimeData` / a GUI toolkit or a third-party rich-clipboard
   package.** May move bytes sooner, but adds heavy or divergent dependencies
   and still needs independent dual-consumer proof and this project's
   absence/failure model — deferred as default stack.
4. **Library-derived plain text from HTML (strip tags / readability).** Would
   shrink the caller surface, but contradicts the seed boundary of an explicit
   matching alternative and adds conversion quality scope — deferred; callers
   supply the alternative.
5. **HTML-only write; text destinations out of scope.** Meets a narrower API
   wording but misses the purpose that text-only destinations receive readable
   text from the same copy — rejected for this story's goal.

Borrowed mechanism: **email multipart alternative parts** (`text/html` +
`text/plain`): one message, two bodies; rich clients show HTML, plain clients
show text. Roles map as: message → one clipboard update; HTML part → fragment
offer; plain part → caller-supplied alternative; MUAs → independent rich vs
text paste targets. Adapt by requiring both parts in the **same** native
offer (Windows `HTML Format` + Unicode text; macOS HTML UTI + string; Linux
multi-MIME), with post-exit paste as required proof. Limit of the analogy:
clipboard envelopes and lifetime differ by OS (byte-offset HTML Format, pasteboard
items, Wayland MIME + seat/focus); unlike SMTP, a helper that can serve only
one type cannot fulfill the multipart promise and must fail or stay
evidence-limited — not pretend two sequential sends were one message.

Challenge: the purpose is **simultaneous** dual pasteability from one copy,
including after writer exit — not merely an HTML-named function. Meeting the
wording with HTML-only publication, sequential overwrites, or same-library
round-trips misses that purpose. Strongest consequential doubt: multi-type
ownership and post-exit lifetime on Wayland (and correct Windows non-ASCII
`HTML Format` offsets) may force helper/compositor evidence limits or a later
resplit — accepted as an execution risk bounded by early native probes, not a
rewrite of the dual-offer goal during refinement. Caller-mismatched "matching"
text can still succeed by contract; that is intentional (no converter), not a
scope defect.

**Architecture:** ADR store is undefined in this repository; no Accepted ADR
constrains this story (architecture check: store missing — no Accepted-ADR
citation completed). North Star
[Rich clipboard content beside text re-exports](../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)
already directs explicit APIs beside `copy`/`paste`, thin normalization, and
in-memory vs native proof — follow it for HTML write. Consequential system
effects: (1) add a rich-write responsibility that publishes **two** typed
representations in one update without overloading text entry points; (2)
platform writers must own HTML envelope encoding (including Windows fragment
offsets) and multi-MIME / multi-format offering, qualities pyperclip text
`copy` does not provide; (3) fail-before-replace and refusal of partial
single-format "success" are part of the public contract; (4) use an actionable
content-error type appropriate to non-image rich writes — do not overload
`ClipboardImageError` for HTML — unless a later Accepted decision introduces a
shared base. No new North Star topic is required unless execution evidence
overturns the explicit dual-offer API shape. HTML write does not require the
`clipboard[images]` extra.

- **Effort hypothesis:** **L**, low confidence; assumes interoperable rich
  targets can be named and multi-representation ownership is feasible across
  the four-desktop set.
- **Depends on:** None. Include the representation handling this outcome
  needs; do not invent a separate generic-backend prerequisite. Independent
  rich and text consumers prove this story; delivered image APIs are
  regression-only.
- **Safe stopping point:** One coherent rich-copy workflow works independently
  of HTML read / files / inspect; unsupported rich access fails explicitly
  instead of silently claiming that two sequential text writes delivered both
  formats; text and image callers remain compatible.

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

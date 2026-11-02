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
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/006-desktop-helpers/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"d4eeaa5af737700198da1f72610779a7621ef2a94984fde291d5b389fcdca34d","plan":"38af20c407bcde14a8618c5793ce256c712c894bd95eb4e9b2032efdcc2588d7"}}
```

**Goal:** Python developers relying on the README's verified desktop claims
keep a CI signal that fails when a verified native HTML-read probe stops
proving anything, and maintainers of the remaining SEED-001 stories reuse one
home for desktop session detection and helper handling instead of copying it
per content kind (correction of SEED-001#read-html; story recoverable at
`9d3ceda:.planning/seeds/SEED-001-clipboard-true-to-its-name.md#read-html`).

**Scope:** Make the gated Windows `paste_html` probe fail rather than skip when
it cannot verify; move Linux session detection, helper-failure detail
formatting, and the CLIPBOARD type listing (xclip `TARGETS`,
`wl-paste --list-types`) out of every content-kind module that copies them
(image write, HTML read/write, `inspect`, and the `paste_files` readers that
landed since this correction was planned) into one private desktop module,
keeping each caller's current semantics, including the file-list reader's
distinct Wayland rule; keep macOS HTML writer and reader together and
`_html_native.py` dispatch only; fold duplicated seam and structural
`paste_html` tests into the behavioral contract, with one no-Pillow import test
replacing the per-file `block_pil` copies. Public API, results, error messages,
and install hints stay unchanged. Unifying the divergent Wayland session rules
is a product decision outside this correction. Plan:
[006-desktop-helpers](../slice-plans/006-desktop-helpers/PLAN.md).

**Key examples:**

- With `CLIPBOARD_NATIVE_PROBE=1` on Windows, a probe report of
  `evidence_limit` fails `native-windows-paste-html` and `ci-passed`; a
  `verified: true` report passes as it does today.
- On Linux with only `XDG_SESSION_TYPE=wayland`, `paste_html()` and
  `inspect()` still select `wl-paste`; with `WAYLAND_DISPLAY` and `DISPLAY`
  both set, `paste_files()` still selects `xclip`. Each reader's error text is
  unchanged.
- An unowned X11 CLIPBOARD still makes `paste_html()` return `None` while
  image-write polling still treats a `TARGETS` failure as "not yet offered".

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

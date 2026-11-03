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

<a id="shared-native-clear-proof"></a>

### Define "cleared" once across the native clear probes

**Identity:** SEED-001#shared-native-clear-proof
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/015-shared-native-clear-proof/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"5933e11c2afbd5558d79a93b99a4dc5e1a352795af1faa7d266787c86ed2aef2","plan":"965fb568f70f1197c1da3910036d17caf4f7a02d36a0dddefefca3059d16218b"}}
```

**Goal:** Maintainers who change what the native `clear()` proof calls
"cleared" make that change in one place, not in parallel copies across four
probes and four wrappers, so the desktops' proofs cannot drift apart. The
documentation names `clear()` wherever it lists the operations that pick
Wayland on a mixed session.

**Scope:** Correction of SEED-001#clear-clipboard's proof and documentation
structure only: one shared "cleared" observation and one Linux step set
behind the X11 / Wayland / Windows / macOS clear probes, wrappers that rely on
each step's own `ok`, every touched probe file within 250 lines, `clear()`
named in the `_is_linux_wayland` docstring and AGENTS.md session sentence,
and `tests/test_clear.py` stops restating the no-Pillow scenario and private
globals. Changes no product code or public API, and keeps every probe step's
name, order and observed evidence. Excludes how X11 `clear()` launches its
relinquish helper in frozen or zipped applications (a separate human
decision).
[Plan](../slice-plans/015-shared-native-clear-proof/PLAN.md)

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

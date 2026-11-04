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

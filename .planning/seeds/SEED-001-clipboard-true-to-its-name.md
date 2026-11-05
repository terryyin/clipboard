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

<a id="primary-selection-polish"></a>

### Correct PRIMARY wording and probe evidence left by the primary-selection execution

**Identity:** SEED-001#primary-selection-polish
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/020-primary-selection-polish/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"cb28a9be01c98c6033700fccb664e97498594b3130782acbd1d93403c3a2abfa","plan":"1d890ecd55c73bd89bbdbd55a462b1cd6c60597d4df77f5dfc6f4af04336cdd5"}}
```

**Goal:** Python users calling `copy_primary` / `paste_primary` get error
messages that always name the primary selection (never "clipboard"), and
maintainers get native PRIMARY evidence whose step names, run ids and test
documentation match the story examples, correcting residue from the
SEED-001#primary-selection execution.

**Scope:**

- *Required behavior.* `copy_primary` input-rejection messages name the
  primary selection (never "clipboard"); `copy`'s rejection wording stays
  "clipboard". With both `DISPLAY` and `WAYLAND_DISPLAY` set, incomplete
  wl-clipboard, no `xclip`, and a pyperclip owner present, PRIMARY calls
  name both `xclip` and wl-clipboard and run nothing.
- *Evidence and docs.* Wayland PRIMARY probe and wrapper step names match
  the primary-selection story's example numbers; the Wayland PRIMARY README
  Evidence bullet cites CI run 41803370471; PRIMARY Wayland failure tests
  and the wl-clipboard fake describe Sway `primary_selection disabled` as
  the recorded conflicting observations (as README already does), not as
  settled fact that writes are dropped; X11 PRIMARY/text/clear probes share
  one `evidence_limit` helper, and the remaining Wayland clear/paste_html
  probes use the existing `evidence_limit()`.
- *Scope limits.* No behavior other than error text; no CLIPBOARD/pyperclip
  fallback; probe wrappers still assert only exit, `ok`, ordered steps and
  floors; evidence-limit exit 2 / CI failure outcomes stay the same.
- *Plan:* [020-primary-selection-polish](../slice-plans/020-primary-selection-polish/PLAN.md).

**Key examples:**

1. Linux PRIMARY in use → `copy_primary("a\x00b")` → `ClipboardContentError`
   naming "primary selection" (not "clipboard"); the earlier PRIMARY offer
   is still readable. The same input to `copy` still names "clipboard".
2. Linux with `DISPLAY` and `WAYLAND_DISPLAY` set, `PATH` carrying only
   `xsel` (no `xclip`, no `wl-copy` / `wl-paste`) → `copy_primary` /
   `paste_primary` raise naming both `xclip` and wl-clipboard; neither
   PRIMARY nor CLIPBOARD is read or replaced.
3. Wayland PRIMARY probe and its wrapper → step ids match the
   primary-selection examples (empty-string write; PATH without `wl-paste`),
   not the misnumbered `5_…` / `7_…` labels left from CLIPBOARD text probes.
4. README Wayland PRIMARY Evidence bullet → cites gated job run
   41803370471 beside the X11 bullet's 41799207621.
5. `tests/test_primary_wayland_failures.py` and
   `tests/fake_wl_clipboard_text.py` → describe Sway
   `primary_selection disabled` as conflicting observations (one drop, one
   write-through), matching README; they do not state the drop as fact.
6. Off an X11-only or Wayland session → each of the three X11
   text/clear/PRIMARY probes and the remaining Wayland clear/paste_html
   probes still exits 2 with `evidence_limit` from the shared helper for
   that desktop.

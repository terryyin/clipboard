# Plan: Define "cleared" once across the native clear probes

**Identity:** SEED-001#shared-native-clear-proof
**Source:** [Define "cleared" once across the native clear probes](../../seeds/SEED-001-clipboard-true-to-its-name.md#shared-native-clear-proof)
**Source review:** [Source review](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Provenance

Retrospective correction of SEED-001#clear-clipboard (story
`git show 1f8d805:.planning/seeds/SEED-001-clipboard-true-to-its-name.md`
anchor `#clear-clipboard`, plan
`git show 1f8d805:.planning/slice-plans/011-clear-clipboard/PLAN.md`; both
removed at wrap-up; reviewed commits
f0ec814..e0c0643). The probes and wrappers came from that plan's slices 2–6
and its later evidence rounds. The historical promises and README Evidence of
SEED-001#clear-clipboard stay as they are; this correction changes no
product behavior.

## Current findings

1. **"Cleared" is defined in parallel copies (structure, drift risk).**
   - X11 and Wayland probes carry near-identical step functions that differ
     only by owner-helper name, listing command and empty-clipboard
     predicate: `_copy_image_owner_ends`
     (`scripts/probe_linux_x11_native_clear.py:144`,
     `scripts/probe_linux_wayland_native_clear.py:231`),
     `_clear_twice_on_cleared` (x11 :175, wayland :262), producer-then-child
     clear (x11 :82, wayland :191) and the file-list step (x11 :127,
     wayland :214), plus duplicated `COPY_IMAGE_CHILD`, `URI_LIST_TYPE`,
     `UNKNOWN_TYPE` and `UNKNOWN_BODY`. They have already drifted: the X11
     producer step requires the producer's owner process to exit, the
     Wayland one does not record it.
   - The Windows probe repeats the same "listing empty and every reader
     absent" rule with its own key names (`_produced_then_child_clear`,
     `_clear_twice`, `scripts/probe_windows_native_clear.py:98`, :135).
   - The macOS probe keeps its own child-clear and reader helpers
     (`scripts/probe_macos_native_clear.py:50-86`,
     `scripts/macos_native_clear_support.py:109-156`) beside
     `scripts/native_clear_support.py` (`child_clear` :89,
     `read_everything` :158, `reads_empty` :179).
   - Each wrapper `tests/test_clear_native_{linux_x11,linux_wayland,windows}.py`
     copies `EMPTY_READS` and re-asserts per field what the step's `ok`
     already computes (for example `test_clear_native_linux_x11.py:65-144`);
     `tests/test_clear_native_macos.py` copies `_EMPTY_READERS`.
   - Over the 250-line file limit
     (`.claude/skills/dough-post-change-refactor/references/refactor-checks.md`):
     Wayland probe 388, X11 probe 285, Windows probe 285 lines.
   Impact: changing what "cleared" means needs parallel edits in up to four
   probes and four wrappers.
2. **Docs omit `clear()` from the Wayland-selection rule.**
   `clipboard/_desktop.py:31` (`_is_linux_wayland` docstring) lists image
   write, HTML read and inspect but not clear, although
   `clipboard/_clear.py:56` dispatches through it; the AGENTS.md sentence
   "HTML/inspect/image write select Wayland" (line 36) omits clear.
3. **Contract-test overlap.** `tests/test_clear.py:14-18` repeats the
   `clear` scenario of `tests/test_no_pillow_extra.py:136-148` and the
   `make test-package` check; `tests/test_clear.py:70-73` asserts private
   globals (`_clipboard_clearer is _default_clipboard_clearer`) while
   `:76-99` already observes the default clearer's behavior.

## Preserved promises and constraints

- No product code, public API, error message or README promise changes.
  Only a docstring in `clipboard/_desktop.py` changes in `clipboard/`.
- Every probe keeps its step (or macOS case) names, numbering and order:
  README Evidence cites them ("steps 7-8", "steps 8-9", "All eight steps").
  Each step still records the independent helper's own output (exit code,
  stdout, stderr), the child `clear()` record, every reader's value, and the
  owner PIDs and exit where it does today. Report key names inside a step
  may become neutral (for example `listing_after`, `classified_empty`);
  README cites no key names (`grep` for `classified`, `_after`,
  `owner_pids`, `xclip_targets_after`, `wl_paste_list` in `README.rst`,
  `docs/` and `.github/workflows/` finds none).
- A wrapper may drop a per-field assertion only when the step's `ok`
  implies it; a wrapper-only condition that matters moves into that step's
  `ok` (stricter, never looser). Wrappers keep: exit code 0, `ok`,
  `failed_steps == []`, the exact ordered step list, environment floors
  (xclip / Xvfb; Sway / wl-clipboard and `compositor_generalization`
  false; Windows version / runner image; macOS product / build), and
  "fails on an evidence limit, never skips" where it holds today.
- Gating stays: default pytest stays desktop-free; probes still exit 2
  with `evidence_limit` off their desktop.
- Native proof is expensive: Linux and Windows probes run only in CI jobs
  `native-linux-x11-clear`, `native-linux-wayland-clear` and
  `native-windows-clear` after publication; the macOS probe replaces the
  developer's live clipboard and runs locally under
  `CLIPBOARD_NATIVE_PROBE=1` (check the screen is unlocked first).
- If a native run shows a step that held before now fails, stop and return
  the observation; do not weaken the step or its `ok`.
- **Excluded:** X11 `clear()` running `sys.executable -I
  <package>/_x11_relinquish.py` in frozen or zipped applications (a human
  decision), including a `make test-package` check of the installed
  `_x11_relinquish.py`: that is packaging proof for the excluded question,
  not part of this structure correction. Also excluded: other content
  kinds' probes (text, inspect, copy_files) and SEED-001#bounded-helper-owner-write.

## Outside-in proof

| Finding | Observable signal | Owning slice |
| --- | --- | --- |
| 2 | `_is_linux_wayland` docstring and AGENTS.md name `clear()` among the operations that select Wayland on a mixed session; review only (no runtime change) | 1 |
| 3 | `nix develop -c make check` green; the no-Pillow `clear` scenario also asserts `"set_clipboard_clearer" in clipboard.__all__`; the merged default-clearer test fails under a scratch edit making `set_clipboard_clearer(None)` keep the injected clearer, passes reverted | 1 |
| 1 (rule) | Desktop-free `tests/test_native_clear_support.py`: the shared "cleared" observation is `ok` for an empty listing with every reader absent, and not `ok` for a non-empty listing, a non-absent reader, a reader error, a child `clear()` that raised, or a surviving owner PID | 2 |
| 1 (Linux) | `nix develop -c make check` green; on Darwin each of the X11 / Wayland probes exits 2 with `evidence_limit`; touched files ≤ 250 lines; after publication `native-linux-x11-clear` and `native-linux-wayland-clear` green with unchanged ordered step lists and the no-owner / `Nothing is copied` wordings, owner exits and reads recorded | 2 |
| 1 (Windows) | `nix develop -c make check` green; Windows probe exits 2 with `evidence_limit` on Darwin; probe ≤ 250 lines; after publication `native-windows-clear` green with its eight step names unchanged, the held case still raising after the 15 s bound with prior formats listed | 3 |
| 1 (macOS) | `nix develop -c make check` green; `CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked --extra images pytest tests/test_clear_native_macos.py -v -rP` passes on the owner's unlocked session with all six cases `ok` and the types before / empty after that README cites | 4 |
| Regression | Local gate `nix develop -c make check` (AGENTS.md) every slice; `nix develop -c make lint-workflows` only if `.github/workflows` changes (not planned) | 1–4 |

## Decisive premises

Observed in this checkout (Darwin 25.6.0, branch
`claude/clear-every-representation-from-the-current-clip` at e0c0643):

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| Default suite is desktop-free and green at the start | Every slice's regression gate | `nix develop -c make check` → `587 passed, 28 skipped` | Settled |
| Probes import their support modules and gate before any helper on Darwin | Local import check in slices 2–3 | `nix develop -c uv run --locked --extra images python scripts/probe_{linux_x11,linux_wayland,windows}_native_clear.py` → each exit 2 with `"evidence_limit": true` and a "not Linux" / "not a Windows desktop" reason | Settled (proves imports, not step bodies) |
| The three native CI jobs run on a branch push and pass with today's probes | Slices 2–3 native proof | `ci.yml` `on: push: branches: ['**']`; `gh run view 41658893626` (head 8a7368d) → `Native Windows clear` / `Native Linux X11 clear (Xvfb)` / `Native Linux Wayland clear (Sway)` all `success`; `git diff --stat 8a7368d e0c0643` touches only the plan, source review and README, so the probes are the ones that passed | Settled |
| README cites step numbers and names, not report keys | Preserved-evidence rule above | `grep` of `README.rst`, `docs/`, `.github/workflows/` for the key names → none; README lines 552–607 cite "steps 7-8", "steps 8-9", "All eight steps" | Settled |
| Wrapper-only conditions not implied by step `ok` | Slices 2–4 wrapper reduction | Compared each wrapper with its step `ok` expressions: X11 step 2 `libx11.display_opened` and `owner_before != 0`; X11 / Wayland file step `file_uri` starting `file:///`. All others are implied by `ok` or tautological (`mime_type in producer cmd`). macOS `_twice_case` `ok` omits the readers, which the wrapper does not assert either | Settled; slice 2 moves the three conditions into `ok` |
| A Wayland independent producer `wl-copy --type <mime>` leaves a background owner that exits after `clear()` (needed once the shared producer step requires owner exit on both desktops) | Slice 2 shared producer step on Sway | The library's own Wayland image owner is the same argv shape, `wl-copy --type image/png` with stdin (`clipboard/_image_write.py:131`); CI run 41651498162 step 5 recorded that owner exiting within 5 s after a child `clear()`; X11's producer step already requires it | Settled by the same mechanism; residual risk named in Plan review |

## Ordered slices

### 1. Clear named in the Wayland-selection rule; contract tests observe, not restate
Type: Structure
Status: done
Proof: rows "2" and "3" above.

Correction (findings 2 and 3; one local proof loop, `make check`):
`_is_linux_wayland`'s docstring lists clear with image write, HTML read and
inspect; AGENTS.md says "HTML/inspect/image write/clear select Wayland".
Delete `test_clear_is_public_without_images_extra` and add
`assert "set_clipboard_clearer" in clipboard.__all__` to the `clear`
scenario in `tests/test_no_pillow_extra.py` (its only assertion not already
covered there or by `make test-package`). Replace
`test_set_clipboard_clearer_none_restores_default` by starting
`test_default_clearer_names_platform_and_seam` with an injected recording
clearer, then `set_clipboard_clearer(None)`, and asserting the "not
available" error and that the injected clearer was never called. Preserved
behavior: public `clear` / `set_clipboard_clearer` surface and messages.

### 2. One "cleared" rule and one Linux step set behind the X11 and Wayland probes
Type: Structure
Status: done
Proof: rows "1 (rule)" and "1 (Linux)" above.

Correction (finding 1, Linux and the shared rule):

- `scripts/native_clear_support.py` gains the single "cleared" observation:
  given an independent listing callable and its empty predicate, it records
  the listing after, whether it classified as empty, every reader
  (`read_everything`), and is `ok` only when the listing is empty and
  `reads_empty` holds. `EMPTY_READS` lives here once; wrappers stop copying
  it. Its docstring covers every desktop's clear probe.
- New `scripts/linux_native_clear_steps.py`: a small Linux desktop
  description (owner-helper name, listing command, empty predicate, offered
  wait, independent producer) and the shared steps used by both probes:
  fresh clipboard reads empty, independent producer then child clear (owner
  PIDs and owner exit required on both desktops), file-list producer, the
  `copy_image` owner ending, and clear twice; plus the shared constants
  (`COPY_IMAGE_CHILD`, `URI_LIST_TYPE`, `UNKNOWN_TYPE`, `UNKNOWN_BODY`,
  `HTML_TYPE`, `HTML_BODY`).
- X11 desktop pieces stay in `scripts/linux_x11_native_clear_support.py`
  (gains the `xclip` producer); Wayland pieces (listing, offered wait,
  nothing-copied predicate, `wl-copy` producer, raw `wl-copy --clear` early
  step) move to new `scripts/linux_wayland_native_clear_support.py`.
- Each probe keeps only gating, `main`, its desktop-only steps (X11 raw
  relinquish and dead `DISPLAY`; Wayland raw `wl-copy --clear` and `PATH`
  without `wl-copy`) and its ordered step list with unchanged names.
- X11 step 2's `ok` adds `display_opened` and `owner_before != 0`; the
  file-list step's `ok` adds the `file:///` URI check.
- The two wrappers assert exit 0, `ok`, `failed_steps == []`, the ordered
  step list and the environment floors only.
- New `tests/test_native_clear_support.py` (imports from `scripts/` as
  `tests/test_linux_x11_native_text_support.py` does) drives the "cleared"
  observation with fake listings and reads.

Every touched file ≤ 250 lines. Publish, then accept the two Linux CI jobs.

Accepted proof (f071961): `nix develop -c make check` 606 passed, 27 skipped
(includes `tests/test_native_clear_support.py`); both Linux probes exit 2
with `evidence_limit` on Darwin; step lists identical to 9eb5a3c; CI run
41741871109 `Native Linux X11 clear (Xvfb)` and `Native Linux Wayland clear
(Sway)` success, `failed_steps: []`, all nine followed owners (four new
Wayland producer owners included) `exited: true`. Learning: the shared rule
keeps `waited_s <= bound_s` in `ok` because the old X11 wrapper asserted it
for the `copy_image` step; dropping it would loosen that step.

### 3. Windows clear probe on the shared rule
Type: Structure
Status: planned
Proof: row "1 (Windows)" above.

Correction (finding 1, Windows): `_produced_then_child_clear` and
`_clear_twice` use the shared "cleared" observation with
`consumer_formats` and the no-formats predicate; the two holder steps move
to `scripts/windows_native_clear_support.py` so the probe is ≤ 250 lines
and the support file stays ≤ 250. Step names, order, producers, bound
arithmetic and the held-case message checks stay. The wrapper asserts exit
0, `evidence_limit` false, `ok`, `failed_steps == []`, the eight-step list
and the Windows floors only. Publish, then accept `native-windows-clear`.

### 4. macOS clear probe on the shared child clear and readers
Type: Structure
Status: planned
Proof: row "1 (macOS)" above.

Correction (finding 1, macOS): the probe's cases use
`native_clear_support.child_clear` / `child_cleared` and the shared
"cleared" observation with the independent JXA type listing (empty means no
types), keeping `pbpaste` as the case's second independent consumer and the
`copy("")` contrast's `copy_empty_in_child`. Remove `readers_in_parent`,
`_empty_after`, `_child` and `clear_in_child`; "clear twice" is two child
clears. `privacy_prompt.every_child_clear_finished_within_bound` is computed
from the child records instead of being a constant. Case names stay. The
wrapper asserts exit 0, `ok`, the six case names and the macOS floors only.
Run the gated probe on the owner's unlocked session (replaces the live
clipboard).

## Current decisions

- One common rule: a clear is proven when a child `clear()` returned, the
  desktop's independent listing classifies as empty, and every public
  reader reads absence. Desktops differ only by listing, empty predicate,
  producer and owner helper; platform-only steps (dead `DISPLAY`, missing
  `wl-copy`, Windows holder bound, macOS `copy("")` contrast and raw early
  mechanism steps) stay per desktop because they prove distinct promises.
- The shared producer step requires producer-owner exit on Wayland as on
  X11, removing the drift instead of keeping a per-desktop flag.
- Shared Linux steps go in a new script module rather than
  `native_clear_support.py`, which is already 202 lines.
- Slice order puts the local-only docs and test cleanup first; slices 2–4
  are independent stopping points, each with its own native proof.

## Plan review

Slice-plan refinement not needed: three findings map to four Structure
slices, each with one proof loop (slice 1 local only; slices 2 and 3 one CI
job set each after publication; slice 4 one local gated run), no new
Behavior promise, and the cumulative design is one shared rule with desktop
descriptions rather than per-desktop special cases.

Remaining concerns: none blocking. Residual risk in slice 2: the Wayland
producer-owner exit is settled by the library owner's identical `wl-copy
--type <mime>` mechanism, not by observing an independent producer's owner;
if Sway shows it surviving, slice 2 stops under the preserved-promise rule
and returns the observation rather than dropping the check.

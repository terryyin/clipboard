# Plan: Keep native HTML-read proof strict and desktop helper knowledge single-homed

**Identity:** SEED-001#desktop-helpers
**Source:** [Keep native HTML-read proof strict and desktop helper knowledge single-homed](../../seeds/SEED-001-clipboard-true-to-its-name.md#desktop-helpers)
**Source review:** [source-review.md](source-review.md)

## Correction input

**Provenance:** execution retrospective of SEED-001#read-html (story
`9d3ceda:.planning/seeds/SEED-001-clipboard-true-to-its-name.md#read-html`,
plan `9d3ceda:.planning/slice-plans/005-read-html/PLAN.md`); reviewed net
diff `50d7677..1a5b92d` (commits 0d3e238, a894a15, 60d5967, e424146, 2e66857,
a9539fa, c541d77, 1796fc5, 8659430, 1a5b92d). Findings re-checked against
`707197321aac` (master after SEED-001#inspect-formats and SEED-001#read-files).

**Current findings (at 707197321aac):**

- F1 (defect): `tests/test_paste_html_native_windows.py` turns probe exit 2
  (evidence limit) into `pytest.skip`, so job `native-windows-paste-html` and
  `ci-passed` stay green while README claims Windows HTML read verified. The
  X11, Wayland, and macOS paste_html native tests do not skip.
- F2 (architecture): Linux session detection exists as `_is_linux_wayland` in
  `clipboard/_image_write.py` (imported by `_html_native.py`) and again in
  `clipboard/_offer_x11.py`, plus `_linux_wayland_without_x11` in
  `clipboard/_files_native_linux.py` with a different rule (Wayland only when
  `DISPLAY` is unset). Helper-failure detail is formatted separately in
  `_html_native.py`, `_html.py`, `_image_write.py`, `_html_native_linux.py`,
  `_files_native_linux.py`, and `_files_native_macos.py`. CLIPBOARD `TARGETS`
  / `wl-paste --list-types` listing exists in `_image_write.py`,
  `_html_native_linux.py`, and `_offer_x11.py` / `_offer_wayland.py` with
  different failure semantics. The macOS HTML writer lives in `_html.py` while
  the macOS reader and platform dispatch live in `_html_native.py`.
- F3 (test cost): `tests/test_paste_html_seam.py` duplicates contract
  failure/absence/value cases and asserts private identity; each reader test
  file repeats raw-offer equality and empty-offer cases; seven copies of the
  `block_pil` subprocess prelude (`test_paste_html_seam`, `test_copy_html_seam`,
  `test_paste_image`, `test_copy_image`, `test_paste_files_seam`,
  `test_paste_files_failures`, `test_inspect_seam`); the probe `FRAGMENT`
  literal is copied into the script and three native wrapper tests.

**Preserved promises and constraints:** public API and `VERSION`;
`paste_html` / `copy_html` / `paste_image` / `copy_image` / `paste_files` /
`inspect` results, `None` versus `ClipboardContentError` /
`ClipboardImageError` semantics, error messages and install hints;
image-write lenient `TARGETS` polling in `_wait_xclip_image_png_offer`; each
reader's current Wayland session rule; read-html approved decisions (package
layout, empty offer `""`, NUL refusal, fragment-only bodies as offered,
`StartHTML` into header, helper-producer verification); default pytest stays
desktop-free; native probes stay gated; every file ≤ 250 lines.

**Out of scope:** unifying the two Wayland session rules (product decision:
on a session with both `DISPLAY` and `WAYLAND_DISPLAY`, `paste_files` reads
X11 while the others read Wayland); retiring older image/`copy_html` evidence
limits (product follow-up); deduplicating the Sway bootstrap in `ci.yml`; a
shared error base class.

## Outside-in proof

| Key example | Signal |
| --- | --- |
| Windows evidence limit fails CI | desktop-free test drives the wrapper with an exit-2 report and sees failure; `native-windows-paste-html` green with `verified: true` |
| Session selection unchanged per reader | existing `test_paste_html_*_reader`, `test_inspect_x11` / `_wayland`, `test_paste_files_native_linux_*` stay green unedited in their assertions; `native-linux-*` CI jobs green |
| Listing failure modes unchanged | `test_paste_html_x11_reader::test_unowned_clipboard_is_none`, `test_inspect_x11` helper-failure cases, `native-linux-x11-copy-image` and `native-linux-wayland-copy-image` jobs green |

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| Windows CI probe currently reports verified, so strict wrapper keeps CI green | Slice 1 CI proof | master run 41433380766 (sha 4a9e903), job 125237206137: `test_windows_independent_producer_paste_html_probe PASSED`, `"verified": true` | Settled |
| Desktop-free tests detect a broken relocated session predicate | Slice 2 proof | scratch `clipboard/_desktop.py` with both predicates raising, callers re-pointed; `nix develop -c uv run --locked --extra images pytest -q --tb=no` → 51 failed (inspect x11/wayland, paste_files linux x11/wayland, paste_html x11/wayland readers); with correct bodies → 309 passed, 15 skipped; reverted | Settled for HTML, inspect, files |
| Image-write session selection is covered by a test | Slice 2 proof | same scratch: no `copy_image` test failed | **False** for default pytest; covered only by `native-linux-x11-copy-image` / `native-linux-wayland-copy-image` CI jobs, which slice 2 names |
| Tests patch `subprocess` / `sys` module objects, not moved function names | Slices 2–3 relocation | `setattr` targets in tests are `<module>.subprocess, "run"`, `<module>.sys, "platform"`, `_html_native_windows._win32_api`; scratch relocation kept them green | Settled |

## Ordered slices

### 1. Fail the Windows native probe when it cannot verify
Type: Behavior
Status: done
Proof: `tests/test_paste_html_native_windows.py` asserts `verified is True`
(evidence limit fails, as on X11/Wayland/macOS); a desktop-free check shows the
wrapper fails on an evidence-limit report and fails without the change;
`nix develop -c make check`; CI job `native-windows-paste-html` passes with
`verified: true` on the published revision.

Behavior: Pre-condition: gated Windows probe that may exit 2. Trigger: CI runs
the job. Postcondition: an evidence limit makes the job and `ci-passed` fail.

### 2. Single-home session detection and helper failure detail
Type: Structure
Status: done
Proof: a private `clipboard/_desktop.py` owns both Linux session predicates
(named for their distinct rules) and helper-failure detail formatting, each
caller keeping its current fallback (`"unknown error"`, `""`, stderr-only
bytes decoding); the macOS HTML writer and reader move together into one
macOS HTML module and `_html_native.py` is dispatch only. No copies remain in
`_image_write.py`, `_offer_x11.py`, `_files_native_linux.py`, `_html.py`,
`_html_native.py`, `_html_native_linux.py`, `_files_native_macos.py`.
`nix develop -c make check` and `nix develop -c make lint-workflows` pass
with unchanged error-message assertions; the next CI run keeps all five
native jobs green (the copy-image jobs are the only proof of image-write
session selection).

Correction: removes F2's session and failure-detail copies that the next
SEED-001 stories (copy-files, portable-text, clear) would otherwise copy again.

### 3. Single-home CLIPBOARD type listing with per-caller failure modes
Type: Structure
Status: done
Proof: `clipboard/_desktop.py` owns the xclip `TARGETS` and
`wl-paste --list-types` invocations with an explicit failure mode per caller:
image polling lenient (failure → empty), HTML read strict with unowned
CLIPBOARD → `None`, `inspect()` bounded with its current timeout and
messages. `_image_write.py`, `_html_native_linux.py`, `_offer_x11.py`,
`_offer_wayland.py` call it. `nix develop -c make check` passes with
unchanged assertions; the next CI run keeps all five native jobs green.

Correction: removes F2's listing copies with their divergent failure handling
kept explicit at one place.

### 4. Fold duplicated seam and structural tests
Type: Structure
Status: done
Proof: duplicated seam cases fold into `tests/test_paste_html_contract.py`;
private-identity and raw-offer equality assertions are removed where a
`paste_html()` behavior assertion covers the same promise; one parametrized
no-Pillow subprocess test replaces the seven `block_pil` copies and covers
each import path they covered; `FRAGMENT` has one home per side (probe vs
test); listed behaviors (fragment, absence, empty `""`, failure wrapping,
reset to default, no Pillow per public function) each keep a named surviving
test; `nix develop -c make check` passes.

Correction: removes F3's duplicated cost without losing a behavior.

## Current decisions

- Correction keeps each caller's existing failure semantics and session rule;
  unify location, not behavior.
- The `paste_files` and `inspect` copies that landed after this correction
  was planned are in scope: the story's goal is one home instead of per-kind
  copies, and F2 already absorbed the `inspect` copies the same way.
- Windows strictness goes first: it is independent, smallest, and fixes the
  only defect.

## Learnings

- Slice 1: module-level `pytestmark` blocked a same-file desktop-free
  evidence-limit check; per-test `skipif` on the gated probe keeps the
  ungated wrapper collectable off Windows. Expecting `AssertionError` (not
  `Skipped`) is what makes the desktop-free check reject skip-on-exit-2.
- Accepted proof (slice 1, pre-publish): removed exit-2 `pytest.skip` from
  `tests/test_paste_html_native_windows.py`; assert `returncode == 0` and
  `verified is True`; `test_evidence_limit_report_fails_windows_paste_html_wrapper`
  fails on synthetic exit-2. `nix develop -c make check` → 310 passed, 15
  skipped. Live `native-windows-paste-html` with `verified: true` remains
  observation on the published revision (settled premise: master run
  41433380766).
- Slice 2: macOS reader/seam tests needed submodule retargets for
  `_html_native_macos.subprocess` once dispatch dropped its own `subprocess`
  import; `sys.platform` patches on `_html_native` still drive selection.
  Accepted proof: `clipboard/_desktop.py` owns both session predicates and
  helper-failure detail; `_html_native_macos.py` co-locates writer+reader;
  `_html_native.py` dispatch-only. `make check` 310/15; `lint-workflows` clean.
  Listing relocation deferred to slice 3.
- Slice 3: `_desktop.py` owns xclip TARGETS / wl-paste list-types with
  lenient (image), HTML-strict (unowned → None), and inspect-bounded modes.
  Accepted proof: `make check` 310/15; `test_unowned_clipboard_is_none` and
  image lenient polling preserved. Native five-job confirmation deferred to CI.
- Slice 4: folded paste_html seam into contract; one parametrized
  `test_no_pillow_extra` replaces seven `block_pil` copies; FRAGMENT one home
  per side. Accepted proof: `make check` 297 passed, 15 skipped.

## Concern evidence

- Slice-plan refinement: not needed — the rewrite already split the former
  combined Structure slice so listing failure modes (the riskier relocation)
  have their own proof loop; each slice is one proof loop with no hidden
  preparation.
- Remaining slice-specific concerns: none identified in this review.


## Story obligations

### X1. Older image/copy_html evidence-limit retirement
Reported: slice 1 — "source review 1e — exclusion of retiring older image/copy_html evidence limits"
Story clause: "Python developers relying on the README's verified desktop claims keep a CI signal that fails when a verified native HTML-read probe stops proving anything"
Disposition: no user cost "keep a CI signal that fails when a verified native HTML-read probe stops proving anything": retiring older image/copy_html evidence limits is correction out-of-scope and does not weaken the Windows paste_html fail-not-skip CI signal
Commitment: 1e, 29

### X2. Unifying Wayland session rules out of scope
Reported: slice 1 — "source review 3b"
Story clause: "Unifying the divergent Wayland session rules is a product decision outside this correction."
Disposition: excluded "Unifying the divergent Wayland session rules is a product decision outside this correction."
Commitment: 3b, 28

### X3. DISPLAY+WAYLAND_DISPLAY split preserved
Reported: slice 1 — "source review 9"
Story clause: "Unifying the divergent Wayland session rules is a product decision outside this correction."
Disposition: excluded "Unifying the divergent Wayland session rules is a product decision outside this correction."
Commitment: 9

### X4. Sway bootstrap dedup out of scope
Reported: slice 1 — "source review 30 — ci.yml Sway bootstrap dedup"
Story clause: "Python developers relying on the README's verified desktop claims keep a CI signal that fails when a verified native HTML-read probe stops proving anything"
Disposition: no user cost "keep a CI signal that fails when a verified native HTML-read probe stops proving anything": Sway bootstrap deduplication in ci.yml is correction out-of-scope and does not affect the Windows HTML-read fail-not-skip CI signal
Commitment: 30

### X5. Shared error base class out of scope
Reported: slice 1 — "source review 31 — shared error base class"
Story clause: "Public API, results, error messages, and install hints stay unchanged."
Disposition: no user cost "Public API, results, error messages, and install hints stay unchanged": a shared error base class is correction out-of-scope and public error types/messages stay as they are
Commitment: 31
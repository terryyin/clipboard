# Plan: Keep native HTML-read proof strict and desktop helper knowledge single-homed

**Identity:** SEED-001#desktop-helpers
**Source:** [Keep native HTML-read proof strict and desktop helper knowledge single-homed](../../seeds/SEED-001-clipboard-true-to-its-name.md#desktop-helpers)

## Correction input

**Provenance:** execution retrospective of SEED-001#read-html (story
`9d3ceda:.planning/seeds/SEED-001-clipboard-true-to-its-name.md#read-html`,
plan `9d3ceda:.planning/slice-plans/005-read-html/PLAN.md`); reviewed net
diff `50d7677..1a5b92d` (commits 0d3e238, a894a15, 60d5967, e424146, 2e66857,
a9539fa, c541d77, 1796fc5, 8659430, 1a5b92d).

**Current findings (at 1a5b92d):**

- F1 (defect): `tests/test_paste_html_native_windows.py` turns probe exit 2
  (evidence limit) into `pytest.skip`, so job `native-windows-paste-html` and
  `ci-passed` stay green while README claims Windows HTML read verified. The
  X11, Wayland, and macOS paste_html native tests do not skip.
- F2 (architecture): `clipboard/_html_native.py` imports `_is_linux_wayland`
  from `clipboard/_image_native.py`; helper-failure detail is formatted three
  ways (`_osascript_failure_detail`, `_helper_failure_detail`,
  `_stderr_text`/`_exit_detail`); the xclip `TARGETS` listing exists twice
  with different failure semantics (image: empty on failure; HTML: raise);
  `_html_native.py` mixes the macOS writer, macOS reader, and dispatch;
  `_image_native.py` re-imports stdlib modules inside functions.
- F3 (test cost): `tests/test_paste_html_seam.py` duplicates contract
  failure/absence/value cases and asserts private identity; each reader test
  file repeats raw-offer equality and empty-offer cases; three copies of the
  `block_pil` subprocess prelude; the probe `FRAGMENT` literal is copied into
  four files.

**Preserved promises and constraints:** public API and `VERSION`;
`paste_html` / `copy_html` / `paste_image` / `copy_image` results, `None`
versus `ClipboardContentError` / `ClipboardImageError` semantics, error
messages and install hints; image-write lenient `TARGETS` polling in
`_wait_xclip_image_png_offer`; the Wayland session rule; read-html approved
decisions (package layout, empty offer `""`, NUL refusal, fragment-only bodies
as offered, `StartHTML` into header, helper-producer verification); default
pytest stays desktop-free; native probes stay gated; every file ≤ 250 lines.

**Out of scope:** retiring older image/`copy_html` evidence limits (product
follow-up); deduplicating the Sway bootstrap in `ci.yml`; a shared error base
class.

## Ordered slices

### 1. Single-home desktop session and helper knowledge
Type: Structure
Status: planned
Proof: a private `clipboard/_desktop.py` (or equivalent) owns
`_is_linux_wayland`, helper-failure detail formatting, and the xclip
`TARGETS` listing, with an explicit per-caller failure mode so image polling
stays lenient and HTML read stays strict; macOS HTML writer/reader live in
their own module and `_html_native.py` is dispatch only; `_image_native.py`
uses module-level imports. `nix develop -c make check` and
`nix develop -c make lint-workflows` pass with unchanged error-message
assertions; the next CI run keeps all five native jobs green.

### 2. Fail the Windows native probe when it cannot verify
Type: Behavior
Status: planned
Proof: `tests/test_paste_html_native_windows.py` asserts `verified is True`
(evidence limit fails, as on X11/Wayland/macOS); a desktop-free check shows the
wrapper fails on an evidence-limit report; CI job `native-windows-paste-html`
passes with `verified: true` on the published revision.

Behavior: Pre-condition: gated Windows probe that may exit 2. Trigger: CI runs
the job. Postcondition: an evidence limit makes the job and `ci-passed` fail.

### 3. Fold duplicated paste_html seam and structural tests
Type: Structure
Status: planned
Proof: duplicated seam cases fold into `tests/test_paste_html_contract.py`;
private-identity and raw-offer equality assertions are removed where a
`paste_html()` behavior assertion covers the same promise; one parametrized
no-Pillow subprocess test covers `paste_html`, `copy_html`, and `paste_image`
import paths; `FRAGMENT` has one home per side (probe vs test); listed
behaviors (fragment, absence, empty `""`, failure wrapping, reset to default,
no Pillow) each keep a named surviving test; `nix develop -c make check`
passes.

## Current decisions

- Correction keeps each caller's existing failure semantics; unify location,
  not behavior.

## Learnings

_(none yet)_

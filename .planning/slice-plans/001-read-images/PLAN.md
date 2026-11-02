# Plan: Read images copied by desktop applications

**Identity:** SEED-001#read-images
**Source:** [Read images copied by desktop applications](../../seeds/SEED-001-clipboard-true-to-its-name.md#read-images)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Python automation developers retrieve a static raster copied by a desktop
application as a Pillow `Image` through an explicit API (`paste_image`),
without platform-specific clipboard code, while `copy` / `paste` / `VERSION`
stay unchanged.

**Included:** optional `clipboard[images]` (Pillow); Linux docs for `xclip` /
`wl-paste`; absence (`None`) vs Pillow image vs distinguishable failures;
file-reference / filename-list offers → `None` (no filesystem open); preservative
reads; Windows desktop, macOS (authorized pasteboard), Linux X11+`xclip`,
Linux Wayland+`wl-paste` with evidence limits.

**Excluded:** animation, screenshot capture, image writing, URL fetch, opening
file references, PNG-bytes-only API, non-Pillow buffers, WSL/SSH/containers as
guaranteed desktops, overloading `paste()`.

## Assumptions

- Public API spelling for this plan: `paste_image()` → `Image | None`, errors
  via exceptions (exact exception types chosen in implementation).
- Preferred native path: normalize Pillow `ImageGrab.grabclipboard()` behind
  the contract (Windows filename lists → `None`).
- ADR store is undefined in this repo; no Accepted ADR constrains this plan.
- PFE: product has no image-read solution today (text-only re-export). Gap is
  explicit; add a new image-read path rather than extending `paste()`.

## Outside-in proof

| Example | Observable signal |
| --- | --- |
| Independent static raster on clipboard | `paste_image()` returns Pillow `Image` with expected size/colors; clipboard still offers the image |
| Alpha when native offer has it | Mode/channels preserve alpha; documented limit if a desktop drops it |
| Text-only clipboard | `paste_image()` is `None`; `paste()` still returns text |
| Filename / file-list offer only | `paste_image()` is `None`; no file open |
| Corrupted image bytes | Failure distinct from `None` |
| No desktop / denied access / missing helper | Actionable failure distinct from `None` |

Automated contract tests use an injectable / in-memory image backend (same
spirit as current pyperclip substitution). Native examples use an independent
producer; same-library round-trips alone do not establish interoperability.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| Public exports are only `copy`, `paste`, `VERSION` | Slices adding `paste_image` | `nix develop -c uv run --locked python -c` printing `dir(clipboard)` | Settled: those three only; `VERSION == 0.0.5` |
| Locked env has no Pillow | Optional extra / import path | same runner, `importlib.util.find_spec('PIL')` | Settled: `False` |
| CI text tests substitute `pyperclip.determine_clipboard` | In-memory image contract tests | Read `tests/test_clipboard.py` | Settled: subprocess + in-memory copy/paste pair |
| No in-product image-read path | New image module/API | Read `clipboard.py` | Settled: pyperclip re-export only (PFE gap) |
| `ImageGrab.grabclipboard` yields a usable image from an independent desktop producer on each supported desktop (with helpers) | Native proof slices | macOS Aqua observed (see Learnings slice 5); Windows / Linux remaining → slice 6 | Open — macOS settled for this checkout; other desktops → slice 6 |

## Ordered slices

### 1. Optional images extra and explicit `paste_image` contract
Type: Behavior
Status: done
Proof: With `clipboard[images]` installable from the project metadata, a
subprocess (or equivalent) that stubs the image backend: text-only →
`paste_image()` is `None` and `paste()` still returns text; stubbed raster →
Pillow `Image` with expected size/mode; clipboard contents unchanged after
read; `paste` / `copy` / `VERSION` still importable without the extra for
text-only use (document import error if `paste_image` used without extra).

Behavior: Pre-condition: package metadata declares optional Pillow extra;
in-memory/stub image backend available in tests. Trigger: call `paste_image`
and text `paste`. Postcondition: absence/image contract holds; text API
preserved; no desktop required for this proof.

### 2. File-reference offers are not images
Type: Behavior
Status: done
Proof: Stub/backend returns a filename list (Windows-shaped); `paste_image()`
is `None`; no filesystem open of those paths (spy/mock on open/path reads).

Behavior: Pre-condition: clipboard offer is file-list only. Trigger:
`paste_image()`. Postcondition: `None`, not an image loaded from disk.

### 3. Failures stay distinct from absence
Type: Behavior
Status: done
Proof: Stub raises/returns malformed image bytes and unavailable-access /
missing-helper conditions; caller sees exceptions (or typed failures)
distinguishable from `None`; text-only still yields `None` without exception.

Behavior: Pre-condition: backend can simulate malformed bytes and access/
helper failure. Trigger: `paste_image()`. Postcondition: failure ≠ absence.

### 4. Docs name extras and Linux helpers
Type: Structure
Status: done
Proof: README (or equivalent) documents `clipboard[images]`, Pillow, and
Linux `xclip` / `wl-paste`; existing text install/usage docs remain accurate.
Enables slices 5–6 consumer setup.

Internal change: packaging/docs only; no new runtime behavior beyond what
slices 1–3 already expose.

### 5. Early probe — native image read on an available desktop
Type: Behavior
Status: done
Proof: On at least one supported desktop in this preparation/execution
environment (Windows, macOS, or Linux with the matching helper), an
independent screenshot or image app copies a static raster; `paste_image()`
returns matching pixels; read is preservative. Record OS, desktop/compositor,
helper version, and Pillow version. Failure stops dependent native claims and
revises the plan.

Behavior: Pre-condition: usable desktop clipboard session for one supported
environment. Trigger: independent copy, then `paste_image()`. Postcondition:
usable Pillow image with expected dimensions/colors.

### 6. Early probe — remaining supported desktops and evidence limits
Type: Behavior
Status: planned
Proof: For each remaining supported desktop not covered in slice 5, either
(a) the same independent-producer observation with recorded environment, or
(b) an explicit evidence-limit note that that desktop is unsupported or
unverified pending a named follow-up — never a silent success. Include one
filename-list or file-reference absence case on Windows when that desktop is
available. Alpha preservation noted when the producer offers it.

Behavior: Pre-condition: slice 5 recorded for one desktop. Trigger: probe or
document each remaining target. Postcondition: every supported desktop has
either native proof or a written evidence limit; no compositor generalization
from a single Wayland result.

## Current decisions

- API name: `paste_image` (explicit; does not overload `paste`).
- Return: `PIL.Image.Image | None`; failures via exceptions.
- Reuse Pillow `ImageGrab.grabclipboard` behind a normalizing contract.
- Follow [.planning/NORTH-STAR.md](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports).

## Learnings

- Slice 1: Default `ImageGrab.grabclipboard` stays behind `set_image_grabclipboard`
  so CI never needs a pasteboard. Non-`Image` backend results currently normalize
  to `None` (prepares slice 2; not yet proved with a filename-list open spy).
- Accepted proof (slice 1): `nix develop -c uv run --locked --extra images pytest tests/test_paste_image.py tests/test_clipboard.py -v` — pass; also `nix develop -c make check` — pass (16 tests).
- CI repair: matrix `tests` job must `uv sync/run --locked --extra images` (same as Makefile); without it preservative subprocesses fail importing Pillow.
- Accepted proof (slice 2): `nix develop -c uv run --locked --extra images pytest tests/test_paste_image.py tests/test_clipboard.py -v` — pass; file-list/URL stubs → `None` with open/path spy `path_hits == []`.
- Slice 3: `ClipboardImageError` wraps grab/decode failures (OSError/NotImplementedError); text-only still `None`.
- Accepted proof (slice 3): `nix develop -c uv run --locked --extra images pytest tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_clipboard.py -v` — failure≠absence coverage lives in `test_paste_image_failures.py` after post-change refactor.
- Accepted proof (slice 4): README.rst documents `clipboard[images]`, Pillow/`paste_image`, Linux `xclip` / `wl-paste`; text install/usage remain accurate.
- Slice 5 (evidence recorded; status not marked done pending delivery): Independent
  producer on this macOS desktop — Pillow wrote known PNGs to temp files; osascript
  placed them via `«class PNGf»`; `paste_image()` consumed with
  `set_image_grabclipboard(None)` (real ImageGrab). Opaque RGB 32×24 matched corner
  and center colors; second `paste_image()` matched first (preservative);
  `ImageGrab.grabclipboard` still returned an image afterward. RGBA 16×16 with
  translucent center `(0,0,255,128)` preserved mode RGBA and alpha 128.
  Environment: macOS 26.6.2 (Build 25G83), Darwin 25.6.0 arm64, desktop Aqua
  (WindowServer/Quartz), helper osascript (built-in), Pillow 11.3.0, Python 3.13.17.
  Probe script: `scripts/probe_macos_native_paste_image.py` (JSON on stdout).
  Optional gated test: `CLIPBOARD_NATIVE_PROBE=1` →
  `tests/test_paste_image_native_macos.py` (skipped in default pytest).

## Concern evidence

- Slice-plan refinement: **not needed** — slices are one cohesive contract
  model (absence / image / failure) plus bounded native probes; no competing
  independent outcome, no unmapped proof, no cumulative special-case design
  requiring a refinement pass within this outcome.
- Remaining slice-specific concerns: **none** beyond the early-probe-bounded
  native premise in the Decisive premises table (slices 5–6).

## Story obligations

### X14. WSL, SSH, containers, and headless CI are not guaranteed desktops
Reported: slice 1 — "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Story clause: "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Disposition: excluded "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Commitment: 14

### X19.1. Animation deferred
Reported: slice 1 — "Out of scope / deferred: Animation."
Story clause: "Animation"
Disposition: excluded "Animation"
Commitment: 19.1

### X19.2. Screenshot capture deferred
Reported: slice 1 — "Out of scope / deferred: Screenshot capture."
Story clause: "screenshot capture"
Disposition: excluded "screenshot capture"
Commitment: 19.2

### X19.3. Image writing deferred
Reported: slice 1 — "Out of scope / deferred: Image writing."
Story clause: "image writing"
Disposition: excluded "image writing"
Commitment: 19.3

### X19.4. Automatic URL fetch deferred
Reported: slice 1 — "Out of scope / deferred: Automatic URL fetch."
Story clause: "automatic URL fetch"
Disposition: excluded "automatic URL fetch"
Commitment: 19.4

### X19.5. Opening file-manager references deferred
Reported: slice 1 — "Out of scope / deferred: Opening file-manager references."
Story clause: "opening file-manager references"
Disposition: excluded "opening file-manager references"
Commitment: 19.5

### X19.6. RTF deferred
Reported: slice 1 — "Out of scope / deferred: RTF."
Story clause: "RTF"
Disposition: excluded "RTF"
Commitment: 19.6

### X19.7. Arbitrary typed bytes deferred
Reported: slice 1 — "Out of scope / deferred: Arbitrary typed bytes."
Story clause: "arbitrary typed bytes"
Disposition: excluded "arbitrary typed bytes"
Commitment: 19.7

### X19.8. History deferred
Reported: slice 1 — "Out of scope / deferred: History."
Story clause: "history"
Disposition: excluded "history"
Commitment: 19.8

### X19.9. Cloud sync deferred
Reported: slice 1 — "Out of scope / deferred: Cloud sync."
Story clause: "cloud sync"
Disposition: excluded "cloud sync"
Commitment: 19.9

### X19.10. PNG-bytes-only APIs deferred
Reported: slice 1 — "Out of scope / deferred: PNG-bytes-only APIs."
Story clause: "PNG-bytes-only APIs"
Disposition: excluded "PNG-bytes-only APIs"
Commitment: 19.10

### X19.11. Library-owned non-Pillow buffers deferred
Reported: slice 1 — "Out of scope / deferred: Library-owned non-Pillow buffers."
Story clause: "library-owned non-Pillow buffers"
Disposition: excluded "library-owned non-Pillow buffers"
Commitment: 19.11

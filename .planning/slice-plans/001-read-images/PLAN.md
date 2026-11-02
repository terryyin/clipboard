# Plan: Read images copied by desktop applications

**Identity:** SEED-001#read-images
**Source:** [Read images copied by desktop applications](../../seeds/SEED-001-clipboard-true-to-its-name.md#read-images)
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
| `ImageGrab.grabclipboard` yields a usable image from an independent desktop producer on each supported desktop (with helpers) | Native proof slices | Not observed in this checkout (no unpaid native producer run authorized here) | Open — bounded by early probe slices 5–6 |

## Ordered slices

### 1. Optional images extra and explicit `paste_image` contract
Type: Behavior
Status: planned
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
Status: planned
Proof: Stub/backend returns a filename list (Windows-shaped); `paste_image()`
is `None`; no filesystem open of those paths (spy/mock on open/path reads).

Behavior: Pre-condition: clipboard offer is file-list only. Trigger:
`paste_image()`. Postcondition: `None`, not an image loaded from disk.

### 3. Failures stay distinct from absence
Type: Behavior
Status: planned
Proof: Stub raises/returns malformed image bytes and unavailable-access /
missing-helper conditions; caller sees exceptions (or typed failures)
distinguishable from `None`; text-only still yields `None` without exception.

Behavior: Pre-condition: backend can simulate malformed bytes and access/
helper failure. Trigger: `paste_image()`. Postcondition: failure ≠ absence.

### 4. Docs name extras and Linux helpers
Type: Structure
Status: planned
Proof: README (or equivalent) documents `clipboard[images]`, Pillow, and
Linux `xclip` / `wl-paste`; existing text install/usage docs remain accurate.
Enables slices 5–6 consumer setup.

Internal change: packaging/docs only; no new runtime behavior beyond what
slices 1–3 already expose.

### 5. Early probe — native image read on an available desktop
Type: Behavior
Status: planned
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

(none yet)

## Concern evidence

- Slice-plan refinement: **not needed** — slices are one cohesive contract
  model (absence / image / failure) plus bounded native probes; no competing
  independent outcome, no unmapped proof, no cumulative special-case design
  requiring a refinement pass within this outcome.
- Remaining slice-specific concerns: **none** beyond the early-probe-bounded
  native premise in the Decisive premises table (slices 5–6).

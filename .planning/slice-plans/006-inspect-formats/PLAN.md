# Plan: Inspect clipboard content kinds and offered formats

**Identity:** SEED-001#inspect-formats
**Source:** [Inspect clipboard content kinds and offered formats](../../seeds/SEED-001-clipboard-true-to-its-name.md#inspect-formats)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Python application and automation developers can learn what the current
clipboard **offer** contains — library-understood **kinds** among
`{text, image, html, files}` plus **native format identifiers** — through an
explicit non-mutating `inspect()` API: present offer → structured snapshot;
empty offer → empty kinds/formats snapshot; denied/unavailable access or
enumeration failure → `ClipboardContentError` (never a fabricated empty
success). Inspection does not replace, clear, or reserve the offer, and does
not claim every listed format can be decoded. Supported desktops: Windows
desktop; macOS Aqua; Linux X11 + helper that can list CLIPBOARD targets; Linux
Wayland + helper that can list offered MIME types on a named compositor. When
a session is unavailable during execution, that desktop records an explicit
evidence limit — never silent verified success. Text, image, and HTML callers
stay compatible; `clipboard[images]` is not required.

**Included:** public `inspect()` snapshot (kinds + native format ids);
injectable inspect backend for desktop-free tests; kind↔native mapping for
known text/image/html/file-list types while still listing undecodable native
ids; empty vs `ClipboardContentError` discipline; non-mutating enumeration
without payload fetches when the platform can list types; gated
independent-producer native probes; helper and snapshot/race docs; per-desktop
floors or honest evidence limits.

**Excluded:** public arbitrary-format binary read/write; wait/watch for offer
changes; a separate long-lived platform-capability probe API beyond distinct
access-failure outcomes; RTF as a first-class kind; promising portable native
format strings across OSes; overloading `paste`/`copy`; default CI desktop
matrix; WSL/SSH/containers as guaranteed desktops; implementing file
paste/copy (reporting `files` when native file-list formats appear is enough);
PRIMARY; bundling Qt / win32clipboard as required public stack; same-library
round-trip as sole native proof; `clipboard[images]` requirement for this
story.

## Assumptions

- Follow North Star explicit-API shape beside `copy`/`paste`; one
  empty / kinds+formats / failure model with platform enumerators.
- PFE: **reuse** delivered `ClipboardContentError`, injectable-backend + gated
  probe patterns from `set_html_clipboard_writer` / `set_image_grabclipboard`,
  and README evidence-limit wording; **gap** — no `inspect` yet; pyperclip
  exposes text `copy`/`paste` and `is_available` only (no format enumeration).
  Do not overload `ClipboardImageError`. Do not default to Qt / heavy toolkit
  stacks; evaluate only if a probe forces reconsideration.
- ADR store is undefined in this repo; no Accepted ADR constrains this plan.
- This preparation checkout is macOS (Darwin). Linux and Windows native
  sessions are owner-held / other-machine observations bounded by early probe
  slices; missing session yields an explicit evidence limit for that desktop.

## Outside-in proof

| Example | Observable signal |
| --- | --- |
| Independent producer HTML+text offer | `inspect()` reports kinds including `html` and `text` plus native HTML/text ids; later consumer still sees the offer; no payload-only probe when types enumerate |
| Image-only offer | kinds include `image`, not `text`/`html`; native image id(s) present |
| Empty clipboard | empty kinds/formats snapshot; not `ClipboardContentError` |
| Native file-list present (undecodable) | kinds include `files`; native file-list id(s) listed; no filesystem read |
| Missing helper / denied access | `ClipboardContentError`; not successful empty snapshot |
| Per-desktop session | Independent-producer inspect success + floors **or** explicit evidence limit |
| Regression | In-memory text + `paste_image` + `copy_html` (+ `paste_html` if present) tests pass; no `clipboard[images]` required for `inspect` |

Automated contract tests stay in-memory. Native examples use an independent
producer; same-library round-trips alone do not establish interoperability.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| `ClipboardContentError`, `copy_html`, `paste_image` delivered; no `inspect` yet | Contract + packaging reuse | `clipboard.VERSION == 0.0.5`; `ClipboardContentError`, `copy_html`, `paste_image` present; `inspect` / `paste_html` absent; `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_copy_html_contract.py tests/test_copy_html_seam.py -q` → 41 passed | Settled |
| Injectable seams exist to mirror for inspect | Structure slice for injectable inspect backend | `set_html_clipboard_writer`, `set_image_grabclipboard` in `clipboard.py` | Settled |
| pyperclip cannot enumerate clipboard formats / kinds | Must implement enumerators, not re-export pyperclip | pyperclip public surface: `copy`, `paste`, `is_available`, backend inits — no format/list API | Settled |
| This checkout can run macOS native pasteboard type-list probes | Slice 3 | `uname -s` → Darwin | Settled: macOS probe runnable here when authorized |
| This checkout can run Windows or Linux native format-list probes | Slices 4–6 | Darwin host; `xclip` / `wl-paste` / `wl-copy` not on `PATH` | Settled: **cannot** here; Linux/Windows are early probes on owner-held sessions |
| Independent producer can supply multi-kind / image / file-list offers on each target | Native Behavior slices | Owner-held desktop + browser/editor/file-manager + helpers / pasteboard | **Early probe** (slices 3–6); missing session → evidence limit for that desktop; probe failure stops dependent claims for that desktop |

## Ordered slices

### 1. Injectable `inspect` enumeration seam
Type: Structure
Status: done
Proof: Public `inspect` exists; default path and a `set_*` injection hook
allow tests to supply a fake enumerator without a desktop; failures raise
`ClipboardContentError` (not `ClipboardImageError`); `copy` / `paste` /
`paste_image` / `copy_html` import and in-memory tests still pass; calling
`inspect` does not require `clipboard[images]`.

Accepted proof (coordinator):
- `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_copy_html_contract.py tests/test_copy_html_seam.py tests/test_inspect_seam.py tests/test_copy_image_failures.py -q` → 64 passed, 1 skipped
- `nix develop -c uv run --locked pytest tests/test_inspect_seam.py::test_inspect_importable_without_images_extra tests/test_inspect_seam.py::test_inspect_public_surface tests/test_inspect_seam.py::test_default_inspect_raises_clipboard_content_error -q` → 3 passed
- `nix develop -c make check` → 80 passed, 6 skipped
- Public surface: `clipboard.inspect`, `set_clipboard_inspector`, `ClipboardOfferSnapshot`, `ClipboardKind` via package facade; default stub raises `ClipboardContentError`

Internal: Add the inspect entry point and injection hook beside existing
content APIs; no native enumeration required yet. Enables slice 2 contract
Behavior. Post-change refactor split oversize `clipboard.py` into package
modules along content seams (`_offer`, `_html`, `_image_*`, `_errors`).

### 2. In-memory `inspect` contract
Type: Behavior
Status: done
Proof: Desktop-free tests show: fake HTML+text offer → kinds include `html`
and `text` with native ids; image-only → `image` without `text`/`html`; empty
→ empty snapshot (not error); fake file-list native id → `files` kind without
filesystem access; access/helper/enumeration failure from the fake →
`ClipboardContentError` (not empty success); inspect does not mutate the fake
offer model; existing text, `paste_image`, and `copy_html` suites stay green.

Accepted proof (coordinator):
- `nix develop -c uv run --locked pytest tests/test_inspect_contract.py tests/test_inspect_seam.py -q` → 18 passed
- `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_copy_html_contract.py tests/test_copy_html_seam.py tests/test_inspect_seam.py tests/test_inspect_contract.py -q` → 59 passed
- Shared `kinds_from_native_formats` / `snapshot_from_native_formats` + `FakeOfferClipboard`

Behavior: Pre-condition: injectable seam from slice 1. Trigger: `inspect`
against fake offers covering mixed kinds, image-only, empty, undecodable
file-list, and backend failure. Postcondition: contract examples 1–5 and 7
hold without a real clipboard.

### 3. Early probe — macOS Aqua offer inspect
Type: Behavior
Status: done
Proof: On this Darwin checkout (or equivalent Aqua session), gated probe: an
**independent** producer offers HTML+text (and separately image-only when
feasible); `inspect()` reports matching kinds and native pasteboard type /
UTI identifiers; a later independent consumer still sees the offer
(non-mutation); floors (OS) recorded; README marks macOS inspect verified at
those floors. If Aqua inspect cannot be observed, record an explicit macOS
inspect evidence limit — never claim verified. Probe failure stops dependent
macOS inspect claims.

Accepted proof (coordinator):
- `CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked pytest tests/test_inspect_native_macos.py -v` → 1 passed
- Floors: macOS 26.6.2 / build 25G83 / Darwin 25.6.0 / arm64; HTML+text kinds `{html,text}`; image-only `{image}`; non-mutation observed
- Darwin default inspector enumerates via osascript/AppKit `types()` → `snapshot_from_native_formats`

Behavior: Pre-condition: contract from slice 2; Darwin session **or** evidence
limit path. Trigger: gated native independent-producer inspect. Postcondition:
examples 1–2 and 6 (macOS branch) or honest limit.

### 4. Early probe — Linux X11 + helper format list
Type: Behavior
Status: planned
Proof: On a usable X11 session with a helper that can list CLIPBOARD targets
(document the exact tool/flags, e.g. `xclip -o -t TARGETS`), gated probe:
independent producer → `inspect()` reports kinds + native MIME/target ids;
clipboard unchanged for a later consumer; deps/floors documented; README marks
X11 inspect verified. If no usable session or helper path exists, record an
explicit X11 inspect evidence limit — never claim verified. Probe failure
stops dependent X11 claims.

Behavior: Pre-condition: contract; owner-held X11+helper session **or**
evidence-limit path. Trigger: gated independent-producer inspect.
Postcondition: key example 1 (X11) / example 6 or honest limit.

### 5. Early probe — Linux Wayland + helper MIME list
Type: Behavior
Status: planned
Proof: On a usable Wayland session with `wl-paste -l` (or equivalent) on a
**named** compositor, same independent-producer kinds+MIME success and
non-mutation; document compositor and helper scope; README marks Wayland
inspect verified for that compositor only. Missing session or failed probe →
explicit Wayland evidence limit or stopped dependent claims — never silent
verified.

Behavior: Pre-condition: contract; owner-held Wayland+helper session **or**
evidence-limit path. Trigger: gated independent-producer inspect.
Postcondition: example 6 (Wayland branch) or honest limit.

### 6. Early probe — Windows desktop format enumeration
Type: Behavior
Status: planned
Proof: On a usable Windows desktop session, gated probe: independent producer
offers HTML+text (and image-only / file-list when feasible); `inspect()`
reports matching kinds and native Windows format names/ids; clipboard
unchanged afterward; floors recorded; README marks Windows inspect verified.
If no Windows session is available, record an explicit Windows inspect
evidence limit — never claim verified. Probe failure stops dependent Windows
claims.

Behavior: Pre-condition: contract; Windows session **or** evidence-limit path.
Trigger: gated independent-producer inspect. Postcondition: examples 1–4
(Windows) / example 6 or honest limit.

### 7. Docs and packaging alignment for inspect
Type: Behavior
Status: planned
Proof: README (and related install/evidence notes) document `inspect`, empty
vs `ClipboardContentError`, non-mutation, snapshot/race limits, kind↔native
mapping floors, Linux enumeration helpers, per-desktop verified floors or
evidence limits from slices 3–6, and that `clipboard[images]` is not required;
desktop-free suites stay green under locked pytest / `make check` as
applicable.

Behavior: Pre-condition: outcomes from slices 2–6. Trigger: docs + packaging
updates. Postcondition: callers can enable paste UIs from inspect without
guessing empty vs denied; evidence wording is honest.

## Current decisions

- Reuse North Star explicit-API shape and `ClipboardContentError`; implement
  platform enumerators (pyperclip cannot list formats).
- Public success means a **kinds + native format ids** snapshot; payload
  reads stay in separate content APIs.
- Never treat access failure as empty; never mutate the clipboard on inspect;
  never require payload fetches when type enumeration suffices.
- Library kinds are a fixed mapped vocabulary; unknown native ids still appear
  in the formats list.
- All four desktops may record evidence limits when no session exists; probe
  failure stops that desktop's verified claim.
- Prefer thin platform enumerators + documented helpers over Qt unless a probe
  forces reuse reconsideration.
- Independent producers required for native proof; same-library round-trips
  are regression-only.
- Do not require `clipboard[images]` for `inspect`; do not overload
  `ClipboardImageError`.

## Learnings

- Default inspect is an always-fail stub until desktop enumerators land;
  injection is the only green path for desktop-free tests (unlike Darwin-capable
  `copy_html`).
- Snapshot shape: frozen `ClipboardOfferSnapshot(kinds: frozenset[ClipboardKind], formats: tuple[str, ...])`.
- Post-slice-1 refactor: single-module `clipboard.py` exceeded the 250-line
  cohesion limit; library is now a `clipboard` package with explicit content
  seams. Public import path unchanged.
- Shared `kinds_from_native_formats` / `snapshot_from_native_formats` is the
  reusable bridge for slices 3–6 enumerators; contract fake proves kinds from
  the type list alone without payload fetch.
- macOS `types()` also returns legacy aliases (`Apple HTML pasteboard type`,
  `NSStringPboardType`); kinds map from known UTIs while aliases remain in
  `formats`.

## Concern evidence

- Slice-plan refinement: not needed — one coherent offer-inspect model, each
  Behavior owns one proof loop (contract or one desktop probe), Structure only
  precedes the contract Behavior, and native session premises are already
  bounded by authorized early probe slices.
- Remaining slice-specific concerns: none identified in this review.

# Plan: Read HTML fragments copied by desktop applications

**Identity:** SEED-001#read-html
**Source:** [Read HTML fragments copied by desktop applications](../../seeds/SEED-001-clipboard-true-to-its-name.md#read-html)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Python document and automation developers can recover the Unicode HTML
**fragment** of a selection copied by an independent browser or rich editor
through an explicit `paste_html()` API: HTML present → fragment string; no HTML
→ `None`; corrupt envelope / access / helper / transfer failure →
`ClipboardContentError`. The read never mutates the clipboard. Supported
desktops: Windows desktop; macOS Aqua; Linux X11 + `xclip` (or equivalent)
requesting `text/html`; Linux Wayland + `wl-paste` (or equivalent) on a named
compositor. When a session is unavailable during execution, that desktop
records an explicit evidence limit — never silent verified success. Text,
image, and delivered `copy_html` callers stay compatible.

**Included:** public `paste_html`; injectable read backend for desktop-free
tests; Windows `HTML Format` fragment extraction (UTF-8 byte offsets,
including non-ASCII); platform readers for macOS HTML pasteboard type and
Linux `text/html`; absence vs `ClipboardContentError` discipline; non-mutating
reads; gated independent-producer native probes; helper and envelope docs;
per-desktop floors or honest evidence limits.

**Excluded:** public structured return of context HTML / source URL (parse
internally only as needed); RTF / attributed-string conversion; synthesizing
HTML from plain text; overloading `paste`/`copy`; default CI desktop matrix;
WSL/SSH/containers as guaranteed desktops; files/inspection/clear/waits/
PRIMARY; bundling Qt / win32clipboard as required public stack; same-library
`copy_html` round-trip as sole native proof; `clipboard[images]` requirement
for this story.

## Assumptions

- Follow North Star explicit-API shape beside `copy`/`paste`; one
  absence / fragment / failure model with platform adapters.
- PFE: **reuse** delivered `ClipboardContentError`, `paste_image`
  absence-vs-failure discipline, injectable-backend + gated probe patterns
  from `set_html_clipboard_writer` / image seams, and README evidence-limit
  wording style; **gap** — no `paste_html` yet; pyperclip is text-only and
  does not decode HTML envelopes. Do not overload `ClipboardImageError`. Do
  not default to Qt / heavy toolkit stacks; evaluate only if a probe forces
  reconsideration. Delivered `copy_html` is regression / fake-producer only,
  not sole native proof.
- ADR store is undefined in this repo; no Accepted ADR constrains this plan.
- This preparation checkout is macOS (Darwin). Linux and Windows native
  sessions are owner-held / other-machine observations bounded by early probe
  slices; missing session yields an explicit evidence limit for that desktop.

## Outside-in proof

| Example | Observable signal |
| --- | --- |
| Independent producer HTML selection | `paste_html()` returns fragment markup; later independent consumer still sees the offer |
| Windows `HTML Format` non-ASCII | Returned string is fragment between offsets, not Version/StartHTML headers or unselected context alone |
| Text-only / empty / image-only / file-list | `paste_html()` → `None` |
| Corrupt / inconsistent HTML metadata | `ClipboardContentError`; clipboard unchanged; no fabricated fragment |
| Missing helper / denied access | `ClipboardContentError`; not silent `None` |
| Per-desktop session | Independent-producer success + floors **or** explicit evidence limit |
| Regression | In-memory text + `paste_image` + `copy_html` tests pass; no `clipboard[images]` required for `paste_html` |

Automated contract tests stay in-memory. Native examples use an independent
producer; same-library `copy_html` round-trips alone do not establish
interoperability.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| `copy_html` / `ClipboardContentError` delivered; no `paste_html` yet | Contract + packaging reuse | `clipboard.VERSION == 0.0.5`; `copy_html`, `ClipboardContentError`, `set_html_clipboard_writer` present; `paste_html` absent; `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_copy_html_contract.py tests/test_copy_html_seam.py -q` → 41 passed | Settled |
| Injectable HTML write seam exists to mirror for HTML read | Structure slice for injectable read backend | `set_html_clipboard_writer` in `clipboard.py` | Settled |
| pyperclip cannot read HTML envelopes / fragments | Must implement HTML readers, not re-export pyperclip | pyperclip public surface remains text `copy`/`paste`; product HTML write is separate | Settled |
| This checkout can run macOS native pasteboard HTML read probes | Slice 3 | `uname -s` → Darwin | Settled: macOS probe runnable here when authorized |
| This checkout can run Windows or Linux native HTML read probes | Slices 4–6 | Darwin host; `xclip` / `wl-paste` / `wl-copy` not on `PATH` | Settled: **cannot** here; Linux/Windows are early probes on owner-held sessions |
| Independent producer can supply HTML fragment on each target | Native Behavior slices | Owner-held desktop + browser/editor + helpers / pasteboard | **Early probe** (slices 3–6); missing session → evidence limit for that desktop; probe failure stops dependent claims for that desktop |

## Ordered slices

### 1. Injectable `paste_html` read seam
Type: Structure
Status: planned
Proof: Public `paste_html` exists; default path and a `set_*` injection hook
allow tests to supply a fake HTML reader without a desktop; failures raise
`ClipboardContentError` (not `ClipboardImageError`); `copy` / `paste` /
`paste_image` / `copy_html` import and in-memory tests still pass; calling
`paste_html` does not require `clipboard[images]`.

Internal: Add the read entry point and injection hook beside existing HTML
write APIs; no native read required yet. Enables slice 2 contract Behavior.

### 2. In-memory `paste_html` contract
Type: Behavior
Status: planned
Proof: Desktop-free tests show: fake HTML fragment offer → returns that
Unicode fragment; text-only / empty / non-HTML offers → `None`; fake Windows
`HTML Format` envelope (including non-ASCII) → fragment between offsets only;
corrupt/inconsistent envelope metadata → `ClipboardContentError` with **no**
clipboard mutation in the fake model; access/helper/transfer failure from the
fake → `ClipboardContentError` (not `None`); existing text, `paste_image`, and
`copy_html` suites stay green.

Behavior: Pre-condition: injectable read seam from slice 1. Trigger:
`paste_html` against fake offers covering absence, fragment, Windows envelope,
corrupt metadata, and backend failure. Postcondition: contract examples 2–5
and 7 hold without a real clipboard.

### 3. Early probe — macOS Aqua HTML read
Type: Behavior
Status: planned
Proof: On this Darwin checkout (or equivalent Aqua session), gated probe: an
**independent** producer (browser or rich editor / non-`clipboard` pasteboard
writer) offers HTML; `paste_html()` returns the selection fragment; a later
independent consumer still sees the offer (non-mutation); floors (OS) recorded;
README marks macOS HTML read verified at those floors. If Aqua HTML read
cannot be observed, record an explicit macOS HTML-read evidence limit — never
claim verified. Probe failure stops dependent macOS HTML-read claims.

Behavior: Pre-condition: contract from slice 2; Darwin session **or** evidence
limit path. Trigger: gated native independent-producer read. Postcondition:
examples 1 and 6 (macOS branch) or honest limit.

### 4. Early probe — Linux X11 + `xclip` HTML read
Type: Behavior
Status: planned
Proof: On a usable X11 session with a helper that can request `text/html`
(document the exact tool/flags), gated probe: independent producer →
`paste_html()` returns fragment; clipboard unchanged for a later consumer;
deps/floors documented; README marks X11 HTML read verified. If no usable
session or helper path exists, record an explicit X11 HTML-read evidence
limit — never claim verified. Probe failure stops dependent X11 claims.

Behavior: Pre-condition: contract; owner-held X11+helper session **or**
evidence-limit path. Trigger: gated independent-producer read. Postcondition:
key example 1 (X11) / example 6 or honest limit.

### 5. Early probe — Linux Wayland + `wl-paste` HTML read
Type: Behavior
Status: planned
Proof: On a usable Wayland session with `wl-paste` (or equivalent) on a
**named** compositor, same independent-producer fragment success and
non-mutation; document compositor and helper scope; README marks Wayland HTML
read verified for that compositor only. Missing session or failed probe →
explicit Wayland evidence limit or stopped dependent claims — never silent
verified.

Behavior: Pre-condition: contract; owner-held Wayland+helper session **or**
evidence-limit path. Trigger: gated independent-producer read. Postcondition:
example 6 (Wayland branch) or honest limit.

### 6. Early probe — Windows desktop HTML Format read
Type: Behavior
Status: planned
Proof: On a usable Windows desktop session, gated probe: independent producer
offers interoperable `HTML Format` (UTF-8 fragment/context byte offsets)
including a non-ASCII case; `paste_html()` returns the fragment only (not
headers/unselected context); clipboard unchanged afterward; floors recorded;
README marks Windows HTML read verified. If no Windows session is available,
record an explicit Windows HTML-read evidence limit — never claim verified.
Probe failure stops dependent Windows claims.

Behavior: Pre-condition: contract; Windows session **or** evidence-limit path.
Trigger: gated independent-producer read with non-ASCII envelope case.
Postcondition: examples 1–2 (Windows) / example 6 or honest limit.

### 7. Docs and packaging alignment for HTML read
Type: Behavior
Status: planned
Proof: README (and related install/evidence notes) document `paste_html`,
absence vs `ClipboardContentError`, non-mutation, Windows fragment-extraction
rule, Linux HTML-read helpers (`xclip` / `wl-paste`), per-desktop verified
floors or evidence limits from slices 3–6, and that `clipboard[images]` is not
required; desktop-free suites stay green under locked pytest / `make check`
as applicable.

Behavior: Pre-condition: outcomes from slices 2–6. Trigger: docs + packaging
updates. Postcondition: callers can install and use HTML read without guessing
envelopes/helpers; evidence wording is honest.

## Current decisions

- Reuse North Star explicit-API shape and `ClipboardContentError`; implement
  HTML readers (pyperclip cannot).
- Public success means the **fragment** string; envelope context/source
  metadata stays internal / deferred.
- Never synthesize HTML from plain text; never mutate the clipboard on read.
- All four desktops may record evidence limits when no session exists; probe
  failure stops that desktop's verified claim.
- Prefer thin platform readers + documented helpers over Qt unless a probe
  forces reuse reconsideration.
- Independent producers required for native proof; same-library `copy_html`
  round-trip is regression-only.
- Do not require `clipboard[images]` for `paste_html`; do not overload
  `ClipboardImageError`.

## Learnings

_(none yet)_

## Concern evidence

- Slice-plan refinement: not needed — one coherent fragment-read model, each
  Behavior owns one proof loop (contract or one desktop probe), Structure only
  precedes the contract Behavior, and native session premises are already
  bounded by authorized early probe slices.
- Remaining slice-specific concerns: none identified in this review.

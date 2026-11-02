# Plan: Read HTML fragments copied by desktop applications

**Identity:** SEED-001#read-html
**Source:** [Read HTML fragments copied by desktop applications](../../seeds/SEED-001-clipboard-true-to-its-name.md#read-html)
**Source review:** [source-review.md](source-review.md)
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
Status: done
Proof: Public `paste_html` exists; default path and a `set_*` injection hook
allow tests to supply a fake HTML reader without a desktop; failures raise
`ClipboardContentError` (not `ClipboardImageError`); `copy` / `paste` /
`paste_image` / `copy_html` import and in-memory tests still pass; calling
`paste_html` does not require `clipboard[images]`.

Internal: Add the read entry point and injection hook beside existing HTML
write APIs; no native read required yet. Enables slice 2 contract Behavior.

### 2. In-memory `paste_html` contract
Type: Behavior
Status: done
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
Status: done
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
Status: done
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
Status: done
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
Status: done
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
Status: done
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
- Developer decision (2026-11-02, slice 1 refactor stop): `clipboard.py`
  exceeded the 250-line refactor limit (510 lines); split it now into a
  `clipboard/` package with cohesive modules and an `__init__` re-exporting the
  unchanged public API, before slice 2 adds envelope decoding.
- Fragment-only `text/html` bodies (macOS `public.html`, Linux `text/html`)
  are returned as the producer offered them, including a browser's leading
  `<meta charset='utf-8'>` (story: "platforms that already offer
  fragment-only `text/html` return that body directly"); document this
  per-desktop envelope behavior in slice 7.

## Learnings

- Slice 1: `clipboard` is now a package. HTML read/write seams and
  `_call_content_backend` live in `clipboard/_html.py`; native HTML helpers in
  `clipboard/_html_native.py`; tests that patch the platform for HTML target
  `clipboard._html_native.sys` / `.subprocess`. Keep each module ≤ 250 lines
  (put envelope decoding in `_html.py` or a new `_html_*` module).
- Slice 1 accepted proof: `nix develop -c uv run --locked pytest
  tests/test_paste_html_seam.py tests/test_copy_html_seam.py
  tests/test_copy_html_contract.py -q` (33 passed); `nix develop -c make check`
  (82 passed, 6 skipped); `make build` and `make test-package` pass.
- Slice 2: reader contract — a reader returns `None` (no HTML) or a private
  offer from `clipboard/_html_envelope.py`: `_cf_html_offer(raw_bytes)` on
  Windows, `_fragment_offer(str | bytes)` on macOS/Linux. Native readers pass
  raw data through; decoding/extraction, trailing-NUL stripping, BOM UTF-16,
  and NUL/encoding refusal live in the envelope module. Empty HTML offer →
  `""` (coordinator decision: HTML offered ⇒ string; `None` only for absence).
  Tests reuse `tests/html_offer.py` (`build_cf_html`, `FakeClipboard`,
  `paste_unchanged`) and the `fake_html_clipboard` fixture.
- Slice 2 accepted proof: `nix develop -c uv run --locked pytest
  tests/test_paste_html_seam.py tests/test_paste_html_contract.py
  tests/test_paste_html_cf_html.py -q` (85 passed); `nix develop -c make
  check` (157 passed, 6 skipped).
- Slice 3: macOS reader `_macos_html_clipboard_reader` and the platform
  dispatch `_default_html_clipboard_reader` live in `clipboard/_html_native.py`
  (osascript JXA `dataForType("public.html")`, tagged `HTML:<base64>` /
  `NONE` / `UNREADABLE` stdout, 10s timeout, failures → `ClipboardContentError`).
  Tests that reach the default reader must force a non-target platform via
  `clipboard._html_native.sys`; rewrite
  `test_non_darwin_default_reader_is_not_available` as each platform lands.
  Real-browser producer without Accessibility: Chrome AppleScript
  `select all` + `copy selection` with `user-select:none` context.
- Slice 3 accepted proof: focused `nix develop -c uv run --locked pytest
  tests/test_paste_html_seam.py tests/test_paste_html_contract.py
  tests/test_paste_html_cf_html.py tests/test_paste_html_macos_reader.py
  tests/test_copy_html_seam.py tests/test_copy_html_contract.py -q` (121
  passed); native `CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked
  pytest tests/test_paste_html_native_macos.py -v` (1 passed: Chrome
  156.0.8078.74, macOS 26.6.2/25G83 arm64).
- Slice 4: X11 reader `_linux_x11_html_clipboard_reader` in
  `clipboard/_html_native_linux.py` (TARGETS then `text/html`; xclip
  "target TARGETS not available" ⇒ unowned ⇒ `None`; owner change between the
  two reads is a strict `ClipboardContentError`). Probes share
  `scripts/stdlib_png.py`. Native proof venue: gated CI job
  `native-linux-x11-paste-html` (Xvfb); delivered with `progress: true`, then
  marked done after observing the run.
- Slice 4 accepted proof: focused 5-file pytest (113 passed); `make check`
  (185 passed, 8 skipped); `make lint-workflows`; CI run 41422813085 job
  `native-linux-x11-paste-html` PASSED on e424146 (Ubuntu 26.04, xclip 0.13,
  Python 3.13.14).
- Slice 5: Wayland reader `_linux_wayland_html_clipboard_reader` in
  `clipboard/_html_native_linux.py` (`wl-paste --list-types`, then
  `--no-newline --type text/html`; exact stderr "Nothing is copied" / "No
  selection" ⇒ `None`, per wl-clipboard 2.0–2.3 source). Linux probes share
  `scripts/native_probe_paste_html.py`; Sway facts in
  `scripts/native_probe_wayland.py`. Native proof venue: gated CI job
  `native-linux-wayland-paste-html` (headless Sway), delivered with
  `progress: true`. Slice 6 must move the "not available" test cases off
  win32 (e.g. `sunos5`).
- Slice 5 accepted proof: focused 6-file pytest (131 passed); `make check`
  (203 passed, 9 skipped); `make lint-workflows`; CI run 41424913377 on
  a9539fa: `native-linux-wayland-paste-html` PASSED (Sway 1.11,
  wl-clipboard 2.2.1 printing "Nothing is copied" when empty) and
  `native-linux-x11-paste-html` PASSED again after the probe refactor.
- Slice 6: Windows reader in `clipboard/_html_native_windows.py` (ctypes
  only, `_win32_api()` seam, bounded `OpenClipboard` retry, read-only,
  returns `_cf_html_offer(raw)`). Coordinator decision: `StartHTML` may point
  into the header (PowerShell `Set-Clipboard -AsHtml` shape) because the
  fragment offsets still yield a trustworthy fragment; `StartFragment` must
  still be past the header. Native venue: gated CI job
  `native-windows-paste-html` on `windows-latest`, which skips (evidence
  limit) when the runner has no usable clipboard session. README.rst and
  ci.yml were already over 250 lines before this story; not split here.
- Slice 6 accepted proof: focused 7-file pytest (144 passed); `make check`
  (216 passed, 10 skipped); `make lint-workflows`; CI run 41427386442 on
  1796fc5: `native-windows-paste-html` PASSED with `verified: true`
  (`windows-latest` does have a usable clipboard session; Windows Server
  2025 10.0.26100, PowerShell 5.1.26100, CLR 4.0.30319.42000). .NET
  Framework `SetText(Html)` / `Set-Clipboard -AsHtml` write non-ASCII as
  ANSI, so those envelopes raise `ClipboardContentError` (correct refusal).
- Developer amendment (2026-11-02, recorded in SEED-001): helper producers
  count as native verification on X11, Wayland, and Windows when named and
  labelled not-a-browser; browser interop there stays unobserved. Source
  review replaced with a fresh review of the amended story.
- Slice 7 accepted proof: README `paste_html` usage, Installation helper
  list, per-desktop envelope behavior, and evidence wording; AGENTS.md names
  the HTML APIs. `make check` (216 passed, 10 skipped); `make build` (twine
  strict, rerun after refactor); `make test-package`; `make lint-workflows`.

## Concern evidence

- Slice-plan refinement: not needed — one coherent fragment-read model, each
  Behavior owns one proof loop (contract or one desktop probe), Structure only
  precedes the contract Behavior, and native session premises are already
  bounded by authorized early probe slices.
- Remaining slice-specific concerns: none identified in this review.

## Story obligations

### G1. Default reader raises on every desktop
Reported: slice 1 — "Default reader: on every platform, including Darwin, it raises `ClipboardContentError` saying there is no native HTML reader for this platform yet"
Story clause: "returns a Unicode HTML fragment string when the current clipboard offer includes an HTML representation"
Disposition: proved by slice 6: default readers for darwin/X11/Wayland/win32 in clipboard/_html_native.py::_default_html_clipboard_reader, observed natively by the macOS probe and CI runs 41422813085, 41424913377, 41427386442

### G2. Reader value returned without validation or envelope decoding
Reported: slice 1 — "The return type is unvalidated in this slice: a non-str, non-None value from the reader is returned as-is."
Story clause: "Extract the **fragment** from platform envelopes"
Disposition: proved by slice 2: clipboard/_html_envelope.py::_decode_html_offer; tests/test_paste_html_contract.py::test_unexpected_reader_value_is_contract_failure, test_malformed_offer_value_is_contract_failure

### G3. Native non-HTML offers distinguished only in the fake
Reported: slice 2 — "The fake can only express \"reader reports no HTML\". Telling HTML apart from image-only or file-list offers in real native type lists is left to slices 3–6."
Story clause: "Do not treat ordinary text, file-list, or image-only offers as HTML success"
Disposition: proved by slice 6: native text-only/image-only (and file-list on macOS) offers returned None in scripts/probe_macos_native_paste_html.py and CI native jobs native-linux-x11-paste-html, native-linux-wayland-paste-html, native-windows-paste-html

### G4. Linux X11 native producer is xclip, not a browser or rich editor
Reported: slice 4 — "The native producer is the helper xclip (`-t text/html -i`), not a browser or rich editor."
Story clause: "native proof uses an **independent producer** (browser or rich editor — not a same-library `copy_html` round-trip alone)"
Disposition: owner changed "an independent helper producer (for example `xclip`, `wl-copy`, or a PowerShell/.NET writer) counts as native verification on Linux X11, Linux Wayland, and Windows when the evidence names the helper and states that it is not a browser or rich editor"

# Plan: Copy HTML with a matching plain-text alternative

**Identity:** SEED-001#copy-html
**Source:** [Copy HTML with a matching plain-text alternative](../../seeds/SEED-001-clipboard-true-to-its-name.md#copy-html)
**Source review:** [source-review.md](./source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Python report authors can hand a Unicode HTML fragment and an explicit
matching plain-text alternative through an explicit `copy_html(html, text)`
API so that, after the writing process exits, an independent rich editor
pastes formatting and a text-only destination pastes the alternative from the
**same** clipboard offer. Supported desktops: Windows desktop; macOS Aqua;
Linux X11 with a multi-type-capable helper; Linux Wayland with a multi-type-
capable helper on a named compositor. When a session is unavailable during
execution, that desktop records an explicit evidence limit — never silent
verified success. Text callers and delivered image APIs stay compatible.

**Included:** public `copy_html`; injectable write backend for desktop-free
tests; fail-before-replace; refusal of partial single-format "success";
dedicated HTML/content error type (not `ClipboardImageError`); platform
writers publishing interoperable HTML envelopes plus plain text together
(Windows `HTML Format` UTF-8 fragment/context offsets for non-ASCII); gated
independent dual-consumer native probes (including writer-exit); helper and
envelope docs; per-desktop floors or honest evidence limits.

**Excluded:** auto HTML-to-text; HTML read (`SEED-001#read-html`); RTF;
overloading `copy`/`paste`; default CI desktop matrix; WSL/SSH/containers as
guaranteed desktops; images/files/inspection/clear/waits/PRIMARY; bundling Qt /
win32clipboard as required public stack; same-library round-trip as sole
native proof; sequential text-then-HTML writes as fulfilling dual offer;
`clipboard[images]` requirement for this story.

## Assumptions

- Follow North Star explicit-API shape beside `copy`/`paste`; dual
  representation is one coherent offer model with platform adapters.
- PFE: reuse injectable-backend test pattern, gated probe script style, and
  fail-before-replace / absence-vs-failure discipline from delivered
  `paste_image` (and planned `copy_image`); **gap** — pyperclip 1.11.0 is
  text-only (no HTML/MIME multi-offer API); this product has no HTML writer
  yet. Do not overload `ClipboardImageError`. Do not default to Qt / heavy
  toolkit stacks; evaluate only if a probe forces reconsideration.
- ADR store is undefined in this repo; no Accepted ADR constrains this plan.
- This preparation checkout is macOS (Darwin). Linux and Windows native
  sessions are owner-held / other-machine observations bounded by early probe
  slices; missing session yields an explicit evidence limit for that desktop
  (unlike `SEED-001#write-images` Linux-mandatory issue #5 floor).

## Outside-in proof

| Example | Observable signal |
| --- | --- |
| Dual offer after writer exit | Independent rich editor pastes formatting; text editor pastes alternative; neither alone replaced the other |
| Windows non-ASCII `HTML Format` | Fragment/context offsets yield correct Unicode fragment; text alternative pastes correctly |
| Replace prior content | After successful `copy_html`, superseded sole text/image offer is not the only remaining content |
| Invalid args | Actionable error before replace; prior offer intact |
| Cannot offer both types together | Actionable failure; no silent text-only success |
| Missing helper / denied access | Actionable error; no silent success |
| Per-desktop session | Dual-consumer + writer-exit success + floors **or** explicit evidence limit |
| Regression | In-memory text + `paste_image` tests pass; image APIs unchanged |

Automated contract tests stay in-memory. Native examples use independent rich
and plain-text consumers; same-library HTML round-trips alone do not establish
interoperability.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| Public surface is text + `paste_image`; no `copy_html` yet | Contract + packaging | `clipboard.VERSION == 0.0.5`; attrs include `copy`, `paste`, `paste_image`, `ClipboardImageError`, `set_image_grabclipboard`; `copy_html` absent; `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py -q` → 18 passed | Settled |
| pyperclip cannot publish HTML + plain text as one offer | Must implement multi-rep writers, not re-export pyperclip | pyperclip 1.11.0 public API is text `copy`/`paste` + backends; no MIME/HTML multi-offer helpers in module surface | Settled |
| Injectable grabclipboard pattern exists to mirror for HTML write | Structure slice for injectable write backend | `set_image_grabclipboard` in `clipboard.py` | Settled |
| README documents Linux **read** helpers; HTML write needs multi-type offer docs | Docs in native / docs slices | README Installation lists X11 `xclip`, Wayland `wl-paste` only; no HTML copy API | Settled: write docs must name multi-type HTML+text offer helpers |
| This checkout can run macOS native pasteboard HTML write probes | Slice 3 | `uname -s` → Darwin | Settled: macOS probe runnable here when authorized |
| This checkout can run Windows or Linux native clipboard HTML write probes | Slices 4–6 | Darwin host; `wl-copy`/`xclip` not found here | Settled: **cannot** here; Linux/Windows are early probes on owner-held sessions |
| Independent rich + text consumers can paste both after writer exit on each target | Native Behavior slices | Owner-held desktop + multi-type helpers / pasteboard | **Early probe** (slices 3–6); missing session → evidence limit for that desktop; probe failure stops dependent claims for that desktop |

## Ordered slices

### 1. Injectable `copy_html` write seam
Type: Structure
Status: done
Proof: Public `copy_html` exists; dedicated HTML/content error type is
importable and distinct from `ClipboardImageError`; default path and a
`set_*` injection hook allow tests to supply a fake dual-offer writer without
a desktop; `copy` / `paste` / `paste_image` import and in-memory tests still
pass; no `clipboard[images]` requirement for calling `copy_html`.

Internal: Add the write entry point, error type, and injection hook beside
existing APIs; no native publication required yet. Enables slice 2 contract
Behavior.

### 2. In-memory `copy_html` contract
Type: Behavior
Status: done
Proof: Desktop-free tests show: valid HTML + text → fake backend receives
**both** representations in one update; invalid args → error with **no**
backend replace call (prior fake offer unchanged); backend that can offer only
one type → error (no partial success); backend failure → error; successful
write replaces prior sole text/image entries in the fake offer model with the
dual offer; existing text and `paste_image` suites stay green.

Behavior: Pre-condition: injectable write seam from slice 1. Trigger:
`copy_html` with valid / invalid / single-type-only / failing-backend inputs
against the fake. Postcondition: contract examples 3–5 and 8 hold without a
real clipboard.

### 3. Early probe — macOS Aqua HTML + text write
Type: Behavior
Status: done
Proof: On this Darwin checkout (or equivalent Aqua session), gated probe:
`copy_html` publishes a known Unicode fragment + alternative; writing process
exits; an **independent** rich consumer recovers formatting and an independent
text consumer recovers the alternative (non-`clipboard` paths); floors (OS)
recorded; README marks macOS HTML write verified at those floors. If Aqua
dual offer cannot be observed, record an explicit macOS HTML-write evidence
limit — never claim verified. Probe failure stops dependent macOS HTML-write
claims.

Behavior: Pre-condition: contract from slice 2; Darwin session **or** evidence
limit path. Trigger: gated native write + independent dual consumers after
exit. Postcondition: example 7 (macOS branch) or honest limit.

### 4. Early probe — Linux X11 multi-type HTML + text write
Type: Behavior
Status: done
Proof: On a usable X11 session with a helper that can offer HTML and plain
text together (document the exact tool/flags), gated probe: `copy_html` →
writer exits → independent rich and text consumers paste correctly; deps/floors
documented; README marks X11 HTML write verified. If no usable session or
multi-type helper path exists, record an explicit X11 HTML-write evidence
limit — never claim verified. Probe failure stops dependent X11 claims.

Behavior: Pre-condition: contract; owner-held X11+multi-type helper session
**or** evidence-limit path. Trigger: gated write + independent dual consumers
after exit. Postcondition: key example 1 (X11) or honest limit.

### 5. Early probe — Linux Wayland multi-type HTML + text write
Type: Behavior
Status: done
Proof: On a usable Wayland session with a multi-type-capable helper on a
**named** compositor, same writer-exit independent dual-consumer success;
document compositor and helper scope; README marks Wayland HTML write verified
for that compositor only. One-type-only helper paths must not be treated as
success. Missing session or failed probe → explicit Wayland evidence limit or
stopped dependent claims — never silent verified.

Behavior: Pre-condition: contract; owner-held Wayland+multi-type helper
session **or** evidence-limit path. Trigger: gated write + independent dual
consumers after exit. Postcondition: example 7 (Wayland branch) or honest
limit.

### 6. Early probe — Windows desktop HTML Format + Unicode text
Type: Behavior
Status: done
Proof: On a usable Windows desktop session, gated probe publishes
interoperable `HTML Format` (UTF-8 fragment/context byte offsets) plus Unicode
text; non-ASCII fragment/context case included; writer exits; independent rich
and text consumers paste correctly; floors recorded; README marks Windows HTML
write verified. If no Windows session is available, record an explicit Windows
HTML-write evidence limit — never claim verified. Probe failure stops
dependent Windows claims.

Behavior: Pre-condition: contract; Windows session **or** evidence-limit path.
Trigger: gated write + independent dual consumers after exit. Postcondition:
examples 1–2 (Windows) / example 7 or honest limit.

### 7. Docs and packaging alignment for HTML write
Type: Behavior
Status: done
Proof: README (and related install/evidence notes) document `copy_html`, the
HTML error type, dual-offer contract, Windows `HTML Format` / non-ASCII note,
Linux multi-type helper requirements, fail/error model, and per-desktop
verified floors or evidence limits from slices 3–6; DD-001 extras checklist
only if new optional deps enter pytest (this story expects none by default);
`make check` / locked pytest stay green for desktop-free suites.

Behavior: Pre-condition: outcomes from slices 2–6. Trigger: docs + packaging
updates. Postcondition: callers can install and use HTML write without guessing
envelopes/helpers; evidence wording is honest.

## Current decisions

- Reuse North Star explicit-API shape; implement multi-rep writers (pyperclip
  cannot).
- Dual HTML+text publication is required for success; partial single-format
  offers fail.
- All four desktops may record evidence limits when no session exists; probe
  failure stops that desktop's verified claim.
- Prefer thin platform writers + documented multi-type helpers over Qt unless
  a probe forces reuse reconsideration.
- Independent dual consumers required for native proof; same-library round-
  trip is regression-only.
- Do not require `clipboard[images]` for `copy_html`; do not overload
  `ClipboardImageError`.

## Learnings

- Slice 1: Public seam uses `ClipboardContentError`, `copy_html(html, text)`,
  and `set_html_clipboard_writer` mirroring `set_image_grabclipboard`. Default
  stub fails with `ClipboardContentError` until a writer is injected; no
  `clipboard[images]` / Pillow requirement. Native dual-offer writers remain
  for later slices.
- Accepted proof (slice 1): `nix develop -c uv run --locked pytest
  tests/test_clipboard.py tests/test_copy_html_seam.py -q` (10 passed);
  `nix develop -c uv run --locked --extra images pytest
  tests/test_paste_image.py tests/test_paste_image_failures.py -q` (13 passed);
  no-images import smoke for the new surface.
- Slice 2: `copy_html` validates args before the writer; empty/whitespace HTML
  and empty text are invalid; writer transfer failures wrap to
  `ClipboardContentError`; injectable one-type / partial writers must raise
  rather than return success after a partial offer.
- Accepted proof (slice 2): `nix develop -c uv run --locked pytest
  tests/test_copy_html_seam.py tests/test_copy_html_contract.py
  tests/test_clipboard.py -q` (25 passed); images paste suites (13 passed);
  after test-fake refactor, `tests/test_copy_html_contract.py` (15 passed).
- Slice 3: Darwin default writer publishes NSPasteboard HTML+string via
  osascript/AppKit; gated `scripts/probe_macos_native_copy_html.py` proves
  independent AppKit HTML + `pbpaste` consumers after writer-process exit.
  Floors: macOS 26.6.2 / 25G83 / arm64. README marks macOS HTML write verified;
  Win/Linux HTML write remain unverified.
- Accepted proof (slice 3): probe JSON `ok: true` /
  `writer_exited_before_consume: true`; contract+seam after refactor 23 passed;
  `CLIPBOARD_NATIVE_PROBE=1` native test passed; paste_image suites reused.
- Slice 4: No usable X11 + multi-type helper on this Darwin host → explicit
  X11 HTML-write evidence limit in README; gated
  `scripts/probe_linux_x11_native_copy_html.py` exits with `verified: false`.
  Non-Darwin default error names multi-type helper expectations.
- Accepted proof (slice 4): contract+seam 23 passed; X11 probe exit 2 /
  evidence_limit; paste_image suites reused.
- Slice 5: No Wayland session/helper → explicit Wayland HTML-write evidence
  limit; compositor non-generalization stated; gated
  `scripts/probe_linux_wayland_native_copy_html.py` refuses verified.
- Accepted proof (slice 5): Wayland probe exit 2 / evidence_limit /
  compositor_generalization false.
- Slice 6: No Windows desktop session → explicit Windows HTML Format +
  Unicode text evidence limit; non-ASCII offset case required for future
  verification; gated `scripts/probe_windows_native_copy_html.py`.
- Accepted proof (slice 6): Windows probe exit 2 / evidence_limit /
  verified false / non_ascii_case_required_for_verification true.
- Slice 7: README documents dual-offer contract, fail-before-replace,
  ClipboardContentError, multi-type Linux helpers, Windows HTML Format note,
  per-desktop floors/limits; no new optional extras (DD-001 N/A).
- Accepted proof (slice 7): `nix develop -c make check` → 48 passed, 2 skipped.

## Concern evidence

- Slice-plan refinement: not needed — Behavior/Structure split is one dual-
  offer write contract plus per-desktop proof loops; cumulative rule is a
  single `copy_html` offer model with platform adapters; native sessions are
  authorized early probes, not unscoped concerns.
- Remaining slice-specific concerns: none beyond the authorized early probes
  in slices 3–6 (owner-held native sessions; absence → evidence limit per
  desktop rather than silent success).

## Story obligations

### X11. No HTML-to-text synthesis
Reported: slice 1 — "Do not synthesize the plain-text alternative from HTML inside this story."
Story clause: "Do not synthesize the plain-text alternative from HTML inside this story."
Disposition: excluded "Do not synthesize the plain-text alternative from HTML inside this story."
Commitment: 11, Q6

### Q1. Non-desktop environments not guaranteed
Reported: slice 1 — "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Story clause: "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Disposition: excluded "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Commitment: Q1

### X2. Sequential writes are not dual success
Reported: slice 1 — "Do not treat two sequential text (or text-then-HTML) writes as fulfilling this story."
Story clause: "Do not treat two sequential text (or text-then-HTML) writes as fulfilling this story."
Disposition: excluded "Do not treat two sequential text (or text-then-HTML) writes as fulfilling this story."
Commitment: X2

### X10. Sequential single-format dual-success claim forbidden
Reported: slice 1 — "Sequential single-format writes claiming dual success are forbidden."
Story clause: "Sequential single-format writes claiming dual success are forbidden."
Disposition: excluded "Sequential single-format writes claiming dual success are forbidden."
Commitment: X10

### X3. No authorization bypass
Reported: slice 1 — "Do not bypass OS pasteboard / clipboard authorization."
Story clause: "Do not bypass OS pasteboard / clipboard authorization."
Disposition: excluded "Do not bypass OS pasteboard / clipboard authorization."
Commitment: X3

### X4. No single-representation success claim
Reported: slice 1 — "Do not leave only one of the two promised representations after claiming success."
Story clause: "Do not leave only one of the two promised representations after claiming success."
Disposition: excluded "Do not leave only one of the two promised representations after claiming success."
Commitment: X4

### X8. Partial offer must not present as success
Reported: slice 1 — "A call that cannot publish HTML and plain text together must not replace current content with a partial offer presented as success"
Story clause: "A call that cannot publish HTML and plain text together must not replace current content with a partial offer presented as success"
Disposition: excluded "A call that cannot publish HTML and plain text together must not replace current content with a partial offer presented as success"
Commitment: X8

### X5. No indefinite hang serving clipboard data
Reported: slice 1 — "Do not hang the caller indefinitely waiting to serve clipboard data."
Story clause: "Do not hang the caller indefinitely waiting to serve clipboard data."
Disposition: excluded "Do not hang the caller indefinitely waiting to serve clipboard data."
Commitment: X5

### X6. No markup execution / remote fetch / pixel-identical layout promise
Reported: slice 1 — "Do not execute markup, fetch remote resources, or promise pixel-identical layout across applications."
Story clause: "Do not execute markup, fetch remote resources, or promise pixel-identical layout across applications."
Disposition: excluded "Do not execute markup, fetch remote resources, or promise pixel-identical layout across applications."
Commitment: X6

### X7.1. Deferred automatic HTML-to-text
Reported: slice 1 — "Automatic HTML-to-text conversion"
Story clause: "Automatic HTML-to-text conversion"
Disposition: excluded "Automatic HTML-to-text conversion"
Commitment: X7.1

### X7.2. Deferred HTML read
Reported: slice 1 — "reading HTML (`SEED-001#read-html`)"
Story clause: "reading HTML (`SEED-001#read-html`)"
Disposition: excluded "reading HTML (`SEED-001#read-html`)"
Commitment: X7.2

### X7.3. Deferred RTF / other rich formats
Reported: slice 1 — "RTF or other rich formats"
Story clause: "RTF or other rich formats"
Disposition: excluded "RTF or other rich formats"
Commitment: X7.3

### X7.4. Deferred full HTML documents contract
Reported: slice 1 — "full HTML documents as a distinct contract from fragments"
Story clause: "full HTML documents as a distinct contract from fragments"
Disposition: excluded "full HTML documents as a distinct contract from fragments"
Commitment: X7.4

### X7.5. Deferred embedded resource packaging
Reported: slice 1 — "embedded resource packaging"
Story clause: "embedded resource packaging"
Disposition: excluded "embedded resource packaging"
Commitment: X7.5

### X7.6. Deferred bundling GUI toolkits / win32clipboard
Reported: slice 1 — "bundling GUI toolkits or `win32clipboard` as a required public dependency"
Story clause: "bundling GUI toolkits or `win32clipboard` as a required public dependency"
Disposition: excluded "bundling GUI toolkits or `win32clipboard` as a required public dependency"
Commitment: X7.6

### X7.7. Deferred default pytest/CI real desktop
Reported: slice 1 — "making default pytest / CI require a real desktop"
Story clause: "making default pytest / CI require a real desktop"
Disposition: excluded "making default pytest / CI require a real desktop"
Commitment: X7.7

### X7.8. Deferred expanding beyond four-desktop set
Reported: slice 1 — "expanding beyond the four-desktop set"
Story clause: "expanding beyond the four-desktop set"
Disposition: excluded "expanding beyond the four-desktop set"
Commitment: X7.8

### X7.9. Deferred rollback/atomicity beyond fail-before-replace
Reported: slice 1 — "inventing rollback/atomicity guarantees beyond fail-before-replace"
Story clause: "inventing rollback/atomicity guarantees beyond fail-before-replace"
Disposition: excluded "inventing rollback/atomicity guarantees beyond fail-before-replace"
Commitment: X7.9

### X7.10. Deferred same-library round-trip as sole native proof
Reported: slice 1 — "same- library HTML round-trip as sole native proof"
Story clause: "same- library HTML round-trip as sole native proof"
Disposition: excluded "same- library HTML round-trip as sole native proof"
Commitment: X7.10

### X9. Silent success on unproved desktop forbidden
Reported: slice 1 — "Silent success on an unproved desktop is forbidden."
Story clause: "Silent success on an unproved desktop is forbidden."
Disposition: excluded "Silent success on an unproved desktop is forbidden."
Commitment: X9

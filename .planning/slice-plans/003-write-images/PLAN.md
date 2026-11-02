# Plan: Copy Python images into desktop applications

**Identity:** SEED-001#write-images
**Source:** [Copy Python images into desktop applications](../../seeds/SEED-001-clipboard-true-to-its-name.md#write-images)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Python report and image-tool authors can hand a generated static raster to an
ordinary desktop application through an explicit `copy_image(Image)` API under
`clipboard[images]`, without a temporary-file import workflow. After the writing
process exits, an independent image or document application pastes recognizable
pixels (dimensions, opaque colors; alpha preserved or documented drop) on each
desktop this story claims. Linux X11 + `xclip` and Linux Wayland + `wl-copy`
writer-exit success are acceptance requirements (issue #5). Windows and macOS
get the same proof when a session is available, or an explicit evidence limit
when not. Text callers and delivered `paste_image` stay compatible.

**Included:** public `copy_image`; injectable write backend for desktop-free
tests; fail-before-replace and stale text/image clearing on success;
`ClipboardImageError` / `ImportError` contracts; platform writers publishing
interoperable native image offers; gated independent-consumer native probes
(including writer-exit); Linux helper docs (`xclip`, `wl-copy`); per-desktop
floors or honest Win/macOS evidence limits.

**Excluded:** path/bytes overloads; animation / screenshot / file-list offers;
overloading `copy`/`paste`; default CI desktop matrix; WSL/SSH/containers as
guaranteed desktops; HTML/files/inspection/clear/waits/PRIMARY; bundling Qt /
pywin32 / win32clipboard as required public stack; same-library `paste_image`
round-trip as sole native proof; Linux completion via evidence-limit alone.

## Assumptions

- Follow North Star explicit-API + `clipboard[images]` shape; extend
  `ClipboardImageError` to write failures without changing text APIs.
- PFE: reuse delivered `paste_image` packaging, error type, injectable-backend
  test pattern, and gated probe script style; **gap** — Pillow `ImageGrab`
  is read-only (`grabclipboard` only); write needs platform-native publication
  (helpers on Linux). Do not default to pyperclipimg/Qt; evaluate only if a
  probe forces reconsideration.
- ADR store is undefined in this repo; no Accepted ADR constrains this plan.
- This preparation checkout is macOS (Darwin). Linux and Windows native
  sessions are owner-held / other-machine observations bounded by early probe
  slices; missing Linux session cannot close those slices with an evidence
  limit — probe failure or absence stops dependent Linux claims and revises
  the plan. Missing Win/macOS session may yield an explicit evidence limit.

## Outside-in proof

| Example | Observable signal |
| --- | --- |
| Linux X11 + `xclip` writer-exit | Independent consumer pastes matching opaque size/colors after process exit; floors + deps documented |
| Linux Wayland + `wl-copy` (named compositor) | Same after exit; success scoped to that compositor |
| RGBA alpha | Consumer pastes transparency **or** docs record explicit drop for that desktop |
| Replace prior text/image | After successful `copy_image`, superseded representation is not recovered by a later paste of that kind |
| Invalid Image | `ClipboardImageError` before replace; prior offer intact |
| Missing helper / denied access | `ClipboardImageError`; no silent success |
| Windows / macOS session | Independent-consumer + writer-exit success + floors **or** explicit evidence limit (never silent verified) |
| Regression | In-memory text + `paste_image` tests pass; `copy_image` without extra → `ImportError` |

Automated contract tests stay in-memory. Native examples use an independent
consumer; `paste_image` round-trips alone do not establish interoperability.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| `paste_image` / `clipboard[images]` / `ClipboardImageError` delivered; no `copy_image` yet | Contract + packaging reuse | `clipboard.VERSION == 0.0.5`; `paste_image` present; `copy_image` absent; `nix develop -c uv run --locked --extra images pytest tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_clipboard.py -q` → 18 passed | Settled |
| Pillow `ImageGrab` has no clipboard write API | Must implement writers, not call ImageGrab write | `dir(ImageGrab)` clip/write/set attrs → only `grabclipboard`; Context7/docs: grabclipboard is read-only | Settled |
| Injectable grabclipboard pattern exists to mirror for write | Structure slice for injectable write backend | `set_image_grabclipboard` in `clipboard.py` | Settled |
| README documents Linux **read** helpers (`xclip`, `wl-paste`); write needs `wl-copy` | Docs in native slices | README Installation lists X11 `xclip`, Wayland `wl-paste` only | Settled: write docs must add `wl-copy` |
| This checkout can run macOS native pasteboard write probes | Slice 3 | `uname -s` → Darwin | Settled: macOS probe runnable here when authorized |
| This checkout can run Windows or Linux native clipboard write probes | Slices 4–6 | Darwin host | Settled: **cannot** here; Linux/Windows are early probes on owner-held sessions |
| Independent consumer can paste after writer exit on each target | Native Behavior slices | Owner-held desktop + helper / pasteboard | **Early probe** (slices 3–6); Linux failure/absence stops Linux acceptance; Win/macOS may record evidence limit |

## Ordered slices

### 1. Injectable `copy_image` write seam
Type: Structure
Status: planned
Proof: Public `copy_image` exists under `clipboard[images]`; default path and
`set_image_*` injection (name aligned with existing grabclipboard seam) allow
tests to supply a fake writer without a desktop; `copy` / `paste` /
`paste_image` import and in-memory tests still pass; without the extra,
`copy_image` raises `ImportError`.

Internal: Add the write entry point and injection hook beside the read path;
no native publication required yet. Enables slice 2 contract Behavior.

### 2. In-memory `copy_image` contract
Type: Behavior
Status: planned
Proof: Desktop-free tests show: valid Pillow Image → fake backend receives a
transferable RGB/RGBA raster; invalid/unloadable Image → `ClipboardImageError`
with **no** backend replace call (prior fake offer unchanged); backend failure →
`ClipboardImageError`; successful write clears prior text/image entries in the
fake offer model; existing text and `paste_image` suites stay green.

Behavior: Pre-condition: injectable write seam from slice 1. Trigger:
`copy_image` with valid / invalid / failing-backend inputs against the fake.
Postcondition: contract examples 4–6 and 8 hold without a real clipboard.

### 3. Early probe — macOS Aqua image write
Type: Behavior
Status: planned
Proof: On this Darwin checkout (or equivalent Aqua session), gated probe:
`copy_image` publishes a known opaque PNG; writing process exits; an
**independent** consumer (e.g. osascript / Preview / grab of pasteboard by a
non-`clipboard` path) recovers matching size/colors; RGBA case records
preserve or documented drop; floors (OS, Pillow) recorded; README marks macOS
write verified at those floors. If Aqua write cannot be observed, record an
explicit macOS write evidence limit — never claim verified. Probe failure stops
dependent macOS write claims.

Behavior: Pre-condition: contract from slice 2; Darwin session **or** evidence
limit path. Trigger: gated native write + independent consumer after exit.
Postcondition: example 7 (macOS branch) or honest limit.

### 4. Early probe — Linux X11 + `xclip` image write
Type: Behavior
Status: planned
Proof: On a usable X11 session with `xclip`, gated probe: `copy_image` →
writer exits → independent image/document app (or non-library consumer)
pastes matching opaque size/colors; alpha case recorded; deps/floors
documented; README marks X11 write verified. **No evidence-limit substitute
for story acceptance** — missing session or failed probe stops Linux X11
acceptance and revises the plan; do not mark issue #5 satisfied without this
or slice 5 both succeeding on their paths.

Behavior: Pre-condition: contract; owner-held X11+`xclip` session. Trigger:
gated write + independent consumer after exit. Postcondition: key example 1.

### 5. Early probe — Linux Wayland + `wl-copy` image write
Type: Behavior
Status: planned
Proof: On a usable Wayland session with `wl-copy` on a **named** compositor,
same writer-exit independent-consumer success; document compositor scope;
README marks Wayland write verified for that compositor only. Missing session
or failed probe stops Wayland acceptance (not an evidence-limit completion).

Behavior: Pre-condition: contract; owner-held Wayland+`wl-copy` session.
Trigger: gated write + independent consumer after exit. Postcondition: key
example 2.

### 6. Early probe — Windows desktop image write
Type: Behavior
Status: planned
Proof: On a usable Windows desktop session, gated probe with independent
consumer after writer exit; native interoperable formats (not arbitrary labeled
PNG bytes alone); floors recorded; README marks Windows write verified. If no
Windows session is available, record an explicit Windows write evidence limit
— never claim verified. Probe failure stops dependent Windows claims.

Behavior: Pre-condition: contract; Windows session **or** evidence-limit path.
Trigger: gated write + independent consumer after exit. Postcondition: example
7 (Windows branch) or honest limit.

### 7. Docs and packaging alignment for image write
Type: Behavior
Status: planned
Proof: README (and related install/evidence notes) document `copy_image`,
`clipboard[images]`, Linux write helpers (`xclip`, `wl-copy`), fail/error
model, and per-desktop verified floors or Win/macOS limits from slices 3–6;
CI/Makefile extras checklist respected if new write tests need the images
extra (DearDough DD-001); `make check` / locked pytest with extras stay green
for desktop-free suites.

Behavior: Pre-condition: outcomes from slices 2–6. Trigger: docs + packaging
updates. Postcondition: callers can install and use write without guessing
helpers; evidence wording is honest.

## Current decisions

- Reuse North Star explicit-API shape; implement write (ImageGrab cannot).
- Linux X11 and Wayland writer-exit proofs are mandatory acceptance; Win/macOS
  may evidence-limit when no session exists.
- Prefer thin platform writers + documented helpers over Qt/pyperclipimg unless
  a probe forces reuse reconsideration.
- Independent consumer required for native proof; `paste_image` round-trip is
  regression-only.

## Learnings

_(none yet)_

## Concern evidence

- Slice-plan refinement: not needed — Behavior/Structure split is one write
  contract plus per-desktop proof loops; cumulative rule is a single
  `copy_image` offer model with platform adapters; Linux mandatory probes are
  authorized early probes, not unscoped concerns.
- Remaining slice-specific concerns: none beyond the authorized early probes
  in slices 3–6 (owner-held native sessions; Linux absence blocks acceptance
  rather than silently succeeding).

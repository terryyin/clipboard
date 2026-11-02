# Plan: Copy Python images into desktop applications

**Identity:** SEED-001#write-images
**Source:** [Copy Python images into desktop applications](../../seeds/SEED-001-clipboard-true-to-its-name.md#write-images)
**Source review:** [source-review.md](source-review.md)
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
- This preparation checkout is macOS (Darwin). Linux writer-exit proof is
  obtained via **gated GitHub Actions** jobs (not owner-held desktop sessions
  and not default pytest): X11 + `xclip` under Xvfb; Wayland + `wl-copy` under
  a **named** CI compositor. Floors must name that CI environment honestly —
  headless CI is still not a product “guaranteed desktop,” but those jobs are
  the authorized observation venue for issue #5. Failed CI probes stop Linux
  acceptance (no evidence-limit substitute). Missing Win/macOS session may
  yield an explicit evidence limit.

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
| This checkout can run Windows or Linux native clipboard write probes | Slices 4–6 | Darwin host | Settled: **cannot** locally; Linux proof venue revised to gated GHA (Xvfb/`xclip`, named Wayland compositor); Windows still session or evidence limit |
| Independent consumer can paste after writer exit on each target | Native Behavior slices | macOS local; Linux via GHA; Windows session or limit | **Early probe** (slices 3–6); Linux CI probe failure stops Linux acceptance; Win/macOS may record evidence limit |

## Ordered slices

### 1. Injectable `copy_image` write seam
Type: Structure
Status: done
Proof: Public `copy_image` exists under `clipboard[images]`; default path and
`set_image_*` injection (name aligned with existing grabclipboard seam) allow
tests to supply a fake writer without a desktop; `copy` / `paste` /
`paste_image` import and in-memory tests still pass; without the extra,
`copy_image` raises `ImportError`.

Internal: Add the write entry point and injection hook beside the read path;
no native publication required yet. Enables slice 2 contract Behavior.

### 2. In-memory `copy_image` contract
Type: Behavior
Status: done
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
Status: done
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
Status: done
Proof: Implement Linux X11/`xclip` writer; gated probe (`copy_image` → writer
exits → independent consumer recovers opaque size/colors; alpha recorded);
add a GitHub Actions job that installs `xclip`, runs under **Xvfb**, and
executes that probe (not default matrix pytest). README marks X11 write
verified at those CI floors. **No evidence-limit substitute** — failed probe
or missing job stops Linux X11 acceptance; issue #5 needs this and slice 5.

Behavior: Pre-condition: contract; GHA ubuntu + Xvfb + `xclip`. Trigger:
gated write + independent consumer after exit in CI. Postcondition: key
example 1 (floors name Xvfb/CI honestly).

### 5. Early probe — Linux Wayland + `wl-copy` image write
Type: Behavior
Status: done
Proof: Implement Wayland/`wl-copy` writer; gated probe with writer-exit
independent consumer; GitHub Actions job under a **named** CI compositor
(e.g. Sway) with `wl-clipboard`; README marks Wayland write verified for
that compositor/CI floors only. Failed probe stops Wayland acceptance (not
an evidence-limit completion).

Behavior: Pre-condition: contract; GHA Wayland compositor + `wl-copy`.
Trigger: gated write + independent consumer after exit in CI. Postcondition:
key example 2.

### 6. Early probe — Windows desktop image write
Type: Behavior
Status: done
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
- **Developer (2026-11-02):** do not block on owner-held Linux desktops; either
  skip Linux probes or prove them in GitHub Actions. Selected: **GHA** (preserves
  issue #5). Skip rejected. Linux proof venue = gated CI jobs with honest floors.

## Learnings

- Write injection named `set_image_writeclipboard` / `_writeclipboard` to mirror
  `set_image_grabclipboard` / `_grabclipboard` without shadowing public `copy_image`.
- Optional-images ImportError gate consolidated as `_pillow_image(operation)` shared
  by `paste_image` and `copy_image` (message still names the calling operation).
- Default `_default_writeclipboard` raises `NotImplementedError` until later writers
  or slice-2 failure wrapping (tracked as G-interim-stub).
- Darwin checkout cannot run Linux probes; owner chose GHA over skipping issue #5.
- Linux xclip under Xvfb: do not wait for exit (CLIPBOARD owner stays up); feed PNG on stdin, leave the process (`start_new_session`), then wait until CLIPBOARD TARGETS lists `image/png` (0.05s alone raced opaque first write).
- Wayland: Weston headless lacks wlr-data-control so `wl-copy` exits 1; proof venue is gated GHA under named compositor **Sway** (`WLR_BACKENDS=headless`) only (S.4/X.8/C.4). Prefer `wl-copy` when Wayland; leave xclip for X11.
- Slice 6 Windows: no usable desktop session on Darwin checkout; `windows-latest` GHA is headless pytest only — took evidence-limit path (README explicit unverified; keep default writer `NotImplementedError` → `ClipboardImageError`; no pywin32).

## Accepted proof (slice 1)

- Command: `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_copy_image.py -q` → 22 passed.
- Observations: public `copy_image` / `set_image_writeclipboard`; injectable fake receives Image; reset restores stub; ImportError without Pillow; text and `paste_image` suites green.

## Accepted proof (slice 2)

- Command: `nix develop -c uv run --locked --extra images pytest tests/test_copy_image.py tests/test_copy_image_failures.py tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py -q` → 41 passed.
- Observations: transferable RGB/RGBA; mode conversion; fail-before-replace; clear text+image in fake offer; backend/stub → `ClipboardImageError`; text/`paste_image` regression green.
- Learning: split success vs failure `copy_image` tests; shared `tests/image_offer.py` fake offer stand-in.

## Accepted proof (slice 3)

- Darwin `_write_macos_pngf` via osascript «class PNGf»; gated probe with writer-exit + ImageGrab independent consumer.
- Native: `CLIPBOARD_NATIVE_PROBE=1 … pytest tests/test_copy_image_native_macos.py` → pass; alpha preserved; floors macOS 26.6.2 / Pillow 11.3.0 recorded in README.
- Desktop-free suites remain green (Darwin stub skip expected).
- Learning: shared `scripts/native_probe_common.py` for macOS/Linux native probes.

## Accepted proof (slice 4)

- Linux `_write_linux_xclip` (detached xclip CLIPBOARD owner after ingest).
- Gated probe + GHA job `native-linux-x11-copy-image` (Xvfb); green on `c6f6585`.
- Floors: ubuntu-latest + Xvfb + xclip; Python 3.13 / Pillow 11.3.0 (README).
- Learning: under Xvfb do not wait for xclip exit; leave it as selection owner.

## Accepted proof (slice 5)

- Linux `_write_linux_wl_copy` (wl-copy / image/png); X11 path waits for TARGETS `image/png`.
- Gated probe + GHA job `native-linux-wayland-copy-image` under **Sway** (`WLR_BACKENDS=headless`); green with X11 on `833bbd3`.
- Floors: ubuntu-latest + Sway + wl-clipboard; Python 3.13 / Pillow 11.3.0 (README); do not generalize beyond Sway.
- Learning: Weston lacks wlr-data-control; use Sway (or other wlroots) for wl-clipboard CI.

## Accepted proof (slice 6)

- No usable Windows desktop session (Darwin checkout; `windows-latest` headless pytest only).
- README Evidence: explicit Windows write evidence limit — never claimed verified.
- Default Windows write remains `NotImplementedError` → `ClipboardImageError` (no silent success; no pywin32).

## Concern evidence

- Slice-plan refinement: not needed — Behavior/Structure split is one write
  contract plus per-desktop proof loops; cumulative rule is a single
  `copy_image` offer model with platform adapters; Linux mandatory probes are
  authorized early probes, not unscoped concerns.
- Remaining slice-specific concerns: none beyond the authorized early probes
  in slices 4–6 (Linux via gated GHA; Windows session or evidence limit).

## Story obligations

### G-x11-ci. Linux X11 writer-exit awaits green GHA probe
Reported: slice 4 — "X11 writer-exit proof is gated on GitHub Actions job native-linux-x11-copy-image under Xvfb; not yet observed green"
Story clause: "Linux X11 and Wayland writer-exit success are acceptance requirements (issue #5); they are not substitutable by an evidence-limit note."
Disposition: proved by slice 4: GitHub Actions run on c6f6585 (job native-linux-x11-copy-image PASSED; opaque writer-exit + independent xclip -o consumer)

### G-wayland-ci. Linux Wayland writer-exit awaits green GHA Sway probe
Reported: slice 5 — "Wayland writer-exit proof is gated on GitHub Actions job native-linux-wayland-copy-image under Sway; not yet observed green"
Story clause: "Linux X11 and Wayland writer-exit success are acceptance requirements (issue #5); they are not substitutable by an evidence-limit note."
Disposition: proved by slice 5: GitHub Actions run on 833bbd3 (job native-linux-wayland-copy-image PASSED under Sway; opaque writer-exit + independent wl-paste consumer; X11 job also PASSED)

### G-interim-stub. Default write raises NotImplementedError
Reported: slice 1 — "default `_default_writeclipboard` raises `NotImplementedError` until a real writer or contract wrapper lands"
Story clause: "Failures other than successful publication (missing helper, denied access, transfer failure, unsupported session) raise `ClipboardImageError` rather than silent no-op."
Disposition: proved by slice 2: tests/test_copy_image_failures.py::test_default_write_stub_wrapped_as_clipboard_image_error (public copy_image wraps stub NotImplementedError into ClipboardImageError; internal stub remains until native writers)

### G-excl-env. Non-desktop environments are not guaranteed desktops
Reported: slice 1 — "WSL, SSH, containers, and headless CI are not additional guaranteed desktops"
Story clause: "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Disposition: excluded "WSL, SSH, containers, and headless CI are not additional guaranteed desktops."
Commitment: S.5, S.6, S.7, S.8

### G-excl-deferred. Deferred APIs and delivery shapes
Reported: slice 1 — "Path/bytes overloads and related deferred delivery shapes from Scope limits"
Story clause: "Path/bytes overloads (callers open to `Image` first); animated / multi-frame / screenshot APIs; file-manager copy offers; HTML / rich / multi-item pasteboards; bundling GUI toolkits or `win32clipboard` as a required public dependency; making default pytest / CI require a real desktop; expanding beyond the four-desktop set; inventing rollback/atomicity guarantees beyond fail-before-replace. Using `paste_image` alone as native proof remains deferred (insufficient). Splitting Linux-first vs Win/macOS into separate stories is deferred unless execution evidence forces a resplit — this story keeps the four-desktop outcome with the Linux acceptance floor above."
Disposition: excluded "Path/bytes overloads (callers open to `Image` first); animated / multi-frame / screenshot APIs; file-manager copy offers; HTML / rich / multi-item pasteboards; bundling GUI toolkits or `win32clipboard` as a required public dependency; making default pytest / CI require a real desktop; expanding beyond the four-desktop set; inventing rollback/atomicity guarantees beyond fail-before-replace. Using `paste_image` alone as native proof remains deferred (insufficient). Splitting Linux-first vs Win/macOS into separate stories is deferred unless execution evidence forces a resplit — this story keeps the four-desktop outcome with the Linux acceptance floor above."
Commitment: D.1, D.2.1, D.2.2, D.2.3, D.3, D.4.1, D.4.2, D.4.3, D.5, D.6, D.7, D.8, D.9, D.10

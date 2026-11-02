# Plan: Native image-read verification on Windows and Linux

**Identity:** SEED-001#read-images-native
**Source:** [Native image-read verification on Windows and Linux](../../seeds/SEED-001-clipboard-true-to-its-name.md#read-images-native)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Close the four-desktop `paste_image` promise for the remaining unverified
targets: Windows desktop, Linux X11 + `xclip`, and Linux Wayland + `wl-paste`.
Each gets independent-producer native proof comparable to the macOS Aqua probe,
or an explicit unverified/unsupported evidence limit — never silent success.
All three remaining desktops may end evidence-limited when no usable session
exists; that still closes the story once each limit is explicit. Text callers
and the verified macOS path stay compatible.

**Included:** gated native probes (scripts + optional pytest, same spirit as
`CLIPBOARD_NATIVE_PROBE` / `scripts/probe_macos_native_paste_image.py`); opaque
raster size/colors; preservative read; alpha when offered or documented drop;
OS / desktop / compositor / helper / Pillow floors; native Windows CF_HDROP /
filename-list → `None` without opening paths when a Windows session is
available; README (and related) evidence wording updated per desktop outcome.

**Excluded:** image writing; new public APIs or return shapes; default pytest /
CI requiring a real desktop; WSL / SSH / containers as guaranteed desktops;
macOS re-verification as the outcome; HTML, files, inspection, clear, waits,
PRIMARY; silent compositor generalization.

## Assumptions

- Public contract stays delivered `paste_image()` → `Image | None` /
  `ClipboardImageError`; reuse Pillow `ImageGrab.grabclipboard` normalization.
- PFE: image-read path and macOS probe pattern already exist; this plan extends
  native evidence and docs, not a second image-read stack.
- ADR store is undefined in this repo; no Accepted ADR constrains this plan.
- This preparation checkout is macOS (Darwin). Windows and Linux native
  sessions are owner-held / other-machine observations bounded by early probe
  slices below; absence of a session yields an evidence limit, not a blocked
  plan.

## Outside-in proof

| Example | Observable signal |
| --- | --- |
| Windows independent opaque PNG | Probe JSON ok; matching size/colors; preservative; floors recorded; README marks Windows verified **or** explicit evidence limit |
| Windows CF_HDROP-only offer | `paste_image()` is `None`; no path open (when Windows session available) |
| Linux X11 + `xclip` independent PNG | Same success pattern; floors recorded; README marks X11 verified **or** evidence limit |
| Linux Wayland + `wl-paste` on named compositor | Success scoped to that compositor; others remain limited **or** Wayland evidence limit |
| Desktop unavailable here | Explicit unverified/unsupported note retained/refreshed; never claimed verified |
| Regression | In-memory `paste_image` tests and gated macOS probe still pass; text API unchanged |

Automated contract tests stay in-memory. Native examples use an independent
producer; same-library round-trips alone do not establish interoperability.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| `paste_image` / `clipboard[images]` contract is delivered | All native probes consume it unchanged | `nix develop -c uv run --locked --extra images pytest tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_clipboard.py -q` → 18 passed; `clipboard.VERSION == 0.0.5` and `paste_image` present | Settled |
| macOS gated probe pattern exists to mirror | Win/Linux probe scripts and gated tests | Read `scripts/probe_macos_native_paste_image.py` and `tests/test_paste_image_native_macos.py` (`CLIPBOARD_NATIVE_PROBE=1`) | Settled: pattern is independent PNG producer → `paste_image` → JSON; pytest gated |
| README names Win/Linux unverified pending this story | Docs updates in probe slices | Read `README.rst` Evidence paragraph | Settled: macOS verified; Windows / X11+`xclip` / Wayland+`wl-paste` "unverified pending SEED-001#read-images-native" |
| In-memory file-list stub → absence without open | Windows native CF_HDROP case builds on contract | `test_file_list_offer_is_absence_without_filesystem_open` in passed suite above | Settled for stub; **native** CF_HDROP remains early-probe (slice 1) |
| This checkout can run Windows or Linux native clipboard probes | Slices 1–3 | `uname -s` / `platform.system()` → Darwin | Settled: **cannot** here; Windows / Linux sessions are early probes or evidence limits |
| Independent producer can place an image on each target desktop | Slices 1–3 native success path | Owner-held desktop session + helper | **Early probe** (slices 1–3); failure or missing session → evidence limit, revise docs, do not claim verified |

## Ordered slices

### 1. Early probe — Windows desktop native image read
Type: Behavior
Status: done
Proof: On a usable Windows desktop session, a gated probe with an independent
producer (not `clipboard` round-trip) places a known opaque PNG; `paste_image()`
returns matching size/colors; second read is preservative; alpha case recorded
(preserved or documented drop); environment floors (OS, desktop, Pillow)
recorded. When the same session can offer CF_HDROP / filename-list only,
`paste_image()` is `None` without opening paths. README marks Windows verified
at those floors. If no Windows session is available to the executing agent or
developer-operated observation, record an explicit Windows evidence limit and
refresh README accordingly — never claim verified. Failure of a run probe stops
dependent Windows claims and revises the plan/docs.

Behavior: Pre-condition: delivered `paste_image`; Windows session **or**
documented unavailability. Trigger: run gated Windows probe / CF_HDROP case, or
write evidence limit. Postcondition: Windows is either natively proved with
floors in docs, or explicitly evidence-limited; default pytest stays desktop-free.

Accepted: Darwin checkout; no Windows session. README.rst Evidence marks
Windows evidence-limited (unverified/unsupported for native proof). Focused
desktop-free pytest 18 passed, 1 skipped.

### 2. Early probe — Linux X11 + `xclip` native image read
Type: Behavior
Status: done
Proof: On a usable Linux X11 session with `xclip` on `PATH`, same
independent-producer opaque (and alpha-when-offered) gated probe pattern;
floors include helper version; README marks X11+`xclip` verified **or**
explicit evidence limit if no such session. Do not infer X11 success from
Wayland or macOS.

Behavior: Pre-condition: delivered `paste_image`; X11+`xclip` session **or**
unavailability. Trigger: gated X11 probe or evidence-limit write.
Postcondition: X11 target honestly verified or limited; CI default still
desktop-free.

Accepted: Darwin checkout; no X11 session, empty DISPLAY, no `xclip`.
README.rst Evidence marks X11+`xclip` evidence-limited
(unverified/unsupported for native proof). Focused desktop-free pytest 18
passed, 1 skipped. Windows/macOS wording preserved; Wayland still pending.

### 3. Early probe — Linux Wayland + `wl-paste` native image read
Type: Behavior
Status: done
Proof: On a usable Wayland session with `wl-paste`, gated independent-producer
probe; record **compositor name/version** in floors; README marks Wayland
verified **only for that compositor** (other compositors remain evidence-limited).
If no Wayland session, explicit Wayland evidence limit — never generalize from
X11 or one unstated compositor.

Behavior: Pre-condition: delivered `paste_image`; Wayland+`wl-paste` session
**or** unavailability. Trigger: gated Wayland probe or evidence-limit write.
Postcondition: Wayland claim is compositor-scoped proof or honest limit.

Accepted: Darwin checkout; no Wayland session and no `wl-paste`.
README.rst Evidence marks Wayland+`wl-paste` evidence-limited
(unverified/unsupported for native proof; no compositor generalization).
Focused desktop-free pytest 18 passed, 1 skipped. Windows/X11 limits and
macOS verified wording preserved.

### 4. Evidence summary and regression gate
Type: Structure
Status: planned
Proof: README Evidence / verified-platforms wording no longer says all three
targets are uniformly "unverified pending SEED-001#read-images-native"; each
of Windows, X11+`xclip`, and Wayland+`wl-paste` has either verified floors or
an explicit limit consistent with slices 1–3. `nix develop -c uv run --locked
--extra images pytest tests/test_paste_image.py tests/test_paste_image_failures.py
tests/test_clipboard.py tests/test_paste_image_native_macos.py -q` passes with
native macOS tests skipped unless gated. Enables wrap-up honesty of the
four-desktop promise.

Internal change: consolidate docs (and AGENTS.md probe pointers if needed)
from slice 1–3 outcomes; no new public API. Preserves external `paste_image`
and text behavior already proved in-memory / macOS.

## Current decisions

- Reuse delivered `paste_image` / North Star explicit-API shape; no redesign.
- Direction: per-desktop gated probes with evidence-limit fallback (not
  docs-only blanket, CI desktop matrix, or ImageGrab rewrite).
- Mirror macOS gated probe pattern per desktop; independent producers only.
- Missing desktop session → evidence limit, not plan blockage; three limits
  still complete the story.
- Wayland proof is compositor-scoped.
- Follow [.planning/NORTH-STAR.md](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports).
- ADR store is undefined in this repo; architecture follows North Star only
  (no Accepted ADR check completed).

## Learnings

- Slice 1: This Darwin execution checkout cannot run a Windows desktop clipboard
  session; Windows closed via explicit README evidence limit, not native proof.
- Slice 2: Same Darwin checkout has no X11 session, empty DISPLAY, and no
  `xclip`; X11+`xclip` closed via explicit README evidence limit.
- Slice 3: Same Darwin checkout has no Wayland session and no `wl-paste`;
  Wayland+`wl-paste` closed via explicit README evidence limit (no compositor
  generalization).

## Story obligations

### G24. Image writing deferred
Reported: slice 1 — "Image writing out of scope / deferred."
Story clause: "Image writing"
Disposition: excluded "Image writing"
Commitment: 24

### G25. New public image APIs deferred
Reported: slice 1 — "New public image APIs or return shapes out of scope / deferred."
Story clause: "new public image APIs or return shapes"
Disposition: excluded "new public image APIs or return shapes"
Commitment: 25

### G26. Desktop CI matrix deferred
Reported: slice 1 — "Default pytest / CI real-desktop matrix out of scope / deferred."
Story clause: "making default pytest / CI require a real desktop or a continuous native desktop matrix"
Disposition: excluded "making default pytest / CI require a real desktop or a continuous native desktop matrix"
Commitment: 26

### G27. Four-desktop set expansion deferred
Reported: slice 1 — "Expanding the four-desktop set out of scope / deferred."
Story clause: "expanding the four-desktop set"
Disposition: excluded "expanding the four-desktop set"
Commitment: 27

### G28. Other content kinds deferred
Reported: slice 1 — "HTML, files, inspection, clear, waits, or PRIMARY out of scope / deferred."
Story clause: "HTML, files, inspection, clear, waits, or PRIMARY"
Disposition: excluded "HTML, files, inspection, clear, waits, or PRIMARY"
Commitment: 28

### G30. Mandatory Win/Linux success deferred
Reported: slice 1 — "Requiring at least one successful Windows or Linux verification is deferred."
Story clause: "Requiring at least one successful Windows or Linux verification (rather than honest limits) is a deferred stronger promise, not this story's acceptance bar."
Disposition: excluded "Requiring at least one successful Windows or Linux verification (rather than honest limits) is a deferred stronger promise, not this story's acceptance bar."
Commitment: 30

## Concern evidence

- Slice-plan refinement: not needed — three independent desktop proof loops plus
  one docs consolidation; cumulative design is one probe/evidence-limit rule
  mirrored per desktop; early probes bound owner-held session premises; no
  unresolved source question inside the understood outcome.
- Remaining slice-specific concerns: none identified.

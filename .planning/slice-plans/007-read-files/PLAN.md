# Plan: Read file references copied by file managers

**Identity:** SEED-001#read-files
**Source:** [Read file references copied by file managers](../../seeds/SEED-001-clipboard-true-to-its-name.md#read-files)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Python desktop tools and automation developers can recover an **ordered list of
local file references** from an independent file manager's clipboard offer
through an explicit `paste_files()` API: local file-list present →
`list[str]` of local paths in offer order; no local file-list → `None`;
corrupt metadata / access / helper / transfer failure →
`ClipboardContentError`. The read never mutates the clipboard, never opens /
copies / moves / deletes referenced files, never treats plain path-looking text
as a file-list success, and never honors or reissues a cut/move marker as a
move. Supported desktops: Windows desktop + Explorer (or equivalent)
`CF_HDROP`; macOS Aqua + Finder (or equivalent) file-URL / filename types;
Linux X11 + helper requesting `text/uri-list`; Linux Wayland + helper
requesting `text/uri-list` on a named compositor. When a session is unavailable
during execution, that desktop records an explicit evidence limit — never
silent verified success. Text, image, and HTML callers stay compatible;
`clipboard[images]` is not required.

**Included:** public `paste_files`; injectable read backend for desktop-free
tests; Windows `CF_HDROP` path-list decoding; macOS file-URL / filename
pasteboard readers; Linux `text/uri-list` `file://` decoding (percent-encoding,
Unicode, spaces) to local paths; ignore cut/move companion markers for library
behavior; absence vs `ClipboardContentError` discipline; non-mutating reads
with no filesystem side effects; gated independent file-manager native probes;
helper and decoding docs; per-desktop floors or honest evidence limits.

**Excluded:** public cut vs copy / PreferredDropEffect / GNOME–KDE cut-verb
metadata; `pathlib.Path` or richer reference types; remote / non-local URI
references; virtual or promised files; outbound `copy_files`; overloading
`paste`/`copy`; parsing plain text as files; default CI desktop matrix;
WSL/SSH/containers as guaranteed desktops; bundling Qt / win32clipboard as
required public stack; same-library `copy_files` round-trip as sole native
proof; `clipboard[images]` requirement for this story.

## Assumptions

- Follow North Star explicit-API shape beside `copy`/`paste`; one
  absence / path-list / failure model with platform adapters.
- PFE: **reuse** delivered `ClipboardContentError`, `paste_image`
  absence-vs-failure discipline, injectable-backend + gated probe patterns
  from `set_html_clipboard_writer` / `set_image_grabclipboard`, and README
  evidence-limit wording style; **gap** — no `paste_files` yet; pyperclip is
  text-only and does not decode file-list formats. Do not overload
  `ClipboardImageError`. Do not default to Qt / heavy toolkit stacks; evaluate
  only if a probe forces reconsideration. Pillow `ImageGrab.grabclipboard`
  filename-list on Windows is an optional **internal** tactic only if it does
  not force the `clipboard[images]` extra on this story. Delivered image/HTML
  writers are regression / fake-producer only, not sole native proof.
- ADR store is undefined in this repo; no Accepted ADR constrains this plan.
- This preparation checkout is macOS (Darwin). Linux and Windows native
  sessions are owner-held / other-machine observations bounded by early probe
  slices; missing session yields an explicit evidence limit for that desktop.

## Outside-in proof

| Example | Observable signal |
| --- | --- |
| Independent FM copies two local files (Unicode + spaces) | `paste_files()` returns ordered local path `list[str]`; later independent consumer still sees the offer; no open/move/delete by the read |
| Linux `text/uri-list` / Windows `CF_HDROP` | Returned strings are decoded local paths, not raw URI text or `paste()` alone |
| Path-looking plain text / empty / image-only / HTML-only | `paste_files()` → `None` |
| Cut/move marker beside local refs | Path list still returned; library does not move, delete, or rewrite offer as cut/move |
| Corrupt / inconsistent file-list metadata | `ClipboardContentError`; clipboard unchanged; no fabricated paths |
| Missing helper / denied access | `ClipboardContentError`; not silent `None` |
| Per-desktop session | Independent FM success + floors **or** explicit evidence limit |
| Regression | In-memory text + `paste_image` + `copy_html` (+ `paste_html` / `inspect` if present) tests pass; no `clipboard[images]` required for `paste_files` |

Automated contract tests stay in-memory. Native examples use an independent
file manager; same-library round-trips alone do not establish interoperability.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| `ClipboardContentError` / `paste_image` / `copy_html` delivered; no `paste_files` yet | Contract + packaging reuse | `clipboard.VERSION == 0.0.5`; `ClipboardContentError`, `paste_image`, `copy_html`, `set_html_clipboard_writer`, `set_image_grabclipboard` present; `paste_files` / `paste_html` / `inspect` absent; `nix develop -c uv run --locked --extra images pytest tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_copy_html_contract.py tests/test_copy_html_seam.py -q` → 41 passed | Settled |
| Injectable seams exist to mirror for file-list read | Structure slice for injectable read backend | `set_html_clipboard_writer`, `set_image_grabclipboard` in `clipboard.py` | Settled |
| pyperclip cannot read native file-list formats | Must implement file-list readers, not re-export pyperclip | pyperclip public surface: `copy`, `paste`, `is_available`, backend inits — no file-list / URI-list API | Settled |
| This checkout can run macOS native Finder file-list paste probes | Slice 3 | `uname -s` → Darwin | Settled: macOS probe runnable here when authorized |
| This checkout can run Windows or Linux native file-list probes | Slices 4–6 | Darwin host; `xclip` / `wl-paste` not on `PATH` | Settled: **cannot** here; Linux/Windows are early probes on owner-held sessions |
| Independent file manager can supply local file-list offers on each target | Native Behavior slices | Owner-held desktop + Explorer/Finder/named Linux FM + helpers / pasteboard | **Early probe** (slices 3–6); missing session → evidence limit for that desktop; probe failure stops dependent claims for that desktop |

## Ordered slices

### 1. Injectable `paste_files` read seam
Type: Structure
Status: done
Proof: Public `paste_files` exists; default path and a `set_*` injection hook
allow tests to supply a fake reader without a desktop; failures raise
`ClipboardContentError` (not `ClipboardImageError`); `copy` / `paste` /
`paste_image` / `copy_html` import and in-memory tests still pass; calling
`paste_files` does not require `clipboard[images]`.

Internal: Add the file-list read entry point and injection hook beside
existing content APIs; no native file-list decoding required yet. Enables
slice 2 contract Behavior.

### 2. In-memory `paste_files` contract
Type: Behavior
Status: done
Proof: Desktop-free tests show: fake two-file offer (Unicode + spaces) →
ordered local path `list[str]`; fake `file://` / path-list payloads decode to
local paths; path-looking plain text / empty / image-only / HTML-only →
`None`; fake cut marker beside refs → path list returned with no move/delete
side effect and no cut reissue on the fake model; corrupt metadata /
access/helper failure from the fake → `ClipboardContentError` (not `None` or
fabricated paths); read does not mutate the fake offer; existing text,
`paste_image`, and `copy_html` suites stay green.

Behavior: Pre-condition: injectable seam from slice 1. Trigger: `paste_files`
against fake offers covering local lists, absence kinds, cut marker, and
backend failure. Postcondition: contract examples 1–6 and 8 hold without a
real clipboard.

### 3. Early probe — macOS Aqua Finder file-list read
Type: Behavior
Status: done
Proof: On this Darwin checkout (or equivalent Aqua session), gated probe: an
**independent** Finder (or equivalent) copies two local files including
Unicode/spaces; `paste_files()` returns matching ordered local paths; a later
independent consumer still sees the offer (non-mutation); no open/move/delete
by the library; floors (OS) recorded; README marks macOS `paste_files`
verified at those floors. If Aqua file-list read cannot be observed, record an
explicit macOS evidence limit — never claim verified. Probe failure stops
dependent macOS file-list claims.

Behavior: Pre-condition: contract from slice 2; Darwin session **or** evidence
limit path. Trigger: gated native independent-FM paste. Postcondition:
examples 1 and 7 (macOS branch) or honest limit.

### 4. Early probe — Linux X11 + helper `text/uri-list`
Type: Behavior
Status: done
Proof: On a usable X11 session with a helper that can request `text/uri-list`
on CLIPBOARD (document the exact tool/flags, e.g. `xclip -o -t text/uri-list`)
and a **named** file manager, gated probe: independent FM → `paste_files()`
returns decoded local paths; clipboard unchanged for a later consumer;
cut-marker companion ignored for side effects when present; deps/floors
documented; README marks X11 `paste_files` verified. If no usable session or
helper path exists, record an explicit X11 evidence limit — never claim
verified. Probe failure stops dependent X11 claims.

Behavior: Pre-condition: contract; owner-held X11+helper+FM session **or**
evidence-limit path. Trigger: gated independent-FM paste. Postcondition: key
examples 1–2 and 4 (X11) / example 7 or honest limit.

### 5. Early probe — Linux Wayland + helper `text/uri-list`
Type: Behavior
Status: done
Proof: On a usable Wayland session with `wl-paste -t text/uri-list` (or
equivalent) on a **named** compositor and named file manager, same
independent-FM local-path success, non-mutation, and cut-marker non-side-
effect; document compositor/helper/FM scope; README marks Wayland
`paste_files` verified for that compositor only. Missing session or failed
probe → explicit Wayland evidence limit or stopped dependent claims — never
silent verified.

Behavior: Pre-condition: contract; owner-held Wayland+helper+FM session **or**
evidence-limit path. Trigger: gated independent-FM paste. Postcondition:
example 7 (Wayland branch) or honest limit.

### 6. Early probe — Windows desktop `CF_HDROP`
Type: Behavior
Status: done
Proof: On a usable Windows desktop session, gated probe: independent Explorer
(or equivalent) copies two local files including Unicode/spaces;
`paste_files()` returns matching ordered local paths from `CF_HDROP`;
clipboard unchanged afterward; cut/move PreferredDropEffect (when present)
does not cause library move/delete or cut reissue; floors recorded; README
marks Windows `paste_files` verified. If no Windows session is available,
record an explicit Windows evidence limit — never claim verified. Probe
failure stops dependent Windows claims.

Behavior: Pre-condition: contract; Windows session **or** evidence-limit path.
Trigger: gated independent-FM paste. Postcondition: examples 1–2 and 4
(Windows) / example 7 or honest limit.

### 7. Docs and packaging alignment for `paste_files`
Type: Behavior
Status: done
Proof: README (and related install/evidence notes) document `paste_files`,
absence vs `ClipboardContentError`, non-mutation, no filesystem side effects,
plain-text rejection, cut-marker ignore rule, Linux `text/uri-list` helpers,
per-desktop verified floors or evidence limits from slices 3–6, and that
`clipboard[images]` is not required; desktop-free suites stay green under
locked pytest / `make check` as applicable.

Behavior: Pre-condition: outcomes from slices 2–6. Trigger: docs + packaging
updates. Postcondition: callers can ingest file-manager copies without
guessing paths from text; evidence wording is honest.

## Execution complete

Product advice: `paste_files` lands as a peer of `paste_image` / `copy_html`:
explicit API, `ClipboardContentError` vs `None`, injectable CI, independent-FM
native proof where a session existed. Keep the backlog order —
`SEED-001#copy-files` is the natural outbound sibling; do not invent a separate
"verify X11/Wayland/Windows paste_files" story unless the owner wants those
evidence limits cleared on real desktops (thin readers and probes are already
in place). Leave Taken `read-html` / `inspect-formats` alone. Assimilate README
Evidence floors into North Star on wrap-up; no priority change.

## Current decisions

- Reuse North Star explicit-API shape and `ClipboardContentError`; implement
  platform file-list readers (pyperclip cannot decode them).
- Public success means an ordered `list[str]` of local filesystem paths;
  `None` means ordinary local file-list absence.
- Never mutate the clipboard; never open/copy/move/delete referenced files;
  never parse plain text as files; never reissue cut as move.
- Ignore cut/move companion markers for library behavior; defer public
  cut/copy metadata.
- All four desktops may record evidence limits when no session exists; probe
  failure stops that desktop's verified claim.
- Prefer thin platform readers + documented helpers over Qt unless a probe
  forces reuse reconsideration; do not require `clipboard[images]`.
- Independent file managers required for native proof; same-library
  round-trips are regression-only.

## Learnings

- Slice 1: public `paste_files` + `set_files_clipboard_reader`; default reader
  raises `ClipboardContentError` (unavailable stub) rather than `None`, matching
  `copy_html`'s unavailable-native pattern so unimplemented native is not
  mistaken for absence.
- Developer authorized package split at the 250-line refactor gate: root
  `clipboard.py` → `clipboard/` package (`_errors`, `_files`, `_html`(+native),
  `_image`(+native)); public `import clipboard` / `VERSION` unchanged.
- Accepted proof (reuse for later slices):
  `nix develop -c uv run --locked --extra images pytest tests/test_paste_files_seam.py tests/test_clipboard.py tests/test_paste_image.py tests/test_paste_image_failures.py tests/test_copy_html_contract.py tests/test_copy_html_seam.py -q` → seam + regression green after package split.


- Slice 2: `paste_files` normalizes injected raw offers (`list[str]`, structured
  `uri-list` / `paths`, absence kinds); `file://` decode with percent-encoding;
  cut/move companion fields ignored by omission (no production recognizer
  required for in-memory ignore); corrupt/access/helper → ClipboardContentError.
- Contract proof split across `tests/test_paste_files_contract.py` (decode/absence)
  and `tests/test_paste_files_failures.py` (cut/corrupt/access/non-mutation) with
  shared `tests/paste_files_offer.py` fakes.


- Slice 3: macOS Aqua `paste_files` verified via Finder-equivalent osascript
  ``NSFilenamesPboardType`` independent producer (gated
  ``scripts/probe_macos_native_paste_files.py``); floors macOS 26.6.2 /
  Darwin 25.6.0; README Evidence updated. Default Darwin reader in
  ``clipboard/_files_native_macos.py`` (dispatch ``clipboard/_files_native.py``).


- Slice 4: Linux X11 ``paste_files`` explicit evidence limit on this Darwin
  host (no ``xclip``/DISPLAY); thin ``xclip -o -selection clipboard -t
  text/uri-list`` reader wired for later owner-held verification; probe
  ``file_manager_generalization: false``.


- Slice 5: Linux Wayland ``paste_files`` explicit evidence limit (no
  ``wl-paste``/WAYLAND_DISPLAY); thin ``wl-paste -t text/uri-list`` reader;
  ``compositor_generalization: false``. Native readers split to
  ``_files_native_{macos,linux}.py`` + dispatch.


- Slice 6: Windows ``paste_files`` / ``CF_HDROP`` explicit evidence limit on
  this Darwin host; thin ctypes DragQueryFileW reader (no win32clipboard
  public dependency) for later owner-held verification.


- Slice 7: README/AGENTS/pyproject document ``paste_files`` contract, helpers,
  and per-desktop evidence (macOS verified; X11/Wayland/Windows limits);
  ``clipboard[images]`` not required; desktop-free ``make check`` green.

## Concern evidence

- Slice-plan refinement: not needed — one coherent local file-list read model,
  each Behavior owns one proof loop (contract or one desktop probe), Structure
  only precedes the contract Behavior, and native session premises are already
  bounded by authorized early probe slices.
- Remaining slice-specific concerns: none identified in this review.

## Story obligations

### X92. Not additional guaranteed desktops
Reported: slice 1 — "WSL/SSH/containers/headless CI are not guaranteed desktops"
Story clause: "WSL, SSH, containers, and headless CI are not additional guaranteed desktops"
Disposition: excluded "WSL, SSH, containers, and headless CI are not additional guaranteed desktops"
Commitment: 92

### X104. Deferred: Public exposure of cut vs copy intent / PreferredDropEffect
Reported: slice 1 — "source review exclusion for commitment 104"
Story clause: "Public exposure of cut vs copy intent / PreferredDropEffect / GNOME–KDE cut verbs as structured return metadata (parse/ignore markers only as needed for the non-move safety rule)"
Disposition: excluded "Public exposure of cut vs copy intent / PreferredDropEffect / GNOME–KDE cut verbs as structured return metadata (parse/ignore markers only as needed for the non-move safety rule)"
Commitment: 104

### X105. Deferred: returning `pathlib.Path` objects or richer reference types
Reported: slice 1 — "source review exclusion for commitment 105"
Story clause: "returning `pathlib.Path` objects or richer reference types"
Disposition: excluded "returning `pathlib.Path` objects or richer reference types"
Commitment: 105

### X106. Deferred: remote / non-local URI references
Reported: slice 1 — "source review exclusion for commitment 106"
Story clause: "remote / non-local URI references"
Disposition: excluded "remote / non-local URI references"
Commitment: 106

### X107. Deferred: virtual or promised files
Reported: slice 1 — "source review exclusion for commitment 107"
Story clause: "virtual or promised files"
Disposition: excluded "virtual or promised files"
Commitment: 107

### X108. Deferred: directory-expansion semantics beyond what the native offer a
Reported: slice 1 — "source review exclusion for commitment 108"
Story clause: "directory-expansion semantics beyond what the native offer already lists"
Disposition: excluded "directory-expansion semantics beyond what the native offer already lists"
Commitment: 108

### X109. Deferred: outbound file-list write (`SEED-001#copy-files`)
Reported: slice 1 — "source review exclusion for commitment 109"
Story clause: "outbound file-list write (`SEED-001#copy-files`)"
Disposition: excluded "outbound file-list write (`SEED-001#copy-files`)"
Commitment: 109

### X110. Deferred: format inspection (`SEED-001#inspect-formats`)
Reported: slice 1 — "source review exclusion for commitment 110"
Story clause: "format inspection (`SEED-001#inspect-formats`)"
Disposition: excluded "format inspection (`SEED-001#inspect-formats`)"
Commitment: 110

### X111. Deferred: bundling GUI toolkits or `win32clipboard` as a required publ
Reported: slice 1 — "source review exclusion for commitment 111"
Story clause: "bundling GUI toolkits or `win32clipboard` as a required public dependency"
Disposition: excluded "bundling GUI toolkits or `win32clipboard` as a required public dependency"
Commitment: 111

### X112. Deferred: making default pytest / CI require a real desktop
Reported: slice 1 — "source review exclusion for commitment 112"
Story clause: "making default pytest / CI require a real desktop"
Disposition: excluded "making default pytest / CI require a real desktop"
Commitment: 112

### X113. Deferred: expanding beyond the four-desktop set
Reported: slice 1 — "source review exclusion for commitment 113"
Story clause: "expanding beyond the four-desktop set"
Disposition: excluded "expanding beyond the four-desktop set"
Commitment: 113

### X114. Deferred: same-library `copy_files` round-trip as sole native proof
Reported: slice 1 — "source review exclusion for commitment 114"
Story clause: "same-library `copy_files` round-trip as sole native proof"
Disposition: excluded "same-library `copy_files` round-trip as sole native proof"
Commitment: 114

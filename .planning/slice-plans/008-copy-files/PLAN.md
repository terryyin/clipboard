# Plan: Copy local file references into file managers

**Identity:** SEED-001#copy-files
**Source:** [Copy local file references into file managers](../../seeds/SEED-001-clipboard-true-to-its-name.md#copy-files)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Python tool and automation developers hand existing local files to a desktop
file manager through an explicit `copy_files(paths)`: valid input replaces the
clipboard with one native **copy** file-list offer that stays pasteable after
the Python writer exits; invalid input, a missing source, or a missing helper,
denied access, or transfer failure raises `ClipboardContentError` before or
instead of a replacement, never silent success. Paths are made absolute at call
time (symlinks kept), order and duplicates pass through, and files and
directories are both offered. Targets: macOS Aqua (`NSPasteboard` file URLs),
Windows desktop (`CF_HDROP` + `Preferred DropEffect` copy), Linux X11
(`xclip` background owner), Linux Wayland (`wl-copy` on a named compositor).
`clipboard[images]` is not required.

**Excluded:** plain-text/name alternative in the same offer; cut/move;
virtual/promised files; non-`file:` URIs; library-side copying, opening, or
pasting of files; PRIMARY; WSL/SSH/containers/headless CI as guaranteed
desktops; persistence across logout/reboot; changing `copy`/`paste`.

## Assumptions

- PFE: **reuse** `ClipboardContentError` and `_call_content_backend`
  wrapping, the `set_*_clipboard_writer` injection pattern, `copy_html`
  fail-before-replace validation, `copy_image`'s Linux background-owner
  lifetime (`xclip` / `wl-copy` with `TARGETS` polling), `paste_files`'s
  session rule (`_linux_wayland_without_x11`) and Windows `ctypes` clipboard
  handling, the macOS `osascript` / AppKit writer pattern, gated
  `CLIPBOARD_NATIVE_PROBE` probes, and README evidence-limit wording.
  **Gap:** no outbound file-list writer exists. Windows PowerShell
  `Set-Clipboard -Path` treats `[` `]` as wildcards and adds a PowerShell
  startup per call; not selected as the default writer.
- If SEED-001#desktop-helpers has landed when a Linux slice starts, its
  private desktop module owns session detection, helper-failure detail, and
  `TARGETS` listing; reuse it instead of the current per-module copies.
- No ADR store exists in this repository; no Accepted ADR constrains this plan.
- Local development is Darwin; Linux desktop proof runs in gated GitHub
  Actions. The helper-offer premise is now verified with real Thunar Paste
  under Xvfb (slice 2). The API writer must repeat that proof in slice 5;
  X11 evidence does not establish Wayland file-manager behavior.
- Local gate: `nix develop -c make check` (AGENTS.md); add
  `nix develop -c make lint-workflows` whenever `.github/workflows` changes.

## Outside-in proof

| Example (seed) | Observable signal | Owning slice |
| --- | --- | --- |
| 1. Two Unicode+space files pasted as copies by a file manager after writer exit | Native file manager paste creates copies in a chosen folder; sources unchanged; floors recorded — or explicit evidence limit | 3 (macOS Finder), 4 (Windows Explorer shell), 5–6 (Linux named FM or limit) |
| 2. Missing source → error, previous text survives | `ClipboardContentError` naming the path; fake writer never called; native probe sees prior text | 1, plus one native check in 3 |
| 3. Empty iterable / bare `str` → error, clipboard untouched | `ClipboardContentError`; writer not called | 1 |
| 4. Relative path → absolute path read back | Fake round trip and native `paste_files()` return absolute paths in order | 1, 3–6 |
| 5. Source removed after copy | No library call involved; README states the reference-not-snapshot rule | 7 |
| 6. Missing Linux helper → error with install hint, clipboard untouched | `ClipboardContentError` with hint; no replacement | 5, 6 |
| Copy (not cut) marker | macOS has no cut marker; Windows `Preferred DropEffect` = 1 read by independent consumer; GNOME copied-files first line `copy` when offered | 4, 5–6 |
| Writer-exit lifetime | Independent consumer in another process reads the offer after the Python writer exited | 3–6 |
| Regression | Existing text, image, HTML, `paste_files`, `inspect` suites green; `copy_files` importable without Pillow | 1, every slice |

`paste_files()` round trips are consistency checks only; native success needs
an independent consumer, and file-manager paste for the example 1 claim.

## Decisive premises

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| No `copy_files` / file-list writer exists | Slice 1 adds the API and seam | `grep -rn "copy_files\|set_files_clipboard_writer" clipboard tests scripts` → no match | Settled |
| Injection and wrapping patterns to mirror exist | Slice 1 seam | `clipboard/_html.py`: `set_html_clipboard_writer`, `_call_content_backend`, `_validate_copy_html_args`; `clipboard/__init__.py` `__getattr__` re-exports | Settled |
| macOS `NSPasteboard writeObjects:` of file `NSURL`s via `osascript` persists after exit and Finder pastes copies | Slice 3 writer and proof | State-changing on the user's clipboard and needs Finder; not observed in preparation | **Early probe** (slice 3) |
| Explorer shell can paste a Python-written `CF_HDROP` on `windows-latest` (`Shell.Application` folder `InvokeVerb("Paste")`) | Slice 4 file-manager proof | Needs a Windows session; Darwin here | **Early probe** (slice 4); unavailable → offer-level proof plus Explorer evidence limit |
| A named Linux file manager pastes a lone `text/uri-list` (or needs `x-special/gnome-copied-files`) from a single-type helper owner | Slices 5–6 MIME choice | Thunar 4.18.8 on Ubuntu 24.04.5/X11 pasted both single-type offers after writer-command exit in [Actions](https://github.com/terryyin/clipboard/actions/runs/41460755116/job/125328858098) | Settled for this X11/Thunar combination; Wayland remains unobserved |
| `xclip` / `wl-copy` serve one MIME type per owner process | Slices 5–6 approach | wl-clipboard manual (`--type` single); xclip `-t` single target; delivered `copy_image` uses one type each | Settled by documentation and delivered behavior; revisit in slice 2 if a helper offers more |

## Ordered slices

### 1. In-memory `copy_files` contract
Type: Behavior
Status: done
Proof: desktop-free tests through public `clipboard.copy_files` with a fake
writer injected by `clipboard.set_files_clipboard_writer`: two Unicode+space
paths (one relative, one a directory) reach the writer as absolute paths in
order, duplicates kept; empty iterable, bare `str` / `bytes`, a non-path item,
and a missing path raise `ClipboardContentError` naming the problem with the
writer never called; non-content writer exceptions become
`ClipboardContentError`; `set_files_clipboard_writer(None)` restores the
default; a fake whose offer feeds the injected `paste_files` reader returns
the same absolute paths; `copy_files` imports without Pillow;
`nix develop -c make check` passes.

Behavior: Pre-condition: no `copy_files`. Trigger: call it with valid and
invalid inputs against a fake writer. Postcondition: seed examples 2–4 hold
without a desktop; the default writer raises `ClipboardContentError` naming
the unsupported platform until slices 3–6 replace it per platform.

### 2. Early probe — which offer a named Linux file manager pastes
Type: Behavior
Status: done
Proof: independent helper-offer experiment, verified in
[Actions run 41460755116](https://github.com/terryyin/clipboard/actions/runs/41460755116/job/125328858098)
at `14e9f6de07c0278e3e147ecd4af2cd3c8f7c12cb`.
Thunar 4.18.8 on Ubuntu 24.04.5/X11 pasted both a lone `text/uri-list`
and a lone `x-special/gnome-copied-files` (`copy\n<uris>`).
Actual destination bytes matched both Unicode/space source files; originals
were unchanged. The writer command exited first. GNOME-format controls
bracketed the URI round, and the same copying assertions rejected the
empty destination before Paste. See [probe documentation and floors](../../../docs/file-manager-offers.md).

Behavior: Pre-condition: helper-made offers need no library API.
Trigger: the gated Thunar/Xvfb Actions experiment. Postcondition: the
single-MIME approach is observed on this named X11 environment. This does
not complete the API writer or verify Wayland/other file managers.

### 3. macOS Aqua native writer and Finder proof
Type: Behavior
Status: planned
Proof: default Darwin writer publishes the paths as file `NSURL`s through
`osascript` / AppKit `writeObjects:` after `clearContents`; gated probe
`scripts/probe_macos_native_copy_files.py` (`CLIPBOARD_NATIVE_PROBE=1`) runs
the writer in a child Python that exits, then an independent `osascript`
consumer reads `public.file-url` items equal to the absolute paths and
`paste_files()` agrees; a missing-path call leaves prior text readable via an
independent consumer; developer-operated round: Cmd+V in a Finder folder the
developer chooses creates copies of both files, originals unchanged. Floors
recorded (macOS, Darwin, arch, Python). Any unobserved step → macOS evidence
limit, never verified.

Behavior: Pre-condition: slice 1. Trigger: `copy_files` on Aqua, writer exits,
Finder paste. Postcondition: seed example 1 (macOS) verified or limited.

### 4. Windows native writer and Explorer shell proof
Type: Behavior
Status: planned
Proof: default win32 writer uses `ctypes` (no pywin32): `OpenClipboard` with
the same bounded retry as the readers, `EmptyClipboard`, a wide `DROPFILES`
`CF_HDROP`, and registered `Preferred DropEffect` DWORD 1; gated job
`native-windows-copy-files` on `windows-latest`: the writer process exits,
an independent PowerShell consumer sees the `FileDropList` paths and drop
effect 1, and `Shell.Application` `NameSpace(dest).Self.InvokeVerb("Paste")`
creates copies in a temp destination with sources unchanged; the probe fails
rather than skips when it cannot verify. If shell paste is unavailable on the
runner, record it in Learnings, keep the offer-level proof, and mark the
Explorer claim an evidence limit. `make lint-workflows` passes.

Behavior: Pre-condition: slice 1. Trigger: `copy_files` on Windows, writer
exits, shell paste. Postcondition: seed example 1 (Windows) verified or
limited; copy marker observed.

### 5. Linux X11 native writer
Type: Behavior
Status: planned
Proof: default X11 writer (session rule shared with `paste_files`) feeds the
slice 2 MIME body (percent-encoded `file://` URIs, CRLF) to a background
`xclip -selection clipboard -t <type>` owner and waits for the type in
`TARGETS`, as `copy_image` does; missing `xclip` or display →
`ClipboardContentError` with install hint, clipboard untouched; gated job
`native-linux-x11-copy-files` (Xvfb + `xclip`): the actual public
`copy_files` call runs in a child Python that exits, independent
`xclip -o -t <type>` returns the URIs and `paste_files()` the paths, then
Thunar Paste creates both copies with matching bytes and unchanged sources.
Reuse slice 2's isolated desktop and assertions, replacing the helper-only
producer with the API child. Slice 2 proves the format premise; it does not
substitute for this implementation proof. Other file managers stay limited.

Behavior: Pre-condition: slices 1–2. Trigger: `copy_files` on X11, writer
exits. Postcondition: seed examples 1 (offer level) and 6 on X11.

### 6. Linux Wayland native writer
Type: Behavior
Status: planned
Proof: default Wayland writer pipes the same body to `wl-copy --type <type>`
(background server keeps the offer); missing `wl-copy` or compositor →
`ClipboardContentError` with install hint; gated job
`native-linux-wayland-copy-files` on Sway: writer exits, independent
`wl-paste --type <type>` returns the URIs and `paste_files()` the paths.
Claims scoped to Sway; FM paste reuses slice 2 only for the same compositor
and body, otherwise evidence limit.

Behavior: Pre-condition: slices 1–2, 5's URI body. Trigger: `copy_files` on
Wayland, writer exits. Postcondition: seed examples 1 (offer level) and 6 on
Sway.

### 7. Document `copy_files` and its evidence
Type: Behavior
Status: planned
Proof: README Usage documents `copy_files`, accepted inputs, absolute-path and
order rule, copy-not-cut, fail-before-replace, writer-exit lifetime,
reference-not-snapshot (example 5), no `clipboard[images]`; Installation lists
the Linux helpers; Evidence lists per-desktop floors or evidence limits from
slices 3–6 without generalizing a file manager or compositor; North Star
evidence line updated; module and function docstrings agree;
`nix develop -c make check` passes.

Behavior: Pre-condition: slices 3–6 results. Trigger: documentation update.
Postcondition: callers know exactly what is verified where.

## Current decisions

- `ClipboardContentError` for every `copy_files` failure, matching
  `copy_html` and `paste_files`.
- Validation precedes the writer, so every platform shares
  fail-before-replace; writers receive absolute `str` paths only.
- Existence is checked once at call time; nothing is promised afterwards.
- Native interoperability claims require an independent consumer; file-manager
  claims require a file-manager paste. `paste_files()` agreement alone is not
  proof.

## Story obligations

### G1. Default writer raises on every platform until native writers land
Reported: slice 1 — "No native writer exists yet. On Darwin, the default `copy_files` raises; slices 3–6 replace it per platform."
Story clause: "replaces the current clipboard with one native file-list offer"
Disposition: interim until slices 3, 4, 5, 6

## Learnings

GitHub Actions can run a real named Linux file manager, so an owner-held
Linux desktop is no longer a prerequisite for the X11 early probe.
Both tested single-format offers work with Thunar 4.18.8. Keep
`text/uri-list` for the planned Linux writer, repeat the actual API-to-Thunar
journey in slice 5, and retain the Wayland/other-file-manager evidence limits.

## Plan review

Refinement not needed: each slice has one outcome and proof loop, the probe
precedes the Linux slices whose MIME choice depends on it, and the shared
contract precedes the platform writers.

Remaining concerns: none beyond the early probes in slices 2–4, which bound
the unobserved native premises above.

# Source review: SEED-001#read-images-native

**Launch:** Fresh general-purpose reviewer; source-only inputs (Goal, Scope, key
examples, exclusions, settled prior-delivery contract). No plan, product, proof,
or conversation inheritance. Reviewer agent id retained in execution conversation.

**Input:** SEED-001#read-images-native section from
`../../seeds/SEED-001-clipboard-true-to-its-name.md` (Goal through key examples
and settled prior-delivery notes), as supplied in the reviewer prompt.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Python automation developers and maintainers can trust the documented Windows and Linux image-read floors for delivered `paste_image`. | slice 4 | observed: README.rst Evidence documents per-desktop floors/limits for paste_image |
| 2 | For each remaining supported desktop, either independent-producer native proof comparable to the macOS Aqua probe, or an explicit unverified/unsupported evidence limit — never a silent success. | slice 4 | observed: README.rst — macOS verified (2a); Win/X11/Wayland each evidence-limited (2b) |
| 2a | Independent-producer native proof comparable to the macOS Aqua probe (alternative). | slice 4 | observed: README.rst macOS Aqua verified via gated probe; Win/X11/Wayland took 2b |
| 2b | Explicit unverified/unsupported evidence limit (alternative). | slice 4 | observed: README.rst each of Windows, X11+xclip, Wayland+wl-paste evidence-limited |
| 3 | Text callers remain compatible. | slice 4 | observed: no text API change; focused test_clipboard.py in regression suite |
| 4 | The verified macOS path remains compatible. | slice 4 | observed: README retains macOS verified; gated macOS test still skippable/passable |
| 5 | For Windows desktop, either gated independent-producer native proof (5a) or explicit evidence-limit note (5b). | slice 1 | observed: README.rst Evidence — Windows evidence-limited (5b); Darwin checkout, no Windows session |
| 5a.1 | Opaque raster size/colors (Windows probe path). | slice 1 | observed: not applicable — 5b evidence-limit path; no Windows session |
| 5a.2 | Preservative read (Windows probe path). | slice 1 | observed: not applicable — 5b evidence-limit path; no Windows session |
| 5a.3 | Alpha preserved or documented drop (Windows probe path). | slice 1 | observed: not applicable — 5b evidence-limit path; no Windows session |
| 5a.4 | Named OS, desktop/compositor, helper, and Pillow floors (Windows probe path). | slice 1 | observed: not applicable — 5b evidence-limit path; no Windows session |
| 5b | Keep an explicit unverified/unsupported evidence-limit note for Windows desktop. | slice 1 | observed: README.rst Evidence paragraph — Windows evidence-limited (unverified/unsupported for native proof) |
| 6 | For Linux X11 with `xclip`, either probe (6a) or evidence-limit note (6b). | slice 2 | observed: README.rst Evidence — X11+xclip evidence-limited (6b); Darwin, no xclip, empty DISPLAY |
| 6a.1 | Opaque raster size/colors (X11 probe path). | slice 2 | observed: not applicable — 6b evidence-limit path; no X11 session |
| 6a.2 | Preservative read (X11 probe path). | slice 2 | observed: not applicable — 6b evidence-limit path; no X11 session |
| 6a.3 | Alpha preserved or documented drop (X11 probe path). | slice 2 | observed: not applicable — 6b evidence-limit path; no X11 session |
| 6a.4 | Named OS, desktop/compositor, helper, and Pillow floors (X11 probe path). | slice 2 | observed: not applicable — 6b evidence-limit path; no X11 session |
| 6b | Keep an explicit unverified/unsupported evidence-limit note for Linux X11 + `xclip`. | slice 2 | observed: README.rst Evidence paragraph — X11+xclip evidence-limited |
| 7 | For Linux Wayland with `wl-paste`, either probe (7a) or evidence-limit note (7b). | slice 3 | observed: README.rst Evidence — Wayland+wl-paste evidence-limited (7b); Darwin, no Wayland session |
| 7a.1 | Opaque raster size/colors (Wayland probe path). | slice 3 | observed: not applicable — 7b evidence-limit path; no Wayland session |
| 7a.2 | Preservative read (Wayland probe path). | slice 3 | observed: not applicable — 7b evidence-limit path; no Wayland session |
| 7a.3 | Alpha preserved or documented drop (Wayland probe path). | slice 3 | observed: not applicable — 7b evidence-limit path; no Wayland session |
| 7a.4 | Named OS, desktop/compositor, helper, and Pillow floors (Wayland probe path). | slice 3 | observed: not applicable — 7b evidence-limit path; no Wayland session |
| 7b | Keep an explicit unverified/unsupported evidence-limit note for that Wayland desktop. | slice 3 | observed: README.rst Evidence paragraph — Wayland+wl-paste evidence-limited |
| 8 | When a Windows session is available, prove native CF_HDROP / filename-list → `None` without opening paths. | slice 1 | observed: precondition unmet — no Windows session on Darwin; native CF_HDROP case not owed on 5b path |
| 9 | Update README (and related install/evidence docs) so verified floors replace, or honest limits retain, the current "unverified pending SEED-001#read-images-native" wording. | slice 4 | observed: README.rst/AGENTS.md — no "unverified pending SEED-001#read-images-native"; honest per-desktop limits |
| 10 | Default automated tests stay desktop-free. | slice 1 | observed: focused pytest 18 passed, 1 skipped without CLIPBOARD_NATIVE_PROBE; README states in-memory default |
| 11 | Native probes remain explicitly gated (same spirit as CLIPBOARD_NATIVE_PROBE / macOS probe script). | slice 4 | observed: README.rst + AGENTS.md name CLIPBOARD_NATIVE_PROBE / probe_macos_native_paste_image.py; default suite ungated |
| 12 | Reuse `paste_image` / `clipboard[images]` as delivered. | slice 1 | observed: no API/code change; docs-only evidence-limit |
| 13 | All-remaining-desktops evidence-limited still fulfills the story when each limit is explicit. | slice 4 | observed: README.rst all three remaining desktops explicitly evidence-limited |
| 14a | Supported desktop: Windows desktop. | slice 1 | observed: README.rst still names Windows as supported target (evidence-limited) |
| 14b | Supported desktop: Linux X11 + `xclip`. | slice 2 | observed: README.rst still names X11+xclip as supported target (evidence-limited) |
| 14c | Supported desktop: Linux Wayland + `wl-paste` scoped to probed compositor. | slice 3 | observed: README.rst names Wayland+wl-paste as supported target (evidence-limited; no compositor-scoped verified claim) |
| 15 | macOS Aqua remains verified and compatible; re-proving macOS is not this story's outcome. | slice 1 | observed: README.rst retains macOS Aqua verified wording; no macOS redesign |
| 16 | Do not claim a desktop verified without an independent-producer observation. | slice 1 | observed: README.rst never claims Windows, X11+xclip, or Wayland+wl-paste verified |
| 17 | Do not generalize one Wayland compositor's result to all Wayland environments. | slice 3 | observed: README.rst forbids generalizing from X11 or an unstated compositor; no Wayland verified claim |
| 18 | Do not bypass OS pasteboard / clipboard authorization. | slice 1 | observed: no clipboard access attempted; docs-only |
| 19 | Do not change `paste()`. | slice 1 | observed: no code change to paste/copy/VERSION |
| 20 | Do not treat file-list / URL-only offers as images. | slice 1 | observed: no contract change; in-memory file-list tests still in focused suite |
| 21a | `paste_image()` → Pillow `Image` \| `None`. | slice 1 | observed: unchanged; suite covers contract |
| 21b | `ClipboardImageError` for failures. | slice 1 | observed: unchanged; failure tests in focused suite |
| 21c | Optional `clipboard[images]`. | slice 1 | observed: unchanged |
| 21d | Pillow `ImageGrab.grabclipboard` normalization. | slice 1 | observed: unchanged |
| 21e | File-list / URL offers → absence. | slice 1 | observed: unchanged; focused suite includes file-list stub |
| 21f | macOS Aqua independently verified. | slice 1 | observed: README.rst macOS verified retained |
| 22 | This story closes remaining native evidence, not redesign. | slice 4 | observed: docs-only evidence/limits; no paste_image redesign |
| 23 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. | slice 1 | observed: README.rst retains that non-guarantee |
| 24 | Image writing out of scope / deferred. | | G24 |
| 25 | New public image APIs or return shapes out of scope / deferred. | | G25 |
| 26 | Default pytest / CI real-desktop matrix out of scope / deferred. | | G26 |
| 27 | Expanding the four-desktop set out of scope / deferred. | | G27 |
| 28 | HTML, files, inspection, clear, waits, or PRIMARY out of scope / deferred. | | G28 |
| 29 | Contract changes beyond failed-probe honesty belong to a separate decision. | slice 4 | observed: no contract change; honesty-only docs |
| 30 | Requiring at least one successful Windows or Linux verification is deferred. | | G30 |
| 31 | Wayland verification scoped to probed compositor; others remain evidence-limited. | slice 3 | observed: no compositor-scoped verification claimed; Wayland evidence-limited overall |
| 32 | Journey: Windows session → independent opaque PNG → matching size/colors; preservative; floors; README verified. | slice 1 | observed: trigger unmet (no Windows session); 5b/36 path instead |
| 33 | Journey: Windows CF_HDROP-only → `None` without opening paths. | slice 1 | observed: trigger unmet (no Windows session); conditional commitment 8 not owed |
| 34 | Journey: Linux X11 + `xclip` independent success. | slice 2 | observed: trigger unmet (no X11+xclip session); 6b path instead |
| 35 | Journey: Linux Wayland + `wl-paste` compositor-scoped success. | slice 3 | observed: trigger unmet (no Wayland+wl-paste session); 7b path instead |
| 36 | Journey: no usable session → explicit unverified/unsupported note; never verified; all-three limits still complete when honest. | slice 1 | observed: README.rst Windows, X11+xclip, and Wayland+wl-paste each evidence-limited |
| 37 | After this work, in-memory paste_image tests and gated macOS probe still pass; copy/paste/VERSION unchanged. | slice 4 | observed: focused pytest 18 passed, 1 skipped; no copy/paste/VERSION code change |
| 38 | Silent success on an unprobed desktop is forbidden. | slice 1 | observed: README.rst explicitly evidence-limits Windows, X11+xclip, and Wayland+wl-paste |
| 39 | Wayland compositor generalization is forbidden. | slice 3 | observed: README.rst forbids X11/unstated-compositor generalization; no Wayland verified claim |

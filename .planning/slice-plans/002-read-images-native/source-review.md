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
| 1 | Python automation developers and maintainers can trust the documented Windows and Linux image-read floors for delivered `paste_image`. | slice 4 | |
| 2 | For each remaining supported desktop, either independent-producer native proof comparable to the macOS Aqua probe, or an explicit unverified/unsupported evidence limit — never a silent success. | slice 4 | |
| 2a | Independent-producer native proof comparable to the macOS Aqua probe (alternative). | slice 4 | |
| 2b | Explicit unverified/unsupported evidence limit (alternative). | slice 4 | |
| 3 | Text callers remain compatible. | slice 4 | |
| 4 | The verified macOS path remains compatible. | slice 4 | |
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
| 7 | For Linux Wayland with `wl-paste`, either probe (7a) or evidence-limit note (7b). | slice 3 | |
| 7a.1 | Opaque raster size/colors (Wayland probe path). | slice 3 | |
| 7a.2 | Preservative read (Wayland probe path). | slice 3 | |
| 7a.3 | Alpha preserved or documented drop (Wayland probe path). | slice 3 | |
| 7a.4 | Named OS, desktop/compositor, helper, and Pillow floors (Wayland probe path). | slice 3 | |
| 7b | Keep an explicit unverified/unsupported evidence-limit note for that Wayland desktop. | slice 3 | |
| 8 | When a Windows session is available, prove native CF_HDROP / filename-list → `None` without opening paths. | slice 1 | observed: precondition unmet — no Windows session on Darwin; native CF_HDROP case not owed on 5b path |
| 9 | Update README (and related install/evidence docs) so verified floors replace, or honest limits retain, the current "unverified pending SEED-001#read-images-native" wording. | slice 4 | |
| 10 | Default automated tests stay desktop-free. | slice 1 | observed: focused pytest 18 passed, 1 skipped without CLIPBOARD_NATIVE_PROBE; README states in-memory default |
| 11 | Native probes remain explicitly gated (same spirit as CLIPBOARD_NATIVE_PROBE / macOS probe script). | slice 4 | |
| 12 | Reuse `paste_image` / `clipboard[images]` as delivered. | slice 1 | observed: no API/code change; docs-only evidence-limit |
| 13 | All-remaining-desktops evidence-limited still fulfills the story when each limit is explicit. | slice 4 | |
| 14a | Supported desktop: Windows desktop. | slice 1 | observed: README.rst still names Windows as supported target (evidence-limited) |
| 14b | Supported desktop: Linux X11 + `xclip`. | slice 2 | observed: README.rst still names X11+xclip as supported target (evidence-limited) |
| 14c | Supported desktop: Linux Wayland + `wl-paste` scoped to probed compositor. | slice 3 | |
| 15 | macOS Aqua remains verified and compatible; re-proving macOS is not this story's outcome. | slice 1 | observed: README.rst retains macOS Aqua verified wording; no macOS redesign |
| 16 | Do not claim a desktop verified without an independent-producer observation. | slice 1 | observed: README.rst never claims Windows or X11+xclip verified |
| 17 | Do not generalize one Wayland compositor's result to all Wayland environments. | slice 3 | |
| 18 | Do not bypass OS pasteboard / clipboard authorization. | slice 1 | observed: no clipboard access attempted; docs-only |
| 19 | Do not change `paste()`. | slice 1 | observed: no code change to paste/copy/VERSION |
| 20 | Do not treat file-list / URL-only offers as images. | slice 1 | observed: no contract change; in-memory file-list tests still in focused suite |
| 21a | `paste_image()` → Pillow `Image` \| `None`. | slice 1 | observed: unchanged; suite covers contract |
| 21b | `ClipboardImageError` for failures. | slice 1 | observed: unchanged; failure tests in focused suite |
| 21c | Optional `clipboard[images]`. | slice 1 | observed: unchanged |
| 21d | Pillow `ImageGrab.grabclipboard` normalization. | slice 1 | observed: unchanged |
| 21e | File-list / URL offers → absence. | slice 1 | observed: unchanged; focused suite includes file-list stub |
| 21f | macOS Aqua independently verified. | slice 1 | observed: README.rst macOS verified retained |
| 22 | This story closes remaining native evidence, not redesign. | slice 4 | |
| 23 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. | slice 1 | observed: README.rst retains that non-guarantee |
| 24 | Image writing out of scope / deferred. | | G24 |
| 25 | New public image APIs or return shapes out of scope / deferred. | | G25 |
| 26 | Default pytest / CI real-desktop matrix out of scope / deferred. | | G26 |
| 27 | Expanding the four-desktop set out of scope / deferred. | | G27 |
| 28 | HTML, files, inspection, clear, waits, or PRIMARY out of scope / deferred. | | G28 |
| 29 | Contract changes beyond failed-probe honesty belong to a separate decision. | slice 4 | |
| 30 | Requiring at least one successful Windows or Linux verification is deferred. | | G30 |
| 31 | Wayland verification scoped to probed compositor; others remain evidence-limited. | slice 3 | |
| 32 | Journey: Windows session → independent opaque PNG → matching size/colors; preservative; floors; README verified. | slice 1 | observed: trigger unmet (no Windows session); 5b/36 path instead |
| 33 | Journey: Windows CF_HDROP-only → `None` without opening paths. | slice 1 | observed: trigger unmet (no Windows session); conditional commitment 8 not owed |
| 34 | Journey: Linux X11 + `xclip` independent success. | slice 2 | observed: trigger unmet (no X11+xclip session); 6b path instead |
| 35 | Journey: Linux Wayland + `wl-paste` compositor-scoped success. | slice 3 | |
| 36 | Journey: no usable session → explicit unverified/unsupported note; never verified; all-three limits still complete when honest. | slice 1 | observed: README.rst Windows and X11+xclip evidence-limit notes; Wayland still pending later slice |
| 37 | After this work, in-memory paste_image tests and gated macOS probe still pass; copy/paste/VERSION unchanged. | slice 4 | |
| 38 | Silent success on an unprobed desktop is forbidden. | slice 1 | observed: README.rst explicitly evidence-limits Windows and X11+xclip |
| 39 | Wayland compositor generalization is forbidden. | slice 3 | |

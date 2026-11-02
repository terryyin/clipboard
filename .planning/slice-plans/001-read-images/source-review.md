# Source review: SEED-001#read-images

**Launch:** Fresh general-purpose reviewer (no conversation inheritance); inputs
were Goal, Scope (required behavior, supported desktops, restrictions, limits,
rejection constraints), key examples, and settled human amendments (Pillow via
`clipboard[images]`; four-desktop promise with helper docs and evidence limits;
API `paste_image() → Image | None`, failures via exceptions). Reviewer was
told to read no other project files and change nothing.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Python automation developers can retrieve a static raster image copied by an ordinary desktop application through one explicit clipboard operation, without writing platform-specific clipboard code. | slice 6 | |
| 2 | `copy`, `paste`, and `VERSION`, and existing text callers, stay unchanged. | slice 1 | observed: tests/test_paste_image.py::test_text_api_importable_without_pillow; tests/test_clipboard.py |
| 3 | An explicit image-read operation returns a Pillow `Image.Image` with usable raster pixels (dimensions, colors, and alpha when the native offer carries it) for one static image placed on the clipboard by an independent producer. | slice 5 | |
| 4 | The optional `clipboard[images]` extra installs Pillow. | slice 1 | observed: tests/test_paste_image.py::test_images_extra_declares_pillow; pyproject.toml `[project.optional-dependencies] images` |
| 5.1 | Linux install docs name `xclip` (X11). | slice 4 | |
| 5.2 | Linux install docs name `wl-paste` (Wayland). | slice 4 | |
| 6.1 | Native encodings convert behind that Pillow contract: PNG. | slice 5 | |
| 6.2 | Native encodings convert behind that Pillow contract: DIB/DIBV5. | slice 6 | |
| 6.3 | Native encodings convert behind that Pillow contract: macOS image types. | slice 5 | |
| 6.4 | Native encodings convert behind that Pillow contract: Linux image MIME. | slice 6 | |
| 7 | The image-read leaves clipboard contents unchanged. | slice 1 | observed: tests/test_paste_image.py::test_paste_image_absence_and_raster_preservative (before_text/after_text; same_object) |
| 8 | Text-only or empty clipboard is ordinary absence (`None`). | slice 1 | observed: tests/test_paste_image.py::test_paste_image_absence_and_raster_preservative[hello text-None-False] |
| 9 | A file-reference / filename-list offer alone is absence of image (not opened or decoded from disk). | slice 2 | observed: tests/test_paste_image.py::test_file_list_offer_is_absence_without_filesystem_open |
| 10 | Malformed image bytes are a distinguishable failure. | slice 3 | |
| 11.1 | Access denied, unavailable desktop, missing required helper, contention, or transfer failure are distinguishable from absence. | slice 3 | |
| 11.2 | Access denied, unavailable desktop, missing required helper, contention, or transfer failure must not collapse to an empty success. | slice 3 | |
| 12.1 | Supported desktop: Windows desktop. | slice 6 | |
| 12.2 | Supported desktop: macOS pasteboard sessions that grant access. | slice 5 | |
| 12.3 | Supported desktop: Linux X11 with `xclip`. | slice 6 | |
| 12.4 | Supported desktop: Linux Wayland with `wl-paste` where the compositor exposes clipboard data. | slice 6 | |
| 13 | Exact helper/OS floors are evidence-backed during planning and proof. | slice 6 | |
| 14 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. | | X14 |
| 15 | Wayland support is not inferred from one compositor. | slice 6 | |
| 16 | Do not change `paste()` to return images. | slice 1 | observed: clipboard.py still re-exports pyperclip `paste`; tests/test_paste_image.py absence case keeps `paste()` text |
| 17 | Do not bypass OS pasteboard authorization. | slice 5 | |
| 18 | Do not treat URL-only or file-reference offers as images. | slice 2 | observed: tests/test_paste_image.py::test_url_only_offer_is_absence; test_file_list_offer_is_absence_without_filesystem_open |
| 19.1 | Out of scope / deferred: Animation. | | X19.1 |
| 19.2 | Out of scope / deferred: Screenshot capture. | | X19.2 |
| 19.3 | Out of scope / deferred: Image writing. | | X19.3 |
| 19.4 | Out of scope / deferred: Automatic URL fetch. | | X19.4 |
| 19.5 | Out of scope / deferred: Opening file-manager references. | | X19.5 |
| 19.6 | Out of scope / deferred: RTF. | | X19.6 |
| 19.7 | Out of scope / deferred: Arbitrary typed bytes. | | X19.7 |
| 19.8 | Out of scope / deferred: History. | | X19.8 |
| 19.9 | Out of scope / deferred: Cloud sync. | | X19.9 |
| 19.10 | Out of scope / deferred: PNG-bytes-only APIs. | | X19.10 |
| 19.11 | Out of scope / deferred: Library-owned non-Pillow buffers. | | X19.11 |
| 20 | Narrowing first delivery to a subset of the supported desktops is out of scope for this story. | slice 6 | |
| 21 | File-reference-only → no image (independent need: do not perform filesystem reads from clipboard offers). | slice 2 | observed: tests/test_paste_image.py::test_file_list_offer_is_absence_without_filesystem_open (path_hits == []) |
| 22 | Access / helper / malformed failures → not absence (independent need: actionable diagnosis per Shared Boundaries). | slice 3 | |
| 23 | API spelling (settled): `paste_image() → Image \| None`; failures via exceptions. | slice 1 | observed: clipboard.py `paste_image` signature and return; ImportError without extra |
| 24 | Keep the four-desktop promise with helper docs and evidence limits (settled with Pillow via `clipboard[images]`). | slice 6 | |
| E1 | Independent screenshot app has copied a static PNG-capable raster → image-read → Pillow Image with matching width, height, expected opaque colors; clipboard still offers that image. | slice 5 | |
| E2 | Desktop app copied an image with alpha → image-read → alpha preserved when native offer includes it; when a supported desktop drops alpha, docs/tests state that limit. | slice 5 | |
| E3 | Clipboard holds only Unicode text → image-read → `None`; `paste()` still returns the text; clipboard unchanged. | slice 1 | observed: tests/test_paste_image.py::test_paste_image_absence_and_raster_preservative[hello text-None-False] |
| E4 | Windows (or other) clipboard holds only a filename / file-list offer → image-read → `None` (no file open); not an image success. | slice 2 | observed: tests/test_paste_image.py::test_file_list_offer_is_absence_without_filesystem_open |
| E5 | Clipboard holds corrupted image bytes under an image type → image-read → distinguishable failure, not absence and not a partial fake image. | slice 3 | |
| E6 | No usable desktop clipboard / denied pasteboard access / required Linux helper missing → image-read → actionable failure distinct from absence. | slice 3 | |

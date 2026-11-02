# Source review: SEED-001#write-images

**Launch:** Fresh general-purpose reviewer (no conversation inheritance); source-only
inputs: Goal, Scope, key examples and exclusions from
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#write-images`. No plan,
return, product, proof, or suspected omission supplied. No human amendments.

**Reviewer return:** Numbered commitments below (coordinator-retained summary of
the isolated review). Allocation precedes slice-1 acceptance.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| G.1 | Hand a generated static raster to an ordinary desktop app through `clipboard` without a temporary-file re-import | slice 7 | |
| G.2 | After writer exit, an independent image/document app pastes recognizable pixels with correct dimensions and supported transparency | slice 7 | |
| G.3 | G.2 holds on each supported desktop this story claims | slice 7 | |
| G.4 | Text callers stay compatible | slice 1 | observed: tests/test_clipboard.py in-memory copy/paste suite still passes under focused regression |
| G.5 | Delivered `paste_image` stays compatible | slice 1 | observed: tests/test_paste_image.py and tests/test_paste_image_failures.py still pass under focused regression |
| R.1 | Add an explicit public write API (proposed spelling `copy_image`) | slice 1 | observed: clipboard.copy_image is public and callable (tests/test_copy_image.py::test_copy_image_is_public_and_callable) |
| R.2 | The API accepts a Pillow `Image` | slice 1 | observed: copy_image(image) forwards the same Pillow Image to the injectable writer (tests/test_copy_image.py::test_injected_writeclipboard_receives_image) |
| R.3 | The API requires the existing optional `clipboard[images]` extra | slice 1 | observed: without Pillow, copy_image raises ImportError naming images/pillow (tests/test_copy_image.py::test_copy_image_without_pillow_raises_import_error) |
| R.4 | A successful call publishes one static raster offer the desktop can paste | slice 2 | |
| R.5 | Invalid or unloadable input is rejected with `ClipboardImageError` before replacing current clipboard contents | slice 2 | |
| R.6 | A successful write replaces prior text representations so a later paste does not see a stale text offer | slice 2 | |
| R.7 | A successful write replaces prior image representations so a later paste does not see a stale image offer | slice 2 | |
| R.8 | Failures other than successful publication raise `ClipboardImageError` rather than silent no-op | slice 2 | |
| R.8a | Missing helper → `ClipboardImageError` (not silent no-op) | slice 4 | |
| R.8b | Denied access → `ClipboardImageError` (not silent no-op) | slice 3 | |
| R.8c | Transfer failure → `ClipboardImageError` (not silent no-op) | slice 2 | |
| R.8d | Unsupported session → `ClipboardImageError` (not silent no-op) | slice 3 | |
| R.9 | Document Linux helper dependencies: `xclip` on X11 | slice 7 | |
| R.10 | Document Linux helper dependencies: `wl-copy` on Wayland | slice 7 | |
| R.11 | Document supported desktop setup | slice 7 | |
| R.12 | Default automated tests stay desktop-free via an injectable write backend | slice 1 | observed: set_image_writeclipboard injects a fake writer; tests receive the Image with no pasteboard (tests/test_copy_image.py::test_injected_writeclipboard_receives_image; clipboard.set_image_writeclipboard) |
| R.13 | Native proof uses an independent consumer (not a same-library `paste_image` round-trip alone) | slice 3 | |
| R.14 | Native proof stays explicitly gated | slice 3 | |
| R.15 | Successful writes remain pasteable after the writing process exits on each claimed desktop | slice 7 | |
| R.16 | Opaque rasters are required | slice 3 | |
| R.17 | When the native offer carries alpha, preserve it or document a platform drop | slice 3 | |
| R.18 | Convert non-RGB(A) modes to a transferable RGB/RGBA raster before offering | slice 2 | |
| R.19 | Document conversion limits | slice 7 | |
| R.20 | Calling without the images extra raises `ImportError` consistent with `paste_image` | slice 1 | observed: tests/test_copy_image.py::test_copy_image_without_pillow_raises_import_error |
| S.1 | Windows desktop is a supported desktop for this story | slice 6 | |
| S.2 | macOS Aqua is a supported desktop for this story | slice 3 | |
| S.3 | Linux X11 + `xclip` is a supported desktop for this story | slice 4 | |
| S.4 | Linux Wayland + `wl-copy` is a supported desktop, scoped to the compositor actually proved | slice 5 | |
| S.5 | WSL is not an additional guaranteed desktop |  | G-excl-env |
| S.6 | SSH is not an additional guaranteed desktop |  | G-excl-env |
| S.7 | Containers are not an additional guaranteed desktop |  | G-excl-env |
| S.8 | Headless CI is not an additional guaranteed desktop |  | G-excl-env |
| S.9 | Linux X11 writer-exit success is an acceptance requirement (issue #5); not substitutable by evidence-limit | slice 4 | |
| S.10 | Linux Wayland writer-exit success is an acceptance requirement (issue #5); not substitutable by evidence-limit | slice 5 | |
| S.11 | Windows requires independent-consumer + writer-exit proof when a session is available | slice 6 | |
| S.12 | macOS requires independent-consumer + writer-exit proof when a session is available | slice 3 | |
| S.13 | When no usable Windows session exists during execution, record an explicit unverified/unsupported evidence limit rather than claiming verified | slice 6 | |
| S.14 | When no usable macOS session exists during execution, record an explicit unverified/unsupported evidence limit rather than claiming verified | slice 3 | |
| X.1 | Do not overload `copy()` to accept or return images | slice 1 | observed: write path is separate `copy_image`; `copy` remains pyperclip text API (clipboard.py; tests/test_clipboard.py) |
| X.2 | Do not overload `paste()` to accept or return images | slice 1 | observed: write path is separate `copy_image`; `paste` remains pyperclip text API (clipboard.py; tests/test_clipboard.py) |
| X.3 | Do not bypass OS pasteboard / clipboard authorization | slice 3 | |
| X.4 | Do not treat a file-path / file-list / URL offer as fulfilling this image-content story | slice 2 | |
| X.5 | Do not leave a superseded text representation readable after a successful image write | slice 2 | |
| X.6 | Do not leave a superseded image representation readable after a successful image write | slice 2 | |
| X.7 | Do not hang the caller indefinitely waiting to serve clipboard data | slice 3 | |
| X.8 | Do not generalize one Wayland compositor's result to all Wayland environments | slice 5 | |
| D.1 | Path/bytes overloads deferred; callers open to `Image` first |  | G-excl-deferred |
| D.2.1 | Animated APIs deferred |  | G-excl-deferred |
| D.2.2 | Multi-frame APIs deferred |  | G-excl-deferred |
| D.2.3 | Screenshot APIs deferred |  | G-excl-deferred |
| D.3 | File-manager copy offers deferred |  | G-excl-deferred |
| D.4.1 | HTML pasteboards deferred |  | G-excl-deferred |
| D.4.2 | Rich pasteboards deferred |  | G-excl-deferred |
| D.4.3 | Multi-item pasteboards deferred |  | G-excl-deferred |
| D.5 | Bundling GUI toolkits or `win32clipboard` as a required public dependency deferred |  | G-excl-deferred |
| D.6 | Making default pytest / CI require a real desktop deferred |  | G-excl-deferred |
| D.7 | Expanding beyond the four-desktop set deferred |  | G-excl-deferred |
| D.8 | Inventing rollback/atomicity guarantees beyond fail-before-replace deferred |  | G-excl-deferred |
| D.9 | Using `paste_image` alone as native proof remains deferred (insufficient) |  | G-excl-deferred |
| D.10 | Splitting Linux-first vs Win/macOS into separate stories is deferred unless execution evidence forces a resplit |  | G-excl-deferred |
| C.1 | Invalid image input must not replace current content | slice 2 | |
| C.2 | Silent success on an unproved desktop is forbidden | slice 3 | |
| C.3 | Windows-only delivery is forbidden as story completion (issue #5) | slice 7 | |
| C.4 | Wayland compositor generalization is forbidden | slice 5 | |
| E8.1 | In-memory `copy` contract tests still pass | slice 1 | observed: tests/test_clipboard.py under focused regression |
| E8.2 | In-memory `paste` contract tests still pass | slice 1 | observed: tests/test_clipboard.py under focused regression |
| E8.3 | In-memory `paste_image` contract tests still pass | slice 1 | observed: tests/test_paste_image.py and tests/test_paste_image_failures.py under focused regression |
| E8.4 | `VERSION` behaves as before | slice 1 | observed: clipboard.VERSION remains "0.0.5" (clipboard.py); release/version expectations unchanged in focused suites |
| E8.5 | Text-only callers behave as before | slice 1 | observed: tests/test_clipboard.py; copy/paste still re-exported from pyperclip |
| E8.6 | Calling `copy_image` without `clipboard[images]` raises `ImportError` | slice 1 | observed: tests/test_copy_image.py::test_copy_image_without_pillow_raises_import_error |

# Source review: SEED-001#clear-clipboard

**Launch:** fresh general-purpose sub-agent, no conversation inheritance, no file access instructed; launched 2026-11-03 by the execution coordinator before slice 1 acceptance.
**Input:** the story's Goal, Scope, Key examples, and recorded decisions from `.planning/seeds/SEED-001-clipboard-true-to-its-name.md#clear-clipboard`, verbatim (Investigation, Considered alternatives, Architecture, plan, and product omitted).
**Reviewer notes:** read 8.8 (prior content intact) as an instance of 4.3, not a general rule; X11 missing-helper wording waits on the mechanism; the Windows retry bound (2.2b) and the seconds bound (4.2) are not stated to be the same value.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| G1 | Python users and automation developers can deliberately empty the current clipboard with one call | slice 6 | |
| G1a | The clear removes every representation that another application or this library offered | slice 6 | |
| G1a.1 | text | slice 6 | |
| G1a.2 | HTML | slice 6 | |
| G1a.3 | image | slice 6 | |
| G1a.4 | file list | slice 6 | |
| G1a.5 | unknown types | slice 6 | |
| G2 | The result of the call is the same on every supported desktop | slice 6 | |
| G3 | Users no longer rely on `copy("")`, which empties the clipboard on Windows and `wl-copy` but leaves an empty text offer on macOS and `xclip` (qualification) | slice 2 | observed: README.rst clear() section contrasts copy("") empty text offer; probe copy_empty_vs_clear case |
| G4 | A failed clear is reported, so the user never believes content is gone when it is not | slice 6 | |
| G5 | Adds the ordinary clipboard "clear" action beside the read and write operations | slice 1 | observed: clipboard/__init__.py __all__ has clear beside copy/paste; tests/test_clear.py::test_clear_is_public_without_images_extra |
| G6 | Clear keeps its meaning as more content kinds are added | slice 6 | |
| 1.1 | A new public `clear()` exists | slice 1 | observed: tests/test_clear.py::test_clear_is_public_without_images_extra; Makefile test-package asserts callable(clipboard.clear) |
| 1.2 | `clear()` does not need the `clipboard[images]` extra | slice 1 | observed: tests/test_no_pillow_extra.py "clear" scenario (PIL blocked, fake called, no PIL loaded) |
| 1.3 | `clear()` leaves the current CLIPBOARD with no offer at all | slice 6 | |
| 1.3a | No old representation is readable afterwards | slice 6 | |
| 1.3b | No empty placeholder (such as an empty text type) is left in its place | slice 6 | |
| 1.4 | Afterwards the library's readers report ordinary absence | slice 6 | |
| 1.4.1 | `paste()` returns `""` | slice 6 | |
| 1.4.2 | `paste_html()` returns `None` | slice 6 | |
| 1.4.3 | `paste_image()` returns `None` | slice 6 | |
| 1.4.4 | `paste_files()` returns `None` | slice 6 | |
| 1.4.5 | `inspect()` returns empty `kinds` and `formats` | slice 6 | |
| 1.5 | Independent native consumers also see an empty clipboard | slice 6 | |
| 1.6 | `clear()` returns `None` | slice 1 | observed: tests/test_clear.py::test_clear_calls_injected_clearer_once_and_returns_none (clear() is None) |
| 1.7 | Calling `clear()` on a clipboard that is already empty succeeds with no error | slice 6 | |
| 1.8 | Calling `clear()` twice in a row succeeds with no error | slice 6 | |
| 1.9 | When this library's own Linux background owner (from `copy_image`, or later writers) is serving the old offer, clearing ends that offer | slice 5 | observed: CI run 41654014945 native-linux-x11-clear step 4 (copy_image xclip owner exits after child clear) and CI run 41651498162 native-linux-wayland-clear step 5 (wl-copy image owner exits) |
| 1.9a | No helper process keeps serving the old offer | slice 5 | observed: CI run 41654014945 native-linux-x11-clear step 4 and CI run 41651498162 native-linux-wayland-clear step 5: library owner PIDs exited within 5 s |
| 2.1 | macOS Aqua: clear the `NSPasteboard` general pasteboard with `clearContents` | slice 2 | observed: clipboard/_clear_macos.py generalPasteboard() clearContents(); tests/test_clear_macos.py::test_darwin_default_clearer_runs_bounded_osascript_clear; native probe html_and_text types_after == [] |
| 2.2 | Windows desktop: call `OpenClipboard` / `EmptyClipboard` / `CloseClipboard` through user32 | slice 6 | |
| 2.2a | Windows retries the open while another process holds the clipboard | slice 6 | |
| 2.2b | The retry stays within a documented bound | slice 6 | |
| 2.3 | Linux X11: give up CLIPBOARD ownership so no owner remains | slice 5 | observed: clipboard/_clear_x11.py + _x11_relinquish.py XSetSelectionOwner(CLIPBOARD, None); CI run 41654014945 native-linux-x11-clear steps 2-5 TARGETS no owner |
| 2.3a | `xclip` has no clear operation; planning chooses the X11 mechanism (qualification) | slice 5 | observed: plan chose libX11 ctypes; CI run 41654014945 native-linux-x11-clear step 2 settled it (no xsel needed) |
| 2.4 | Linux Wayland: `wl-copy --clear` | slice 4 | observed: clipboard/_clear_wayland.py runs wl-copy --clear; CI run 41651498162 native-linux-wayland-clear steps 2-6 ok |
| 2.5 | Session selection uses the existing writer rule: Wayland when `WAYLAND_DISPLAY` or the session type says so | slice 4 | observed: clipboard/_clear.py uses _desktop._is_linux_wayland; tests/test_clear_wayland.py::test_wayland_default_clearer_runs_bounded_wl_copy_clear [wayland-only, both-sessions, xdg-session-type] |
| 2.5a | This matches how image write, HTML and inspect choose a session (qualification) | slice 4 | observed: same _desktop._is_linux_wayland rule as image write / HTML / inspect; tests/test_clear_wayland.py both-sessions case selects Wayland |
| 3.1 | On X11, `inspect()` returns an empty snapshot when CLIPBOARD has no owner (`xclip` "target TARGETS not available") instead of raising | slice 3 | observed: CI run 41649816028 (342f12c) native-linux-x11-clear step 1: xclip 0.13 exit 1 'target TARGETS not available', inspect() empty; tests/test_inspect_x11.py::test_unowned_clipboard_inspects_as_empty_snapshot (both wordings) |
| 3.2 | On Wayland, `inspect()` returns an empty snapshot when nothing is copied (`wl-paste` "Nothing is copied" / "No selection") instead of raising | slice 3 | observed: CI run 41649816028 (342f12c) native-linux-wayland-clear step 1: wl-paste -l exit 1 'Nothing is copied', inspect() empty; tests/test_inspect_wayland.py::test_nothing_copied_inspects_as_empty_snapshot (both wordings) |
| 3.3 | Reason: inspect's contract already says an empty offer gives an empty snapshot (qualification) | slice 3 | observed: clipboard/_desktop.py _xclip_targets_inspect / _wl_paste_list_types_inspect return () on no owner / nothing copied |
| 3.4 | Other non-zero helper exits still raise (exclusion) | slice 3 | observed: tests/test_inspect_x11.py test_xclip_helper_failure_raises_* and tests/test_inspect_wayland.py test_wl_paste_helper_failure_raises_* still raise |
| 4.1 | A failed clear raises `ClipboardContentError` naming the cause, never a silent success, for each listed cause | slice 6 | |
| 4.1.1 | No visible desktop session | slice 5 | observed: tests/test_clear.py no-session test: 'no desktop session is visible' |
| 4.1.2 | Missing helper: `wl-clipboard` install hint on Wayland; names whatever the chosen mechanism needs on X11 | slice 5 | observed: CI run 41651498162 native-linux-wayland-clear step 7 names wl-clipboard; tests/test_clear_x11.py libx11 failure names libx11-6; CI run 41654014945 native-linux-x11-clear step 6 names DISPLAY |
| 4.1.3 | Windows clipboard held past the bound | slice 6 | |
| 4.1.4 | Access denied | slice 6 | |
| 4.1.5 | A helper or native call fails | slice 6 | |
| 4.2 | Failures are reported within a bound of seconds | slice 6 | |
| 4.3 | A failed clear promises nothing about what is on the clipboard afterwards beyond what the platform did (exclusion) | slice 6 | |
| 5.1 | Clearing acts on the current CLIPBOARD once (qualification) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.2 | Content offered after the clear is a newer copy, not a failed clear (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.2.1 | Another application copying (example) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.2.2 | A clipboard manager immediately offering its saved entry again (KDE Klipper, compositor persistence) (example) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.2.3 | A sync service (example) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.3 | `clear()` does not check the clipboard again afterwards (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.4 | `clear()` does not report such a re-offer (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.5 | `clear()` does not erase any of the following (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.5.1 | OS clipboard history (Windows Win+V, managers' saved entries) (exclusion) | slice 6 | |
| 5.5.2 | Cloud or Universal Clipboard copies (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.5.3 | Remote devices (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 5.6 | `clear()` claims no secure deletion (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |
| 6.1 | An independent producer puts HTML + text on the clipboard; after `clear()`, an independent consumer sees no types | slice 6 | |
| 6.2 | Separately, an independent image producer; after `clear()`, an independent consumer sees no types | slice 6 | |
| 6.3 | Proof sessions, one per platform | slice 6 | |
| 6.3.1 | macOS: gated owner-desktop probe (`CLIPBOARD_NATIVE_PROBE=1`), `osascript` producer, type list and `pbpaste` consumers | slice 2 | observed: tests/test_clear_native_macos.py + scripts/probe_macos_native_clear.py passed under CLIPBOARD_NATIVE_PROBE=1 on macOS 26.6.2 (osascript producers, JXA types + pbpaste consumers) |
| 6.3.2 | Windows: gated `windows-latest` job, PowerShell `Set-Clipboard` producer, format enumeration / `Get-Clipboard` consumers | slice 6 | |
| 6.3.3 | X11: the existing Xvfb + `xclip` job, with no clipboard manager | slice 5 | observed: CI run 41654014945 native-linux-x11-clear (Xvfb 2:21.1.22, xclip 0.13): tests/test_clear_native_linux_x11.py PASSED |
| 6.3.4 | Wayland: the existing Sway + `wl-clipboard` job | slice 4 | observed: CI run 41651498162 native-linux-wayland-clear (Sway 1.11, wl-clipboard 2.2.1): tests/test_clear_native_linux_wayland.py PASSED |
| 6.4 | The README names those sessions and their helper versions | slice 6 | |
| 6.5 | GNOME, KDE and any desktop with a clipboard manager are evidence limits, not verified claims (exclusion) | slice 6 | |
| 6.6 | Default pytest stays desktop-free through an explicit injection seam | slice 1 | observed: clipboard/_clear.py set_clipboard_clearer seam; tests/test_clear.py fakes only, desktop-free |
| 7.1 | Clearing PRIMARY (SEED-001#primary-selection) (exclusion) | slice 6 | |
| 7.2 | Clearing the macOS Find pasteboard (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph: only the general pasteboard, not the Find pasteboard; _clear_macos.py generalPasteboard only |
| 7.3 | Clearing other named pasteboards (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph: not other named pasteboards; _clear_macos.py generalPasteboard only |
| 7.4 | Clearing only one kind while keeping others (exclusion) | slice 6 | |
| 7.5 | Snapshot and restore (exclusion) | slice 6 | |
| 7.6 | Erasing history, clipboard managers, or synced copies (exclusion) | slice 6 | |
| 7.7 | Checking that the clipboard stays empty afterwards (exclusion) | slice 6 | |
| 7.8 | WSL, SSH, containers and headless CI are not guaranteed desktops (exclusion) | slice 6 | |
| 7.9 | Changing what `copy("")` does belongs to SEED-001#portable-text (exclusion) | slice 6 | |
| 8.1 | HTML + text from another app, `clear()` returns `None`; `paste()` `""`, `paste_html()` `None`, `inspect()` empty; independent paste inserts nothing | slice 6 | |
| 8.2 | Image from another app, `clear()`; `paste_image()` `None`, no independent consumer can read it | slice 6 | |
| 8.3 | Already empty: `clear()` returns `None`, and again returns `None` | slice 6 | |
| 8.4 | macOS `copy("")` leaves `inspect().kinds == {"text"}`; `clear()` leaves `inspect().formats == ()` on every supported desktop | slice 6 | |
| 8.5 | X11: `copy_image` background `xclip` owner; after `clear()` it stops serving and exits; `xclip -o -t TARGETS` reports no owner | slice 5 | observed: CI run 41654014945 native-linux-x11-clear step 4: copy_image xclip owner exits after clear(), xclip -o -t TARGETS reports no owner |
| 8.6 | X11 no owner: `inspect()` empty snapshot instead of raising; same on Wayland when nothing is copied | slice 3 | observed: CI run 41649816028 (342f12c) both clear jobs step 1: inspect() empty, paste() '', paste_html/paste_files/paste_image None on fresh Xvfb and fresh Sway |
| 8.7 | Linux with neither `DISPLAY` nor `WAYLAND_DISPLAY`: `clear()` raises saying no desktop session is visible; Wayland without `wl-copy`: error names `wl-clipboard` | slice 5 | observed: tests/test_clear.py no-session test; CI run 41651498162 native-linux-wayland-clear step 7 (PATH without wl-copy names wl-clipboard) |
| 8.8 | Windows held past the bound: raises naming the held clipboard, previous content still there; released within the bound: succeeds | slice 6 | |
| 8.9 | KDE Klipper re-offer after `clear()` is a newer offer outside the promise; the README names it | slice 2 | observed: README.rst clear() Boundary paragraph names KDE Klipper prevent empty clipboard as a newer offer |
| 9.1 | `clear()` means "no offer at all"; an empty placeholder does not count (qualification) | slice 6 | |
| 9.2 | The Linux inspect empty-offer change is included in this story (qualification) | slice 3 | observed: slice 3 commit 342f12c changes the Linux inspect listings in clipboard/_desktop.py |
| 9.3 | A clipboard manager's re-offer after the clear is outside the promise and is not detected (exclusion) | slice 2 | observed: README.rst clear() Boundary paragraph (no re-check in clipboard/_clear.py) |

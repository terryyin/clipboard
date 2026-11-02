# Source review: SEED-001#portable-text

Launch: fresh general-purpose sub-agent, no conversation inheritance, 2026-11-02, coordinator Hitomi-chan.
Input: only the story section `.planning/seeds/SEED-001-clipboard-true-to-its-name.md` lines 244–438 (heading "Use the text clipboard reliably and diagnose unavailable access") copied verbatim to a temporary file; instructed to read nothing else, change nothing, and return numbered commitments, examples and exclusions without slice ownership.
Return: retained below verbatim in substance (commitment text condensed where the reviewer quoted at length).

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| G1 | Existing users of `copy(text)` / `paste()` get exact Unicode text exchange with independent desktop applications on the supported desktops (5a) | slice 7 | |
| G2 | When the desktop clipboard cannot be reached, users get a bounded, named failure instead of a silent `""` or no-op | slice 7 | |
| G3 | Users can trust the simplest API and recover from session problems without guessing; the baseline behind the package name | slice 7 | |
| 1a | `copy(text)` replaces the clipboard with exactly `text` | slice 7 | |
| 1b | `paste()` returns exactly the text the clipboard offers, as a `str` | slice 7 | |
| 1c.1 | Unicode and emoji survive unchanged in both directions | slice 7 | |
| 1c.2 | Multiline strings survive unchanged in both directions | slice 7 | |
| 1c.3 | Leading and trailing whitespace survives unchanged in both directions | slice 7 | |
| 1c.4 | The empty string survives in both directions (per D4: `paste()` then returns `""`) | slice 7 | |
| 1d | 1c holds when the Python process has no UTF-8 locale (launchd, cron, IDE-spawned) | slice 3 | |
| 1e | Text written stays pasteable after the Python process exits (Linux via helper background owner; delegated paths carry no lifetime promise) | slice 7 | |
| 1f | `paste()` returns `""` for ordinary absence: empty clipboard or no text representation (image-only) | slice 6 | |
| 1g | `paste()` never returns `None` | slice 1 | observed: observed: tests/test_clipboard.py test_paste_returns_empty_string_when_reader_offers_no_text (reader None → "" str) |
| 1h | Native line endings pass through untranslated: Windows app text comes back with `\r\n` | slice 6 | |
| 1i | `paste().splitlines()` is the portable way to split lines (guidance) | slice 7 | |
| 2a.1 | A missing helper raises `ClipboardContentError` | slice 5 | |
| 2a.2 | No visible desktop session raises `ClipboardContentError` | slice 2 | |
| 2a.3 | A display or compositor that no longer answers raises `ClipboardContentError` | slice 5 | |
| 2a.4 | Denied access raises `ClipboardContentError` (macOS Paste-from-Other-Apps denial unverified; may stay an evidence limit) | slice 7 | |
| 2a.5 | A stalled clipboard owner raises `ClipboardContentError` | slice 6 | |
| 2a.6 | Helper or transfer failure raises `ClipboardContentError` | slice 5 | |
| 2b | The error names the cause, and the fix where one is known | slice 5 | |
| 2b.1 | Known fix: install hint naming `xclip` / `wl-clipboard` | slice 2 | |
| 2b.2 | Known cause message: no `DISPLAY` or `WAYLAND_DISPLAY` | slice 2 | |
| 2b.3 | Known cause message: the failing helper's own message | slice 5 | |
| 2c | Failure arrives within a documented bound of seconds | slice 7 | |
| 2d.1 | Never an indefinite wait | slice 6 | |
| 2d.2 | Never a fabricated `""` | slice 5 | |
| 2d.3 | Never a silent no-op write | slice 5 | |
| 2e | Linux helper exit status and stderr are read, not discarded | slice 5 | |
| 2f | Non-UTF-8 declared native text is decoded by that declaration (X11 `STRING` Latin-1) or reported as `ClipboardContentError` | slice 4 | |
| 2g | `UnicodeDecodeError` never escapes `paste()` | slice 5 | |
| 2h | Empty text and failed access never share `""`; unknown helper stderr wording defaults to failure | slice 5 | |
| 2i | Text failures carry the pyperclip or helper error as `__cause__` | slice 1 | observed: observed: tests/test_clipboard.py test_backend_failures_become_content_errors (__cause__ is original), test_default_backend_translates_pyperclip_failure |
| 3a | A `str` containing `\x00` raises `ClipboardContentError` before the clipboard is replaced | slice 1 | observed: observed: tests/test_clipboard.py test_copy_rejects_lossy_text_before_writing ("a\x00b" raises naming NUL; writes == []; paste() still "previous") |
| 3b | A `str` that cannot be UTF-8 encoded (lone surrogate) fails the same way, before replacing | slice 1 | observed: observed: tests/test_clipboard.py test_copy_rejects_lossy_text_before_writing ("\ud800" raises naming UTF-8; writes == []; paste() still "previous") |
| 3c | No in-memory fallback presented as the system clipboard | slice 1 | observed: observed: clipboard/_text.py default backend delegates to pyperclip only; in-memory fake exists only in tests/conftest.py fake_text_clipboard |
| 3d | The injection seam used by tests is explicit | slice 1 | observed: observed: clipboard.set_text_clipboard_writer / set_text_clipboard_reader in clipboard/_text.py and __all__; tests/conftest.py fake_text_clipboard |
| 4a.1 | `copy` / `paste` keep their names | slice 1 | observed: observed: clipboard/__init__.py exports copy, paste from clipboard._text |
| 4a.2 | `copy` / `paste` keep their positional signatures | slice 1 | observed: observed: clipboard/_text.py copy(text), paste(); tests/test_clipboard.py test_copy_paste_round_trip_through_text_seam calls positionally |
| 4a.3 | `copy` / `paste` keep their `str` results | slice 1 | observed: observed: tests/test_clipboard.py test_copy_paste_round_trip_through_text_seam asserts type(result) is str |
| 4b | `pyperclip` stays a dependency | slice 1 | observed: observed: pyproject.toml pyperclip dependency unchanged; clipboard/_text.py default backend imports pyperclip |
| 4c | Working text access this story does not own keeps working through pyperclip with only failure translation | slice 2 | |
| 4c.1 | WSL (`clip.exe` / PowerShell bridge) | slice 2 | |
| 4c.2 | A mechanism the caller selected with `pyperclip.set_clipboard` | slice 2 | |
| 4c.3 | X11 desktops with only `xsel` | slice 2 | |
| 4c.4 | X11 desktops with only Klipper | slice 2 | |
| 4c.5 | X11 desktops with only Qt | slice 2 | |
| 4d | The 4c paths carry no new bounded-failure or lifetime promise and are documented as unverified | slice 7 | |
| 4e | Non-`str` arguments keep pyperclip's `str()` coercion (`copy(42)` copies `"42"`) | slice 1 | observed: observed: tests/test_clipboard.py test_copy_coerces_non_str_like_pyperclip (42 → writer gets "42") |
| 4f | README notes that a caller catching `pyperclip.PyperclipException` now sees a change | slice 7 | |
| 5a.1 | Owned default path: Windows desktop (`CF_UNICODETEXT`) | slice 6 | |
| 5a.2 | Owned default path: macOS Aqua (`pbcopy` / `pbpaste` with a UTF-8 locale) | slice 3 | |
| 5a.3 | Owned default path: Linux X11 (`xclip`, `UTF8_STRING` first) | slice 4 | |
| 5a.4 | Owned default path: Linux Wayland (`wl-copy` / `wl-paste`, background owner), named compositor only | slice 5 | |
| 5b | Session selection keeps pyperclip's order so no working user changes mechanism | slice 2 | |
| 5b.1 | WSL first | slice 2 | |
| 5b.2 | Then Wayland when `WAYLAND_DISPLAY` is set and both `wl-copy` and `wl-paste` are on `PATH` | slice 2 | |
| 5b.3 | Otherwise X11 when `DISPLAY` is set | slice 2 | |
| 6a | X11 and Wayland proven with independent producers/consumers under gated Xvfb + `xclip` and Sway + `wl-clipboard` jobs | slice 5 | |
| 6a.1 | Round trip after the writer exits | slice 5 | |
| 6a.2 | Dead `DISPLAY` / stale `WAYLAND_DISPLAY` | slice 5 | |
| 6a.3 | Helper off `PATH` | slice 5 | |
| 6b | Windows proven under a gated `windows-latest` job using PowerShell `Set-Clipboard` / `Get-Clipboard` | slice 6 | |
| 6b.1 | Round trip | slice 6 | |
| 6b.2 | CRLF | slice 6 | |
| 6b.3 | Held clipboard | slice 6 | |
| 6c | macOS proven with an owner-desktop probe (`CLIPBOARD_NATIVE_PROBE=1`) using independent `osascript` / `pbpaste` | slice 3 | |
| 6c.1 | The macOS probe includes a no-locale subprocess | slice 3 | |
| 6d | A desktop without that observation is a README evidence limit, not a verified claim | slice 7 | |
| 6e | Default pytest stays desktop-free through an explicit text seam | slice 1 | observed: observed: make check 335 passed / 16 skipped desktop-free; in-process text tests use tests/conftest.py fake_text_clipboard |
| E1a | `copy("  héllo 👋\nline 2 ")` then exit → independent consumer shows exactly those characters, spaces and newline | slice 7 | |
| E1b | Independent producer copies the same text → `paste()` returns it exactly | slice 7 | |
| E2a | macOS no-locale process `copy("héllo 👋")` → `pbpaste` in user terminal shows `héllo 👋` | slice 3 | |
| E2b | Same no-locale process → `paste()` returns `héllo 👋` | slice 3 | |
| E3 | `copy("")` → `paste()` returns `""` on every supported desktop (other representations not promised) | slice 7 | |
| E4a | Clipboard holds `keep` → `copy("a\x00b")` raises naming the NUL → `paste()` still returns `keep` | slice 3 | |
| E4b | Same for `"\ud800"`: raises, clipboard keeps `keep` | slice 3 | |
| E5a | Linux `DISPLAY=:99` with no server, `xclip` installed → `paste()` raises quoting xclip's display failure within the bound | slice 4 | |
| E5b | Same setup → `copy("x")` raises instead of returning as if written | slice 4 | |
| E5c | Same with `WAYLAND_DISPLAY` naming a socket whose compositor is gone | slice 5 | |
| E6a | Neither `DISPLAY` nor `WAYLAND_DISPLAY` → `paste()` raises saying no desktop session is visible | slice 2 | |
| E6b | `DISPLAY` set and no `xclip` on `PATH` → error names `xclip` and its install hint | slice 4 | |
| E7a | X11 CLIPBOARD owner that never answers → `paste()` raises after the documented bound | slice 4 | |
| E7b | Windows clipboard held open past the bound → raises | slice 6 | |
| E7c | Windows clipboard released within the bound → succeeds as before | slice 6 | |
| E8 | Image-only clipboard → `paste()` returns `""` and `inspect()` reports the image kind; no exception | slice 6 | |
| E9a | Windows Notepad copies two lines → `paste()` returns `"line 1\r\nline 2"` | slice 6 | |
| E9b | `copy("line 1\nline 2")` pastes into Notepad as two lines (hypothesis to settle in Windows job) | slice 6 | |
| E10a | WSL → `copy` / `paste` keep using the existing Windows bridge | slice 2 | |
| E10b | WSL with failing `powershell.exe` → raises `ClipboardContentError` rather than `""` | slice 2 | |
| D1 | Text failures use `ClipboardContentError`; its meaning grows from rich content to clipboard content including text | slice 1 | observed: observed: clipboard/_errors.py ClipboardContentError docstring names text; tests/test_clipboard.py test_backend_failures_become_content_errors |
| D2 | Non-`str` arguments keep pyperclip's coercion | slice 1 | observed: observed: tests/test_clipboard.py test_copy_coerces_non_str_like_pyperclip |
| D3 | No newline translation on either side | slice 6 | |
| D4 | `copy("")` promises only that `paste()` then returns `""` | slice 7 | |
| ALT-a | Considered: keep bare re-export and document limits (weighed, not chosen) | slice 7 | |
| ALT-b | Considered: wrap pyperclip only (weighed, not chosen) | slice 7 | |
| ALT-c | Considered: add `copy_text` / `paste_text` beside unchanged API (weighed, not chosen) | slice 7 | |
| ALT-d | Considered: upstream fixes to pyperclip, welcome in parallel | slice 7 | |
| ALT-R | Recommended: own the four default paths (5a), delegate everything else with failure translation (4c) | slice 7 | |
| X1 | Excluded: newline normalization on write or read | slice 7 | |
| X2 | Excluded: rejecting `bytes` / `None` / other non-`str` input | slice 7 | |
| X3 | Excluded: PRIMARY selection | slice 7 | |
| X4 | Excluded: clearing other representations | slice 7 | |
| X5 | Excluded: waiting for text | slice 7 | |
| X6 | Excluded: RTF | slice 7 | |
| X7 | Excluded: a macOS AppKit (`pyobjc`) text path | slice 7 | |
| X8 | Excluded: verified support for `xsel`, Klipper, Qt (still working per 4c) | slice 7 | |
| X9 | Excluded: verified support for Cygwin, SSH, containers, headless CI, remote desktops (E6a/E6b still promised) | slice 7 | |
| X10 | Excluded: persistence across logout or reboot | slice 7 | |
| X11 | Excluded: new bounded-failure or lifetime promise on delegated paths | slice 7 | |
| X12 | Excluded: whether other representations remain after `copy("")` | slice 7 | |
| X13 | Excluded: unifying text Wayland selection with `paste_html` / `paste_files` rules (desktop-helpers decision) | slice 7 | |

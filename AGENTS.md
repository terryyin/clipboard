# Clipboard

A small Python library exposing `copy`, `paste`, and `VERSION`. Text
`copy` / `paste` are package-owned on macOS (`pbcopy` / `pbpaste`), Linux X11
(`xclip`) and Wayland (wl-clipboard), use pyperclip's `CF_UNICODETEXT` backend
on Windows, and delegate to pyperclip elsewhere (WSL, X11 without `xclip`, other
platforms; a resolved pyperclip mechanism never displaces an owned backend,
only `set_text_clipboard_writer` / `set_text_clipboard_reader` delegate
deliberately); every text
failure raises `ClipboardContentError` (`paste()` returns `""` for absence,
never `None`). It also offers optional image read/write via `paste_image` /
`copy_image` when the `clipboard[images]` extra (Pillow) is installed, HTML
dual-offer writes and fragment reads via `copy_html` / `paste_html`, local file-list
reads via `paste_files`, local file-list copy offers via `copy_files` (writer
seam `set_files_clipboard_writer`; validation before the clipboard is
replaced), non-mutating offer inspection via `inspect`
(kinds + native formats; no images extra), and `clear` (clearer seam
`set_clipboard_clearer`; no offer at all afterwards; native on all four
desktops: macOS Aqua, Linux Wayland (`wl-copy --clear`), Linux X11 (libX11
`XSetSelectionOwner` via `ctypes` in a bounded child) and Windows (user32
`EmptyClipboard` after inspect's bounded `OpenClipboard` retry), Linux with
no session raises "no desktop session is visible", other platforms raise
"not available"). Image access/helper/transfer or
malformed-image failures raise `ClipboardImageError` rather than returning
`None` (or silently succeeding on write). HTML, file-list (`paste_files` and
`copy_files`), inspect, and clear invalid-input, access, helper, transfer,
enumeration, or malformed-envelope failures raise
`ClipboardContentError` (`paste_html` returns `None` only when no HTML is
offered). Linux session detection, helper-failure detail formatting,
CLIPBOARD type listing (`xclip` TARGETS / `wl-paste --list-types`), and
empty-clipboard classification (`xclip` no-owner / `wl-paste` nothing-copied
wordings, which read as absence) live in private `clipboard/_desktop` with
per-caller failure modes; content-kind
modules must not copy those helpers. On a session with both `DISPLAY` and
`WAYLAND_DISPLAY`, `paste_files` and `copy_files` still select X11 while
HTML/inspect/image write select Wayland. Gated Windows `paste_html` native proof fails the job
when the probe reports an evidence limit (no skip).

Use Nix for development tools, as in the neighboring Lizard project. Run tools
with `nix develop -c <command>`; Git commands can run directly. Nix pins the
interpreter and tools in `flake.lock`; uv pins Python dependencies in `uv.lock`.

- Setup: `nix develop -c make deps`
- Check Python: `nix develop -c make check`
- Check GitHub Actions: `nix develop -c make lint-workflows`
- Build and validate distributions: `nix develop -c make build`
- Build and test installed distributions: `nix develop -c make test-package`
- Format Python: `nix develop -c make format`

Preserve the public API and keep the version in `clipboard.VERSION`.
Default tests use an in-memory clipboard backend so CI needs no desktop
session; optional native text / pasteboard / file-list probes stay gated via
`CLIPBOARD_NATIVE_PROBE` (see README Evidence, e.g.
`scripts/probe_macos_native_paste_image.py`, the text probes
`tests/test_text_native_{macos,linux_x11,linux_wayland,windows}.py`, the
`clear` probes `tests/test_clear_native_{macos,linux_wayland,linux_x11,windows}.py`, and the
`copy_files` probes
`scripts/probe_{macos,windows,linux_x11,linux_wayland}_native_copy_files.py`).
Desktop-free tests must pass on every matrix OS: fake the platform only via
the `fake_platform` fixture (never `sys.platform`; the `tests/conftest.py`
guard fails it), use file names valid on every OS (host-only names such as
`"` or `\` only as gated additions shared expectations ignore), supply
POSIX-only stdlib attributes (`os.killpg`) through fakes, and assert the error
type plus the named platform rather than copied message wording.
Release setup and maintainer steps are documented in `docs/releasing.md`.
Project-owned retrospective findings live in `ProjectFindings.md`; process
findings about published Open Dough guidance stay in `DearDough.md`, which
also holds the shared `DD-NNN` numbering for both files.
Never create or push a release tag unless the maintainer explicitly requests it.

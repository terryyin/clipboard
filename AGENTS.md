# Clipboard

A small Python library exposing `copy`, `paste`, and `VERSION` through
pyperclip, plus optional image read/write via `paste_image` / `copy_image`
when the `clipboard[images]` extra (Pillow) is installed. Access, helper,
transfer, or malformed-image failures raise `ClipboardImageError` rather than
returning `None` (or silently succeeding on write).
HTML write/read via `copy_html` / `paste_html` needs no extra; its access,
helper, transfer, or malformed-envelope failures raise `ClipboardContentError`
(`paste_html` returns `None` only when no HTML is offered).

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
session; optional native pasteboard probes stay gated via
`CLIPBOARD_NATIVE_PROBE` (see README and
`scripts/probe_macos_native_paste_image.py`).
Release setup and maintainer steps are documented in `docs/releasing.md`.
Never create or push a release tag unless the maintainer explicitly requests it.

# Plan: Fail fast when packaged apps cannot run the X11 clear helper

**Identity:** SEED-001#x11-clear-packaged-apps
**Source:** [Fail fast when packaged apps cannot run the X11 clear helper](../../seeds/SEED-001-clipboard-true-to-its-name.md#x11-clear-packaged-apps)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

One outcome: on the native Linux X11 clear path, a recognized frozen runtime
(`sys.frozen` truthy) or a helper script that is not a file on the
filesystem raises an X11-specific, actionable `ClipboardContentError` before
any child starts; the README documents the limit; and `make test-package`
proves, for the wheel and the sdist, that the installed helper launches and
reports a structured failure with an unusable `DISPLAY`.

Exclusions (from the story): any frozen or archive-only X11 clear support,
guards on other platforms or other helper-launching writers (the sibling
SEED-001#bounded-helper-owner-write owns a shared launcher for writers),
frozen runtimes that set no `sys.frozen` beyond the missing-file guard, and
native clear probe changes. Ordinary installations keep the existing command,
`_X11_CLEAR_TIMEOUT_S`, classification and messages.

Assumption: the guard lives in `clipboard/_clear_x11.py` beside
`_relinquish_command` (PFE: the existing launcher, `_error` prefix and
`ClipboardContentError` already own this path; nothing elsewhere launches
`_x11_relinquish.py`). The packaging smoke extends the existing
`test-package` Makefile loop, which CI already runs on `ubuntu-latest`
(`.github/workflows/ci.yml:46`).

## Outside-in proof

| Key example | Observable signal | Owning slice |
| --- | --- | --- |
| 1 frozen app | Desktop-free test: `fake_platform` Linux, `DISPLAY` only, `sys.frozen = True` (monkeypatched, `raising=False`), `subprocess.run` faked to record calls: `clipboard.clear()` raises `ClipboardContentError` naming X11 and `set_clipboard_clearer`; zero recorded launches. Fails today (observed below: the child is launched). | 1 |
| 1 with bundled source | Same with `_RELINQUISH_SCRIPT` an existing file: still raises, zero launches. | 1 |
| 2 archive-only | `_RELINQUISH_SCRIPT` set to a path inside a zip (not a file): raises naming the missing helper file and `set_clipboard_clearer`; zero launches. Fails today ("helper exited with status 2"). | 1 |
| 3 ordinary install | Existing `tests/test_clear_x11.py` launch-command, classification and timeout tests stay green unchanged. | 1 |
| 4 unaffected paths | Frozen + Wayland and frozen + caller clearer: `clear()` reaches the Wayland/caller path (existing fakes), no X11 guard error. | 1 |
| README | X11 clear paragraph states the frozen / archive-only limit and the `set_clipboard_clearer` remedy. | 1 |
| 5 packaging | `./scripts/dev make test-package`: for each of `dist/*.whl` and `dist/*.tar.gz`, from an isolated install with cwd outside the source tree, the installed `_relinquish_command()` helper path is under the isolated environment (not the repo), and the child run with an unusable `DISPLAY` exits 3 with one JSON line whose `failure` is in `{display, libx11}`; a scratch edit that excludes or breaks the helper makes the target fail. CI package job green. | 2 |
| Regression | `./scripts/dev make check`; full CI green. | 1, 2 |

Local gates: AGENTS.md names `./scripts/dev make check` for Python changes and
`make test-package` for installed distributions; slice 2 changes the latter
target, so it is that slice's local proof.

## Ordered slices

### 1. X11 clear refuses frozen and archive-only runtimes
Type: Behavior
Status: done
Proof: rows 1–4 and README above; `./scripts/dev make check`.

Behavior: Linux X11 session (`DISPLAY` only) in a frozen runtime, or with the
helper script not a file → `clipboard.clear()` → `ClipboardContentError`
("Linux X11 clipboard clear failed: …" naming the condition and
`set_clipboard_clearer`) before any `subprocess.run`; ordinary installs
unchanged. Tests assert error type, X11 and the remedy name, not copied
wording (AGENTS.md test rule).

### 2. Packaging check launches the installed X11 clear helper
Type: Behavior
Status: done
Proof: row 5 above; `./scripts/dev make test-package`; CI package job.

Behavior: built wheel and sdist → `make test-package` → each isolated install
runs its own installed helper with an unusable `DISPLAY` and the target
passes only on the structured failure (exit 3, `display` or `libx11`), with no
desktop session. Keep the check small (a script under `scripts/` called from
the existing loop, or an inline `python -I -c`), choosing whichever stays
readable; it must not import the source tree.

## Execution complete

Product advice: reasoned no-change. The delivered guard and packaging check
match the story, and no correction is needed. The sibling
SEED-001#bounded-helper-owner-write already owns frozen/archive behaviour for
the other helper-launching writers, so no new backlog item is recommended.
Process findings DD-025 (CI-environment premise not observed) and DD-026
(mkShell variable merged onto the derivation) are recorded in
ProjectFindings.md.

## Current decisions

- "Recognized frozen runtime" means `getattr(sys, "frozen", False)` is truthy;
  the missing-file guard covers bundlers that set no flag but ship modules
  only inside an archive.
- The guard applies only to the native X11 clearer; a caller-supplied clearer
  and other platforms are not guarded.
- An unusable `DISPLAY` for the packaging check is one no X server can serve
  (for example `:65535`); `libx11` is accepted so the target also passes on a
  macOS developer machine.

## Decisive premises (observed during preparation, 2026-11-04)

Observed in this workspace with the pinned Python 3.13 from the Nix store
(`/nix/store/d5dyl94h…-python3-3.13.17/bin/python3 -I`), because
`./scripts/dev` could not start (see Pre-Take note); scratch outputs removed.

1. **Frozen runtime launches a child today** (consumes slice 1's failing
   test). With `DISPLAY=:0`, `sys.frozen = True` and a recording
   `subprocess.run`, `_clear_x11._x11_clipboard_clearer()` launched
   `[sys.executable, "-I", ".../clipboard/_x11_relinquish.py"]`. Confirmed.
2. **Archive installs point at a non-file helper and still launch today.**
   Zipping `clipboard/` and importing it via zipimport gives
   `_RELINQUISH_SCRIPT = .../app.zip/clipboard/_x11_relinquish.py`,
   `is_file()` False. With that path, the real clearer launched the child and
   raised "helper exited with status 2: … can't open file …". Confirmed.
3. **Wheel and sdist ship the helper and the installed copy launches.**
   `python -m build --no-isolation` (main checkout's dev venv, read-only)
   produced both; the sdist lists `clipboard/_x11_relinquish.py`. A fresh
   venv with the wheel, and one with a wheel built from the extracted sdist,
   each resolved `_relinquish_command()[-1]` under the venv's
   `site-packages`, and running it from `/` with `DISPLAY=:65535` exited 3
   with `{"failure": "libx11", …}` (macOS). Confirmed; on CI Linux the
   classification is expected to be `display` (existing
   `tests/test_x11_relinquish.py::test_relinquish_script_runs_standalone_without_a_display`
   already accepts both).
4. **Proof route.** `./scripts/dev make test-package` is the planned local
   route; it was unavailable here (Pre-Take note). The CI `ubuntu-latest`
   job running `make check lint-workflows test-package` is the available
   hosted route.

## Pre-Take note

`./scripts/dev` fails offline in every checkout on this machine: the pinned
dev shell (uv 0.11.21, actionlint, `nix-shell`) is not in the Nix store, so
`nix develop --offline --max-jobs 0` reports "Unable to start any build".
Local gates need it restored first, which needs downloads the developer
authorizes (AGENTS.md online setup).

## Plan review

Refinement not needed: two independent Behavior slices, each one proof loop,
no shared special cases. No remaining slice-specific concerns identified in
this review.

## Learnings

- Local gates run as `nix develop -c make …` (AGENTS.md); `./scripts/dev`
  named above was reverted in `0b08521`, and the online dev shell now starts.
- Slice 1 accepted proof: `nix develop -c uv run --locked --extra images pytest
  tests/test_clear_x11.py tests/test_clear_wayland.py -q` (24 passed; 4 new
  tests failed first) and `nix develop -c make check` (612 passed, 27
  skipped). The guard message uses the plain helper path, not `repr`, so the
  Windows matrix assertion `str(script) in message` holds.
- Slice 2 accepted local proof: `nix develop -c make test-package` (macOS,
  wheel and sdist each `launched: failure libx11`); negative checks (helper
  excluded via MANIFEST.in; `FAILURE_EXIT = 4`) each failed the target and
  were restored; `make check` and `make lint-workflows` pass. uv
  `--isolated --with` layers cached installs onto `sys.path`
  (`~/.cache/uv/archive-v0/.../site-packages`), not under `sys.prefix`, so
  the installed-helper check matches a `site-packages` entry. The Linux
  `display` outcome awaits the CI package job (obligation O1).
- CI run 41773836492 (`e600e48`, all jobs green): the `ubuntu-latest`
  "Lint and package (Nix)" job printed `failure libx11` for both
  distributions, not `display`. The Nix dev shell (`flake.nix` packages:
  python313, uv, gnumake, actionlint) exposes no libX11 to its Python, so
  `load_libx11` finds none; premise 3's "expected to be `display`" on CI does
  not hold. E5a stays open (O1) awaiting the developer's choice: add libX11
  to the Linux dev shell so CI exercises `display`, or amend the story's
  example to accept `libx11` in the Nix package job.
- Developer decision (2026-11-04): option 1, add libX11 to the Linux dev
  shell. `flake.nix` sets `CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR` on Linux only
  (not `LD_LIBRARY_PATH`, so system `xclip` keeps its own libX11); the check
  puts it on the helper child's `LD_LIBRARY_PATH` and then requires
  `display`. Local proof: `make test-package` still `libx11` on macOS (var
  unset); forcing the var to `/nonexistent` fails the target with "helper
  failure 'libx11' is not display"; `make check` (612 passed) and
  `make lint-workflows` pass; the x86_64-linux shell evaluates the var to
  `libx11-1.8.14/lib`. O1 closes on the CI package job printing `display`.
- CI run 41776343130 (`9f5e5ff`) still printed `libx11`: `mkShell {…} // {…}`
  merged the variable onto the derivation value, not into `mkShell`'s
  arguments, so it never reached the shell environment (and the check,
  seeing no variable, accepted `libx11`). Fixed by `mkShell ({…} // {…})`;
  `drvAttrs ? CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR` is now true on
  x86_64-linux and false on aarch64-darwin. Check `drvAttrs`, not the
  derivation's attributes, when proving a shell variable.


## Story obligations

### O1. CI Linux package job reports libx11, not display
Reported: slice 2 — "make test-package was observed only on macOS (failure libx11); the ubuntu-latest package job running the new check needs the published revision."
Story clause: "on the CI Linux runner, wheel then sdist"
Disposition: proved by slice 2: CI run 41776839169 (a7c6e5a) 'Lint and package (Nix)' on ubuntu-latest: make test-package printed 'Installed X11 clear helper /home/runner/.cache/uv/archive-v0/.../site-packages/clipboard/_x11_relinquish.py launched: failure display' for wheel and sdist; check requires display when the Linux shell supplies libX11

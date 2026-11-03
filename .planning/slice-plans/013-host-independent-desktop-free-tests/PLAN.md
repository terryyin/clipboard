# Plan: Make desktop-free platform tests pass on every matrix OS

**Identity:** SEED-003#host-independent-desktop-free-tests
**Source:** [Make desktop-free platform tests pass on every matrix OS](../../seeds/SEED-003-host-independent-tests.md#host-independent-desktop-free-tests)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

One outcome: the desktop-free suite fakes another platform only where the
product reads it, so it gives the same result on every CI matrix OS, and a
new global `sys.platform` fake fails locally. Internal structure only: no
public API, message, or library behavior change; `clipboard.VERSION`
unchanged.

Excluded (from the story): native probes and their CI venues, product
behavior or message changes, new matrix cells, and skips that reflect a
genuine host capability (real pasteboard probes, file-URI decoding in
`tests/test_copy_files_contract.py`).

Assumption: every product platform read happens at call time (no
module-level `sys.platform` branch in `clipboard/`), so one private seam read
at call time keeps today's selection behavior.

## Outside-in proof

| Promise (story example) | Observable signal | Owning slice |
| --- | --- | --- |
| Faking a platform does not change stdlib behavior (ex. 1, 2) | Local guard: no test leaves the shared `sys.platform` different from the host's value after its call phase; `nix develop -c make check` green on Darwin | 1 |
| A new global fake fails locally (ex. 6) | Scratch test doing `monkeypatch.setattr(sys, "platform", "win32")` fails under the guard, passes when switched to the shared fixture; scratch reverted | 1 |
| `text_session` "linux" on a non-Linux host selects X11/Wayland without touching `sys.platform` (ex. 2) | Existing `tests/test_text_session.py`, `tests/test_text_dispatch.py`, `tests/test_text_x11.py`, `tests/test_text_wayland.py` green under the guard | 1 |
| Pretend-Darwin `copy_files` writer runs on Windows (ex. 1) | CI `Python 3.10/3.14 on windows-latest` reports the `darwin_helper` tests in `tests/test_copy_files_default_writer.py` as passed, not skipped | 2 |
| Cross-OS file names (ex. 3) and `os.killpg` supplied by the fake (ex. 4) | Existing fixtures kept; full CI matrix green | 2 |
| Platform-gated message assertions survive rewording (ex. 5) | Audited host-gated assertions check error type and named platform, not copied wording; full CI matrix green | 2 |
| Project rule | `AGENTS.md` names the fixture and the rules | 2 |
| Regression | `nix develop -c make check` (AGENTS.md "Check Python") each slice; full CI matrix (`ci.yml` runs on every branch push) | 1, 2 |

## Ordered slices

### 1. Module-local platform faking with a global-fake guard
Type: Structure
Status: done
Proof: rows 1–3 above.

Correction (test-suite weakness, DD-010): add one private platform seam in
the package (for example `clipboard/_platform.py` with a call-time accessor)
and route the eight reading modules through it (`_desktop_text`, `_offer`,
`_offer_windows`, `_files_native`, `_files_native_windows`, `_html`,
`_html_native`, `_image_write`), including the platform named in their
messages. Add one shared fixture in `tests/conftest.py` that fakes that seam,
make `text_session` use it, and migrate every in-process test that patches
`<module>.sys.platform` or `sys.platform` (21 files observed below) and the
subprocess scenarios in `tests/test_clipboard.py` and
`tests/test_no_pillow_extra.py` that assign `sys.platform`. Remove the
`import sys as sys` re-export from `clipboard/__init__.py` once nothing uses
`clipboard.sys` (search production, tests and scripts). Add a
`pytest_runtest_call` hook wrapper in `tests/conftest.py` that fails a test
whose call phase leaves `sys.platform` different from the host's value.
Preserved behavior: every existing desktop-free test still passes with the
same assertions on this host.

Accepted proof (Darwin, 2026-11-03): seam `clipboard/_platform.py`
`current()`, read once per dispatch function in the eight modules; fixture
`fake_platform` and `pytest_runtest_call` guard in `tests/conftest.py`.
`nix develop -c make check` 538 passed, 24 skipped (baseline counts); after
refactor `nix develop -c uv run --locked --extra images pytest -q` over every
covering test file 510 passed, 22 skipped. A scratch
`monkeypatch.setattr(sys, "platform", "win32")` test failed under the guard
and passed with `fake_platform("win32")` (deleted). `grep -rn sys.platform`:
product reads only in `_platform.py`; tests and scripts read the real host for
capability gates only. Source review ids: [source-review.md](source-review.md).

### 2. Pretend-platform tests run on every matrix OS, with the project rule
Type: Behavior
Status: done
Proof: rows 4–7 above.

Behavior: CI matrix on a story-branch push → the pretend-Darwin writer group
runs and passes on `windows-latest` (its global-fake skip in `darwin_helper`
removed), every cell is green, and `AGENTS.md` tells future work to fake the
platform only through the shared fixture, use file names valid on every
matrix OS (host-only names only as gated additions), supply POSIX-only stdlib
attributes through fakes, and assert error type plus named platform rather
than copied wording. Audit host-gated tests (`skipif` on `sys.platform`, or
host-conditional expectations) for copied message wording and global-fake
skips; leave skips whose reason is a genuine host capability, stating it.
If the Windows cell still fails the Darwin group for a host reason the seam
cannot remove, keep that skip with the true reason and record the learning
here; no human decision is needed for that fallback.

Accepted local proof (Darwin, 2026-11-03): `darwin_helper` skip removed;
`test_default_write_stub_wrapped_as_clipboard_image_error` now fakes `win32`
and runs on every host; seven unimplemented-platform assertions check error
type plus the named platform or the product message source; `AGENTS.md` rule
added. `nix develop -c make check` 539 passed, 23 skipped; the 12
`darwin_helper` tests pass with `-v`. Kept host-capability skip:
`tests/test_copy_files_contract.py` URI decoding. CI run 41656910713 on
5380548 passed every matrix cell; on `windows-latest` the `darwin_helper` group and X11 owner-shutdown
tests ran and passed (no skip).

## Execution complete

Product advice: no change. The story's outcome holds across the matrix with
no correction needed; it addresses the causes recorded in
[DD-010](../../../ProjectFindings.md#dd-010--desktop-free-unavailable-path-test-asserted-host-os)
and [DD-005](../../../ProjectFindings.md#dd-005--platform-stub-wording-change-broke-windows-only-assertion),
whose status wrap-up may settle. Minor, uncorrected:
`tests/test_inspect_seam.py` keeps a host branch whose two arms assert the
same thing (older, no host-dependence risk).

## Decisive premises

Observed in this workspace (Darwin host, `nix develop -c uv run --locked
--extra images pytest`), scratch edits reverted before any record write:

- **Global fakes and their consumers (slice 1).** Scratch
  `pytest_runtest_call` hook wrapper printing tests whose call phase left
  `sys.platform` ≠ host: 168 tests in 21 files —
  `test_text_wayland` 30, `test_text_x11` 23, `test_paste_html_wayland_reader`
  18, `test_text_dispatch` 15, `test_paste_html_x11_reader` 14,
  `test_text_session` 13, `test_copy_files_windows_writer` 12,
  `test_paste_html_windows_reader` 9, `test_inspect_x11` 6,
  `test_inspect_wayland` 5, `test_inspect_windows` 3,
  `test_paste_files_native_linux_{x11,wayland}` 3 each,
  `test_text_native_linux_bound` 3, `test_copy_files_default_writer`,
  `test_copy_html_seam`, `test_paste_files_native_windows`,
  `test_paste_files_seam` 2 each, `test_copy_html_contract`,
  `test_paste_html_contract`, `test_paste_html_macos_reader` 1 each;
  suite 538 passed, 24 skipped in 7.6 s. Tests faking `darwin` do not show on
  a Darwin host (for example `darwin_helper`, `test_paste_html_macos_reader`
  line 37); the guard reports them on the Linux and Windows cells, and a
  search for `setattr(.*"platform"` / `sys.platform =` lists them for slice 1.
  The same run shows the guard discriminates (it reports every global fake).
- **Call-time reads (slice 1).** `grep -rn "^[^ #].*sys.platform" clipboard`
  finds only the `__init__.py` re-export; those 168 tests passing with
  per-test fakes observe that selection reads the platform at call time.
- **Windows stdlib hazard (slice 2).** Recorded cause in DD-010 and the
  `darwin_helper` comment (5df300b, 152faa2): the shared fake sent
  `Path.as_uri` into urllib's macOS-only `_scproxy` on Windows. Not
  observable on this host; the route is CI's `windows-latest` cells, which
  run on every branch push (`ci.yml` `on: push: branches: ['**']`). Slice 2's
  proof is that observation, with the stated fallback.

## Current decisions

- One private call-time seam rather than per-module platform constants: one
  fake covers every reader and keeps import-time behavior unchanged.
- Guard by runtime hook in `tests/conftest.py`, not a source scan; the
  subprocess scenarios are migrated explicitly in slice 1 since the hook
  cannot see child processes.
- `tests/test_text_x11.py` `os.killpg` handling: SEED-001#bounded-x11-text-write
  (plan 012, being Taken) removes the `proc.kill()` fallback and its
  `delattr(killpg)` test while keeping the `raising=False` stub; this plan
  only keeps the stub and does not touch that fallback. Whichever lands
  second rebases over the other's test edits.

## Plan review

Slice-plan refinement not needed: two slices with one proof loop each (local
guard for the structural migration, CI matrix for cross-host behavior and
the rule); no fragmentation, independent outcome, or sizing concern found.
No remaining slice-specific concerns were identified.

## Learnings

- Slice 1: `darwin_helper` now fakes only the seam, so its Windows skip's
  stated cause (shared `sys.platform` sending `Path.as_uri` into `_scproxy`)
  no longer applies; slice 2 removes it and watches the Windows cell for any
  remaining file-name or URI host difference.
- Subprocess scenarios assign `clipboard._platform.current` after import; this
  relies on every product platform read happening at call time.

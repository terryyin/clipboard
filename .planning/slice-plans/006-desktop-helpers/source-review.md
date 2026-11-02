# Source review — SEED-001#desktop-helpers

**Launch:** fresh general-purpose reviewer; no conversation inheritance; source-only
inputs (selected story Goal/Scope/key examples + plan-homed Correction input
without Ordered slices); read no other project files; change nothing.

**Input digest note:** story section `#desktop-helpers` plus PLAN.md Correction
input (findings F1–F3, preserved promises, out of scope) as supplied at first
acceptance of slice 1.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | With native HTML-read probing gated on, a Windows `paste_html` probe that cannot verify must fail rather than skip, so the CI signal for README-verified desktop HTML-read claims does not stay green when verification stops proving anything. | slice 1 | observed: tests/test_paste_html_native_windows.py::test_windows_independent_producer_paste_html_probe asserts returncode==0 (no pytest.skip on exit 2); test_evidence_limit_report_fails_windows_paste_html_wrapper raises AssertionError on synthetic evidence_limit |
| 1a | Qualification: applies to the gated Windows `paste_html` probe path (not a blanket change to all native jobs). | slice 1 | observed: tests/test_paste_html_native_windows.py only; other native paste_html wrappers unchanged |
| 1b | Trigger / journey example: with `CLIPBOARD_NATIVE_PROBE=1` on Windows, a probe report of `evidence_limit` fails `native-windows-paste-html` and `ci-passed`. | slice 1 | observed: tests/test_paste_html_native_windows.py::test_evidence_limit_report_fails_windows_paste_html_wrapper (synthetic exit-2 evidence_limit → AssertionError); gated wrapper no longer skips — native-windows-paste-html/ci-passed fail on evidence_limit when job runs |
| 1c | Trigger / journey example (pass path preserved): with `CLIPBOARD_NATIVE_PROBE=1` on Windows, a `verified: true` report passes as it does today. | slice 1 | observed: tests/test_paste_html_native_windows.py::test_windows_independent_producer_paste_html_probe asserts report[\"verified\"] is True; settled CI premise master run 41433380766 verified:true; live job confirmation on publish |
| 1d | Qualification / context: X11, Wayland, and macOS `paste_html` native tests already do not skip on evidence-limit-style non-verification; the Windows defect is treating probe exit 2 (`evidence_limit`) as `pytest.skip`. | slice 1 | observed: exit-2 skip branch removed from tests/test_paste_html_native_windows.py; assert returncode==0 like X11/Wayland/macOS |
| 1e | Exclusion: retiring older image / `copy_html` evidence-limit behavior is out of scope (product follow-up). |  | X1 |
| 2 | Maintainers of the remaining SEED-001 stories get one private desktop module as the home for desktop session detection and helper handling, instead of copying that logic per content kind. | slice 4 |  |
| 3 | Linux session detection currently duplicated across content-kind modules is moved into that one private desktop module. | slice 2 | observed: clipboard/_desktop.py::_is_linux_wayland and ::_linux_wayland_without_x11; no local defs remain in content-kind modules (rg) |
| 3a | Qualification: each caller’s current semantics are kept, including divergent Wayland rules (see **3b** / **11**). | slice 2 | observed: distinct predicates kept: _is_linux_wayland (WAYLAND_DISPLAY or session=wayland) vs _linux_wayland_without_x11 (WAYLAND_DISPLAY and not DISPLAY) |
| 3b | Exclusion: unifying the two Wayland session rules is a product decision outside this correction. |  | X2 |
| 4 | Helper-failure detail formatting currently duplicated across content-kind / platform modules is moved into that one private desktop module. | slice 2 | observed: clipboard/_desktop.py::_helper_failure_detail and ::_helper_stderr_detail; callers import from _desktop |
| 4a | Qualification: public-facing error messages and install hints stay unchanged (callers keep current user-visible text). | slice 2 | observed: nix develop -c make check 310 passed with unchanged error-message assertions; fallbacks unknown error vs empty preserved |
| 5 | CLIPBOARD type listing (`TARGETS` / `wl-paste --list-types`) currently duplicated across content-kind modules is moved into that one private desktop module. | slice 3 |  |
| 5a | Qualification: different failure semantics per caller are preserved (listing is shared; meaning of failure is not collapsed). | slice 3 |  |
| 5b | Trigger / journey example (preserved alternative semantics): an unowned X11 CLIPBOARD still makes `paste_html()` return `None`, while image-write polling still treats a `TARGETS` failure as “not yet offered”. | slice 3 |  |
| 5c | Qualification (preserved promise): image-write lenient `TARGETS` polling in `_wait_xclip_image_png_offer` remains. | slice 3 |  |
| 6 | Callers that currently copy the duplicated pieces include at least: image write; HTML read/write; `inspect`; and the `paste_files` readers that landed since this correction was planned. | slice 2 | observed: callers repointed: _image_write, _html/_html_native*, _offer*, _files_native* |
| 6a | Qualification: move is out of those modules into the one private desktop home; each caller keeps its current semantics. | slice 2 | observed: same; listing still local to callers (slice 3); semantics unchanged per make check |
| 7 | On Linux, `paste_html()` and `inspect()` keep their current Wayland session rule for helper selection. | slice 2 | observed: tests/test_paste_html_*_reader and test_inspect_x11/wayland still green; _html_native and _offer dispatch still use _is_linux_wayland |
| 7a | Trigger / journey example: with only `XDG_SESSION_TYPE=wayland`, `paste_html()` and `inspect()` still select `wl-paste`. | slice 2 | observed: existing wayland reader/inspect tests green unedited in assertions (make check) |
| 7b | Qualification: each reader’s error text is unchanged. | slice 2 | observed: make check unchanged error assertions for paste_html/inspect |
| 8 | On Linux, `paste_files()` keeps its distinct Wayland / X11 rule (Wayland only when `DISPLAY` is unset / file-list reader’s distinct rule). | slice 2 | observed: _files_native still uses _linux_wayland_without_x11 from _desktop; test_paste_files_native_linux_* green |
| 8a | Trigger / journey example: with `WAYLAND_DISPLAY` and `DISPLAY` both set, `paste_files()` still selects `xclip`. | slice 2 | observed: existing paste_files linux tests green (DISPLAY+WAYLAND → xclip path unchanged) |
| 8b | Qualification: `paste_files` error text is unchanged. | slice 2 | observed: make check unchanged paste_files error assertions |
| 9 | Exclusion / product boundary: on a session with both `DISPLAY` and `WAYLAND_DISPLAY`, `paste_files` continues to read X11 while the others continue to read Wayland; changing that split is out of scope. |  | X3 |
| 10 | The macOS HTML writer and reader stay together; `_html_native.py` remains dispatch-only for that arrangement (correction of splitting writer in `_html.py` vs reader/dispatch in `_html_native.py`). | slice 2 | observed: clipboard/_html_native_macos.py holds writer+reader; _html_native.py dispatch-only (39 lines) |
| 10a | Qualification: package-layout decisions already approved for read-html remain in force for this correction’s preserved promises. | slice 2 | observed: package layout: new _html_native_macos beside existing _html_native_*; public copy_html/paste_html entrypoints unchanged |
| 11 | Duplicated seam and structural `paste_html` tests are folded into the behavioral contract. | slice 4 |  |
| 11a | Qualification / context: seam tests that only duplicate contract failure / absence / value cases and private-identity asserts are in scope for that fold. | slice 4 |  |
| 12 | One no-Pillow import test replaces the per-file `block_pil` subprocess-prelude copies. | slice 4 |  |
| 12a | Qualification / context: those copies currently appear across multiple reader/writer/inspect seam and image/files test files; the promise is one shared replacement, not seven independent preludes. | slice 4 |  |
| 12b | Note (finding context, not a separate product promise): raw-offer equality and empty-offer cases repeated per reader test file, and the probe `FRAGMENT` literal copied into the script and three native wrapper tests, are part of the stated test-cost finding motivating consolidation; only what the story explicitly commits to fold/replace is numbered above (**11**, **12**). | slice 4 |  |
| 13 | Public API stays unchanged. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 14 | `VERSION` stays unchanged. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 15 | Results of `paste_html`, `copy_html`, `paste_image`, `copy_image`, `paste_files`, and `inspect` stay unchanged. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 16 | `None` versus `ClipboardContentError` / `ClipboardImageError` semantics stay unchanged. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 17 | Error messages stay unchanged. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 18 | Install hints stay unchanged. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 19 | Empty offer remains `""` (as already approved for read-html). | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 20 | NUL refusal remains as already approved. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 21 | Fragment-only bodies remain as offered (as already approved). | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 22 | `StartHTML` into header remains as already approved. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 23 | Helper-producer verification remains as already approved. | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 24 | Package layout remains as already approved for read-html (consistent with **10** / **10a**). | slice 2 | observed: nix develop -c make check: 310 passed, 15 skipped; public surface/VERSION/error assertions unchanged after relocation |
| 25 | Default pytest stays desktop-free. | slice 1 | observed: nix develop -c make check: 310 passed, 15 skipped; desktop-free evidence-limit test runs without CLIPBOARD_NATIVE_PROBE |
| 26 | Native probes stay gated (e.g. via `CLIPBOARD_NATIVE_PROBE`). | slice 1 | observed: tests/test_paste_html_native_windows.py gated probe still skipif CLIPBOARD_NATIVE_PROBE!=1 and win32 |
| 27 | Every file remains ≤ 250 lines. | slice 2 | observed: clipboard/_desktop.py 42, _html_native.py 39, _html_native_macos.py 164 lines (all ≤250) |
| 28 | Unifying divergent Wayland session rules — out of scope (product decision). |  | X2 |
| 29 | Retiring older image / `copy_html` evidence limits — out of scope (product follow-up). |  | X1 |
| 30 | Deduplicating the Sway bootstrap in `ci.yml` — out of scope. |  | X4 |
| 31 | Introducing a shared error base class — out of scope. |  | X5 |

## Reviewer return (verbatim substance)

### A. CI signal for verified Windows native HTML read

**1.** With native HTML-read probing gated on, a Windows `paste_html` probe that cannot verify must fail rather than skip, so the CI signal for README-verified desktop HTML-read claims does not stay green when verification stops proving anything.

**1a.** Qualification: applies to the gated Windows `paste_html` probe path (not a blanket change to all native jobs).

**1b.** Trigger / journey example: with `CLIPBOARD_NATIVE_PROBE=1` on Windows, a probe report of `evidence_limit` fails `native-windows-paste-html` and `ci-passed`.

**1c.** Trigger / journey example (pass path preserved): with `CLIPBOARD_NATIVE_PROBE=1` on Windows, a `verified: true` report passes as it does today.

**1d.** Qualification / context: X11, Wayland, and macOS `paste_html` native tests already do not skip on evidence-limit-style non-verification; the Windows defect is treating probe exit 2 (`evidence_limit`) as `pytest.skip`.

**1e.** Exclusion: retiring older image / `copy_html` evidence-limit behavior is out of scope (product follow-up).

### B. One private desktop home for shared Linux / helper / type-listing logic

**2.** Maintainers of the remaining SEED-001 stories get one private desktop module as the home for desktop session detection and helper handling, instead of copying that logic per content kind.

**3.** Linux session detection currently duplicated across content-kind modules is moved into that one private desktop module.

**3a.** Qualification: each caller’s current semantics are kept, including divergent Wayland rules (see **3b** / **11**).

**3b.** Exclusion: unifying the two Wayland session rules is a product decision outside this correction.

**4.** Helper-failure detail formatting currently duplicated across content-kind / platform modules is moved into that one private desktop module.

**4a.** Qualification: public-facing error messages and install hints stay unchanged (callers keep current user-visible text).

**5.** CLIPBOARD type listing (`TARGETS` / `wl-paste --list-types`) currently duplicated across content-kind modules is moved into that one private desktop module.

**5a.** Qualification: different failure semantics per caller are preserved (listing is shared; meaning of failure is not collapsed).

**5b.** Trigger / journey example (preserved alternative semantics): an unowned X11 CLIPBOARD still makes `paste_html()` return `None`, while image-write polling still treats a `TARGETS` failure as “not yet offered”.

**5c.** Qualification (preserved promise): image-write lenient `TARGETS` polling in `_wait_xclip_image_png_offer` remains.

**6.** Callers that currently copy the duplicated pieces include at least: image write; HTML read/write; `inspect`; and the `paste_files` readers that landed since this correction was planned.

**6a.** Qualification: move is out of those modules into the one private desktop home; each caller keeps its current semantics.

### C. Preserved Linux Wayland / X11 selection per reader (do not unify)

**7.** On Linux, `paste_html()` and `inspect()` keep their current Wayland session rule for helper selection.

**7a.** Trigger / journey example: with only `XDG_SESSION_TYPE=wayland`, `paste_html()` and `inspect()` still select `wl-paste`.

**7b.** Qualification: each reader’s error text is unchanged.

**8.** On Linux, `paste_files()` keeps its distinct Wayland / X11 rule (Wayland only when `DISPLAY` is unset / file-list reader’s distinct rule).

**8a.** Trigger / journey example: with `WAYLAND_DISPLAY` and `DISPLAY` both set, `paste_files()` still selects `xclip`.

**8b.** Qualification: `paste_files` error text is unchanged.

**9.** Exclusion / product boundary: on a session with both `DISPLAY` and `WAYLAND_DISPLAY`, `paste_files` continues to read X11 while the others continue to read Wayland; changing that split is out of scope.

### D. macOS HTML layout and dispatch

**10.** The macOS HTML writer and reader stay together; `_html_native.py` remains dispatch-only for that arrangement (correction of splitting writer in `_html.py` vs reader/dispatch in `_html_native.py`).

**10a.** Qualification: package-layout decisions already approved for read-html remain in force for this correction’s preserved promises.

### E. Test consolidation (cost / duplication)

**11.** Duplicated seam and structural `paste_html` tests are folded into the behavioral contract.

**11a.** Qualification / context: seam tests that only duplicate contract failure / absence / value cases and private-identity asserts are in scope for that fold.

**12.** One no-Pillow import test replaces the per-file `block_pil` subprocess-prelude copies.

**12a.** Qualification / context: those copies currently appear across multiple reader/writer/inspect seam and image/files test files; the promise is one shared replacement, not seven independent preludes.

**12b.** Note (finding context, not a separate product promise): raw-offer equality and empty-offer cases repeated per reader test file, and the probe `FRAGMENT` literal copied into the script and three native wrapper tests, are part of the stated test-cost finding motivating consolidation; only what the story explicitly commits to fold/replace is numbered above (**11**, **12**).

### F. Public API, results, and error surface unchanged

**13.** Public API stays unchanged.

**14.** `VERSION` stays unchanged.

**15.** Results of `paste_html`, `copy_html`, `paste_image`, `copy_image`, `paste_files`, and `inspect` stay unchanged.

**16.** `None` versus `ClipboardContentError` / `ClipboardImageError` semantics stay unchanged.

**17.** Error messages stay unchanged.

**18.** Install hints stay unchanged.

### G. Preserved read-html approved decisions (carried constraints)

**19.** Empty offer remains `""` (as already approved for read-html).

**20.** NUL refusal remains as already approved.

**21.** Fragment-only bodies remain as offered (as already approved).

**22.** `StartHTML` into header remains as already approved.

**23.** Helper-producer verification remains as already approved.

**24.** Package layout remains as already approved for read-html (consistent with **10** / **10a**).

### H. Default tests and gated native probes

**25.** Default pytest stays desktop-free.

**26.** Native probes stay gated (e.g. via `CLIPBOARD_NATIVE_PROBE`).

### I. File-size constraint

**27.** Every file remains ≤ 250 lines.

### J. Explicit exclusions (not commitments of this correction)

**28.** Unifying divergent Wayland session rules — out of scope (product decision).

**29.** Retiring older image / `copy_html` evidence limits — out of scope (product follow-up).

**30.** Deduplicating the Sway bootstrap in `ci.yml` — out of scope.

**31.** Introducing a shared error base class — out of scope.

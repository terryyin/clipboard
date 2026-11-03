# Source review: SEED-003#host-independent-desktop-free-tests

Launch: fresh general-purpose sub-agent (no conversation inheritance), 2026-11-03,
during slice 1 proof acceptance. Input: only the story's Goal, Scope (required
behavior, proof, scope limits, restrictions) and Key examples 1-6 from
`.planning/seeds/SEED-003-host-independent-tests.md#host-independent-desktop-free-tests`,
verbatim; no plan, return, product or proof. Instructed to read no files and change
nothing. Reviewer's clarification notes: skips are removed only where global faking
was the reason (X5 keeps host-capability skips); the guard fails the test (E6).

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | The desktop-free suite (`make check`) gives the same result on the macOS, Linux and Windows CI matrix cells as on the maintainer's or executing agent's own host. | slice 2 |  |
| 2 | Host assumptions no longer show up as story-branch CI repair cycles for maintainers and executing agents who add platform-branch behavior. | slice 2 |  |
| 3 | The story changes how tests fake a platform, not what the library does. Library behavior is unchanged. | slice 1 | observed: slice 1 diff: product edits only swap sys.platform for clipboard._platform.current() (clipboard/_platform.py); make check 538 passed/24 skipped as baseline |
| 4 | One shared test helper or fixture fakes the platform (either form is allowed). | slice 1 | observed: tests/conftest.py fake_platform fixture (setter patching clipboard._platform.current) |
| 4.1 | The helper fakes the platform only where the product reads it. | slice 1 | observed: tests/conftest.py fake_platform patches only clipboard._platform.current; sys.platform untouched (guard in pytest_runtest_call passes for all 538 tests) |
| 4.2 | `pathlib`, `urllib`, `subprocess` and other stdlib code keep the host's real behavior while the helper is active. | slice 2 |  |
| 5 | Product modules read the platform through a private seam that the helper can replace. | slice 1 | observed: clipboard/_platform.py current(); grep: only product sys.platform read is there; 8 modules call _platform.current() |
| 5.1 | The seam is an internal structural change with no observable change in library behavior. | slice 1 | observed: message f-strings keep identical text with _platform.current(); make check 538 passed/24 skipped unchanged on Darwin |
| 6 | Every existing desktop-free test, fixture and subprocess scenario that assigns or patches the shared `sys.platform` is moved to the helper. | slice 1 | observed: grep 'setattr(.*"platform"\|sys.platform *=\|.sys' over tests/scripts: only real-host == reads remain |
| 6.1 | This covers tests. | slice 1 | observed: 21 in-process test files migrated to fake_platform (git diff tests/test_*); grep shows no sys.platform patch |
| 6.2 | This covers fixtures. | slice 1 | observed: tests/conftest.py text_session uses fake_platform; darwin_helper fixture uses fake_platform |
| 6.3 | This covers subprocess scenarios. | slice 1 | observed: tests/test_clipboard.py _SUBPROCESS_PRELUDE as_wsl_session and test_set_clipboard_alone_does_not_displace_owned_backend; tests/test_no_pillow_extra.py paste_html scenario assign _platform.current |
| 7 | Host skips that existed only because of the global `sys.platform` faking are removed. | slice 2 |  |
| 7.1 | As a result, the pretend-Darwin writer group runs on every matrix OS. | slice 2 |  |
| 8 | Shared fixtures use file names that are valid on every matrix OS. | slice 2 |  |
| 8.1 | A host-only awkward name (such as `"` or `\` on POSIX) is allowed only as an explicitly gated addition. | slice 2 |  |
| 8.2 | Shared expectations must not depend on such a gated host-only name. | slice 2 |  |
| 9 | Tests that need a POSIX-only stdlib attribute (such as `os.killpg`) get it from the fake rather than requiring it from the host. | slice 2 |  |
| 10 | Platform-gated message assertions check: | slice 2 |  |
| 10.1 | the exception type, and | slice 2 |  |
| 10.2 | either the platform-identifying fact (for example the named platform) or the product's own message source, | slice 2 |  |
| 10.3 | not copied wording. | slice 2 |  |
| 11 | A short project rule in `AGENTS.md` directs future desktop-free tests to the helper and to these rules. | slice 2 |  |
| 12 | The existing CI matrix passes. | slice 2 |  |
| 12.1 | `ubuntu-latest` passes. | slice 2 |  |
| 12.2 | `macos-latest` passes. | slice 2 |  |
| 12.3 | `windows-latest` passes. | slice 2 |  |
| 13 | Locally, a guard detects any test that leaves the shared `sys.platform` different from the host's value. | slice 1 | observed: tests/conftest.py pytest_runtest_call wrapper fails a test leaving sys.platform != _HOST_PLATFORM; scratch monkeypatch.setattr(sys,'platform','win32') test failed, fake_platform version passed (scratch deleted) |
| 14 | The existing public API is preserved. | slice 1 | observed: clipboard/__init__.py diff removes only the private 'import sys as sys' test re-export; no public name changed |
| 15 | `clipboard.VERSION` is preserved. | slice 1 | observed: clipboard.VERSION untouched in diff |
| 16 | No required restrictions apply beyond 14 and 15. | slice 2 |  |
| X1 | Native probes and their CI venues are out of scope. | slice 2 |  |
| X2 | Product behavior changes are out of scope. | slice 2 |  |
| X3 | Product message changes are out of scope. | slice 2 |  |
| X4 | New matrix cells are out of scope. | slice 2 |  |
| X5 | Tests whose skip reflects a genuine host capability, rather than global faking, are out of scope (for example a real pasteboard probe, or file-URI decoding that differs by host). Their skips may stay. | slice 2 |  |
| E1 | Shows 4.1, 4.2 and 7.1. On a Windows runner, the pretend-Darwin `copy_files` writer tests run with no skip. The helper fakes macOS for the product's platform choice, `Path.as_uri` keeps Windows behavior, and urllib's macOS-only `_scproxy` is never imported. | slice 2 |  |
| E2 | Shows 4, 5, 6.2 and 13. The `text_session` fixture configured for `"linux"` on a macOS or Windows host selects the X11 or Wayland owner as it would on Linux. After the test, the shared `sys.platform` is unchanged because it was never patched. | slice 1 | observed: tests/test_text_session.py, test_text_dispatch.py, test_text_x11.py, test_text_wayland.py green on Darwin with text_session('linux',...) via fake_platform under the guard |
| E3 | Shows 8, 8.1 and 8.2. A file-list fixture with a space and a Unicode name (`report final.pdf`, `données é.csv`) is created on every matrix OS. A name containing `"` or `\` is only a gated POSIX addition. | slice 2 |  |
| E4 | Shows 9. The X11 owner-shutdown test runs on Windows, where `os.killpg` does not exist, because the fake supplies it. | slice 2 |  |
| E5 | Shows 10. Rewording an unimplemented-platform message (as d408685 did) does not fail a test that only runs on another OS, because the assertion checks the error type and the named platform. | slice 2 |  |
| E6 | Shows 13. A new test that assigns `sys.platform` directly fails the local suite on any host through the guard, before it reaches the Windows matrix cell. | slice 1 | observed: scratch tests/test_scratch_platform_guard.py: FAILED 'test left sys.platform=win32 (host darwin)' under nix develop -c uv run --locked --extra images pytest; deleted after |

---
id: SEED-003
status: active
planted: 2026-11-03
planted_during: Terry Yin's combined feedback cycle (project findings triage)
trigger_when: now
scope: One bounded test-suite improvement; S–M effort hypothesis
---

# Keep desktop-free tests independent of the CI host

<a id="host-independent-desktop-free-tests"></a>

### Make desktop-free platform tests pass on every matrix OS

**Identity:** SEED-003#host-independent-desktop-free-tests
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/013-host-independent-desktop-free-tests/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"975bee75b1971adb40a68b072931f0276d387795d448dbd7e9eb412484f1f9ea","plan":"1db185e9f1c5001def1fc3da95e0c3f0eacb4f94ba0874b8f9ff3fb194d92b30"}}
```

**Goal:** Maintainers and executing agents adding platform-branch behavior
get a desktop-free suite (`make check`) that gives the same result on the
macOS, Linux and Windows CI matrix cells as on their own host, so host
assumptions no longer surface as story-branch CI repair cycles. This keeps
cross-platform clipboard work (the project's North Star) cheap to deliver; the
story changes how tests fake a platform, not what the library does.

**Evidence:** [Project finding DD-010](../../ProjectFindings.md#dd-010--desktop-free-unavailable-path-test-asserted-host-os)
records three executions (SEED-001#read-files, SEED-001#portable-text,
SEED-001#copy-files), each needing one or two Windows-matrix repairs
(b00d9ab; c086e20; 5df300b and 152faa2): an `assert sys.platform !=
"win32"`, an unguarded `os.killpg` patch, a fixture file name with `"` and
`\`, and faking the shared `sys.platform` so stdlib `urllib` took its macOS
branch on Windows. Related:
[DD-005](../../ProjectFindings.md#dd-005--platform-stub-wording-change-broke-windows-only-assertion)
(a Windows-only assertion copied the shared stub wording).

**Current state (observed 2026-11-03 on this branch).** Product modules read
`sys.platform` directly (`_desktop_text`, `_offer`, `_offer_windows`,
`_files_native`, `_files_native_windows`, `_html`, `_html_native`,
`_image_write`). Every test that "fakes the platform" therefore patches the one
shared `sys` module, whatever module name it reaches it through
(`clipboard._files_native.sys`, `_offer.sys`, `clipboard.sys`, the
`text_session` fixture in `tests/conftest.py`, and the subprocess scenarios in
`tests/test_clipboard.py` and `tests/test_no_pillow_extra.py` that assign
`sys.platform`). The suite is green today only through host workarounds:
`darwin_helper` in `tests/test_copy_files_default_writer.py` skips the whole
pretend-Darwin writer group on Windows, its awkward-name fixture drops the
`"`/`\` name on Windows, and the X11 writer tests patch `os.killpg` with
`raising=False`.

**Scope:**

- *Required behavior:* one shared test helper or fixture fakes the platform
  only where the product reads it, so `pathlib`, `urllib`, `subprocess` and
  other stdlib code keep the host's real behavior. Product modules read the
  platform through a private seam that helper can replace; this is an internal
  structural change with no observable library behavior change.
- Migrate every existing desktop-free test, fixture and subprocess scenario
  that assigns or patches the shared `sys.platform` to the helper, and remove
  the host skips that existed only because of that global faking (the
  pretend-Darwin writer group then runs on every matrix OS).
- Shared fixtures use file names valid on every matrix OS. A host-only awkward
  name (such as `"` or `\` on POSIX) is allowed only as an explicitly gated
  addition that shared expectations do not depend on.
- Tests needing a POSIX-only stdlib attribute (such as `os.killpg`) supply it
  through the fake rather than requiring it from the host.
- Platform-gated message assertions check the exception type and the
  platform-identifying fact (for example the named platform) or the product's
  own message source, not copied wording.
- A short project rule in `AGENTS.md` directs future desktop-free tests to the
  helper and these rules.
- *Proof:* the existing CI matrix (`ubuntu-latest`, `macos-latest`,
  `windows-latest`) passes; locally, a guard detects any test that leaves the
  shared `sys.platform` different from the host's value.
- *Scope limits (deferred, not prevented):* native probes and their CI venues,
  product behavior or message changes, new matrix cells, and tests whose skip
  reflects a genuine host capability (for example a real pasteboard probe or
  file-URI decoding that differs by host) rather than global faking.
- *Required restrictions:* none beyond the existing public API and
  `clipboard.VERSION` preservation.
- **Effort:** S–M, medium confidence; assumes the eight product modules can
  read the platform through one private seam without changing import-time
  behavior.

**Key examples:**

1. On a Windows runner, the pretend-Darwin `copy_files` writer tests run
   (no skip): the helper fakes macOS for the product's platform choice while
   `Path.as_uri` keeps Windows behavior and never imports urllib's macOS-only
   `_scproxy`.
2. The `text_session` fixture configured for `"linux"` on a macOS or Windows
   host selects the X11 or Wayland owner as on Linux, and after the test the
   shared `sys.platform` is unchanged (it was never patched).
3. A file-list fixture with a space and a Unicode name (`report final.pdf`,
   `données é.csv`) is created on every matrix OS; a `"`/`\` name is only a
   gated POSIX addition.
4. The X11 owner-shutdown test runs on Windows, where `os.killpg` does not
   exist, because the fake supplies it.
5. Rewording an unimplemented-platform message (as d408685 did) does not fail
   a test that only runs on another OS, because the assertion checks the error
   type and the named platform.
6. A new test that assigns `sys.platform` directly fails the local suite on
   any host via the guard, before reaching the Windows matrix cell.

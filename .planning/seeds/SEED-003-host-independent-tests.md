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
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Maintainers and executing agents adding platform-branch
  behavior get a desktop-free suite that gives the same result on the macOS,
  Linux and Windows matrix cells as locally, instead of discovering host
  assumptions through story-branch CI repair cycles.
- **Evidence:** [DearDough DD-010](../../DearDough.md#dd-010--desktop-free-unavailable-path-test-asserted-host-os)
  records three executions (SEED-001#read-files, SEED-001#portable-text,
  SEED-001#copy-files), each needing one or two Windows-matrix repairs
  (b00d9ab; c086e20; 5df300b and 152faa2): an `assert sys.platform !=
  "win32"`, an unguarded `os.killpg` patch, a fixture file name with `"` and
  `\`, and faking the shared `sys.platform` so stdlib `urllib` took its macOS
  branch on Windows. Each execution's later briefs avoided the trap, but the
  lesson lived only in those briefs. The shared `text_session` fixture in
  `tests/conftest.py` still patches the global `sys.platform`. Related:
  [DD-005](../../DearDough.md#dd-005--platform-stub-wording-change-broke-windows-only-assertion)
  (a Windows-only assertion copied the shared stub wording).
- **Evaluation:** Desktop-free tests that exercise another platform's branch
  fake the platform only where the product reads it (module-local), use file
  names valid on every matrix OS, and never require a host-specific stdlib
  attribute; the full matrix passes. The next stories touching platform
  branches need no host-assumption CI repair.
- **Scope:** A shared test helper or fixture for module-local platform faking,
  migration of existing tests and fixtures that patch the global
  `sys.platform` or depend on POSIX-only names or attributes, and a short
  project rule in `AGENTS.md` so future work uses the helper. Platform-gated
  message assertions check the exception type or the product's own message
  source rather than copied wording.
- **Excluded:** Native probes and their CI venues, product behavior changes,
  and new matrix cells.
- **Effort:** S–M, medium confidence; assumes the product modules read the
  platform through a small number of module-level names.

**Key examples:**

1. A test faking macOS on a Windows runner exercises the macOS helper path
   while `pathlib`/`urllib` keep behaving as on Windows.
2. A file-list fixture with spaces and Unicode names is created successfully
   on Windows, macOS and Linux.
3. A test of the X11 owner shutdown runs on Windows without `os.killpg`
   present.
4. Rewording an unimplemented-platform message does not fail a test that only
   runs on another OS.

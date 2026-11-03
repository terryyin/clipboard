# Source review: SEED-001#bounded-x11-text-write

Launch: fresh general-purpose reviewer (no conversation inheritance) during
execution on 2026-11-03, told to use only the supplied text, read no project
files and change nothing. Input: the verbatim story section
(`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#bounded-x11-text-write`:
heading, Identity, Goal, Scope, maintainer queue note). No plan, return or
proof was supplied.

Returned exclusions (no ids): E1 "Excludes the same pattern in `copy_image`";
E2 "Excludes ... any change to selection rules". Non-promise: the maintainer
queue-order note. Reviewer note: "owned X11 writer only" read as limiting code
changes to the writer, with commitments 5 and 6 explicitly listed by Scope.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Callers of `copy(text)` on Linux X11 get the documented bounded `ClipboardContentError` instead of an indefinite hang (when the X server stalls and the text is larger than a pipe buffer) | slice 1 | observed: tests/test_text_x11_write_stall.py::test_large_text_raises_within_bound_when_owner_never_reads_stdin (200,000 chars, non-reading real owner → ClipboardContentError < bound+2s; fails pre-fix at 6s watchdog) |
| 2 | SEED-001#portable-text's "never an indefinite wait" holds for every text size | slice 1 | observed: same stall test for >64 KiB; small text: tests/test_text_x11.py::test_owner_that_never_offers_raises_after_the_bound |
| 3 | feed `xclip` its input without a blocking unbounded pipe write | slice 1 | observed: clipboard/_text_native_x11.py _start_owner: unlinked TemporaryFile as stdin, no pipe write; tests/fake_xclip_text.py FakeX11.popen asserts stdin is not PIPE |
| 4.1 | keeping the background owner | slice 1 | observed: _start_owner start_new_session=True, stdout DEVNULL (asserted in FakeX11.popen); tests/test_text_x11.py writer tests |
| 4.2 | keeping exact-bytes read-back | slice 1 | observed: _owner_serves compares UTF8_STRING to exact bytes; FakeOwner data read from stdin file; tests/test_text_x11.py writer tests pass |
| 4.3 | keeping stderr quoting | slice 1 | observed: tests/test_text_x11.py::test_owner_exiting_early_raises_quoting_its_stderr |
| 4.4 | keeping owner cleanup | slice 1 | observed: tests/test_text_x11_write_stall.py signalled == [owner.pid]; tests/test_text_x11.py::test_owner_that_never_offers_raises_after_the_bound |
| 5 | remove the test-only `os.killpg` fallback | slice 2 | |
| 6.1 | make the gated Wayland text wrapper fail rather than skip on a missing session | slice 3 | |
| 6.2 | make the gated Wayland text wrapper fail rather than skip on a missing helper | slice 3 | |

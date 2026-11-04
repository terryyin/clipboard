# Linux file-manager clipboard experiment

The `native-linux-x11-file-manager-offers` job in `ci.yml` runs Thunar on
Ubuntu 24.04 inside an isolated D-Bus session with Xvfb and Openbox. It
compares helper-made offers of `text/uri-list` and
`x-special/gnome-copied-files` (`copy` followed by file URIs).

The probe is independent of the planned `copy_files` API. Its results cover
the named Thunar/X11 environment; other file managers and Wayland require
their own paste observations.

## Observed result

[Actions run 41460755116, native file-manager job](https://github.com/terryyin/clipboard/actions/runs/41460755116/job/125328858098)
at `14e9f6de07c0278e3e147ecd4af2cd3c8f7c12cb` verified copies with both
single-format offers:

| Offer | Thunar Paste result |
| --- | --- |
| `text/uri-list` | Both destination files matched; originals unchanged |
| `x-special/gnome-copied-files` with `copy` | Both destination files matched; originals unchanged, before and after the URI-list round |

Tested environment: Ubuntu 24.04.5, Thunar 4.18.8, xclip 0.13,
xdotool 3.20160805.1, Openbox package 3.6.1-12build5,
Xvfb package 2:21.1.12-1ubuntu1.9, Python 3.13.14.
Each writer command exited before Paste. These helper-offer results settle
format interoperability for this environment; a library writer still needs
to repeat the file-manager proof through its public API.

That API-level proof is the separate `native-linux-x11-copy-files` job
(`tests/test_copy_files_native_linux_x11.py`): the public `copy_files` writes
`text/uri-list` from a child process that exits, then Thunar pastes it. Its
result is recorded in docs/evidence-wait-html-files.rst.

## What the probe checks

Each round creates two files with spaces and Unicode in their names, waits
for the `xclip` writer command to exit, checks the sole advertised payload
format, independently reads its exact bytes, and sends Ctrl+V to Thunar's
destination window. Successful paste requires both destination files with
matching bytes and unchanged originals. GNOME-format positive controls run
before and after the URI-list round. An empty destination must fail the
copy assertions before Paste is sent.

`no copies observed` means the destination stayed empty during the bounded
observation; it is not a claim about every Linux file manager. Failed
startup, missing helpers, failed positive controls, or invalid data fail
the job rather than count as format rejection.

The job uploads `file-manager-offers.json`, `thunar.log`, and `openbox.log`
as the `file-manager-offers-<attempt>` artifact, including when the probe
fails. JSON records the OS, Python, Thunar, helper and desktop package
versions, clipboard targets, writer exit, and per-format outcomes.

The probe requires `CLIPBOARD_NATIVE_PROBE=1` and
`CLIPBOARD_FILE_MANAGER_ISOLATED=1`. Run it only in its own D-Bus/X11
session: it replaces that session's clipboard and quits its Thunar process.
The normal test suite skips this desktop experiment. Desktop-free assertion
tests check missing copies, damaged copies, changed sources, and failed
file-manager startup.

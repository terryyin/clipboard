"""Linux Wayland clear: ``wl-copy --clear`` empties the regular selection.

``wl-copy --clear`` sets the selection to no source at all, so the previous
owner (another application, or a background ``wl-copy`` left by this
library's own writers) loses it and ``wl-paste -l`` reports nothing copied.
stdin is closed (``--clear`` reads nothing) and stderr goes to an unlinked
file, never a pipe a forked helper could hold open, so the bounded run cannot
hang on an inherited pipe.
"""

from __future__ import annotations

import subprocess
import tempfile

from clipboard._desktop import _helper_failure_detail
from clipboard._errors import ClipboardContentError

# Same bound as the Wayland text write (copy("") runs this command too).
_WAYLAND_CLEAR_TIMEOUT_S = 10.0
_WL_COPY_CLEAR_CMD = ["wl-copy", "--clear"]
_COMMAND = " ".join(_WL_COPY_CLEAR_CMD)


def _error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(f"Linux Wayland clipboard clear failed: {detail}")


def _logged_stderr(log) -> str:
    log.seek(0)
    return log.read().decode("utf-8", "replace")


def _wayland_clipboard_clearer() -> None:
    """Leave the Wayland selection with no offer at all; return ``None``.

    A missing ``wl-copy`` (with a ``wl-clipboard`` install hint), a non-zero
    exit (with wl-copy's stderr), a timeout, or an ``OSError`` raises
    ``ClipboardContentError``.
    """
    with tempfile.TemporaryFile() as log:
        try:
            result = subprocess.run(
                _WL_COPY_CLEAR_CMD,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=log,
                check=False,
                timeout=_WAYLAND_CLEAR_TIMEOUT_S,
                start_new_session=True,
            )
        except FileNotFoundError as exc:
            raise _error(
                "wl-copy was not found on PATH; install wl-clipboard (e.g. "
                "`sudo apt-get install wl-clipboard`) and ensure wl-copy is "
                "on PATH"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ClipboardContentError(
                f"Linux Wayland clipboard clear timed out (limit "
                f"{_WAYLAND_CLEAR_TIMEOUT_S:g}s); compositor stalled or not "
                f"answering ({_COMMAND})"
            ) from exc
        except OSError as exc:
            raise _error(f"could not run wl-copy ({exc})") from exc
        if result.returncode != 0:
            detail = _helper_failure_detail(
                subprocess.CompletedProcess(
                    result.args, result.returncode, "", _logged_stderr(log)
                )
            )
            raise _error(
                f"{_COMMAND} exited with status {result.returncode}"
                + (f": {detail}" if detail else "")
            )

"""Bounded Linux text-helper runs shared by the owned X11 and Wayland paths.

Every helper run has a deadline, and every failure becomes
``ClipboardContentError`` naming the desktop, the helper command, its exit
status and stderr, with the original exception (or a ``CalledProcessError``
carrying the captured output) as ``__cause__``. Callers recognise ordinary
absence from known stderr wording *before* calling ``_text_exit_error``;
anything they do not recognise is a failure, never ``""``.
"""

from __future__ import annotations

import subprocess
import time

from clipboard._desktop import _helper_stderr_detail
from clipboard._errors import ClipboardContentError

# Linux text reads and writes share the HTML readers' 10 s bound.
_LINUX_TEXT_TIMEOUT_S = 10.0
# Never hand a helper a zero / negative timeout once the deadline is spent.
_MIN_HELPER_TIMEOUT_S = 0.05


def _install_hint(helper: str, package: str) -> str:
    return (
        f"install {package} (e.g. `sudo apt-get install {package}`) and ensure "
        f"{helper} is on PATH"
    )


# Error subject: what the helper serves. A selection other than CLIPBOARD
# names itself (e.g. "primary selection text") so it never reads as CLIPBOARD.
_CLIPBOARD_TEXT = "clipboard text"


def _text_error(
    desktop: str, operation: str, detail: str, *, subject: str = _CLIPBOARD_TEXT
) -> ClipboardContentError:
    return ClipboardContentError(
        f"Linux {desktop} {subject} {operation} failed: {detail}"
    )


def _text_launch_error(
    desktop: str,
    operation: str,
    helper: str,
    package: str,
    exc: OSError,
    *,
    subject: str = _CLIPBOARD_TEXT,
) -> ClipboardContentError:
    """A helper that could not start: missing from PATH (with hint) or OSError."""
    if isinstance(exc, FileNotFoundError):
        detail = f"{helper} was not found on PATH; {_install_hint(helper, package)}"
    else:
        detail = f"could not run {helper} ({exc})"
    return _text_error(desktop, operation, detail, subject=subject)


def _remaining(deadline: float, bound: float) -> float:
    """Time left before ``deadline``, never above ``bound`` nor below the floor.

    Clamping to ``bound`` matters: a coarse clock can read the same tick at
    deadline creation and here, and ``(t + bound) - t`` can round above it.
    """
    return max(min(deadline - time.monotonic(), bound), _MIN_HELPER_TIMEOUT_S)


def _run_text_helper(
    cmd: list[str],
    *,
    desktop: str,
    operation: str,
    package: str,
    deadline: float,
    bound: float,
    subject: str = _CLIPBOARD_TEXT,
) -> subprocess.CompletedProcess[bytes]:
    """Run a read-only helper (stdin from /dev/null) before ``deadline``.

    Timeout, missing helper and ``OSError`` raise ``ClipboardContentError``;
    a non-zero exit is returned for the caller to classify.
    """
    try:
        return subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=_remaining(deadline, bound),
        )
    except subprocess.TimeoutExpired as exc:
        raise _text_error(
            desktop,
            operation,
            f"{' '.join(cmd)} did not answer within the {bound:g}s bound "
            "(clipboard owner stalled or display contended)",
            subject=subject,
        ) from exc
    except OSError as exc:
        raise _text_launch_error(
            desktop, operation, cmd[0], package, exc, subject=subject
        ) from exc


def _text_exit_error(
    desktop: str,
    operation: str,
    cmd: list[str],
    result: subprocess.CompletedProcess[bytes],
    *,
    subject: str = _CLIPBOARD_TEXT,
) -> ClipboardContentError:
    """Quote a failed helper run's status and stderr; cause keeps the output."""
    detail = _helper_stderr_detail(result)
    error = _text_error(
        desktop,
        operation,
        f"{' '.join(cmd)} exited with status {result.returncode}"
        + (f": {detail}" if detail else ""),
        subject=subject,
    )
    error.__cause__ = subprocess.CalledProcessError(
        result.returncode, cmd, result.stdout, result.stderr
    )
    return error


def _decode_text(
    raw: bytes,
    encoding: str,
    desktop: str,
    what: str,
    *,
    subject: str = _CLIPBOARD_TEXT,
) -> str:
    """Decode helper output by its declared encoding; never leak decode errors."""
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError as exc:
        raise _text_error(
            desktop, "read", f"{what} is not valid {encoding} ({exc})", subject=subject
        ) from exc


def _helper_log(log) -> bytes:
    """Everything a writer helper logged to its unlinked stderr file."""
    log.seek(0)
    return log.read()


def _helper_log_suffix(log) -> str:
    """``": <stderr>"`` for an error message, or ``""`` when nothing logged."""
    detail = _helper_log(log).decode("utf-8", "replace").strip()
    return f": {detail}" if detail else ""


def _logged_exit_error(
    desktop: str,
    operation: str,
    cmd: list[str],
    status: int,
    log,
    *,
    subject: str = _CLIPBOARD_TEXT,
) -> ClipboardContentError:
    """``_text_exit_error`` for a writer helper whose stderr went to ``log``."""
    return _text_exit_error(
        desktop,
        operation,
        cmd,
        subprocess.CompletedProcess(cmd, status, None, _helper_log(log)),
        subject=subject,
    )

"""Wait until a freshly started headless compositor answers Wayland clients.

Sway creates ``$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY`` before its event loop
serves clients, so the socket alone does not mean a client's request will be
answered: on a slow runner the probe's first ``wl-copy --clear`` can block
past its bound. This waits for the socket, then for a ``wl-paste
--list-types`` round trip that lists an offer or reports nothing copied (read
only: it never selects anything, so a fresh session stays unselected). On a
deadline it prints the compositor log and exits 1.

Usage: ``python scripts/await_wayland_compositor.py --log <compositor log>``
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from clipboard._desktop import (
    _helper_failure_detail,
    _wl_paste_reports_nothing_copied,
)

DEADLINE_S = 30.0
ATTEMPT_TIMEOUT_S = 5.0
RETRY_S = 0.2
LIST_TYPES = ["wl-paste", "--list-types"]


def _answered(run) -> tuple[bool, str]:
    """One bounded round trip: (compositor answered, detail when it did not)."""
    try:
        result = run(
            LIST_TYPES,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=ATTEMPT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return False, f"wl-paste --list-types timed out ({ATTEMPT_TIMEOUT_S:g}s)"
    except OSError as exc:
        return False, f"could not run wl-paste ({exc})"
    if result.returncode == 0 or _wl_paste_reports_nothing_copied(result.stderr or ""):
        return True, ""
    detail = _helper_failure_detail(result)
    return False, f"wl-paste --list-types exited {result.returncode}: {detail}"


def await_compositor(
    socket: Path,
    *,
    deadline_s: float = DEADLINE_S,
    run=subprocess.run,
    clock=time.monotonic,
    sleep=time.sleep,
) -> str | None:
    """``None`` once the compositor answers; else the last reason it did not."""
    deadline = clock() + deadline_s
    reason = f"no Wayland socket at {socket}"
    while True:
        if socket.is_socket():
            answered, reason = _answered(run)
            if answered:
                return None
        if clock() >= deadline:
            return reason
        sleep(RETRY_S)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log", type=Path, required=True, help="compositor log")
    args = parser.parse_args(argv)
    socket = Path(os.environ["XDG_RUNTIME_DIR"]) / os.environ["WAYLAND_DISPLAY"]
    reason = await_compositor(socket)
    if reason is None:
        print(f"Wayland compositor answering at {socket}")
        return 0
    print(f"Wayland compositor not answering within {DEADLINE_S:g}s: {reason}")
    try:
        print(f"--- {args.log} ---\n{args.log.read_text(errors='replace')}")
    except OSError as exc:
        print(f"(compositor log unreadable: {exc})")
    return 1


if __name__ == "__main__":
    sys.exit(main())

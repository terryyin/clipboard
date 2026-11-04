#!/usr/bin/env python3
"""Gated probe: Windows desktop ``wait_for_kind`` / ``wait_for_text_change``
against an independent PowerShell ``Set-Clipboard`` producer.

The four steps are ``native_wait_support``'s, shared with the macOS, Linux
X11 and Linux Wayland wait probes. Setup before steps 1, 2 and 4:
``clipboard.clear()`` in this process; the independent ctypes consumer
(``windows_clipboard_consumer.py``) must then enumerate no formats.

Step 1: a child Python starts ``wait_for_kind("text", timeout=20)`` on the
empty clipboard; about 1 s after its first observation an independent
Windows PowerShell 5.1 ``Set-Clipboard`` process copies text (the copy counts
as finished when that process exits). Holds when the returned snapshot lists
``"text"``, an earlier observation saw no text, and the wait returned after
the copy within one interval plus two observations plus 0.1 s. Every
observation's kinds and native formats are recorded
(``child.outcome.observations``, summarised as ``observed_kinds``), with the
consumer's format listing after the copy. Step 2: a child
``wait_for_kind("html", timeout=1)`` with nothing copied returns ``None``
within the timeout plus one observation. Step 3: an independent
``Set-Clipboard`` copies the old text, a child
``wait_for_text_change(timeout=20)`` reads it as its baseline, and an
independent ``Set-Clipboard`` copies the new text, which the wait returns.
Step 4: baseline old text, ``clear()``, then an identical independent recopy;
the wait returns ``None`` at its 3 s timeout.

Prints one JSON object on stdout with the runner image and OS version. Exit
0 when every step holds, 1 naming the failed steps, and 2 with
``evidence_limit`` off ``win32`` (the wrapper fails on it; never a skip or a
silent verified success). Not run by default pytest. **Replaces the live
clipboard.**
"""

from __future__ import annotations

import subprocess
import sys

from native_wait_harness import INTERVAL_S, WaitDesktop
from native_wait_support import report, run_steps
from windows_native_clear_support import consumer_formats, no_formats
from windows_powershell_producers import PRODUCERS, powershell


def set_clipboard_produce(text: str) -> dict:
    """Independent producer: ``Set-Clipboard`` with the text from a UTF-8 file."""
    try:
        produced = powershell(PRODUCERS["text_only"], text)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"producer": "Set-Clipboard", "error": f"{type(exc).__name__}: {exc}"}
    return {
        "producer": "Set-Clipboard",
        "returncode": produced.returncode,
        "stderr": produced.stderr.strip()[-1000:],
    }


DESKTOP = WaitDesktop(
    producer="set_clipboard",
    produce=set_clipboard_produce,
    listing=consumer_formats,
    is_empty=no_formats,
)


def main() -> int:
    if sys.platform != "win32":
        report(
            ok=False,
            verified=False,
            evidence_limit=True,
            reason=f"not a Windows desktop (platform {sys.platform!r})",
        )
        return 2
    from windows_native_text_support import windows_floors

    steps = run_steps(DESKTOP)
    failed = [s["step"] for s in steps if not s["ok"]]
    env = {
        **windows_floors(),
        "producer": "Windows PowerShell 5.1 Set-Clipboard (independent process)",
        "consumer": "ctypes EnumClipboardFormats (windows_clipboard_consumer.py)",
        "library_under_test": (
            "clipboard.wait_for_kind / clipboard.wait_for_text_change in a child Python"
        ),
    }
    report(
        ok=not failed,
        verified=not failed,
        evidence_limit=False,
        desktop="Windows desktop",
        failed_steps=failed,
        steps=steps,
        environment=env,
        floors={
            "windows_version": env["windows_version"],
            "windows_build": env["windows_build"],
            "powershell": env["powershell"],
            "interval_s": INTERVAL_S,
        },
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

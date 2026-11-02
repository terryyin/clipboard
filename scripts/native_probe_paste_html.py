"""Shared fixtures and paste_html() runners for gated native paste_html probes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FRAGMENT = (
    '<a href="https://example.com/caf%C3%A9" style="color:#c00">'
    "<b>café → naïve 日本</b></a>"
)
PLAIN_TEXT = "café → naïve 日本 (plain text only)"


def paste_html() -> dict:
    """paste_html() in this process through the default native reader."""
    import clipboard

    clipboard.set_html_clipboard_reader(None)
    try:
        return {"paste_html": clipboard.paste_html()}
    except clipboard.ClipboardContentError as exc:
        return {"paste_html": None, "error": f"ClipboardContentError: {exc}"}


def child_paste_html(
    env: dict, *, root: Path, names_key: str, names: tuple[str, ...]
) -> dict:
    """paste_html() in a child with a modified environment; record the outcome.

    ``names_key`` reports whether the child's output contains every string in
    ``names`` (the helper and its install hint).
    """
    child = (
        "import clipboard\n"
        "try:\n"
        "    print(repr(clipboard.paste_html()))\n"
        "except clipboard.ClipboardContentError as exc:\n"
        "    print('ClipboardContentError:', exc)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", child],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    out = result.stdout.strip()
    return {
        "returncode": result.returncode,
        "outcome": out or result.stderr.strip(),
        "content_error": out.startswith("ClipboardContentError:"),
        names_key: all(name in out for name in names),
    }

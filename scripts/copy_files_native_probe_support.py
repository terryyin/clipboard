"""Shared offer shape for gated copy_files native probes across desktops.

Owns the relative-file + directory + duplicate round arguments and the
``Path.resolve()`` absolute expectations writers publish (e.g. macOS
``/tmp`` → ``/private/tmp``). Platform probes supply their own child writer
and independent consumer.
"""

from __future__ import annotations

import os
from pathlib import Path

# Further offer-level round: relative file, directory, same file again.
DIRECTORY_NAME = "a dir"
RELATIVE_DIRECTORY_DUPLICATE_ARGS = (
    "report final.pdf",
    DIRECTORY_NAME,
    "report final.pdf",
)


def absolute_relative_directory_duplicate(source: Path) -> tuple[list[str], list[str]]:
    """Relative args and the absolute paths ``copy_files`` must publish."""
    relative = list(RELATIVE_DIRECTORY_DUPLICATE_ARGS)
    absolute = [str((source / name).resolve()) for name in relative]
    return relative, absolute


def prepare_relative_directory_duplicate(source: Path) -> tuple[list[str], list[str]]:
    """Create the directory entry and return relative args plus absolute paths."""
    (source / DIRECTORY_NAME).mkdir()
    return absolute_relative_directory_duplicate(source)


def uri_list_body(paths: list[str]) -> bytes:
    """CRLF ``file://`` URI list body matching the X11/Wayland writers."""
    return "".join(f"{Path(p).as_uri()}\r\n" for p in paths).encode("ascii")


def ensure_repo_on_pythonpath(
    env: dict[str, str] | None, root: Path | str
) -> dict[str, str]:
    """Ensure the repo root is importable even when the child's cwd is elsewhere."""
    child_env = dict(env) if env is not None else dict(os.environ)
    root_s = str(root)
    existing = child_env.get("PYTHONPATH", "")
    parts = [p for p in existing.split(os.pathsep) if p]
    if root_s not in parts:
        child_env["PYTHONPATH"] = (
            root_s if not existing else root_s + os.pathsep + existing
        )
    return child_env


def paste_files_consistency() -> dict:
    """Public ``paste_files()`` with the default reader (consistency only)."""
    import clipboard

    clipboard.set_files_clipboard_reader(None)
    try:
        return {"value": clipboard.paste_files(), "error": None}
    except clipboard.ClipboardContentError as exc:
        return {"value": None, "error": str(exc)}

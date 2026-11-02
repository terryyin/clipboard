"""In-memory file-list offer stand-in and path side-effect spies for contract tests."""

from __future__ import annotations

import builtins
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

UNICODE_PATH = "/tmp/docs/unicodé report.txt"
SPACED_PATH = "/tmp/photos/a file.png"
ORDERED_PATHS = [SPACED_PATH, UNICODE_PATH]

URI_LIST_TWO_LOCAL = (
    "# comment ignored\n"
    "file:///tmp/photos/a%20file.png\n"
    "file:///tmp/docs/unicod%C3%A9%20report.txt\n"
)


@dataclass
class FakeFilesClipboard:
    """Mutable in-memory file-list offer model for contract tests."""

    offer: Any = None
    reader_calls: int = 0
    cut_reissues: list[Any] = field(default_factory=list)
    writes: list[Any] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)

    def reader(self) -> Any:
        self.reader_calls += 1
        return self.offer

    def reissue_cut(self, *args: Any) -> None:
        """Would rewrite the offer as cut/move — must never be called by paste_files."""
        self.cut_reissues.append(args)
        self.writes.append(("cut", args))
        self.side_effects.append("cut_reissue")


def install_path_side_effect_spies(
    monkeypatch: pytest.MonkeyPatch, paths: list[str]
) -> list[str]:
    """Record open/copy/move/delete/exists hits that name an offered path."""
    hits: list[str] = []

    def record_if_offered(target: object) -> None:
        try:
            as_str = os.fspath(target)  # type: ignore[arg-type]
        except TypeError:
            return
        for path in paths:
            if path == as_str or path in as_str or as_str in path:
                hits.append(as_str)

    def wrap(real):
        def tracking(first, *args, **kwargs):
            record_if_offered(first)
            return real(first, *args, **kwargs)

        return tracking

    def wrap_method(real):
        def tracking(self, *args, **kwargs):
            record_if_offered(self)
            return real(self, *args, **kwargs)

        return tracking

    def wrap_two(real):
        def tracking(src, dst, *args, **kwargs):
            record_if_offered(src)
            record_if_offered(dst)
            return real(src, dst, *args, **kwargs)

        return tracking

    monkeypatch.setattr(builtins, "open", wrap(builtins.open))
    monkeypatch.setattr(os, "open", wrap(os.open))
    monkeypatch.setattr(os, "remove", wrap(os.remove))
    monkeypatch.setattr(os, "unlink", wrap(os.unlink))
    monkeypatch.setattr(os, "rename", wrap_two(os.rename))
    monkeypatch.setattr(os, "replace", wrap_two(os.replace))
    monkeypatch.setattr(shutil, "copy", wrap_two(shutil.copy))
    monkeypatch.setattr(shutil, "copy2", wrap_two(shutil.copy2))
    monkeypatch.setattr(shutil, "move", wrap_two(shutil.move))
    monkeypatch.setattr(Path, "open", wrap_method(Path.open))
    monkeypatch.setattr(Path, "read_bytes", wrap_method(Path.read_bytes))
    monkeypatch.setattr(Path, "unlink", wrap_method(Path.unlink))
    monkeypatch.setattr(Path, "rename", wrap_method(Path.rename))
    monkeypatch.setattr(Path, "exists", wrap_method(Path.exists))
    monkeypatch.setattr(Path, "is_file", wrap_method(Path.is_file))
    return hits

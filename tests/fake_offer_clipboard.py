"""In-memory offer stand-in for desktop-free inspect() contract tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import clipboard
from clipboard._offer import snapshot_from_native_formats


@dataclass
class FakeOfferClipboard:
    """Mutable in-memory offer: native type list + optional payloads.

    Inspect paths must derive kinds from ``formats`` alone via
    ``snapshot_from_native_formats`` — never ``fetch_payload`` or
    ``read_filesystem``.
    """

    formats: list[str] = field(default_factory=list)
    payloads: dict[str, Any] = field(default_factory=dict)
    payload_fetches: list[str] = field(default_factory=list)
    filesystem_reads: list[str] = field(default_factory=list)
    paste_text_value: str = ""
    access_error: Exception | None = None

    def seed(
        self,
        formats: list[str],
        *,
        payloads: dict[str, Any] | None = None,
        paste_text: str = "",
    ) -> None:
        self.formats = list(formats)
        self.payloads = dict(payloads or {})
        self.paste_text_value = paste_text
        self.payload_fetches.clear()
        self.filesystem_reads.clear()
        self.access_error = None

    def clear(self) -> None:
        self.seed([])

    def deny_access(self, message: str) -> None:
        self.access_error = clipboard.ClipboardContentError(message)

    def fail_enumeration(self, message: str) -> None:
        self.access_error = OSError(message)

    def fetch_payload(self, fmt: str) -> Any:
        self.payload_fetches.append(fmt)
        return self.payloads[fmt]

    def read_filesystem(self, path: str) -> bytes:
        self.filesystem_reads.append(path)
        return b""

    def paste_text(self) -> str:
        """Stand-in for text paste(); emptiness must not drive kind presence."""
        return self.paste_text_value

    def inspector(self) -> clipboard.ClipboardOfferSnapshot:
        if self.access_error is not None:
            raise self.access_error
        # Type enumeration alone — no body reads, no filesystem, no paste().
        return snapshot_from_native_formats(self.formats)

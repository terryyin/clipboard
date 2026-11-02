"""A tiny opaque red PNG built with the stdlib, for image-only probe offers.

Native ``paste_html`` probes need an image-only clipboard offer but must not
require Pillow (``clipboard[images]``), so they share this hand-built PNG.
"""

from __future__ import annotations

import struct
import zlib


def solid_red_png_bytes() -> bytes:
    """A 4x4 opaque red RGB PNG."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        crc = struct.pack(">I", zlib.crc32(body))
        return struct.pack(">I", len(data)) + body + crc

    rows = b"".join(b"\x00" + b"\xff\x00\x00" * 4 for _ in range(4))
    header = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )

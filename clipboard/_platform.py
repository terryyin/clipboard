"""Private call-time platform seam.

Product modules read the running platform only through ``current()``
so tests can fake it here without changing the shared ``sys.platform`` that
the standard library also reads.
"""

from __future__ import annotations

import sys


def current() -> str:
    """Return the running platform name (``sys.platform``) at call time."""
    return sys.platform

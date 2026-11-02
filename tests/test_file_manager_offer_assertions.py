"""The native experiment's oracle must reject missing and damaged copies."""

from pathlib import Path
from runpy import run_path

import pytest

PROBE = (
    Path(__file__).resolve().parents[1]
    / "scripts/probe_linux_x11_file_manager_offers.py"
)
assert_copies = run_path(str(PROBE))["_assert_copies"]


@pytest.mark.parametrize("damage", ["missing", "corrupt-copy", "changed-source", None])
def test_copy_oracle_requires_exact_destination_and_unchanged_source(tmp_path, damage):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    expected = {"report final.txt": b"one", "données é.csv": b"two"}
    for name, content in expected.items():
        (source / name).write_bytes(content)
        (destination / name).write_bytes(content)
    first = next(iter(expected))
    if damage == "missing":
        (destination / first).unlink()
    elif damage == "corrupt-copy":
        (destination / first).write_bytes(b"damaged")
    elif damage == "changed-source":
        (source / first).write_bytes(b"changed")
    if damage:
        with pytest.raises(AssertionError):
            assert_copies(source, destination, expected)
    else:
        assert_copies(source, destination, expected)

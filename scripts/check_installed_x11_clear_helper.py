"""Launch the installed X11 clear helper and require its structured failure.

Run with ``python -I`` inside an isolated install of a built distribution.
It launches the helper through the library's own command with a ``DISPLAY``
no X server serves, so no desktop session is needed: the helper must start,
exit 3 and print one JSON line whose ``failure`` is ``display`` (Linux with
libX11) or ``libx11`` (no libX11, e.g. macOS). It proves only that the
distribution ships a helper that launches, not that a clipboard is cleared.

When ``CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR`` names a libX11 directory (the
Linux Nix dev shell sets it), only the helper child gets it on
``LD_LIBRARY_PATH`` and its failure must be ``display``.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from clipboard import _clear_x11

SOURCE_TREE = Path(__file__).resolve().parents[1]
UNUSABLE_DISPLAY = ":65535"
LIBX11_DIR = os.environ.get("CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR", "")


def fail(message):
    raise SystemExit(f"installed X11 clear helper check failed: {message}")


def main():
    command = _clear_x11._relinquish_command()
    helper = Path(command[-1]).resolve()
    if helper.is_relative_to(SOURCE_TREE):
        fail(f"helper {helper} resolves inside the source tree {SOURCE_TREE}")
    # uv's isolated environments layer cached installs in via sys.path, so the
    # install is identified by its site-packages directory, not sys.prefix.
    installs = [Path(p).resolve() for p in sys.path if Path(p).name == "site-packages"]
    if not any(helper.is_relative_to(install) for install in installs):
        fail(f"helper {helper} is not inside an installed site-packages")
    if not helper.is_file():
        fail(f"helper {helper} is missing from the distribution")
    env = {k: v for k, v in os.environ.items() if k != "DISPLAY"}
    env["DISPLAY"] = UNUSABLE_DISPLAY
    if LIBX11_DIR:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(
            filter(None, [LIBX11_DIR, env.get("LD_LIBRARY_PATH")])
        )
    with tempfile.TemporaryDirectory() as cwd:
        result = subprocess.run(
            command,
            env=env,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    detail = f"stdout={result.stdout!r} stderr={result.stderr!r}"
    if result.returncode != 3:
        fail(f"helper exited with status {result.returncode}, not 3: {detail}")
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        fail(f"helper printed {len(lines)} lines, not one JSON line: {detail}")
    try:
        failure = json.loads(lines[0])["failure"]
    except (ValueError, TypeError, KeyError):
        fail(f"helper output is not a JSON failure line: {detail}")
    expected = {"display"} if LIBX11_DIR else {"display", "libx11"}
    if failure not in expected:
        wanted = " or ".join(sorted(expected))
        fail(f"helper failure {failure!r} is not {wanted}: {detail}")
    print(f"Installed X11 clear helper {helper} launched: failure {failure}")


if __name__ == "__main__":
    main()

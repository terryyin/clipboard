"""Shared steps and the one "cleared" rule for every desktop's ``clear`` probe.

``cleared_step`` is the single definition of a proven clear, used by the
Linux X11 / Wayland, Windows and macOS probes: every child ``clear()``
returned, the desktop's independent listing (called after the clear)
classifies as empty under that desktop's predicate, every followed clipboard
owner exited within the bound, and every public reader reads absence
(``EMPTY_READS``: ``inspect()`` empty, ``paste()`` ``""``, ``paste_html`` /
``paste_files`` / ``paste_image`` ``None``) rather than an error.
``read_everything`` records each reader's value or error in this process.
``helper`` records an independent helper run (exit code, stdout, stderr) so
the observed helper wording lands in the report. ``child_clear`` runs
``clipboard.clear()`` in a separate Python process that exits before the
clipboard is observed. ``helper_pids`` / ``wait_pids_exit`` (Linux ``/proc``
only) follow a clipboard owner process (for example a background ``wl-copy``
or ``xclip``) until it ends, and ``distro`` names the Linux distribution.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

HELPER_TIMEOUT_S = 15
CHILD_TIMEOUT_S = 60
# How long a clipboard owner may take to exit once it loses the selection.
OWNER_EXIT_BOUND_S = 5.0
_ROOT = Path(__file__).resolve().parents[1]
EMPTY_READS = {
    "inspect": {"value": {"kinds": [], "formats": []}},
    "paste": {"value": ""},
    "paste_html": {"value": None},
    "paste_files": {"value": None},
    "paste_image": {"value": None},
}
_CHILD_CLEAR = """
import json
import clipboard

try:
    clipboard.clear()
except clipboard.ClipboardContentError as exc:
    print(json.dumps({"raised": "ClipboardContentError", "message": str(exc)}))
    raise SystemExit(3)
print(json.dumps({"raised": None}))
"""


def helper(cmd: list[str], env: dict | None = None) -> dict:
    """Run an independent clipboard helper; record its exit and output."""
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=HELPER_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "cmd": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr.strip(),
    }


def child_python(code: str, env: dict | None = None) -> dict:
    """Run ``code`` in a separate Python that exits; record exit, output, time."""
    started = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=_ROOT,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=CHILD_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "elapsed_s": round(time.monotonic() - started, 3),
    }


def child_clear(env: dict | None = None) -> dict:
    """``clipboard.clear()`` in a child Python; ``outcome`` is its JSON line."""
    run = child_python(_CHILD_CLEAR, env=env)
    try:
        run["outcome"] = json.loads(run.get("stdout", "").splitlines()[-1])
    except (IndexError, ValueError):
        run["outcome"] = None
    return run


def child_cleared(run: dict) -> bool:
    """Whether a ``child_clear`` run returned normally from ``clear()``."""
    return run.get("returncode") == 0 and run.get("outcome") == {"raised": None}


def helper_pids(name: str, *, argv_contains: str | None = None) -> set[int]:
    """Live (non-zombie) PIDs whose ``comm`` is ``name`` (Linux ``/proc``)."""
    pids = set()
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            if (proc / "comm").read_text().strip() != name:
                continue
            if _is_zombie(proc):
                continue
            raw_argv = (proc / "cmdline").read_bytes()
            argv = raw_argv.replace(b"\0", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        if argv_contains is None or argv_contains in argv:
            pids.add(int(proc.name))
    return pids


def _is_zombie(proc: Path) -> bool:
    stat = (proc / "stat").read_text()
    return stat.rsplit(")", 1)[-1].split()[0] == "Z"


def _alive(pid: int) -> bool:
    proc = Path("/proc") / str(pid)
    try:
        return not _is_zombie(proc)
    except OSError:
        return False


def wait_pids_exit(pids: set[int], bound_s: float = OWNER_EXIT_BOUND_S) -> dict:
    """Wait up to ``bound_s`` for ``pids`` to exit; record what is left."""
    started = time.monotonic()
    alive = {pid for pid in pids if _alive(pid)}
    while alive and time.monotonic() - started < bound_s:
        time.sleep(0.05)
        alive = {pid for pid in alive if _alive(pid)}
    return {
        "pids": sorted(pids),
        "still_alive": sorted(alive),
        "exited": bool(pids) and not alive,
        "waited_s": round(time.monotonic() - started, 3),
        "bound_s": bound_s,
    }


def _attempt(read) -> dict:
    try:
        return {"value": read()}
    except Exception as exc:  # noqa: BLE001 — record for the JSON report
        return {"error_type": type(exc).__name__, "error": str(exc)}


def read_everything() -> dict:
    """Every public reader's value (JSON-shaped) or error, in this process."""
    import clipboard

    def snapshot() -> dict:
        snap = clipboard.inspect()
        return {"kinds": sorted(snap.kinds), "formats": list(snap.formats)}

    def image() -> object:
        found = clipboard.paste_image()
        return None if found is None else f"{found.mode} {found.size}"

    return {
        "inspect": _attempt(snapshot),
        "paste": _attempt(clipboard.paste),
        "paste_html": _attempt(clipboard.paste_html),
        "paste_files": _attempt(clipboard.paste_files),
        "paste_image": _attempt(image),
    }


def reads_empty(reads: dict) -> bool:
    """Whether ``read_everything`` saw an empty clipboard and no errors."""
    return reads == EMPTY_READS


def _owner_exited(owner_exit: dict) -> bool:
    return (
        owner_exit.get("exited") is True
        and owner_exit["waited_s"] <= (owner_exit["bound_s"])
    )


def cleared_step(
    name: str,
    listing,
    is_empty,
    *,
    held: bool = True,
    clears: tuple[dict, ...] = (),
    owner_exit: dict | None = None,
    reader=read_everything,
    **observed,
) -> dict:
    """The one "cleared" rule: clears returned, listing empty, readers absent.

    ``listing`` is the desktop's independent consumer (called now, after the
    clear), ``is_empty`` its empty-clipboard predicate; ``held`` carries the
    step's own preconditions (producer ran, type offered). A followed
    ``owner_exit`` (``wait_pids_exit``) must show every owner ended within
    its bound.
    """
    after = listing()
    empty = bool(is_empty(after))
    reads = reader()
    ok = (
        held
        and all(child_cleared(run) for run in clears)
        and (owner_exit is None or _owner_exited(owner_exit))
        and empty
        and reads_empty(reads)
    )
    if owner_exit is not None:
        observed["owner_exit"] = owner_exit
    return step(
        name, ok, **observed, listing_after=after, classified_empty=empty, reads=reads
    )


def step(name: str, ok: bool, **observed) -> dict:
    return {"step": name, "ok": bool(ok), **observed}


def distro() -> str | None:
    try:
        return platform.freedesktop_os_release().get("PRETTY_NAME")
    except OSError:
        return None


def report(**fields) -> None:
    print(json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False))

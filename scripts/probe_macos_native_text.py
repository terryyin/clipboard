#!/usr/bin/env python3
"""Independent producer/consumer probe: macOS pasteboard text <-> copy/paste.

Producers and consumers that are not this library run in other processes:
osascript ``set the clipboard`` (JXA) and ``the clipboard as «class utf8»``,
``pbpaste`` under a UTF-8 ``LANG``, and a JXA ``NSPasteboard`` writer for the
cleared and image-only offers. A child Python started with an empty
environment (absolute interpreter path, ``env={}``; it drops any locale
variable Python's PEP 538 coercion injects before importing ``clipboard``)
checks that the owned path does not depend on the caller's locale.

Prints one JSON object; exits non-zero naming any unobserved step (evidence
limit). Requires darwin. Overwrites the clipboard. Not run by default pytest.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from native_probe_common import die, macos_environment
from stdlib_png import solid_red_png_bytes

ROOT = Path(__file__).resolve().parents[1]
TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "
KEEP = "keep"
HELPER_TIMEOUT = 30
LOCALE_VARS = ("LANG", "LC_ALL", "LC_CTYPE", "LC_MESSAGES", "LC_COLLATE")

_SA = "var app = Application.currentApplication(); app.includeStandardAdditions = true;"
_PB = 'ObjC.import("AppKit"); var pb = $.NSPasteboard.generalPasteboard;'

_CHILD = """
import json, os, sys
injected = {k: os.environ.pop(k) for k in %r if k in os.environ}
sys.path.insert(0, %r)
import clipboard
out = {"injected_locale_vars": injected, "environ": dict(os.environ)}
try:
    if sys.argv[1] == "copy":
        clipboard.copy(json.loads(sys.argv[2]))
    else:
        out["paste"] = clipboard.paste()
except Exception as exc:
    out["error"] = f"{type(exc).__name__}: {exc}"
print(json.dumps(out))
"""


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, check=False, timeout=HELPER_TIMEOUT, **kwargs
    )


def _jxa(script: str) -> str:
    result = _run(["osascript", "-l", "JavaScript", "-e", script], text=True)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "").strip())
    return result.stdout.strip()


def _produce(text: str) -> None:
    """Independent producer: Standard Additions ``set the clipboard to``."""
    _jxa(f"{_SA} app.setTheClipboardTo({json.dumps(text)}); 'ok';")


def _osascript_consumer(expression: str = "the clipboard as «class utf8»") -> str:
    """Independent AppleScript consumer; drops the newline osascript appends.

    Plain ``the clipboard`` coerces to classic text and turns LF into CR, so
    exactness is judged on the ``«class utf8»`` form.
    """
    result = _run(["osascript", "-e", expression])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
    raw = result.stdout
    return (raw[:-1] if raw.endswith(b"\n") else raw).decode("utf-8")


def _pbpaste_consumer() -> dict:
    """Independent consumer: ``pbpaste`` under the user's UTF-8 locale."""
    result = _run(["/usr/bin/pbpaste"], env={"LANG": "en_US.UTF-8"})
    return {"returncode": result.returncode, "bytes": result.stdout.hex()}


def _types() -> list[str]:
    return json.loads(_jxa(f"{_PB} JSON.stringify(ObjC.deepUnwrap(pb.types) || []);"))


def _empty_env_child(*args: str) -> dict:
    code = _CHILD % (LOCALE_VARS, str(ROOT))
    result = _run([sys.executable, "-c", code, *args], env={}, text=True)
    if result.returncode != 0:
        return {"error": f"child exited {result.returncode}: {result.stderr.strip()}"}
    return json.loads(result.stdout)


def _step(name: str, ok: bool, **observed) -> dict:
    return {"step": name, "ok": ok, **observed}  # ok False -> evidence limit


def _probe(tmpdir: Path) -> list[dict]:
    import clipboard

    steps = []
    expected = TEXT.encode("utf-8").hex()

    _produce(TEXT)
    got = clipboard.paste()
    steps.append(_step("1_independent_producer_to_paste", got == TEXT, paste=got))

    child = _empty_env_child("copy", json.dumps(TEXT))
    pb = _pbpaste_consumer()
    osa = _osascript_consumer()
    steps.append(
        _step(
            "2_empty_env_child_copy_to_independent_consumers",
            "error" not in child
            and pb == {"returncode": 0, "bytes": expected}
            and osa == TEXT,
            child=child,
            pbpaste_utf8=pb,
            expected_bytes=expected,
            osascript_the_clipboard=osa,
            plain_the_clipboard_context=_osascript_consumer("the clipboard"),
        )
    )

    _produce(TEXT)
    child = _empty_env_child("paste")
    steps.append(
        _step("3_empty_env_child_paste", child.get("paste") == TEXT, child=child)
    )

    clipboard.copy("")
    got = clipboard.paste()
    pb, types = _pbpaste_consumer(), _types()
    ok = got == "" and type(got) is str
    steps.append(
        _step("4_copy_empty_then_paste", ok, paste=got, pbpaste=pb, types=types)
    )

    for name, bad, marker in (
        ("5a_nul_refused_keeps_prior", "a\x00b", "NUL"),
        ("5b_lone_surrogate_refused_keeps_prior", "\ud800", "surrogate"),
    ):
        _produce(KEEP)
        error = None
        try:
            clipboard.copy(bad)
        except clipboard.ClipboardContentError as exc:
            error = str(exc)
        osa = _osascript_consumer()
        ok = error is not None and marker in error and osa == KEEP
        steps.append(_step(name, ok, error=error, osascript_the_clipboard=osa))

    _produce(KEEP)
    _jxa(f"{_PB} pb.clearContents; 'ok';")
    types = _types()
    got = clipboard.paste()
    ok = got == "" and types == []
    steps.append(_step("6a_cleared_reads_empty", ok, paste=got, types=types))

    png = tmpdir / "image.png"
    png.write_bytes(solid_red_png_bytes())
    _jxa(
        f"{_PB} pb.clearContents; "
        f"var d = $.NSData.dataWithContentsOfFile({json.dumps(str(png))}); "
        'pb.setDataForType(d, "public.png"); "ok";'
    )
    types = _types()
    try:
        got, error = clipboard.paste(), None
    except Exception as exc:  # noqa: BLE001 — record for the JSON report
        got, error = None, f"{type(exc).__name__}: {exc}"
    text_types = [t for t in types if "text" in t or t == "NSStringPboardType"]
    steps.append(
        _step(
            "6b_image_only_reads_empty",
            got == "" and error is None and "public.png" in types and not text_types,
            paste=got,
            error=error,
            types=types,
        )
    )
    return steps


def _locale_control() -> dict:
    """Context only: does bare ``pbcopy`` without any locale corrupt the text?"""
    _run(["/usr/bin/pbcopy"], env={}, input=TEXT.encode("utf-8"))
    raw = bytes.fromhex(_pbpaste_consumer()["bytes"])
    return {"env_i_pbcopy_exact": raw == TEXT.encode("utf-8"), "bytes": raw.hex()}


def main() -> None:
    if sys.platform != "darwin":
        die(f"probe requires macOS (darwin); got {sys.platform!r}")
    try:
        import clipboard
    except ImportError as exc:
        die(f"missing clipboard import: {exc}")
    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)

    with tempfile.TemporaryDirectory(prefix="clipboard-text-probe-") as raw:
        try:
            control = _locale_control()
            steps = _probe(Path(raw))
        except (RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
            die(f"evidence limit: independent pasteboard helper failed: {exc}")

    limits = [step["step"] for step in steps if not step["ok"]]
    report = {
        "ok": not limits,
        "evidence_limits": limits,
        "environment": macos_environment(
            helper="pbcopy / pbpaste (macOS built-in, LC_ALL=en_US.UTF-8)",
            reader="clipboard.paste default (owned macOS path)",
            writer="clipboard.copy default (owned macOS path)",
            backend=clipboard._text._select_text_backend(),
        ),
        "steps": steps,
        "locale_control": control,
        "commitments": {
            "independent_producer": "osascript JXA setTheClipboardTo",
            "independent_consumers": (
                "osascript 'the clipboard as «class utf8»'; "
                "/usr/bin/pbpaste with LANG=en_US.UTF-8"
            ),
            "empty_env_child": (
                "absolute sys.executable, env={}; PEP 538 coercion's locale "
                "variables dropped before importing clipboard"
            ),
            "gating": "CLIPBOARD_NATIVE_PROBE=1 on darwin only",
            "authorization": "normal macOS pasteboard; no entitlement bypass",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if limits:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

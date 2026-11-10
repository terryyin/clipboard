"""Replay JUnit through the production converter and collector CLIs (Node required)."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REVISION = "a" * 40
CASES = (
    '<testcase file="tests/test_a.py" time="0.125" />'
    '<testcase file="tests/test_a.py" time="0.250"><failure /></testcase>'
    '<testcase file="tests/test_b.py" time="0"><skipped /></testcase>'
    '<testcase file="tests/test_b.py" />'
)


def run(*command):
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode == 0, (command, result.stdout, result.stderr)
    return result


def fragment(directory, cases, *, attempt="1", revision=REVISION):
    directory.mkdir()
    report = directory / "junit.xml"
    report.write_text(f"<testsuite>{cases}</testsuite>", encoding="utf-8")
    times = directory / "times.txt"
    outcomes = directory / "outcomes.txt"
    result = run(
        sys.executable,
        str(SCRIPTS / "junit-outcomes.py"),
        str(report),
        "--times",
        str(times),
    )
    outcomes.write_text(result.stdout, encoding="utf-8")
    fragments = directory / "fragments"
    run(
        "node",
        str(SCRIPTS / "ci-proof-summary.mjs"),
        "fragment",
        "--outcomes",
        str(outcomes),
        "--unit",
        "case",
        "--times",
        str(times),
        "--by-file",
        "--entry",
        "tests",
        "--part",
        "1",
        "--of",
        "1",
        "--attempt",
        attempt,
        "--revision",
        revision,
        "--out",
        str(fragments),
    )
    # The producer retains XML beside JSON. It must not become another part.
    shutil.copyfile(report, fragments / "ci-proof-junit.xml")
    return fragments


def summarize(directory, fragments):
    directory.mkdir(exist_ok=True)
    output = directory / "ci-proof-summary.json"
    run(
        "node",
        str(SCRIPTS / "ci-proof-summary.mjs"),
        "summarize",
        "--fragments",
        str(fragments),
        "--expect",
        "tests=1:case",
        "--repository",
        "terryyin/clipboard",
        "--run-id",
        "1",
        "--attempt",
        "1",
        "--revision",
        REVISION,
        "--out",
        str(output),
    )
    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["schemaVersion"] == 2
    assert summary["repository"] == "terryyin/clipboard"
    assert summary["runId"] == summary["runAttempt"] == 1
    assert summary["revision"] == REVISION
    assert [entry["path"] for entry in summary["entries"]] == ["tests"]
    assert output.stat().st_size < 1024 * 1024
    [evidence] = summary["entries"][0]["evidence"]
    assert evidence["unit"] == "case"
    return evidence


def assert_gap(evidence, status):
    assert evidence["parts"] == [{"part": 1, "status": status}]
    assert [evidence[field] for field in ("passed", "failed", "other")] == [0, 0, 0]
    assert "durationMs" not in evidence
    assert "files" not in evidence


def check_pipeline(work):
    mixed_fragments = fragment(work / "mixed", CASES)
    evidence = summarize(work / "mixed", mixed_fragments)
    assert [evidence[field] for field in ("passed", "failed", "other")] == [2, 1, 1]
    assert evidence["durationMs"] == 375
    assert evidence["untimed"] == 1
    assert evidence["parts"] == [
        {
            "part": 1,
            "status": "present",
            "passed": 2,
            "failed": 1,
            "other": 1,
            "durationMs": 375,
            "untimed": 1,
            "breakdown": True,
        }
    ]
    assert evidence["files"] == [
        {
            "path": "tests/test_a.py",
            "passed": 1,
            "failed": 1,
            "other": 0,
            "durationMs": 375,
        },
        {
            "path": "tests/test_b.py",
            "passed": 1,
            "failed": 0,
            "other": 1,
            "durationMs": 0,
            "untimed": 1,
        },
    ]

    untimed_fragments = fragment(
        work / "untimed",
        '<testcase file="tests/test_a.py" />'
        '<testcase file="tests/test_a.py"><error /></testcase>',
    )
    untimed = summarize(work / "untimed", untimed_fragments)
    assert [untimed[field] for field in ("passed", "failed", "other")] == [1, 1, 0]
    assert "durationMs" not in untimed
    assert untimed["untimed"] == 2
    assert untimed["files"] == [
        {
            "path": "tests/test_a.py",
            "passed": 1,
            "failed": 1,
            "other": 0,
            "untimed": 2,
        }
    ]

    assert_gap(summarize(work / "missing", work / "absent-fragments"), "missing")
    for name, identity in (
        ("wrong-attempt", {"attempt": "2"}),
        ("wrong-revision", {"revision": "b" * 40}),
    ):
        fragments = fragment(work / name, CASES, **identity)
        assert_gap(summarize(work / name, fragments), "missing")

    duplicates = work / "duplicate-fragments"
    duplicates.mkdir()
    [original] = mixed_fragments.glob("*.json")
    for name in ("first.json", "second.json"):
        shutil.copyfile(original, duplicates / name)
    assert_gap(summarize(work / "ambiguous", duplicates), "ambiguous")
    print(
        "CI proof pipeline passed: repeated/failing cases, "
        "zero/untimed, identity and gaps"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, help="retain replay reports and summaries here"
    )
    args = parser.parse_args()
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        check_pipeline(args.out)
    else:
        with tempfile.TemporaryDirectory(prefix="clipboard-ci-proof-") as directory:
            check_pipeline(Path(directory))


if __name__ == "__main__":
    main()

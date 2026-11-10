"""Convert pytest's xunit1 cases to outcome and optional seconds/path reports."""

import argparse
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PureWindowsPath


def case_rows(report):
    outcomes, times = [], []
    for case in ET.parse(report).iter("testcase"):
        path = case.get("file")
        if (
            not path
            or PureWindowsPath(path).drive
            or any(character in path for character in "\\\t\r\n")
            or any(part in ("", ".", "..") for part in path.split("/"))
        ):
            raise ValueError(f"testcase {case.get('name')} names no repository file")
        failed = case.find("failure") is not None or case.find("error") is not None
        if failed:
            status = "failed"
        elif case.find("skipped") is not None:
            status = "other"
        else:
            status = "passed"
        outcomes.append(f"{status}\t{path}\n")
        if case.get("time") is not None:
            seconds = float(case.get("time"))
            if seconds < 0 or not math.isfinite(seconds * 1000):
                raise ValueError(f"testcase {case.get('name')} has invalid seconds")
            times.append(f"{seconds}\t{path}\n")
    return "".join(outcomes), "".join(times)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--times", type=Path, help="write measured seconds/path rows here"
    )
    args = parser.parse_args()
    try:
        outcomes, times = case_rows(args.report)
        if args.times is not None:
            args.times.write_text(times, encoding="utf-8")
    except (OSError, ValueError, ET.ParseError) as error:
        sys.exit(str(error))
    sys.stdout.write(outcomes)


if __name__ == "__main__":
    main()

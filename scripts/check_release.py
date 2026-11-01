"""Reject malformed release tags and tags that disagree with package metadata."""

import argparse
import re
from importlib.metadata import version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="Version tag, such as 0.0.5 or v0.0.5")
    args = parser.parse_args()
    package_version = version("clipboard")
    tag_version = args.tag.removeprefix("v")
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", tag_version):
        parser.error("release tags must be X.Y.Z or vX.Y.Z (no prerelease suffix)")
    if tag_version != package_version:
        parser.error(
            f"tag {args.tag!r} does not match clipboard.VERSION ({package_version})"
        )
    print(f"Release tag matches clipboard {package_version}")


if __name__ == "__main__":
    main()

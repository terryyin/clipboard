import sys
import xml.etree.ElementTree as ET

for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.get("file") is None:
        sys.exit(f"testcase {case.get('name')} names no file")
    failed = case.find("failure") is not None or case.find("error") is not None
    if failed:
        status = "failed"
    elif case.find("skipped") is not None:
        status = "other"
    else:
        status = "passed"
    print(f"{status}\t{case.get('file')}")

"""Desktop-free checks of the X11 text probe's environment floors.

The native probe wrapper requires ``environment.xvfb_version``; these fake
``subprocess.run`` so the version lookup is pinned without Xvfb or dpkg.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import linux_x11_native_text_support as support  # noqa: E402

DPKG = ["dpkg-query", "-W", "-f=${Version}", "xvfb"]
XVFB = ["Xvfb", "-version"]


@pytest.fixture
def answers(monkeypatch):
    table = {}

    def run(cmd, **kwargs):
        answer = table.get(tuple(cmd), FileNotFoundError(2, "No such file", cmd[0]))
        if isinstance(answer, BaseException):
            raise answer
        returncode, stdout, stderr = answer
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

    monkeypatch.setattr(support.subprocess, "run", run)
    return table


def test_apt_package_version_is_reported(answers):
    answers[tuple(DPKG)] = (0, "2:21.1.18-1ubuntu1", "")
    answers[tuple(XVFB)] = (0, "", "")

    assert support.xvfb_version() == "xvfb 2:21.1.18-1ubuntu1"


@pytest.mark.parametrize(
    "stderr",
    [
        "\nX.Org X Server 1.21.1.18\nX Protocol Version 11, Revision 0\n",
        "\nXvfb Version 21.1.18\n",
    ],
)
def test_without_dpkg_the_xvfb_banner_on_stderr_is_reported(answers, stderr):
    answers[tuple(DPKG)] = (1, "", "dpkg-query: no packages found matching xvfb\n")
    answers[tuple(XVFB)] = (1, "", stderr)

    assert support.xvfb_version() == stderr.strip().splitlines()[0]


def test_no_xvfb_reports_none(answers):
    assert support.xvfb_version() is None

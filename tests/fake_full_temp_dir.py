"""A full temporary directory: ``tempfile.TemporaryFile`` payload writes fail.

``install_full_temp_dir`` also replaces ``subprocess.Popen`` with a recorder
that fails the test if any helper starts; it returns that launch list.
"""

import subprocess
import tempfile


def install_full_temp_dir(monkeypatch) -> list:
    real_temporary_file = tempfile.TemporaryFile

    class FullTempFile:
        def __init__(self, *args, **kwargs):
            self._file = real_temporary_file(*args, **kwargs)

        def write(self, data):
            raise OSError(28, "No space left on device")

        def __getattr__(self, name):
            return getattr(self._file, name)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self._file.close()

    monkeypatch.setattr(tempfile, "TemporaryFile", FullTempFile)

    launched: list = []

    def popen(*args, **kwargs):
        launched.append(args)
        raise AssertionError("no helper may start when the payload cannot be written")

    monkeypatch.setattr(subprocess, "Popen", popen)
    return launched

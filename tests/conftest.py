"""Shared pytest fixtures for clipboard contract tests."""

import pytest


@pytest.fixture
def restore_image_grabclipboard():
    import clipboard

    yield
    clipboard.set_image_grabclipboard(None)


@pytest.fixture
def restore_html_clipboard_writer():
    import clipboard

    yield
    clipboard.set_html_clipboard_writer(None)


@pytest.fixture
def restore_files_clipboard_reader():
    import clipboard

    yield
    clipboard.set_files_clipboard_reader(None)


@pytest.fixture
def restore_files_clipboard_writer():
    import clipboard

    yield
    clipboard.set_files_clipboard_writer(None)


@pytest.fixture
def restore_clipboard_inspector():
    import clipboard

    yield
    clipboard.set_clipboard_inspector(None)


@pytest.fixture
def restore_image_writeclipboard():
    import clipboard

    yield
    clipboard.set_image_writeclipboard(None)


@pytest.fixture
def restore_html_clipboard_reader():
    import clipboard

    yield
    clipboard.set_html_clipboard_reader(None)


@pytest.fixture
def fake_html_clipboard(restore_html_clipboard_reader):
    """In-memory HTML offer model wired in as the paste_html reader."""
    from html_offer import FakeClipboard

    import clipboard

    board = FakeClipboard()
    clipboard.set_html_clipboard_reader(board.reader)
    return board


@pytest.fixture
def restore_text_clipboard():
    import clipboard

    yield
    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)


@pytest.fixture
def fake_text_clipboard(restore_text_clipboard):
    """In-memory text clipboard wired in through the explicit text seam."""
    import clipboard

    class FakeTextClipboard:
        def __init__(self):
            self.contents = None
            self.writes = []

        def writer(self, text):
            self.writes.append(text)
            self.contents = text

        def reader(self):
            return self.contents

    board = FakeTextClipboard()
    clipboard.set_text_clipboard_writer(board.writer)
    clipboard.set_text_clipboard_reader(board.reader)
    return board


_TEXT_SESSION_VARS = ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE")


@pytest.fixture
def text_session(monkeypatch, tmp_path, restore_text_clipboard):
    """Configure a text desktop session shape on the default backend.

    ``text_session(platform, env, helpers, proc_version, qt)`` patches the
    platform, session variables, ``shutil.which``, the ``/proc/version`` path,
    and Qt discovery so no real clipboard or desktop is touched.
    """
    import shutil
    import sys

    import clipboard
    from clipboard import _desktop_text

    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)

    def configure(
        platform,
        env=None,
        helpers=(),
        proc_version="Linux version 6.8.0-generic (gcc)",
        qt=False,
    ):
        monkeypatch.setattr(sys, "platform", platform)
        for name in _TEXT_SESSION_VARS:
            monkeypatch.delenv(name, raising=False)
        for name, value in (env or {}).items():
            monkeypatch.setenv(name, value)
        found = set(helpers)
        monkeypatch.setattr(
            shutil,
            "which",
            lambda name, *a, **k: f"/usr/bin/{name}" if name in found else None,
        )
        proc = tmp_path / "proc_version"
        if proc_version is not None:
            proc.write_text(proc_version)
        monkeypatch.setattr(_desktop_text, "_PROC_VERSION_PATH", str(proc))
        monkeypatch.setattr(_desktop_text, "_qt_binding_installed", lambda: qt)

    return configure

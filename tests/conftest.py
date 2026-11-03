"""Shared pytest fixtures for clipboard contract tests."""

import sys

import pytest

# Captured once at import so the guard compares against the real host.
_HOST_PLATFORM = sys.platform


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    """Fail a test whose call phase leaves ``sys.platform`` changed.

    The standard library also reads the shared ``sys.platform``, so faking it
    globally can change stdlib behavior on some hosts. Fake the product's
    platform through the ``fake_platform`` fixture instead.
    """
    try:
        result = yield
    finally:
        observed = sys.platform
        sys.platform = _HOST_PLATFORM
    if observed != _HOST_PLATFORM:
        pytest.fail(
            f"test left sys.platform={observed!r} (host {_HOST_PLATFORM!r}); "
            "fake the product platform with the fake_platform fixture",
            pytrace=False,
        )
    return result


@pytest.fixture
def fake_platform(monkeypatch):
    """Return a setter that fakes the platform the package reads.

    ``fake_platform("win32")`` patches the private ``clipboard._platform``
    seam only; the shared ``sys.platform`` (and stdlib behavior) stays the
    host's.
    """
    from clipboard import _platform

    def configure(platform):
        monkeypatch.setattr(_platform, "current", lambda: platform)

    return configure


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
def restore_clipboard_clearer():
    import clipboard

    yield
    clipboard.set_clipboard_clearer(None)


@pytest.fixture
def linux_clear_session(monkeypatch, restore_clipboard_clearer, fake_platform):
    """Default clearer on a pretend Linux with the given session variables.

    ``linux_clear_session(display=, wayland=, session_type=, **wl_copy)``
    returns the ``FakeWlCopyClear`` answering ``wl-copy --clear``; set its
    ``x11_child`` to let the session reach the libX11 clear child.
    """
    from fake_clear_helpers import FakeWlCopyClear

    import clipboard
    from clipboard import _clear_wayland

    fake_platform("linux")
    clipboard.set_clipboard_clearer(None)

    def install(*, display=None, wayland=None, session_type=None, **kwargs):
        for name, value in (
            ("DISPLAY", display),
            ("WAYLAND_DISPLAY", wayland),
            ("XDG_SESSION_TYPE", session_type),
        ):
            if value is None:
                monkeypatch.delenv(name, raising=False)
            else:
                monkeypatch.setenv(name, value)
        helper = FakeWlCopyClear(**kwargs)
        monkeypatch.setattr(_clear_wayland.subprocess, "run", helper)
        return helper

    return install


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
def text_session(monkeypatch, tmp_path, restore_text_clipboard, fake_platform):
    """Configure a text desktop session shape on the default backend.

    ``text_session(platform, env, helpers, proc_version, qt)`` patches the
    platform, session variables, ``shutil.which``, the ``/proc/version`` path,
    and Qt discovery so no real clipboard or desktop is touched.
    """
    import shutil

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
        fake_platform(platform)
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

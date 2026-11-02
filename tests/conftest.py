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

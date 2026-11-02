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

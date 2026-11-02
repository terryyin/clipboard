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

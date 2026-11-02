"""Fake pyperclip mechanism for text session dispatch tests."""

import pyperclip


class FakePyperclip:
    def __init__(self, monkeypatch, *, available=False):
        self.contents = None
        self.writes = []
        self.reads = 0
        self.copy_error = None
        self.paste_error = None
        monkeypatch.setattr(pyperclip, "is_available", lambda: available)
        monkeypatch.setattr(pyperclip, "copy", self.copy)
        monkeypatch.setattr(pyperclip, "paste", self.paste)

    def copy(self, text):
        if self.copy_error is not None:
            raise self.copy_error
        self.writes.append(text)
        self.contents = text

    def paste(self):
        self.reads += 1
        if self.paste_error is not None:
            raise self.paste_error
        return self.contents

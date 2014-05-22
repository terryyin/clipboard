clipboard
=========

A cross platform clipboard operation library of Python. Works for Windows, Mac and Linux.

Well, as I was trying to implement this, I realize that everything is included in pyperclip already: https://pypi.python.org/pypi/pyperclip/

But anyway, `clipboard` is a better name. You are free to choose:-) I might add more features to it.

Usage:

::

   import clipboard
   clipboard.copy("abc")  # now the clipboard content will be string "abc"
   text = clipboard.paste()  # text will have the content of clipboard

clipboard
=========

A cross platform clipboard library for Python (Windows, macOS, Linux). Text
``copy`` / ``paste`` follow this package's own contract: it owns the macOS
and Linux helper paths, uses pyperclip's Windows backend, and delegates other
environments to pyperclip; richer APIs sit beside them.

Install::

   python -m pip install clipboard

Full Usage, Installation, Evidence, and Development notes live under
``docs/`` (this short landing is also the PyPI long description):

* `Text and Linux PRIMARY <https://github.com/terryyin/clipboard/blob/master/docs/usage-text.rst>`_
* `Images, HTML, inspect, paste_html <https://github.com/terryyin/clipboard/blob/master/docs/usage-rich.rst>`_
* `File lists, clear, and waits <https://github.com/terryyin/clipboard/blob/master/docs/usage-files-wait.rst>`_
* `Installation <https://github.com/terryyin/clipboard/blob/master/docs/installation.rst>`_
* `Evidence (text, PRIMARY, clear) <https://github.com/terryyin/clipboard/blob/master/docs/evidence-text-primary-clear.rst>`_
* `Evidence (waits, HTML, files) <https://github.com/terryyin/clipboard/blob/master/docs/evidence-wait-html-files.rst>`_
* `Development and Publishing <https://github.com/terryyin/clipboard/blob/master/docs/development.rst>`_

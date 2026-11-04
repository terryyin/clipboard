Development
-----------

Nix flakes (`Nix <https://nixos.org/download/>`_), like Lizard: ``flake.lock``
pins Python 3.13, uv, Make, actionlint (and, on Linux, libX11 for the
package check); ``uv.lock`` pins deps.

::

   nix develop
   make deps check lint-workflows build test-package

Or ``nix develop -c make check``. Without Nix: Python 3.13 + uv + same Make
targets. Windows: ``uv sync --locked``, ``uv run --locked --extra images
pytest``, ``uv run --locked ruff check .``. Do not install into system Python.
GHA covers Nix plus Python 3.10–3.14, installs wheel/sdist outside the tree,
and uses an in-memory clipboard (no desktop). ``make test-package`` also runs
each installed distribution's X11 clear helper with an unusable ``DISPLAY``
and requires its structured failure (``display`` in the Linux Nix shell,
``libx11`` where libX11 is absent). X11/Wayland image-write probes
and the X11, Wayland, and Windows ``paste_html``, ``copy_files``, and text
probes are separate gated jobs.

Publishing
----------

A matching version tag runs checks and publishes via PyPI Trusted Publishing,
then a GitHub release. Configure the ``pypi`` environment and trusted
publisher first. See
`the release guide <https://github.com/terryyin/clipboard/blob/master/docs/releasing.md>`_.

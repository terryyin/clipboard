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

CI proof in Intent
------------------

The judged ``ci.yml`` publishes one ``ci-proof-summary-attempt-<n>`` artifact
for the desktop-free pytest suite. Only the Ubuntu Python 3.13 matrix leg
reports; other matrix legs and release calls do not repeat that proof. Outcome
counts are explicit test cases (``--unit case`` / ``--expect tests=1:case``),
not legacy results or measured test-file outcomes. A file breakdown lists
repository-relative paths with that file's case counts; the path count is not
a test-file result.

``scripts/junit-outcomes.py`` converts xunit1 cases to outcome/path rows and
optional ``--times`` seconds/path rows. The copied ``scripts/ci-proof-*.mjs``
collector sums recorded case durations in milliseconds, including failed cases
and pytest's reported phases, and ``--by-file`` retains repository-relative
per-file case counts. This is summed test execution time, not job wall time.
Recorded zero is measured; a missing duration stays untimed, and a partial sum
is incomplete. Missing, malformed or ambiguous evidence stays a proof gap
rather than a complete zero-time result. Attempt and revision matching keep
that proof with its selected run.

The representative ``ci-proof-fragments-tests-1-attempt-<n>`` artifact retains
``ci-proof-junit.xml`` beside its fragment for one day, so its case sums can be
compared with Intent's ``tests`` and file views. The summary artifact contains
only ``ci-proof-summary.json`` and is retained for 30 days.

Converter regression tests are part of ordinary pytest. The real CLI pipeline
replay requires Node 20.12 or later and runs in the representative producer after
its pinned Node setup. Run it locally with::

   nix develop -c uv run --locked python scripts/check_ci_proof_pipeline.py

Publishing
----------

A matching version tag runs checks and publishes via PyPI Trusted Publishing,
then a GitHub release. Configure the ``pypi`` environment and trusted
publisher first. See
`the release guide <https://github.com/terryyin/clipboard/blob/master/docs/releasing.md>`_.

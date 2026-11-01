# Releasing Clipboard

A version tag runs checks, builds a wheel and source distribution, publishes
those artifacts to PyPI, then creates a GitHub release with the same files.
Both `X.Y.Z` and `vX.Y.Z` tags are accepted. The tag must match
`clipboard.VERSION` exactly after removing an optional `v`.

## One-time maintainer setup

These account settings require a repository administrator and a PyPI project
owner. The workflow uses OIDC Trusted Publishing and needs no PyPI API token.

1. Open [the GitHub environments settings](https://github.com/terryyin/clipboard/settings/environments)
   and create an environment named **pypi**. Add yourself as a required reviewer
   if you want to approve each publication. Restrict deployment to version tags
   using tag patterns `*.*.*` and `v*.*.*`. Without a reviewer rule, a matching
   tag can publish automatically after checks pass. GitHub's availability of
   protection rules depends on repository visibility and plan.
2. Sign in to PyPI as an owner of `clipboard` and
   [add a GitHub Trusted Publisher](https://pypi.org/manage/project/clipboard/settings/publishing/?provider=github&owner=terryyin&repository=clipboard&workflow_filename=release.yml).
   Enter these exact values:

   | Field | Value |
   | --- | --- |
   | PyPI project | `clipboard` |
   | GitHub owner | `terryyin` |
   | Repository | `clipboard` |
   | Workflow filename | `release.yml` |
   | Environment | `pypi` |

3. Merge the workflow and lockfiles into `master`. In repository branch rules,
   require **CI passed**, the stable check that requires lint, packaging, and
   every Python matrix job to succeed. Enable Dependabot version updates if
   repository policy requires it.

See [PyPI's publisher setup instructions](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
The environment name must agree between PyPI and the workflow.

## Prepare a release

1. Choose an unused version newer than the latest version on
   [PyPI](https://pypi.org/project/clipboard/#history). As of November 1, 2026,
   PyPI has `0.0.4`, but this checkout declares `0.0.2`. Resolve that discrepancy
   deliberately; do not tag the checkout's existing version. `0.0.5` is an
   example next version, not an already approved release.
2. Update only `VERSION` in `clipboard.py`. Refresh the project entry in the
   lockfile with `nix develop -c uv lock` and commit both changes.
3. Run `nix develop -c make check lint-workflows build`, review the changes, and
   merge them into `master`. Wait for the cross-platform CI checks to pass.
   `nix develop -c make test-package` also tests installation of both distributions.
4. On a clean, up-to-date `master`, create and push the chosen tag. For example,
   **only after setting `VERSION = "0.0.5"` and completing the checks**:

   ```sh
   git tag -a v0.0.5 -m "Release 0.0.5"
   git push origin v0.0.5
   ```

5. Open [Actions → Release](https://github.com/terryyin/clipboard/actions/workflows/release.yml).
   If required reviewers are configured, approve the **pypi** deployment after
   reviewing the tagged source and the `distributions-<attempt>` artifact.
6. Confirm the new version on PyPI and the GitHub release with its attached
   wheel and source archive.

The release calls the same CI workflow on the tagged commit, including the
Python/OS matrix, lint, metadata validation, and package installation checks.
Publication waits for all checks and downloads the build artifact by its
immutable ID. Only the publication job receives an OIDC token; only the GitHub
release job receives repository write permission.

## If a release fails

- If validation or build fails, no publication occurs. Fix and check the source
  before choosing a new release tag; do not move an existing release tag.
- If publishing fails before any upload, correct the publisher or environment
  settings and rerun failed jobs. The workflow downloads the original build
  artifact, so it publishes the reviewed files.
- If some or all files already reached PyPI, inspect that release first. PyPI
  does not allow replacing an uploaded filename. Do not blindly rerun the
  publisher or add `skip-existing`; finish a partial upload using the saved
  artifacts and maintainer judgment, or prepare a new version.
- If only the GitHub release job fails, rerun that failed job. If a release was
  partly created, inspect it and attach missing artifacts with `gh release upload`.

## Updating dependencies

- `nix develop -c uv lock --upgrade` updates Python dependencies within the
  ranges in `pyproject.toml`; commit `uv.lock` and run the checks.
- `nix flake update` updates the pinned development tools; commit `flake.lock`
  and run the checks. If uv's Nix version changes, update the version pinned in
  `.github/workflows/ci.yml` to match it.
- Dependabot opens weekly updates for Nix inputs, Python dependencies, and Actions.
  Actions are pinned to commit SHAs with readable version comments.

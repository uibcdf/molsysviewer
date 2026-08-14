# Releasing and publishing

Use this page when you cut a release or publish the JS runtime.

## Citation and source preservation

A release is not complete when its packages are uploaded. Before tagging, run
`python devtools/prepare_release.py X.Y.Z` and the citation step in the release
gate. After publishing the GitHub Release, Zenodo must archive the tagged source
and `python devtools/verify_zenodo_release.py X.Y.Z` must pass. A pushed tag alone
does not trigger Zenodo.

See {doc}`release_and_citation` for the contributor procedure and
[`devguide/release_and_citation.md`](https://github.com/uibcdf/molsysviewer/blob/main/devguide/release_and_citation.md)
for the normative metadata and recovery contract.

## Versioning

- The Python version is produced by `versioningit` from Git tags.
- The JS package version is synchronized from Python during `npm run build`
  using `molsysviewer/js/scripts/sync-python-version.mjs`.
- Development runtime rebuilds should use `npm run build:runtime`; that command
  does not synchronize version metadata.

Compatibility rule

- The Python package version and the npm runtime version must match.
- Docs-lite HTML exports should be served with the matching runtime version.
  If you mismatch versions, message ops or option schemas can drift and break embeds.

See also

- {doc}`protocol_and_payloads`

## JS runtime (npm)

Package: `@uibcdf/molsysviewer` published from `molsysviewer/js/`.

Flow
1. Ensure `molsysviewer/js/package.json` version matches the intended tag.
2. Create and push a tag `X.Y.Z` (or `X.Y.Z-rc.N`).
3. Pushing the tag runs `.github/workflows/npm-publish.yaml`, which publishes
   using Trusted Publisher (OIDC).

**Conda is different, on purpose.** It publishes from a GitHub *Release*, not
from a tag. A tag is a checkpoint and there are many; a conda package is
something people install, and the cadence is a decision. So a version can be on
npm and not on conda, and that is not a defect.

**A tag is what publishes to npm, and that is deliberate.** It used to trigger
only on `release: published`. From `0.8.0` this project tagged without creating
GitHub Releases, so the trigger stopped firing and npm sat at `0.7.0` while
Python reached `0.20.0` — **thirteen versions**, discovered on 2026-08-05 and
republished by hand. The runtime is not a package anybody installs on purpose: it
is what an exported view fetches, so it has to exist for every version that can
export. That is why its trigger is the thing that always happens.

**Do not dispatch an old tag to fill a gap without thinking.** The workflow runs
`npm publish` with no `--tag`, so it sets `latest`. Publishing `0.12.0` today
would move `latest` backwards from the current release, and nothing on our side
would say so. Versions `0.8.0` through `0.19.0` are missing from npm and are
staying missing by decision; if that is ever revisited, the publish needs an
explicit dist-tag first.

**Check it, do not assume it.** After tagging:

```bash
gh run list --workflow=npm-publish.yaml --limit 1
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@X.Y.Z/dist/viewer.js"
```

A `404` there means every `view.export.html(..., shared_runtime="cdn")` written
by a user of that version points at nothing. That is a public API path failing on
somebody else's website, months later, with nothing on our side to notice.

How the version is chosen

- `npm run build` syncs the JS version from the Python version.
- `npm run build:runtime` only rebuilds the runtime artifact and must be used
  for ordinary TypeScript development when version metadata should remain
  untouched.
- A release tag `X.Y.Z` defines the version for both artifacts.
- The docs-lite export should point to the same `X.Y.Z` runtime URL.

## Python packages (pip/conda)

- The Python wheel includes `molsysviewer/viewer.js` and `.map` as package data.
- Conda build uses `devtools/conda-build/build.sh`, which builds the JS bundle
  and then installs the Python package.

GitHub workflow
- `.github/workflows/build_and_upload_conda_packages.yaml`

Key points
- Do not edit `viewer.js` or `.map` by hand.
- Keep the JS build manual and controlled.
- Avoid committing `pythonVersion` changes produced from a dirty local
  `versioningit` value.

## Pre-releases

If you publish a pre-release (`X.Y.Z-rc.N`), publish both:

- the Python package (pip/conda) and
- the npm runtime (`@uibcdf/molsysviewer@X.Y.Z-rc.N`)

Then ensure docs-lite exports point at the same pre-release runtime URL.

## Current Pre-`0.16.0` Practical Gate

Before cutting the next strong pre-`1.0` checkpoint, verify:

- the recommended smoke subset in `devguide/smoke_test.md` is green
- the current mature product stories are still easy to find from docs:
  - panel/workspace runtime
  - add-on reference runtime
  - figure export from the workbench
- the public notebook-facing APIs still match those stories
- no new structural host/runtime gap appeared during the last tightening pass

# Releasing and publishing

Use this page when you cut a release or publish the JS runtime.

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
3. GitHub Actions runs `.github/workflows/npm-publish.yaml` and publishes
   using Trusted Publisher (OIDC).

Docs-lite exports load the runtime from jsDelivr:

```
https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@X.Y.Z/dist/viewer.js
```

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

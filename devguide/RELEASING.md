# MolSysViewer — Releasing & NPM Publishing

This guide covers publishing the JS runtime bundle to npm so docs-light
exports can load it from a CDN.

## Runtime package
- Package name: `@uibcdf/molsysviewer` (published from `molsysviewer/js`).
- Build output:
  - `molsysviewer/js/dist/viewer.js` + `viewer.js.map` (npm package).
  - `molsysviewer/viewer.js` + `.map` (Python package).

## Publishing flow (Trusted Publisher)
Releases are published via GitHub Actions:
`.github/workflows/npm-publish.yml`.

Steps:
1. Ensure `molsysviewer/js/package.json` version matches the intended tag.
2. Create and push a tag `x.y.z` (or `x.y.z-rc.1`).
3. The workflow builds and publishes to npm automatically using OIDC.

## Conda packages
The conda build workflow reads `RELEASE_VERSION` from the release tag and
injects it into `devtools/conda-build/meta.yaml` when building:
`.github/workflows/build_and_upload_conda_packages.yaml`.

## CDN URL
Docs-light exports use jsDelivr:

```
https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@x.y.z/dist/viewer.js
```

This is only a fallback; local docs builds still use
`docs/_static/molsysviewer-runtime.js` when available.

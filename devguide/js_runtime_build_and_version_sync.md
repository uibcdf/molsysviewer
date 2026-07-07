# JS runtime build and version sync

This note records the repository policy for rebuilding the TypeScript runtime
without introducing accidental package-version churn.

## Development rebuild

Use this command when TypeScript changes need a refreshed runtime artifact:

```bash
cd molsysviewer/js
npm run build:runtime
```

`build:runtime` runs the bundler only. It regenerates:

- `molsysviewer/viewer.js`
- `molsysviewer/viewer.js.map`

It does not rewrite `molsysviewer/js/package.json`.

## Release and packaging build

Use this command only when the JS package metadata must be synchronized with
the Python package version:

```bash
cd molsysviewer/js
npm run build
```

`npm run build` first executes `sync-python-version.mjs`, then runs
`build:runtime`. The sync step reads `molsysviewer/_version.py`, whose contents
come from `versioningit`.

In a dirty working tree, `versioningit` can produce a local version such as:

```text
X.Y.Z+N.gSHA.dirty
```

If `npm run build` is run in that state, `molsysviewer/js/package.json` may be
rewritten with that value in `pythonVersion`. That local metadata should not be
committed as part of ordinary development work.

## Practical rule

- During implementation and validation: use `npm run build:runtime`.
- During release, conda packaging, or npm publication: use `npm run build`.
- If only `pythonVersion` changed because a release build was run from a dirty
  tree, restore it before committing unrelated work.

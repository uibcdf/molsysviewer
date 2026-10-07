# CI and automation

This page describes how CI is organized and what you should run locally before opening a PR.

## CI entry points

CI lives under `.github/workflows/`.
The most common workflows cover:

- Python tests (`pytest`).
- Building and publishing conda packages.
- Publishing the JS runtime package to npm (Trusted Publisher).

## What you run locally

Before opening a PR, you run the checks that match what you changed:

- Python changes: `pytest`.
- JS changes: `cd molsysviewer/js && npm run test:js`.
- Docs changes: `make -C docs html`.

## Placeholder

Add the concrete workflow names and required environment variables here once the CI matrix is stable.

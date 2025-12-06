# Unit Tests Overview

This document summarizes the JS/TS and Python unit test layout and how to run them.

## JS/TS Unit Tests

- Location: `molsysviewer/js/tests/unit`.
- Runner: Node + esbuild bundle.
- Commands:
  - `npm run test:js` — build and run the bundled unit tests.
  - `npm run coverage:js` — same as above but with c8 coverage; outputs `coverage-js/lcov.info`.
- Purpose: exercise small pieces of the JS/TS controller/helpers without a browser.

## Python Unit Tests

- Location: `tests/` at the repo root.
- Runner: pytest.
- Typical invocation (see CI): `pytest -v --cov-config=.coveragerc --cov=molsysviewer --cov-report=xml`.
- Many tests stub `widget.send` to avoid frontend traffic; use the real demo viewers (`molsysviewer.demo`) instead of mocks wherever possible.

## Notes

- JS/TS unit and E2E tests are separated: unit tests do not need a browser, E2E does (see `TESTS_E2E.md`).
- Coverage: Python uploads to Codecov; JS coverage is produced via c8 (not currently uploaded in E2E). Ensure you run `npm ci` before `npm run test:js` to install devDependencies.


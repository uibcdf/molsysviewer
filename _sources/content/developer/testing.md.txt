# Testing & QA

- Favor lightweight unit tests on Python APIs (shape options, loaders).
- JS/TS: prefer logic tests for option normalization and message routing (no build required).
- Keep `npm run build` manual; do not auto-regenerate `viewer.js` in tests.
- Use tags in tests to add/clear shapes deterministically.
- For docs demos, prefer pre-rendered HTML via `view.export.html(..., shared_runtime=...)` instead of executing widgets during tests/build.
- When adding new shape options, cover normalization (length checks, defaults) and error cases.
- If touching message handlers, assert that tags and shape refs are registered/cleared as expected.
- JS/TS tests: focus on pure functions (option mapping, data prep). Avoid depending on Mol* runtime unless absolutely necessary.
- Python tests: validate option normalization, type casting, and message payload shapes.
- Manual checks: when changing TS, do a manual pass in a notebook if you rebuild locally; otherwise rely on unit-level coverage.

Python tests
- Location: `tests/`
- Runner: `pytest`

JS/TS unit tests
- Location: `molsysviewer/js/tests/unit`
- Commands: `npm run test:js`, `npm run coverage:js`

E2E tests (Playwright)
- Location: `molsysviewer/js/tests/e2e`
- Command: `npm run test:e2e`
- The default command runs every E2E suite sequentially through one shared Chromium process.
- Requires a local Chrome/Chromium with WebGL; you can set `PW_CHROMIUM_BIN=/path/to/chrome`.
- Browser launch and WebGL2 failures fail the run. `E2E_ALLOW_SKIP=1` is an explicit opt-out for environments where E2E validation is intentionally unavailable.
- E2E tests are currently run manually, not in CI.

# Testing & QA

- Favor lightweight unit tests on Python APIs (shape options, loaders).
- JS/TS: prefer logic tests for option normalization and message routing (no build required).
- Keep `npm run build` manual; do not auto-regenerate `viewer.js` in tests.
- Use tags in tests to add/clear shapes deterministically.
- For docs demos, prefer pre-rendered HTML via `write_html` instead of executing widgets during tests/build.
- When adding new shape options, cover normalization (length checks, defaults) and error cases.
- If touching message handlers, assert that tags and shape refs are registered/cleared as expected.
- JS/TS tests: focus on pure functions (option mapping, data prep). Avoid depending on Mol* runtime unless absolutely necessary.
- Python tests: validate option normalization, type casting, and message payload shapes.
- Manual checks: when changing TS, do a manual pass in a notebook if you rebuild locally; otherwise rely on unit-level coverage.

```{toctree}
:hidden:
:maxdepth: 1
```

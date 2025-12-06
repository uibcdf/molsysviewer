# E2E Tests (MolSysViewer)

This document summarizes how to run and what to expect from the end-to-end (E2E) test that exercises the viewer in a headless browser.

## Structure

- `molsysviewer/js/tests/unit`: JS/TS unit tests (run with `npm run test:js`, coverage with `npm run coverage:js`).
- `molsysviewer/js/tests/e2e`: Playwright test that loads a structure, creates a region, and hides it. It drives Mol* in a headless browser.

## Dependencies (E2E)

- Playwright as the driver (`npm install` in `molsysviewer/js`).
- Browser: currently we rely on a **local Chrome/Chromium**. Provide its path via `PW_CHROMIUM_BIN=/path/to/chrome` when running the test (e.g., `PW_CHROMIUM_BIN=/usr/bin/google-chrome npm run test:e2e`).
- WebGL must be available in that browser. We do not use xvfb/mesa for this flow; assume a local browser capable of WebGL.

## How to run

From `molsysviewer/js`:

```bash
PW_CHROMIUM_BIN=/usr/bin/google-chrome npm run test:e2e
```

The test builds the harness and E2E bundle, launches the browser, then:
1. Sends `load_structure_from_string` with a minimal PDB.
2. Creates a region with all atoms.
3. Runs `hide_region`.

Expected outcomes:
- `[E2E] passed` if no console errors and WebGL is available.
- If the browser cannot launch due to crashpad/sandbox or WebGL is unavailable, the test prints a warning and exits (skip) to avoid blocking.

## Notes

- E2E is currently run **manually** with a local Chrome/Chromium that supports WebGL; it is not wired into CI.
- Playwright is still needed as the driver even when using your own Chrome/Chromium.
- If we reintroduce fallback to Playwright’s Chromium in the future, we must ensure the environment allows headless launch and WebGL.
- Full Jupyter/kernel UI testing is **not automated**: for now, UI verification in notebook/Lab remains manual. The E2E harness checks logic via Playwright but does not launch Jupyter. A future Playwright+Jupyter flow would be heavier and more fragile; if needed, revisit with a dedicated setup.

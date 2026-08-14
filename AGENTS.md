# Guidelines for AI Agents

This document provides critical instructions for all AI assistants or automation tools contributing to this repository.

## 🚫 Do *Not* Modify Generated Files

The following files **must not be edited manually**:

* `molsysviewer/viewer.js`
* `molsysviewer/viewer.js.map`

These files are **build artifacts** generated automatically from the TypeScript sources located in the `js/` directory. Any manual edits will be overwritten and may corrupt the build process.

## 🚫 Do *Not* Read Generated Files

The following files **must not be readed** to avoid oversized context and irrelevant diffs:

* `molsysviewer/viewer.js`
* `molsysviewer/viewer.js.map`
* `docs/_static/views/*.html`

These files are **build artifacts** generated automatically from the TypeScript sources located in the `js/` directory. Any manual edits will be overwritten and may corrupt the build process.
The content of these files is not relevant for understanding or modifying the viewer's logic.
Their content is redundant with the TypeScript source files. Read only the TypeScript source files.
The HTML files under `docs/_static/views/` are auxiliary exports for documentation embeds and do not add
developer-relevant context beyond the docs sources.

## ✔️ Source of Truth

The authoritative JavaScript/TypeScript sources live here:

```
js/src/
    index.ts
    managers/
    shapes/
    plugin/
    messages/
```

**Only these files should be edited** when modifying frontend logic. After changes, the build system must be executed to regenerate `viewer.js` and `viewer.js.map`.

## 🛠️ Build Process (summary)

1. Edit TypeScript files inside `js/src/`.
2. For development rebuilds, run `npm run build:runtime` from
   `molsysviewer/js/`. This regenerates the runtime bundle without rewriting
   JS package version metadata.
3. Use `npm run build` only for release/packaging flows where syncing the JS
   package version from Python is intentional. It runs
   `sync-python-version.mjs` first and may rewrite
   `molsysviewer/js/package.json`, including `pythonVersion`.
4. The bundler (esbuild) produces updated versions of:

   * `molsysviewer/viewer.js`
   * `molsysviewer/viewer.js.map`

AI agents must never write directly to these generated outputs.
If `npm run build` is used accidentally in a dirty working tree and only
`pythonVersion` changes to a local version such as `X.Y.Z+...dirty`, do not
commit that metadata churn; use `npm run build:runtime` for normal TS
validation work instead.

## 🤖 General Development Rules for AI Agents

1. Always prefer editing TypeScript source files over build artifacts.
2. Do not create duplicate build outputs.
3. Preserve the structure of the `molsysviewer/` package.
4. Maintain consistency with the project's developer documentation under `docs/content/developer/`.
5. Docs: follow `docs/content/developer/documentation/web/build_and_layout.md`; use static views in `_static/views/` for embeds.
6. When in doubt, **ask before modifying files outside `js/src/`**.
7. MolSys payload schema (Python → TS): top-level `structures` list, each with `coordinates` (Å), optional `box` as three vectors (Å), and `time`. Do not reintroduce legacy names like `positions` or `frames`.
8. Tests should avoid mocks: use the real demo viewers in `molsysviewer.demo` (`dialanine`, `pentalanine`, `tctim`, `chicken_villin_HP35`) to build regression/unit tests.
9. If a specific local setup shows a MolSysMT/Numba cache failure, document the exact traceback before adding an environment workaround. Do not assume `NUMBA_CACHE_DIR` overrides are required by default.
10. JS/TS tests:
    - Unit tests in `molsysviewer/js/tests/unit` (run with `npm run test:js`, coverage with `npm run coverage:js`).
    - E2E in `molsysviewer/js/tests/e2e` (headless Playwright against real Mol*). `npm run test:e2e` runs all suites through one shared Chromium process. You can force a local Chrome/Chromium with `PW_CHROMIUM_BIN=/path/to/chrome npm run test:e2e`. Browser launch or WebGL2 failure is an error by default; only an explicit `E2E_ALLOW_SKIP=1` opts out. These are run manually (not in CI) in an environment with a browser and WebGL; do not use xvfb/mesa for E2E.
11. The `sandbox/` directory is a scratch area for developer experiments. Changes there may be committed without review, and should not drive architectural decisions or test expectations.
12. **Test-run discipline**: Run tests only when the implementation is believed to be correct — not speculatively. Before re-running after a failure, read the full traceback, form a diagnosis, and fix the root cause. One run per fix attempt: no blind iteration. Sequence: (a) run the specific test file first (`pytest tests/test_foo.py -x -q`); (b) after it's green, run the full suite once (`pytest tests/ --tb=no -q`) to check for regressions. Never run the full suite more than once per implementation task.
13. For TypeScript runtime validation during development, prefer
    `npm run build:runtime` over `npm run build`. The latter is a
    release/packaging command because it synchronizes package versions from the
    Python `versioningit` output.
14. **Agent-oriented Python test output**: for the `pytest` runs in rule 12, an
    agent may render output compactly with `pytest-receptor` —
    `pytest --receptor=llm tests/test_foo.py -x` and `pytest --receptor=llm tests/`.
    It changes nothing about pass/fail; **normal `pytest` remains the
    authority**. Do **not** pair it with `--tb=no`/`--tb=line` (they delete the
    location evidence the compact report needs), so drop `--tb=no` from the
    rule-12 full-suite check when using it. It is pre-1.0 and under evaluation:
    report any disagreement with pytest, any failure its compact output was not
    enough to diagnose, or any wrong grouping, in the `pytest-receptor`
    repository under `devguide/pending_bugs/` (or `pending_proposals/`). See
    [`devguide/pytest_receptor.md`](devguide/pytest_receptor.md).

## Filing a defect or a proposal

**`devguide/reporting_protocol.md` is normative.** Read it before writing anything into
`devguide/pending_bugs/` or `devguide/pending_proposals/`.

The short version:

- If it deserves a document in one of those two directories, it deserves a GitHub issue.
  **Open the issue first**, to obtain the number.
- Start the document from `devguide/templates/report.md`. Every queue entry carries front
  matter: `summary`, `issue`, `status`, `opened`, `verification`, `area`, and `severity`
  for a bug.
- The document holds the analysis and changes continuously. The issue holds state and is
  written at exactly two moments: open and close.
- Closing needs a **`guard`** — the test that fails if the defect returns — or, for a
  proposal whose outcome is a rule, the **`normative`** document that absorbed it. Then the
  document moves to `devguide/archive/`.
- **Archive, never delete.** An archived document is immutable evidence: a claim that turns
  out to be false gets an appended, dated correction, not an edit.
- Cross-repository references are `uibcdf/<repo>#<number>`, never a path into another
  repository's `devguide/`.
- Plans and inventories are **not** queue entries. They live elsewhere in `devguide/`.

`tests/test_reporting_protocol.py` enforces what can be checked offline.

## Developer documentation (where to look first)

Use `docs/content/developer/index.md` as the entrypoint.

Common topics

- Setup: `docs/content/developer/dev_setup.md`
- Repo map: `docs/content/developer/repo_structure.md`
- JS/TS workflow: `docs/content/developer/js_workflow.md`
- Python ↔ TS contracts: `docs/content/developer/protocol_and_payloads.md`
- Public API and stability: `docs/content/developer/public_api.md`
- Regions/layers semantics: `docs/content/developer/regions_layers.md`
- Debugging: `docs/content/developer/debugging.md`
- Docs workflow + RTD parity: `docs/content/developer/docs_workflow.md`
- Releasing/version sync: `docs/content/developer/releasing.md`
- Configuration surface (planned/stub): `docs/content/developer/configuration.md`
- Demo systems for tests/docs: `docs/content/developer/demo_systems.md`

## 📌 Why This Matters

Editing generated files breaks:

* reproducibility,
* version control clarity,
* build determinism,
* debugging and maintenance workflows.

Follow these rules to ensure the viewer remains stable and maintainable.

## Mol* Source Context

When working on MolSysViewer, you MUST assume that the full Mol* (molstar) source tree is available locally under: `src_molstar`
This means:

- You should NOT treat Mol* as a black box.
- You may reason about internal Mol* APIs, viewer behaviors, render pipelines, geometry builders, representation logic,
  and state updates by referencing the local source code.
- When planning, debugging, or proposing refactors in JavaScript/TypeScript, refer to the Mol* source when clarity or
  correctness depends on understanding internal implementations.
- This context applies ONLY to work inside the MolSysViewer repository.

## External Tooling Guides (Required for Development)

These guides are required reading for anyone developing this library. They describe how external tools must be used here.

- `SMONITOR_GUIDE.md` — Required guide for SMonitor integration and diagnostics.

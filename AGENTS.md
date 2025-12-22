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
2. Run the build (`npm run build` or the project-specific command).
3. The bundler (esbuild) produces updated versions of:

   * `molsysviewer/viewer.js`
   * `molsysviewer/viewer.js.map`

AI agents must never write directly to these generated outputs.

## 🤖 General Development Rules for AI Agents

1. Always prefer editing TypeScript source files over build artifacts.
2. Do not create duplicate build outputs.
3. Preserve the structure of the `molsysviewer/` package.
4. Maintain consistency with the project's devguide (`devguide/`).
5. Docs: follow `docs/Provisional_Docs_Guidelines.md`; use static views in `_static/views/` for embeds.
6. When in doubt, **ask before modifying files outside `js/src/`**.
7. MolSys payload schema (Python → TS): top-level `structures` list, each with `coordinates` (Å), optional `box` as three vectors (Å), and `time`. Do not reintroduce legacy names like `positions` or `frames`.
8. Tests should avoid mocks: use the real demo viewers in `molsysviewer.demo` (`dialanine`, `pentalanine`, `tctim`, `chicken_villin_HP35`) to build regression/unit tests.
9. When importing/running molsysviewer (and molsysmt), set `NUMBA_CACHE_DIR=/tmp/numba_cache` in your session to avoid numba cache errors when molsysmt is used from a local checkout.
10. JS/TS tests:
    - Unitarios en `molsysviewer/js/tests/unit` (ejecutar con `npm run test:js`, cobertura con `npm run coverage:js`).
    - E2E en `molsysviewer/js/tests/e2e` (headless Playwright: carga estructura, crea región, hide). Por defecto usa Chromium de Playwright; se puede forzar un Chrome/Chromium local con `PW_CHROMIUM_BIN=/ruta/al/chrome npm run test:e2e`. Si el lanzamiento está bloqueado por crashpad/sandbox/WebGL ausente, el test se omite con aviso. Actualmente se ejecuta manualmente (no en CI) en un entorno con navegador y WebGL; no usar xvfb/mesa para los E2E.

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

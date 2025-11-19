# Guidelines for AI Agents

This document provides critical instructions for all AI assistants or automation tools contributing to this repository.

## 🚫 Do *Not* Modify Generated Files

The following files **must not be edited manually**:

* `viewer.js`
* `viewer.js.map`

These files are **build artifacts** generated automatically from the TypeScript sources located in the `js/` directory. Any manual edits will be overwritten and may corrupt the build process.

## ✔️ Source of Truth

The authoritative JavaScript/TypeScript sources live here:

```
js/src/
    widget.ts
    shapes.ts
    structure.ts
    ...
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
5. When in doubt, **ask before modifying files outside `js/src/`**.

## 📌 Why This Matters

Editing generated files breaks:

* reproducibility,
* version control clarity,
* build determinism,
* debugging and maintenance workflows.

Follow these rules to ensure the viewer remains stable and maintainable.

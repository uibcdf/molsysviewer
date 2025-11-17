# MolSysViewer — Repository Structure
_Last updated: 2025-02 (Integrated Legacy Notes)_

This document describes the modern structure of MolSysViewer after the
architecture reset, with all relevant lessons from the legacy design integrated
into a stable and maintainable code layout.

---

## 📁 Directory Overview

```
molsysviewer/
│
├── molsysviewer/
│   ├── __init__.py
│   ├── viewer.py            # Python public API + messaging
│   ├── widget.py            # anywidget bridge, loads viewer.js
│   └── viewer.js            # auto-generated TypeScript bundle (DO NOT EDIT)
│
└── js/
    ├── package.json         # NPM dependencies (molstar, esbuild, ts)
    ├── tsconfig.json        # TypeScript configuration
    └── src/
        ├── widget.ts        # anywidget renderer
        └── shapes.ts        # custom Mol* shapes (spheres, meshes, arrows...)
```

---

## 🐍 Python Layer

### `viewer.py`
- Exposes a clean Python API:
  - `load_pdb_string(...)`
  - `load_mmcif_string(...)`
  - `load_from_url(...)`
  - `show_test_sphere_transparent(...)`
  - `clear()`
- Queues messages until JS widget reports `"ready"`.
- Responsible for user-facing behavior.

### `widget.py`
- Extremely thin:
  - loads the generated javascript bundle
  - defines `MolSysViewerWidget` class

### `viewer.js`
- Built automatically from TypeScript sources.
- Bundles Mol\* internals.
- Single source of truth for all JS behavior.

---

## 🟦 TypeScript Layer (`js/`)

### `src/widget.ts`
- Implements the anywidget `render()` function.
- Creates the Mol* `PluginContext`.
- Initializes canvas via `initViewerAsync`.
- Receives messages from Python and dispatches operations:
  - structure loading
  - adding shapes
  - clearing scene
- Future home of picking events and Py callbacks.

### `src/shapes.ts`
- Defines all custom shape logic.
- Wraps Mol* geometry utilities:
  - MeshBuilder
  - Shape
  - ShapeRepresentation
  - Color utilities
- Will map TopoMT & PharmacophoreMT objects → visual objects.

---

## 🧠 Legacy Knowledge Incorporated
- Avoid global `window.molstar` patterns.
- Avoid labextensions; anywidget is simpler and future-proof.
- Avoid reuse of the old MolSysViewerModel/View system.
- Full control of Mol* internals is mandatory for scientific visualization.
- Separate shape logic (`shapes.ts`) from widget rendering (`widget.ts`).

---

## 🔄 Data Flow (Python → JS)

1. Python calls:
   ```python
   v.load_pdb_string(text)
   ```
2. `viewer.py` sends:
   ```json
   { "op": "load_structure_from_string", "format": "pdb", "data": "..." }
   ```
3. JS (`widget.ts`) receives and invokes `loadStructureFromString(...)`.
4. Mol* builds trajectory and applies default representation.
5. Viewer updates.

---

## 🔄 Data Flow (Python → JS Shapes)

1. Python calls:
   ```python
   v.show_test_sphere_transparent(center=(0,0,0), radius=10)
   ```
2. JS dispatches to `addTransparentSphereToPlugin(...)` in `shapes.ts`.
3. The shape is added to Mol* scene graph.

---

## 🎯 Architectural Goals
- Clear separation of responsibilities.
- Maintainability and readability.
- Extensibility for complex scientific shapes.
- Zero reliance on deprecated Jupyter technologies.

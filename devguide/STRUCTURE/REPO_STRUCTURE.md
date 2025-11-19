# MolSysViewer — Repository Structure
_Last updated: 2025-11_

This document describes the stable layout of the MolSysViewer repository.

---

# 1. High-Level Layout

```
molsysviewer/
│
├── molsysviewer/
│   ├── __init__.py
│   ├── viewer.py
│   ├── widget.py
│   └── viewer.js
│
└── js/
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── widget.ts
        ├── shapes.ts
        └── structure.ts
```

---

# 2. Python Layer

### `viewer.py`
- Public API (load, shapes, messaging)
- Queues messages until JS side reports `"ready"`

### `widget.py`
- Loads the JS bundle
- Minimal anywidget wrapper

### `viewer.js`
- Bundled automatically from TypeScript
- Contains Mol* runtime

---

# 3. TypeScript Layer

### `widget.ts`
- Initializes Mol* only once
- Handles messages
- Calls shape/structure helpers

### `shapes.ts`
- Implements geometric primitives
- Future home for meshes, arrows, cylinders

### `structure.ts`
- Wraps Mol* parsing & loading
- Converts strings/URLs → structure + representation

---

# 4. Data Flow

### Structure Loading
Python → JS → Mol* builders → default representation

### Shape Rendering
Python → JS dispatcher → shapes.ts → Mol* shape representation

---

# 5. Principles
- Clear separation between Python API and JS rendering
- No global objects
- No JupyterLab extensions
- All geometry generated in TS

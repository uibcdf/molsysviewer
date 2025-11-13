
# MolSysViewer — Repository Structure Overview

This document summarizes the planned structure of the **MolSysViewer** project.  
It is designed as a clear, readable reminder of *what we will build* and *how it will be organized*.

---

## Project Purpose

**MolSysViewer** is an interactive molecular visualization tool for Jupyter, based on **Mol\*** and fully integrated with:

- **MolSysMT** (molecular systems),
- **TopoMT** (topographic features: cavities, mouths, rims, etc.),
- molecular dynamics trajectories,
- dynamic overlays (hydrogen bonds and similar frame-dependent interactions).

It will become the standard viewer for the whole MolSys ecosystem.

---

## High-Level Structure

```
MolSysViewer/
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── molsysviewer/
├── js/
├── docs/
├── examples/
└── tests/
```

Each part has a specific role.

---

# 1. Root of the repository

| File / Folder | Purpose |
|---------------|---------|
| **pyproject.toml** | Defines the Python package (`molsysviewer`), dependencies, build system. |
| **README.md** | User-friendly introduction, installation instructions, minimal examples. |
| **LICENSE** | Likely MIT, consistent with MolSysMT/TopoMT. |
| **CONTRIBUTING.md** | Guidelines for contributors (style, PRs, issues). |
| **.gitignore**, **.pre-commit-config.yaml**, **.github/workflows** | Development tooling: CI, linting, formatting. |

---

# 2. Python package: `molsysviewer/`

This is the **Python side** of MolSysViewer.

```
molsysviewer/
├── __init__.py
├── _version.py
├── viewer.py
├── widget.py
├── messaging.py
├── data_models.py
├── adapters/
│   ├── molysmt_adapter.py
│   └── topomt_adapter.py
└── representations/
    ├── cavities.py
    ├── hbonds.py
    ├── trajectories.py
    └── shapes.py
```

### 2.1 Core modules

### `viewer.py` — High‑level API
Provides the user-facing class:

```python
class MolSysViewer:
    @classmethod
    def from_molysmt(cls, system): ...
    @classmethod
    def from_pdb_string(cls, pdb): ...
    def add_trajectory(self, traj): ...
    def show_cavity(self, cavity, mode="cloud", opacity=0.4): ...
    def show_hbonds(self, hbonds_by_frame): ...
```

This is the *ergonomic interface* users will call inside notebooks.

---

### `widget.py` — The ipywidget

```python
class MolSysViewerWidget(DOMWidget):
    _model_name = "MolSysViewerModel"
    _view_name = "MolSysViewerView"
    _model_module = "molsysviewer"
    _view_module = "molsysviewer"

    state = Dict().tag(sync=True)
    frame = Int(0).tag(sync=True)
```

This class connects Python ↔ JS.

---

### `messaging.py` — Commands sent to the frontend

Handles messages like:

- `LOAD_PDB_STRING`
- `SET_REPRESENTATION`
- `SET_FRAME`
- `SET_CAVITY_POINTCLOUD`
- `SET_CAVITY_MESH`
- `SET_DYNAMIC_LINES`

---

### `data_models.py` — Scientific data → Visual data

Defines standard structures (likely `dataclasses`):

- `CavityCloud` (positions, radii, color, opacity)
- `CavityMesh` (vertices, faces)
- `TrajectoryData`
- `HbondSeries`
- `ShapeData` (generic spheres, lines)

This ensures a **clean, typed pipeline** before sending data to JS.

---

## 2.2 Integrations

### `adapters/`

- `molysmt_adapter.py`  
  Converts MolSysMT systems into:
  - PDB/mmCIF-like strings,
  - coordinate/topology data,
  - trajectory frames.

- `topomt_adapter.py`  
  Translates TopoMT entities (`Cavity`, `Mouth`, `BaseRim`, etc.) into:
  - `CavityCloud`,
  - `CavityMesh`,
  - open surfaces.

Adapters **decouple** MolSysViewer from internal details of MolSysMT/TopoMT.

---

## 2.3 Representations (Python side)

Helpers that send appropriate commands to the widget:

- `cavities.py` — cloud/mesh views of cavities.
- `hbonds.py` — dynamic H‑bond overlays.
- `trajectories.py` — trajectory loading & frame control.
- `shapes.py` — spheres, cylinders, lines.

`viewer.py` orchestrates these modules to provide a simple API.

---

# 3. Front-end TypeScript: `js/`

This is the **browser side**:

```
js/
├── package.json
├── tsconfig.json
├── webpack.config.js
└── src/
    ├── index.ts
    ├── widget.ts
    ├── molstar_plugin.ts
    ├── representations/
    └── utils/
```

### Key components:

### `index.ts`
Registers the widget with Jupyter.

### `widget.ts`
Defines the JS model & view:

- Creates the HTML container.
- Initializes Mol\*.
- Receives Python messages via `msg:custom`.

### `molstar_plugin.ts`
The actual Mol\* viewer instance:

- Loads structures & trajectories.
- Updates cavity clouds & meshes.
- Draws dynamic overlays.
- Provides clipping & advanced rendering hooks.

### Custom Mol\* representations
Located in `js/src/representations/`:

- `cavities-repr.ts`
- `hbonds-repr.ts`
- `pointcloud-repr.ts`

### Utilities
Located in `js/src/utils/`:

- `messaging.ts`
- `molstar-helpers.ts`

---

# 4. Documentation: `docs/`

Later, the documentation will include:

- `architecture.md` — diagrams & flow.
- `user-guide.md` — how to visualize systems/cavities/trajs.
- `dev-guide.md` — how to extend MolSysViewer.
- `api-reference.md` — detailed Python API.

---

# 5. Examples: `examples/`

Jupyter notebooks demonstrating real workflows:

1. Basic viewer usage  
2. MolSysMT system visualization  
3. TopoMT cavity clouds & meshes  
4. Dynamic overlays (H‑bonds, etc.)

---

# 6. Tests: `tests/`

Python tests verify:

- Viewer instantiation  
- Data model correctness  
- Adapters  
- Messaging commands  

Later: smoke tests for JS.

---

## Key Idea to Remember

**MolSysViewer is a two‑layer system:**

1. **Python layer**  
   - Integrates MolSysMT & TopoMT  
   - Builds data models  
   - Sends visualization commands  

2. **TypeScript/Mol\* layer**  
   - Renders molecules, trajectories, cavities, overlays  
   - Handles updates from Python  

The structure is designed to be **flexible, extensible**, and to allow future development of a **web version** using the same Mol\* core.

---

End of file.

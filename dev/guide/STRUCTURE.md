# 📁 MolSysViewer — Repository Structure

## 0. Name, Purpose, and Vision

**Project name:** `MolSysViewer`
**Python package:** `molsysviewer`
**Technologies:** Python 3.10+, TypeScript, ipywidgets, Mol*

**Purpose:**
MolSysViewer is the standard interactive viewer of the **MolSysMT / TopoMT** ecosystem. It provides:

* 3D molecular visualization using **Mol***,
* integration with **MolSysMT** for systems and trajectories,
* integration with **TopoMT** for cavities, mouths, rims, and interfaces,
* dynamic overlays (H-bonds, distances, frame-dependent interactions),
* smooth use from inside Jupyter notebooks.

Think of MolSysViewer as the unified visual front-end of the UIBCDF molecular modeling ecosystem.

---

# 1. Overall Repository Structure

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

Meaning of each part:

* **Root** → packaging, metadata, quick documentation.
* **molsysviewer/** → Python backend.
* **js/** → TypeScript frontend + Mol*.
* **docs/** → user and developer documentation.
* **examples/** → demonstration notebooks.
* **tests/** → Python tests (and future JS smoke tests).

---

# 2. Project Root

| File                                        | Purpose                                                         |
| ------------------------------------------- | --------------------------------------------------------------- |
| **pyproject.toml**                          | Python package configuration: name, dependencies, build system. |
| **README.md**                               | Quick introduction, installation instructions, minimal example. |
| **LICENSE**                                 | Likely MIT, consistent with MolSysMT/TopoMT.                    |
| **CONTRIBUTING.md**                         | Guidelines on PRs, issues, style, development flow.             |
| **.gitignore**, **.pre-commit-config.yaml** | Developer tooling (linting, formatting).                        |
| **.github/workflows/**                      | GitHub Actions for CI, JS build, testing.                       |

---

# 3. Python Package `molsysviewer/`

The Python backend provides the user API, the data transformation layer, the integration with MolSysMT/TopoMT, and communication with the frontend.

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

---

## 3.1 Core Python API

### `viewer.py` — High-level user API

This is the class users will interact with in notebooks:

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

It orchestrates adapters, data models, the ipywidget, and representation helpers.

---

### `widget.py` — The ipywidget

Defines the widget rendered inside Jupyter:

```python
class MolSysViewerWidget(DOMWidget):
    _model_name = "MolSysViewerModel"
    _view_name = "MolSysViewerView"
    _model_module = "molsysviewer"
    _view_module = "molsysviewer"

    state = Dict().tag(sync=True)
    frame = Int(0).tag(sync=True)
```

This is the Python ↔ JavaScript synchronization layer.

---

### `messaging.py` — Commands to the frontend

A clean API to send operations:

* `LOAD_PDB_STRING`
* `SET_REPRESENTATION`
* `SET_FRAME`
* `SET_CAVITY_POINTCLOUD`
* `SET_CAVITY_MESH`
* `SET_DYNAMIC_LINES`

Example:

```python
def send_command(widget, op: str, payload: dict):
    widget.send({"op": op, "payload": payload})
```

---

### `data_models.py` — Visual data structures

Typed structures (usually `dataclasses`) that package scientific data to be sent to the frontend:

* `CavityCloud`
* `CavityMesh`
* `TrajectoryData`
* `HbondSeries`
* `ShapeData` (spheres, cylinders, lines)

The goal is to ensure clean, consistent graphics-ready data.

---

## 3.2 Integration with MolSysMT and TopoMT — `adapters/`

Adapters decouple the viewer from external library details.

### `molysmt_adapter.py`

Converts MolSysMT objects into:

* PDB/mmCIF-like strings,
* topology and selections,
* trajectories → `TrajectoryData`.

### `topomt_adapter.py`

Converts TopoMT entities:

* `Cavity`, `Mouth`, `BaseRim`, `Interface`, etc.
* into `CavityCloud`, `CavityMesh`, and geometric shapes.

The viewer only understands “clouds, meshes, shapes”.
Adapters map scientific entities to these visual models.

---

## 3.3 Representation helpers (Python)

### `representations/cavities.py`

Handling cavity clouds, meshes, colors, opacities.

### `representations/hbonds.py`

Handling per-frame hydrogen-bond line overlays.

### `representations/trajectories.py`

Trajectory loading, frame stepping, visual styles.

### `representations/shapes.py`

Geometric primitives:

* sphere clouds,
* cylinders,
* lines,
* points.

The viewer coordinates these helpers to expose a unified API.

---

# 4. TypeScript Frontend — `js/`

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

---

## 4.1 Root JS files

* `package.json` – JS dependencies, scripts.
* `tsconfig.json` – TypeScript configuration.
* `webpack.config.js` – Bundling and build pipeline.

---

## 4.2 Main TypeScript Components

### `src/index.ts`

Registers the widget (model + view) for Jupyter.

---

### `src/widget.ts`

Defines the JS-side widget:

* creates the HTML container,
* initializes Mol*,
* listens to messages from Python (`msg:custom`),
* forwards actions to the Mol* plugin.

---

### `src/molstar_plugin.ts`

The visualization engine:

* instantiates and configures Mol*,
* loads structures and trajectories,
* updates cavity clouds and meshes,
* renders dynamic overlays (H-bonds, shapes),
* manages themes, clipping, advanced Mol* configuration.

---

## 4.3 Custom TS Representations

Located in `js/src/representations/`:

* `cavities-repr.ts`
* `hbonds-repr.ts`
* `pointcloud-repr.ts`

These modules define the custom geometry, materials and rendering logic used for clouds, meshes, and dynamic lines.

---

## 4.4 Utilities

Found in `js/src/utils/`:

* `messaging.ts` — helpers to interpret Python commands.
* `molstar-helpers.ts` — utilities for Mol* (geometry construction, color mapping, frame handling).

---

# 5. Documentation — `docs/`

Suggested structure:

```
docs/
├── index.md
├── architecture.md
├── user-guide.md
├── dev-guide.md
└── api-reference.md
```

Contents:

* **architecture.md**: how Python, ipywidgets and Mol* work together.
* **user-guide.md**: loading structures, cavities, trajectories, H-bonds, overlays.
* **dev-guide.md**: extending the viewer with new representations or adapters.
* **api-reference.md**: full Python API documentation.

---

# 6. Examples — `examples/`

Demonstration notebooks:

1. **Basic Usage** — load a PDB and display it.
2. **MolSysMT Integration** — visualize systems and trajectories.
3. **TopoMT Cavities** — display cavity clouds and meshes.
4. **Dynamic Overlays** — frame-dependent H-bonds and contacts.

---

# 7. Tests — `tests/`

Python tests include:

* creation of the viewer,
* validation of `data_models`,
* adapters coherence,
* structure of messages in `messaging`.

Future additions:

* JS smoke tests,
* Python ↔ JS synchronization tests.

---

# 8. Key Idea (Final Summary)

MolSysViewer is a **two-layer coordinated visualization system**:

**A. Python layer:**

* orchestrates scientific data,
* builds visual data models,
* controls state and user API,
* communicates with Jupyter.

**B. TypeScript/Mol* layer:**

* renders molecules, trajectories, cavities, and overlays,
* manages custom representations,
* updates interactively based on Python events.

The design is:

* extensible (new representations and adapters),
* decoupled (MolSysMT/TopoMT do not leak into the viewer core),
* ready for a future **web-native** version.

---


# MolSysViewer Development Roadmap

This roadmap breaks the project into concrete, sequential development phases, each producing a stable and testable component.  
It complements the architectural design in `MolSysView_DESIGN_OVERVIEW.md`.

---

# Phase 1 — Core Infrastructure (Weeks 1–2)

### 1.1. Create project structure
- `molsysviewer/core.py`
- `molsysviewer/basic.py`
- `molsysviewer/cam.py`
- `molsysviewer/shapes.py`
- `molsysviewer/structure.py`
- future modules: `hbonds.py`, `topology.py`

### 1.2. Implement MolSysView class skeleton
- `_molsys` attribute  
- `atom_mask`  
- `visible_atom_indices` property  
- `_send()` communication method (minimal)

### 1.3. Basic module (`basic`)
- `info()`
- `hide()`
- `show()`
- `isolate()`
- `reset_visibility()`

### 1.4. Facade mapping for basic and cam

Deliverables:
- runnable viewer with working `.show()`, `.hide()`, `.info()`  
- initial documentation + unit tests

---

# Phase 2 — Camera and View (Weeks 2–3)

### 2.1. `cam` module
- `center_on()`
- `reset_view()`

### 2.2. Front-end handlers
- implement `"center_on_atoms"`
- implement default camera reset

Deliverables:
- user can load a molecule, center, zoom, and reset the view.

---

# Phase 3 — Shapes (Weeks 3–5)

### 3.1. `shapes` module
- `add_spheres(selection, center='atoms'|'geom'|'mass', radius, color, alpha)`
- `add_spheres_for_selections(...)`

### 3.2. Front-end handlers
- `"add_spheres"`
- shape management (IDs, remove shapes later)

Deliverables:
- visual overlays using Mol\* sphere primitives

---

# Phase 4 — Structure Module (Weeks 5–8)

### 4.1. Numeric functions (`get_*`)
- `get_distances`
- `get_angles`
- `get_dihedral_angles`
- `get_neighbors`
- `get_contacts`
- `get_radius_of_gyration`
- `principal_component_analysis`

### 4.2. Visual functions (`show_*`)
- `show_distances`
- `show_angles`
- `show_dihedral_angles`
- `show_neighbors`
- `show_principal_axes`

Deliverables:
- full numeric + visual geometry toolkit using MolSysMT + Mol\*

---

# Phase 5 — Hbonds and Topology (Weeks 8–10)

### 5.1. Hbonds module
- `get_hbonds`
- `show_hbonds`

### 5.2. Topology module
- `get_bonds`
- `show_bonds`
- integration with MolSysMT topology tools

Deliverables:
- hydrogen bonds and topology overlays

---

# Phase 6 — Advanced Shape Primitives (Weeks 10–12)

### 6.1.
- `add_plane`
- `add_arrow`
- `add_mesh`
- optional:
  - volumetric shapes
  - scalar fields

Deliverables:
- visually rich overlays for advanced molecular analysis.

---

# Phase 7 — Engines and Performance (Weeks 12–14)

### 7.1. Engine framework
Add `engine=` argument to structure methods:
- `"molsysmt"` — default  
- `"molstar"` — optional \
- `"numpy"`, `"numba"` — performance backends

### 7.2. Benchmarking suite

---

# Phase 8 — Polishing, Documentation, Demos (Weeks 14–16)

### 8.1. Documentation
- API reference
- Module guides
- Tutorial notebooks

### 8.2. Examples
- full demo notebook
- integration with MolSysMT workflows
- TopoMT & PharmacophoreMT-friendly views

---

# Long-term Ideas

- Dynamic representations (movie mode)
- MD trajectory support
- Plugin architecture for shapes
- Integration with computational backends (CUDA, cupy)
- Interactive measurement tools

---

This roadmap ensures a clean, progressive build-out of MolSysViewer, from core fundamentals to advanced visualization and scientific features.

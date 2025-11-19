# MolSysViewer — ROADMAP (Unified and Definitive)
_Last updated: 2025-11_

This unified roadmap consolidates all prior planning documents 
(`ROADMAP.md`, `MolSysView_ROADMAP.md`, `NEXT_STEPS.md`) into a single, 
coherent and authoritative development plan for **MolSysViewer**.

---

# Phase 0 — Architecture Reset (Completed)

### Achievements
- Full migration away from legacy JupyterLab-extension code.
- Adoption of **anywidget** for modern rendering.
- Build system based on **TypeScript + esbuild**.
- Full control of the Mol\* runtime via `initViewerAsync`.
- Corrected Mol\* initialization sequencing.
- Robust, asynchronous Python ↔ JavaScript messaging.
- First working custom shapes (transparent spheres).

---

# Phase 1 — Core Features (Active)

## 1. Molecule Input
- [x] Load PDB/mmCIF strings  
- [x] Load from remote URLs  
- [ ] Load native MolSysMT systems  
- [ ] Load multi-frame trajectories  

---

## 2. Shape System (v1)
- [x] Transparent sphere  
- [x] `add_sphere()` Python API  
- [x] `add_spheres()` vectorized API  
- [ ] Point primitives (billboards)  
- [ ] Arrows  
- [ ] Cylinders  
- [ ] Mesh loading  
- [ ] Text labels  

---

## 3. Scene Management (v1)
- [ ] Object tagging (`tag=`)  
- [ ] `viewer.clear(tag=...)`  
- [ ] Camera utilities  
- [ ] Visibility toggles for custom objects  

---

# Phase 1.5 — Immediate Next Steps  
(Previously in `NEXT_STEPS.md`, now formalized)

### Shape Grouping
- `tag=` parameter  
- Tag registry  
- `clear(tag=...)` implementation  

### New Shape Primitives
- Billboards / points  
- Arrows  
- Cylinders  
- Mesh importers  
- 3D labels  

### Camera Utilities
- `center_on()`  
- `focus_on_sphere()`  
- `fit_to_bbox()`  

### Rendering Engine Enhancements
- Vectorized `add_spheres` inside JS  
- Efficient multi-sphere representations  
- Internal shape manager (IDs, delete, visibility)  
- Debugging tools: logging, HUD text, performance stats  

---

# Phase 2 — Integration with the uibcdf Ecosystem

## TopoMT Integration
- [ ] Alpha-sphere rendering  
- [ ] Pocket surfaces  
- [ ] Cavity rims and mouth borders  
- [ ] Feature-based color schemes  

## PharmacophoreMT Integration
- [ ] Pharmacophoric spheres  
- [ ] Donor/acceptor arrow glyphs  
- [ ] Aromatic ring discs  
- [ ] Exclusion volumes  

## MolSysMT Integration
- [ ] Load MolSysMT systems directly  
- [ ] Shared selections/highlights  
- [ ] Trajectory stepping (previous, next, play, loop)  

---

# Phase 3 — UX / UI Enhancements

- [ ] Scene inspector panel  
- [ ] Prebuilt color palettes  
- [ ] Text overlays for annotations  
- [ ] Screenshot export  
- [ ] Scene serialization to JSON  

---

# Phase 4 — Structure Module

## Numerical Functions (`get_*`)
- [ ] Distances  
- [ ] Angles  
- [ ] Dihedrals  
- [ ] Neighbors / contacts  
- [ ] Radius of gyration  
- [ ] PCA  
- [ ] Transformations (rotate, center, align)  

## Visual Functions (`show_*`)
- [ ] Show distances  
- [ ] Show angles  
- [ ] Show dihedrals  
- [ ] Show neighbors  
- [ ] Show principal axes  

---

# Phase 5 — Hbonds & Topology Module

## Hydrogen Bonds
- [ ] `get_hbonds()`  
- [ ] `show_hbonds()`  

## Topology
- [ ] `get_bonds()`  
- [ ] `show_bonds()`  
- [ ] Integration with MolSysMT topology tools  

---

# Phase 6 — Advanced Shape Primitives

- [ ] Planes  
- [ ] Advanced meshes  
- [ ] Volumetric representations  
- [ ] Scalar fields (e.g., ESP, density)  

---

# Phase 7 — Engines & Performance

## Multi-Engine Support
- `"molsysmt"` (default scientific engine)  
- `"molstar"` (ultrafast mass distance operations)  
- `"numpy"`  
- `"numba"`  
- `"cupy"` (GPU acceleration, future)  

## Benchmarking Suite
- Load times  
- Render performance  
- Shape scalability  

---

# Phase 8 — Documentation, Tests & Demos

- Comprehensive tutorials  
- API reference  
- Example Jupyter notebooks  
- Integration with MolSysMT, TopoMT, PharmacophoreMT  
- Unit tests and visual tests  

---

# Long-Term Vision

MolSysViewer aims to become the **central visualization engine** of the uibcdf 
ecosystem — powering cavity detection, pharmacophore visualization, molecular 
analysis, machine learning annotations, interactive exploration, and integrated 
simulation workflows.

---

# Legacy Notes  
(Useful concepts preserved from older roadmaps)

- Scene inspector panel  
- Clipping planes  
- Regional highlighting  
- JS → Python callbacks  
- Animation systems (time-driven)  
- Volume rendering  

---

# Current Status (Summary)

MolSysViewer now stands on a **solid, modern, extensible foundation** and is 
ready to grow into a fully capable visualization and analysis platform tightly 
integrated with the MolSys* ecosystem.


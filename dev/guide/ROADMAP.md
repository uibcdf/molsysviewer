# MolSysViewer — Development Roadmap
_Last updated: 2025-02 (Integrated Legacy Notes)_

This roadmap integrates all current architectural decisions (TypeScript + Mol*
bundle + anywidget) with the valuable long-term insights extracted from the
legacy checkpoints. It provides a consolidated, forward-looking plan aligned
with the needs of MolSysMT, TopoMT, PharmacophoreMT, and future uibcdf tools.

---

## ✔ Phase 0 — Architecture Reset (Completed)

### Achievements
- Fully dropped the old JupyterLab labextension prototype.
- Adopted **anywidget** as the widget backbone.
- Moved to **local TypeScript build system** using `esbuild`.
- Installed **Mol\*** from NPM and built a custom viewer bundle.
- Implemented clean `PluginContext` initialization via `initViewerAsync`.
- Established a robust communication pipeline (Python ↔ JS).

### Lessons Incorporated (Legacy)
- A CDN-based Mol* viewer is insufficient: hides internals needed for scientific
  visualization.
- JupyterLab labextensions were over-complicated and fragile.
- A clean restart provides long-term maintainability and reduces accidental complexity.

---

## 🚧 Phase 1 — Core Functionalities (In Progress)

### 1. Molecule Loading
- [x] Load structures from PDB/mmCIF strings.
- [x] Load molecules from URLs.
- [ ] Load MolSysMT molecular objects directly (atoms, frames, selections).
- [ ] Multi-frame support with `setFrame(...)`.

### 2. Custom Shape Rendering (Critical)
- [ ] Working implementation of:
  - transparent spheres  
  - points  
  - arrows/vectors  
  - cylinders  
  - surfaces/meshes  
- [ ] Stable internal shapes API (used by TopoMT & PharmacophoreMT).
- [ ] Consistent color and opacity handling.

### 3. Scene + API Improvements
- [ ] `viewer.add_sphere(...)`
- [ ] `viewer.add_mesh(vertices, faces, ...)`
- [ ] `viewer.clear()`
- [ ] `viewer.set_representation(type)`
- [ ] `viewer.center_on(selection)`

---

## 🔧 Phase 2 — Integration with uibcdf Ecosystem

### 1. TopoMT Integration
- [ ] Render cavity volumes (meshes)
- [ ] Render alpha spheres and cluster groupings
- [ ] Render mouths/rims (1D curves)
- [ ] Camera focus on selected feature
- [ ] Color schemes for concavity/convexity/mixed/boundary shapes

### 2. PharmacophoreMT Integration
- [ ] Pharmacophoric spheres (hydrophobic)
- [ ] Donor/acceptor arrows
- [ ] Aromatic ring discs
- [ ] Exclusion volumes
- [ ] Feature grouping and labeling

### 3. MolSysMT Integration
- [ ] Display molecules from MolSysMT containers
- [ ] Synchronize selections/highlights
- [ ] Display trajectories
- [ ] Plugin-like preset system

---

## 🔍 Phase 3 — UX / UI Enhancements
- [ ] Scene inspector panel (toggle shapes/structure visibility)
- [ ] Color presets and themes
- [ ] Text overlays for debug/status
- [ ] Screenshot export
- [ ] JSON-based scene serialization

---

## ✨ Phase 4 — Advanced Features
- [ ] Time animations
- [ ] Surface clipping planes
- [ ] Fragment-based highlighting
- [ ] Reactive JS-to-Python callbacks

---

## 🚀 Vision
MolSysViewer is the visualization pillar for the uibcdf ecosystem: a clean,
modern, extensible molecular visualization backend that supports the whole
range of scientific workflows — molecular structures, topographic cavities,
pharmacophores, ML-driven annotations, and interactive exploration.


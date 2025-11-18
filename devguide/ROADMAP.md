# MolSysViewer — Roadmap
_Last updated: 2025-11_

This roadmap reflects the **current stable foundation** as well as the next
planned expansions across Python, TypeScript, Mol*, and future scientific
integrations.

---

# Phase 0 — Architecture Reset (Completed)

### Achievements
- Replaced all legacy JupyterLab-extension code.
- Adopted **anywidget** for rendering.
- Adopted **TypeScript + esbuild** for bundling.
- Full control of Mol* runtime using `initViewerAsync`.
- Repaired the Mol* initialization path.
- Implemented stable Python ↔ JS messaging.

---

# Phase 1 — Core Features (Active)

### 1. Molecule Input
- [x] Load PDB/mmCIF strings
- [x] Load from remote URLs
- [ ] Load MolSysMT molecular systems
- [ ] Load multi-frame trajectories

### 2. Shape System
- [x] Transparent sphere
- [x] `add_sphere` Python API
- [x] `add_spheres` Python API
- [ ] Points
- [ ] Arrows
- [ ] Cylinders
- [ ] Mesh surfaces
- [ ] Labels

### 3. Scene Management
- [ ] Object tagging system
- [ ] `viewer.clear(tag=...)`
- [ ] Camera utilities
- [ ] Visibility toggles

---

# Phase 2 — Integration with the uibcdf Ecosystem

### TopoMT
- [ ] Alpha-sphere rendering
- [ ] Pocket surfaces
- [ ] Cavity mouths/rims
- [ ] Feature-color schemes

### PharmacophoreMT
- [ ] Pharmacophoric spheres
- [ ] Donor/acceptor arrows
- [ ] Aromatic ring discs
- [ ] Exclusion volumes

### MolSysMT
- [ ] Native view of molecular systems
- [ ] Shared selections/highlights
- [ ] Trajectory stepping controls

---

# Phase 3 — UX / UI Enhancements
- [ ] Scene inspector panel
- [ ] Color presets
- [ ] Text overlays
- [ ] Screenshot export
- [ ] JSON scene serialization

---

# Phase 4 — Advanced Features
- [ ] Time-based animations
- [ ] Clipping planes
- [ ] Region-based highlighting
- [ ] Reactive events (JS → Python callbacks)

---

# Vision

MolSysViewer will serve as the **unified visualization engine** for all uibcdf
projects—supporting cavities, pharmacophores, molecular editing, ML annotations,
and interactive exploratory analysis.

# MolSysViewer — Next Steps
_Last updated: 2025-11_

This document centralizes forward development plans.

---

# 1. Mini-API Enhancements (Python)

### Shape Grouping
- Add `tag=` parameter
- Maintain registries
- Implement `clear(tag=...)`

### Additional Primitives
- Points (billboards)
- Arrows
- Cylinders
- Labels
- Mesh loading

### Camera Utilities
- `center_on()`
- `focus_on_sphere()`
- `fit_to_bbox()`

---

# 2. Rendering Engine Enhancements (TypeScript)

### Shape Optimization
- Vectorized `add_spheres` in JS
- Single-shape representations for many spheres

### Internal Shape Manager
- Registry
- Tagging
- Deletion
- Visibility toggles

### Debug Tools
- Logging toggles
- Overlay text

---

# 3. Scientific Integrations

### TopoMT
- Alpha-spheres
- Pocket meshes
- Rim curves

### PharmacophoreMT
- Hydrophobic spheres
- Donor/acceptor arrows
- Aromatic ring discs
- Exclusion volumes

### MolSysMT
- Direct loading
- Synced selections
- Trajectory stepping

---

# 4. Interaction Features
- Click → Python callbacks
- Hover highlight
- Region selection
- Scene export/import
- Snapshots

---

# 5. Long-Term Concepts
- Clipping planes
- Interactive measurements
- Volume rendering
- GPU-accelerated meshes

---

# 6. Principles
- Keep Python simple
- Keep TS powerful but isolated
- Avoid render loops
- Support scientific extensibility

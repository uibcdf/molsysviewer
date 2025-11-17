# MolSysViewer — Development Checkpoint
_Date: 2025-02 (Integrated Legacy Notes)_

This checkpoint unifies the current state of the project with all valuable
insights preserved from the older checkpoints.

---

# 1. Where We Stand Today

### ✔ Working Elements
- Mol* PluginContext initializes cleanly.
- Canvas, camera, and view controls operate correctly in Jupyter.
- Python ↔ JS messaging system is stable.
- TypeScript bundle compiles via esbuild.
- The architecture supports complete control of Mol* internals.

### ✔ Integrated Legacy Insights
- A clean restart was the correct decision.
- Custom shapes are essential for TopoMT/PharmacophoreMT.
- MolSysViewer must serve as the visualization backbone for the uibcdf ecosystem.
- The Python API must be simple, elegant, declarative where possible.
- Internal shape logic must be isolated and testable.

---

# 2. What We Have Learned

## Technical Lessons (Legacy + Modern)
- Mol* CDN is insufficient for scientific visualization.
- Mol* 5.x changed APIs (`initViewerAsync`, new builder patterns).
- Custom geometry requires low-level access to geometry modules.
- anywidget is more minimalistic and powerful than traditional labextensions.
- The old labextension architecture was not sustainable.

## Architectural Insights
- Clear separation between:
  - Python API
  - widget renderer
  - shape utilities
- Need for a stable internal contract for shapes:
  - TopoMT surfaces → meshes
  - PharmacophoreMT features → spheres/arrows/discs

---

# 3. Pending Work (Critical Path)

### Molecule Loading
- Finalize string → structure → representation pipeline.
- Add MolSysMT integration layer.

### Shape System
- Implement working transparent sphere.
- Implement points, arrows, cylinders.
- Implement meshes for cavity surfaces.
- Support 1D curves for mouths/rims.

### High-Level Python API
- `add_sphere()`
- `add_mesh()`
- `add_surface()`
- `center_on()`

---

# 4. Medium-Term Goals

### TopoMT
- Cavity rendering (surfaces)
- Cluster highlighting
- Mouth/rim curves

### PharmacophoreMT
- Spheres, arrows, planes, discs
- Group and label features

### MolSysMT
- Trajectories
- Selections synchronised with viewer

---

# 5. Long-Term Vision

MolSysViewer is evolving into a powerful, extensible, scientifically capable
visualization engine tailored to the needs of molecular modeling, structural
analysis, cavity exploration, pharmacophore modeling, and ML-driven annotation
workflows.

Its design philosophy is founded on:
- simplicity in Python
- power in TypeScript/Mol*
- extensibility for research
- long-term maintainability


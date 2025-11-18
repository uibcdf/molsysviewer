# MolSysViewer – Architecture Design Overview
**Integration with MolSysMT, module structure, and Mol\* visual engine**

> **MolSysViewer = Brain (MolSysMT) + Retina (Mol\*)**  
> This document defines the general architecture, module layout, public API patterns,
> engine logic, and Python ↔ frontend interactions required to build a modern, extensible,
> and scientifically robust molecular viewer.

---

# 1. Design Philosophy

MolSysViewer is conceived as an **interactive molecular viewer** deeply integrated with the MolSys* ecosystem:

- **MolSysMT** is the *scientific engine* (selections, analysis, geometry, structural transformations).
- **Mol\*** is the *visual engine* (rendering, shapes, overlays, camera).
- **MolSysView** is the *integration layer*:
  - maintains the loaded molecular system,
  - offers a clean, rich Python API,
  - organizes functionality into modules,
  - synchronizes scientific calculations with visual outputs.

Guiding rules:

### 1.1. Scientific computations → MolSysMT  
Distances, angles, PCA, RMSD, neighbors, hbonds, topology, selections.

### 1.2. Visual rendering → Mol\*  
Spheres, lines, arcs, labels, camera movements, hide/show.

### 1.3. MolSysView = Modules + Facade  
Exactly like MolSysMT:
- internal modules (basic, structure, shapes, cam, hbonds, topology),
- plus a public *facade* exposing high-level access:
  - `.info()`
  - `.get_distances()`, `.show_distances()`
  - `.center_on()`
  - `.add_spheres()`
  - `.get_hbonds()`, `.show_hbonds()`

---

# 2. Internal State

## 2.1. `_molsys`  
Native MolSysMT object representing the loaded molecular system.
This is the **ground truth** for:
- topology,
- coordinates,
- selections,
- masses,
- geometry computations.

## 2.2. `atom_mask`  
Boolean mask controlling **visibility** of atoms in the viewer.

- `True` → atom visible  
- `False` → atom hidden

Consistent with MolSysMT’s internal semantics.

## 2.3. `visible_atom_indices`  
A computed property:

```python
@property
def visible_atom_indices(self):
    return np.where(self.atom_mask)[0]
```

Used to inform Mol\* which atoms are displayed.

---

# 3. Module Architecture

Each module is a Python file (e.g., `basic.py`, `shapes.py`) containing a class.  
Each module receives a reference to the parent MolSysView instance:

```python
class BasicModule:
    def __init__(self, view):
        self._view = view
```

Modules can access:
- `self._view._molsys`
- `self._view.atom_mask`
- `self._view.visible_atom_indices`
- message-sending helpers for frontend communication.

---

# 4. Module Definitions

## 4.1. Module: `basic`  
Controls visibility and high-level system functions:

- `info(selection='all', level='atoms')`
- `hide(selection)`
- `show(selection='all')`
- `isolate(selection)`
- `reset_visibility()`

### Facade:
`.info()`, `.hide()`, `.show()`, `.isolate()`

---

## 4.2. Module: `cam` (or `view`)  
Camera & scene control:

- `center_on(selection)`
- `reset_view()`
- (future) `set_background`, `set_camera_mode`, animations.

### Facade:
`.center_on()`, `.reset_view()`

---

## 4.3. Module: `shapes`  
3D graphics: spheres, lines, arrows, planes, meshes.

- `add_spheres(selection, center='atoms'|'geom'|'mass', radius=..., color=..., alpha=...)`
- `add_spheres_for_selections(dict)`
- (future) `add_arrow`, `add_plane`, etc.

MolSysMT computes centers/geometry → Mol\* draws.

### Facade:
`.add_spheres()`

---

## 4.4. Module: `structure`  
Mirrors `molsysmt.structure`.

Dual-pattern API:

- `get_*` → numeric computation (MolSysMT)
- `show_*` → visual overlay (Mol\*)

### Numeric operations:
- `get_distances`
- `get_angles`
- `get_dihedral_angles`
- `get_neighbors`
- `get_contacts`
- `get_radius_of_gyration`
- `principal_component_analysis`
- transformations: `translate`, `rotate`, `center`, `least_rmsd_fit`

### Visual operations:
- `show_distances`
- `show_angles`
- `show_dihedral_angles`
- `show_neighbors`
- `show_principal_axes`

### Facade:
`.get_distances()`, `.show_distances()`, `.get_dihedral_angles()`, etc.

---

## 4.5. Module: `hbonds` (future)

- `get_hbonds(selection, engine='molsysmt')`
- `show_hbonds(selection, ...)`

### Facade:
`.get_hbonds()`, `.show_hbonds()`

---

## 4.6. Module: `topology` (future)

- `get_bonds`, `show_bonds`
- `get_angles`, `show_angles`

---

# 5. Engine Selection

Argument:

```python
engine="molsysmt"
```

Controls which computational engine to use.  
Possible values:

- `"molsysmt"` — default
- `"molstar"` — optional: delegate to Mol\* for distance/measure speed
- `"numpy"`, `"numba"`, `"cupy"` — potential future optimizations

Example:
```python
v.structure.get_distances(sel1, sel2, engine="molsysmt")
```

---

# 6. MolSysView Facade

Example public API mapping:

```python
class MolSysView:
    ...

    # basic
    def info(self, *a, **k): return self.basic.info(*a, **k)
    def hide(self, *a, **k): return self.basic.hide(*a, **k)
    def show(self, *a, **k): return self.basic.show(*a, **k)
    def isolate(self, *a, **k): return self.basic.isolate(*a, **k)

    # cam
    def center_on(self, *a, **k): return self.cam.center_on(*a, **k)
    def reset_view(self, *a, **k): return self.cam.reset_view(*a, **k)

    # structure
    def get_distances(self, *a, **k): return self.structure.get_distances(*a, **k)
    def show_distances(self, *a, **k): return self.structure.show_distances(*a, **k)

    # hbonds
    def get_hbonds(self, *a, **k): return self.hbonds.get_hbonds(*a, **k)
    def show_hbonds(self, *a, **k): return self.hbonds.show_hbonds(*a, **k)

    # shapes
    def add_spheres(self, *a, **k): return self.shapes.add_spheres(*a, **k)
```

---

# 7. Python ↔ Mol\* Communication

All visual actions emit a JSON-like dictionary to the frontend:

```python
self._send({
    "op": "some_operation",
    "options": { ... }
})
```

Examples:

```python
{"op": "center_on_atoms", "atom_indices": [...]}
{"op": "add_spheres", "centers": [...], "radii": [...], "color": ...}
{"op": "update_visibility", "visible_indices": [...]}
{"op": "add_measurement", "kind": "distance", "atoms": [...], "label": "12.3 Å"}
```

Mol\* handles actual rendering.

---

# 8. Development Phasing

1. **Phase 1**  
   - implement `basic` and `cam`  
   - basic visibility control  
   - camera operations  
   - facade helpers (.info(), .hide(), etc.)

2. **Phase 2**  
   - implement `shapes`  
   - sphere overlays and simple shapes

3. **Phase 3**  
   - implement `structure`  
   - numeric get_*  
   - visual show_*

4. **Phase 4**  
   - add hbonds and topology modules

5. **Phase 5**  
   - advanced shapes (planes, meshes, arrows)
   - additional engines  
   - performance optimization

---

This file defines the full architecture for MolSysViewer and provides a long-term blueprint for its evolution.

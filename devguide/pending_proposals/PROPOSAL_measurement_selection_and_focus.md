# PROPOSAL: Support for selections and `focus()` in Measurements

## Problem Statement
The current measurement API (Distance, Angle, Dihedral) only accepts explicit `atom_indices` as input. This forces users to manually compute indices before measuring. Furthermore, individual measurement objects lack a `focus()` method, making it difficult to navigate to a specific measurement in a complex scene.

## Proposed Changes

### 1. Support for Selections
Refactor `add_distance`, `add_angle`, and `add_dihedral` to accept MolSysMT selections:

```python
# New Signature Example
def add_distance(
    self, 
    selection_a: str | Any, 
    selection_b: str | Any, 
    tag: str | None = None, 
    ...
)
```

**Logic:**
- Use `msm.select()` to resolve `selection_a` and `selection_b` into atom indices.
- If multiple atoms are selected per point, the frontend automatically uses their centroid (consistent with current Mol* behavior).

### 2. Implement `focus()` for Measurement objects
Add a `focus()` method to the `Measurement` class in `molsysviewer/layers.py`:

```python
class Measurement(SceneObject):
    def focus(self, **kwargs):
        """Center the camera on the atoms involved in this measurement."""
        # 1. Retrieve atom indices from the measurement record
        # 2. Call view.zoom(selection=combined_indices, **kwargs)
```

## Benefits
- **Consistency:** Aligns the measurements API with `new_region()`, `zoom()`, and the proposed `add_label()` refactor.
- **Power:** Allows complex queries like `view.measurements.add_distance('res_id 10 and atom_name CA', 'res_id 50 and atom_name CA')`.
- **Navigation:** Makes it easy to jump between different points of interest using `view.measurements['m1'].focus()`.

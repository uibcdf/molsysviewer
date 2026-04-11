# PROPOSAL: Support for selections and multiple atoms in `add_label()`

## Problem Statement
The current annotation API is unnecessarily restrictive. The `view.annotations.add_label()` method only accepts a single `group_index` as an anchor point. This prevents users from:
1. Labeling specific individual atoms.
2. Labeling the centroid of a custom selection (e.g., a binding pocket or a ligand).
3. Using standard MolSysMT selection strings to define the anchor.

## Proposed Changes
Refactor `add_label()` to follow the standard selection pattern used in `new_region()` and `zoom()`:

### New Signature
```python
def add_label(
    self, 
    text: str, 
    selection: str | Any = None, 
    *, 
    atom_indices: list[int] | None = None, 
    tag: str | None = None, 
    ...
)
```

### Logic
1.  If `selection` is provided (as a string), resolve it to `atom_indices` using `msm.select`.
2.  If `atom_indices` are provided directly, use them.
3.  The frontend (Mol*) should receive the full list of `atom_indices`. Mol* automatically calculates the visual anchor at the geometric center of the provided atoms.
4.  Deprecate the `group_index` argument in favor of the more flexible `selection` pattern.

## Benefits
- **Consistency:** Aligns the annotation API with the rest of the library.
- **Flexibility:** Allows labeling any part of the system (e.g., `selection='res_name HEM'`, `selection='atom_index 100'`).
- **Power:** Users can label abstract points like "Centroid of Chain A" without manual index calculation.

# PROPOSAL: Dedicated API for orientation axes and best-fit plane

## Status

✅ Implemented 2026-04-28 — `view.show_orientation_axes()` and `view.show_best_fit_plane()`.
Both create a named region and send `set_region_representation` with the Mol* type directly,
bypassing `ALLOWED_REPRESENTATIONS` (which intentionally keeps these types private).
14 tests in `tests/test_geometry_helpers.py`.

## Context

Mol* has two built-in structure representation types that are not molecular
visualization styles but structural helpers:

- `"orientation"` — draws the principal orientation axes of a structure
  (or selection).
- `"plane"` — draws the best-fit plane through a structure (or selection).

Both were removed from `ALLOWED_REPRESENTATIONS` (and from
`REPRESENTATION_PARAM_SCHEMAS`) in MolSysViewer because they do not belong
alongside `cartoon`, `ball-and-stick`, etc. They are not accessible through
`set_representation()`.

Currently they are reachable only via the `molstar_repr_type` escape-hatch
(undocumented, not user-discoverable).

## Proposed API

Add dedicated toggle methods, not representation names:

```python
view.show_orientation_axes(selection=None)   # toggle principal axes
view.show_best_fit_plane(selection=None)     # toggle best-fit plane
```

Or as region methods:

```python
view.regions['protein'].show_orientation_axes()
view.regions['protein'].show_best_fit_plane()
```

## Why defer

- These are niche helpers (crystallography, structural analysis).
- No user has requested them yet.
- Adding them before there is demand would be over-engineering.

## When to pick up

- If a user requests axes or plane visualization.
- When designing a structural analysis / geometry utilities layer.

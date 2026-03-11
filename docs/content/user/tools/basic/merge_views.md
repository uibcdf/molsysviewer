# `merge_views`

`molsysviewer.tools.basic.merge_views(...)` builds a new view by merging several existing views into one larger molecular system and importing their scene state.

Use it when you want to combine:

- the molecular systems,
- regions,
- layers,
- shapes,
- and atom visibility

from multiple viewers into a single new viewer.

## Minimal example

```python
from molsysviewer import demo, tools

view_a = demo["dialanine"]
view_b = demo["dialanine"]

view_a.new_region(atom_indices=[0, 1, 2], tag="frag", representation="sticks")
view_b.shapes.add_links(atom_pairs=[[0, 1]], tag="contacts")

merged = tools.basic.merge_views([view_a, view_b])
merged
```

## Policy

`merge_views(...)` is a pure operation. It returns a fresh viewer and does not mutate the inputs.

Current merge policy:

- the **first** input view is the source of global state:
  - whole/global representation,
  - global hidden state,
  - camera snapshot,
  - controls/autohide/positions;
- regions, layers, shapes, and atom visibility are imported from **all** views;
- tag collisions are renamed deterministically on later views with suffixes such as `__2`, `__3`, ...

## Example: colliding tags

If two input views both contain a region tagged `frag`, the merged viewer keeps:

- `frag` from the first view
- `frag__2` from the second view

The same collision rule applies to layers and shape tags.

## Notes

- `merge_views(...)` accepts `MolSysView` objects, not raw molecular systems.
- Under the hood it uses `molsysmt.merge(...)` for the molecular-system merge step.
- Imported atom-index-based scene state is remapped onto the merged topology.

(User_Overlays_Shapes_Vectors)=
# Displacement vectors

Displacement vectors render arrows (cylinder + cone) to visualise directions
and magnitudes — for example, normal modes, force vectors, or per-atom
displacements between two structures.

## Minimal example

```python
import molsysviewer as mv
import numpy as np

view = mv.demo["dialanine"]
view

# Four vectors at explicit origins
origins = np.array([[0, 0, 0], [4, 0, 0], [8, 0, 0], [12, 0, 0]], dtype=float)
vectors = np.array([[0, 0, 3], [0, 0, -2], [1, 1, 2], [-1, 0, 3]], dtype=float)

view.shapes.add_displacement_vectors(
    origins=origins,
    vectors=vectors,
    tag="mode-arrows",
)
```

## Using atom positions as origins

```python
# Use the current structure coordinates as arrow origins
view.shapes.add_displacement_vectors(
    origins=None,
    vectors=displacements,      # shape (n_atoms, 3), Å
    atom_indices=list(range(len(displacements))),
    tag="anm-mode1",
)
```

## Key options

| Parameter | Default | Description |
|---|---|---|
| `origins` | — | `(n, 3)` origin coordinates. Required unless `atom_indices` is given. |
| `vectors` | — | `(n, 3)` displacement vectors. |
| `atom_indices` | `None` | Use current structure coordinates as origins. |
| `length_scale` | `1.0` | Global scale factor applied to vector lengths. |
| `min_length` | `"0.0 nm"` | Vectors shorter than this after scaling are skipped. |
| `max_length` | `None` | If set, normalize so the longest vector equals this value. |
| `color_by` | `None` | `"norm"` — color by vector magnitude; `"component"` — color by a single axis. |
| `palette` | `None` | Color palette name or Matplotlib colormap for continuous coloring. |
| `color_component` | `2` | Axis index (0/1/2) used when `color_by="component"`. |
| `radius_scale` | `0.05` | Arrow shaft radius relative to final length. |
| `tag` | auto | Tag for selective clear/hide. |
| `layer_tag` | `None` | Group tag for batch visibility control. |

## Coloring by norm

```python
view.shapes.add_displacement_vectors(
    origins=origins,
    vectors=vectors,
    color_by="norm",
    palette="RdBu",     # diverging Matplotlib colormap
    tag="colored-arrows",
)
```

## Clearing

```python
view.shapes.clear(tag="mode-arrows")   # remove one set
view.shapes.clear()                     # remove all shapes
```

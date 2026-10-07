(User_Overlays_Shapes_Links)=
# Links (networks)

Links render cylinders connecting pairs of points or atoms — useful for
interaction networks, hydrogen-bond graphs, or custom connectivity overlays.

## Minimal example — atom pairs

```python
import molsysviewer as mv

view = mv.demo["tctim"]
view

# Connect atom 10 to atom 42, and atom 55 to atom 78
view.shapes.add_links(
    atom_pairs=[[10, 42], [55, 78]],
    color=0x4499ff,
    tag="hbond-network",
)
```

## Explicit coordinate pairs

```python
# Provide start/end coordinates directly (Å)
pairs = [
    [[0, 0, 0], [5, 0, 0]],
    [[5, 0, 0], [5, 5, 0]],
]
view.shapes.add_links(
    coordinate_pairs=pairs,
    radius="0.15 nm",
    color=0xff8800,
    alpha=0.7,
    tag="custom-links",
)
```

## Per-link colors and radii

```python
view.shapes.add_links(
    atom_pairs=[[10, 42], [55, 78], [100, 130]],
    color=[0xff0000, 0x00ff00, 0x0000ff],
    radius=["0.1 nm", "0.2 nm", "0.15 nm"],
    tag="colored-links",
)
```

## Key options

| Parameter | Default | Description |
|---|---|---|
| `atom_pairs` | `None` | List of `[i, j]` atom-index pairs. Uses current structure coordinates. |
| `coordinate_pairs` | `None` | List of `[[x1,y1,z1], [x2,y2,z2]]` explicit pairs (Å). |
| `structure_coordinate_pairs` | `None` | Per-structure coordinate pairs for trajectory-aware links. |
| `radius` | `"0.2 nm"` | Cylinder radius (scalar or one per link). |
| `color` | `0x4499ff` | Hex color (scalar or one per link). |
| `alpha` | `1.0` | Global transparency (0–1). |
| `color_by` | `None` | `"link"`, `"pocket"`, or `"chain"` for categorical coloring. |
| `tag` | auto | Tag for selective clear/hide. |
| `layer_tag` | `None` | Group tag for batch visibility control. |

## Trajectory-aware links

Links update automatically when the trajectory frame changes:

```python
# structure_coordinate_pairs[i] = coordinate pairs for structure i, or None to hide
view.shapes.add_links(
    structure_coordinate_pairs=[pairs_frame0, pairs_frame1, None, ...],
    tag="dynamic-links",
)
```

## Clearing

```python
view.shapes.clear(tag="hbond-network")
view.shapes.clear()
```

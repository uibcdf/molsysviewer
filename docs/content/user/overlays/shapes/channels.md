# Channels (tubes)

Channel tubes render a smoothed pathway through a set of ordered centers and
radii. The typical use-case is visualizing an ion channel, a ligand tunnel, or
any other route computed by a topology tool.

## Quick start

```python
from molsysviewer import demo

view = demo["1TCD"]
view.styles.apply(tag="polymer-cartoon")

centers = [(10.0, 5.0, 0.0), (12.0, 5.5, 0.5),
           (14.0, 6.0, 1.2), (16.0, 6.5, 2.0)]
radii   = [1.8, 1.5, 1.4, 1.6]

layer = view.shapes.add_channel_tube(
    centers=centers,
    radii=radii,
    color_mode="distance",
    alpha=0.7,
    tag="tunnel-A",
)
view
```

## API

```python
layer = view.shapes.add_channel_tube(
    centers=centers,               # ordered (x, y, z) list in Å
    radii=radii,                   # radius at each center in Å
    color_mode="distance",         # "distance", "segment", or None
    colors=None,                   # hex int per center — overrides color_mode
    color_map=None,                # palette (list of hex ints or named string)
    solvent_distances=None,        # float per center — used by some color modes
    radial_segments=8,             # tube cross-section resolution
    smoothing_subdivisions=3,      # smoothing passes
    alpha=0.8,
    tag="my-channel",
    layer_tag="channels",
    name=None,
)
```

`centers` and `radii` must have at least two entries and the same length.

## Color modes

| `color_mode` | What drives the color |
|---|---|
| `"distance"` | distance along the tube centerline |
| `"segment"` | each center–center segment gets a distinct hue |
| `None` | single flat color from `colors[0]` or palette default |

Combine `color_mode` with `color_map` for custom palettes:

```python
layer = view.shapes.add_channel_tube(
    centers=centers,
    radii=radii,
    color_mode="distance",
    color_map=[0x0066ff, 0x00ccff, 0xffffff],
    tag="gradient-tube",
)
```

## Per-center colors

Override the color scheme entirely with one hex integer per center:

```python
layer = view.shapes.add_channel_tube(
    centers=centers,
    radii=radii,
    colors=[0xff0000, 0xff8800, 0xffff00, 0x00ff00],
    tag="manual-colors",
)
```

## Layer visibility

```python
layer.hide()
layer.show()
layer.delete()
```

## Trajectory-aware placement

Pass per-structure coordinate arrays so the tube tracks atom positions across
trajectory frames:

```python
# structure_centers: one list-of-(x,y,z) per structure; None = hidden for that frame
layer = view.shapes.add_channel_tube(
    centers=centers,
    radii=radii,
    structure_centers=[frame0_centers, frame1_centers, None, ...],
    tag="traj-channel",
)
```

## Cookbook

- {doc}`../../../cookbook/channel_tube` — full workflow with TopoMT route data.

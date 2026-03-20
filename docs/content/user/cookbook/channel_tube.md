# Channel tube

Goal
- Sweep ordered alpha-sphere centers/radii into a tube.
- Color by segment or solvent distance; apply spline smoothing.

Code sketch

```python
import molsysviewer as viewer

centers = [(0,0,0), (2,0.5,0.2), (4,1,0.5), (6,1.5,1.0)]
radii   = [1.2, 1.0, 0.9, 1.1]

v = viewer.MolSysView()
v.show()
v.shapes.add_channel_tube(
    centers=centers,
    radii=radii,
    color_mode="segment",  # or "distance"
    smoothing=0.5,
    tag="channel-demo",
)
v.export.html("_static/views/channel_tube.html")
```

What to tweak
- `color_mode`: `"segment"` uses per-segment colors; `"distance"` uses solvent distances if provided.
- `solvent_distances` or `colors`/`color_map` to drive coloring.
- `smoothing_subdivisions`: increase to smooth the spline sweep.
- `radial_segments`: increase for a rounder tube.
- `alpha`: overall transparency.
- `tag`: group channels for selective clear.

Embed the exported view

```python
from molsysviewer.thirds.jupyter import load_html_in_notebook
load_html_in_notebook("_static/views/channel_tube.html")
```

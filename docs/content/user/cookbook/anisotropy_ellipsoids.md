# Anisotropy ellipsoids/disks

Goal
- Visualize anisotropy from eigenvalues/eigenvectors or tensors.
- Clamp eccentricity and color by anisotropy or custom map.

Code sketch

```python
import molsysviewer as mv

v = mv.MolSysView()
v.show()
v.shapes.add_anisotropy_ellipsoids(
    centers=[(0,0,0), (3,0,0)],
    eigenvalues=[[3,2,1],[2,1.5,0.8]],
    eigenvectors=[
        [[1,0,0],[0,1,0],[0,0,1]],
        [[0,1,0],[0,0,1],[1,0,0]],
    ],
    scale=1.0,
    max_eccentricity=5.0,
    color_mode="anisotropy",
    tag="ellipsoid-demo",
)
v.write_html("_static/views/anisotropy_ellipsoids.html")
```

What to tweak
- Provide either `eigenvalues` + `eigenvectors`, or `tensors`, or `principal_directions` (disks).
- `scale`: global scaling of axes.
- `max_eccentricity`: clamp to avoid extreme shapes.
- `color_mode`: `"anisotropy"` (default) or a custom color map via `color_map`/`colors`.
- `values`: optional per-center scalar to drive coloring.
- `alpha`: transparency for the glyphs.

Embed the exported view

```python
from molsysviewer.thirds.jupyter import load_html_in_notebook
load_html_in_notebook("_static/views/anisotropy_ellipsoids.html")
```

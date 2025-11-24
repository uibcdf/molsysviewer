# Pocket surface from alpha-spheres

Goal
- Build a Gaussian pocket surface from alpha-sphere centers/radii.
- Show multiple iso levels with distinct colors/alphas.
- Export a static view for the docs.

Code sketch

```python
import molsysviewer as mv

centers = [(0,0,0), (3,0,0), (1.5,2,0)]
radii = [2.0, 1.8, 1.2]

v = mv.MolSysView()
v.show()
v.shapes.add_pocket_surface(
    atom_indices=[0],  # placeholder; replace with real atom indices for clipping/position
    iso_levels=[0.08, 0.15],
    iso_colors=[0x44CCFF, 0x003366],
    grid={"resolution": 1.0, "smoothness": 1.0},
    tag="pocket-surface",
)
v.write_html("_static/views/pocket_surface.html")
```

What to tweak
- `atom_indices`: real atom ids defining the pocket region; used for positioning/clipping.
- `grid`: `resolution`, `smoothness`, `radius_offset` control the Gaussian field.
- `iso_levels`/`iso_colors`/`iso_alphas`: multiple surfaces from one field.
- `clip_plane` or `mouth_atom_indices` if you need clipping at openings.
- `tag`: group related shapes for selective clear.

Embed the exported view

```python
from molsysviewer.thirds import load_html_in_jupyter_notebook
load_html_in_jupyter_notebook("_static/views/pocket_surface.html")
```

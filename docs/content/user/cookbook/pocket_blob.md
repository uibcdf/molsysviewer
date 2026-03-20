# Pocket blob (Gaussian field)

Goal
- Generate a volumetric blob from alpha-spheres with custom iso thresholds and smoothing.
- Support multiple iso levels/colors/alphas.

Code sketch

```python
import molsysviewer as viewer

v = viewer.MolSysView()
v.show()
v.shapes.add_pocket_blob(
    centers=[(0,0,0), (3,0,0), (1.5,2,0)],
    radii=[2.0, 1.8, 1.2],
    iso_levels=[0.08, 0.15],
    iso_colors=[0x44CCFF, 0x003366],
    iso_alphas=[0.35, 0.5],
    smoothing=1.0,
    tag="pocket-blob",
)
v.export.html("_static/views/pocket_blob.html")
```

What to tweak
- `smoothing`: higher → smoother field, lower → sharper.
- `iso_levels`/`iso_colors`/`iso_alphas`: multiple surfaces from one field.
- `radius_scale`: scale radii before computing the field.
- `color_map` and `values`: color per center via a numeric property.
- `tag`: group blobs for selective clear.

Embed the exported view

```python
from molsysviewer.thirds.jupyter import load_html_in_notebook
load_html_in_notebook("_static/views/pocket_blob.html")
```

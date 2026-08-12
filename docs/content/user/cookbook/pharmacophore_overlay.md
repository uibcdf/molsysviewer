# Pharmacophore overlay

Goal
- Render pharmacophore glyphs with standard colors/transparency.
- Combine with pockets or channels in the same scene.

Code sketch

```python
import molsysviewer as msv

v = msv.MolSysView()
v.show()
v.shapes.add_interaction_sites(
    centers=[(0,0,0), (3,0,0), (6,0,0)],
    kinds=["aromatic", "hydrophobic", "hbond_acceptor"],
    alphas=[0.5, 0.4, 0.6],
    tag="ph4-demo",
)
v.export.html("_static/views/pharmacophore_overlay.html")
```

What to tweak
- `radii`: glyph size (single value or per feature).
- `directions`: optional for arrows/disks; one per feature if needed.
- `colors`: override standard palette; otherwise defaults per kind.
- `alphas`: transparency per feature or a single float.
- Combine with pockets or channels in the same scene using tags.

Embed the exported view

```python
from molsysviewer.thirds.jupyter import load_html_in_notebook
load_html_in_notebook("_static/views/pharmacophore_overlay.html")
```

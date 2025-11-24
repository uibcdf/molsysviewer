# Pharmacophore overlays

Planned content:
- Render pharmacophore glyphs with standard colors and transparency.
- Combine with pockets or channels in the same scene.
- Export a static view: `MolSysView.write_html("_static/views/pharmacophore.html")`.
- Embed in this page:

```python
from molsysviewer.thirds import load_html_in_jupyter_notebook
load_html_in_jupyter_notebook("_static/views/pharmacophore.html")
```

Interactive preview (static export):

<iframe src="_static/views/pharmacophore.html" width="100%" height="360px"></iframe>

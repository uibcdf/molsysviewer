# Pockets & blobs

Planned content:
- Build Gaussian pocket surfaces from alpha-spheres with multi-iso and color maps.
- Pocket blobs with iso thresholds and smoothing.
- Export a static view: `MolSysView.write_html("_static/views/pockets.html")`.
- Embed in this page:

```python
from molsysviewer.thirds import load_html_in_jupyter_notebook
load_html_in_jupyter_notebook("_static/views/pockets.html")
```

Interactive preview (static export):

<iframe src="_static/views/pockets.html" width="100%" height="360px"></iframe>

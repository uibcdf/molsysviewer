# Channels & tubes

Planned content:
- Sweep ordered alpha-sphere centers into a channel tube with spline smoothing.
- Color by segment or solvent distance.
- Export a static view: `MolSysView.write_html("_static/views/channels.html")`.
- Embed in this page:

```python
from molsysviewer.thirds import load_html_in_jupyter_notebook
load_html_in_jupyter_notebook("_static/views/channels.html")
```

Interactive preview (static export):

<iframe src="_static/views/channels.html" width="100%" height="360px"></iframe>

# Quickstart

Outline for the minimal demo:
- Load a small PDB string with `MolSysView.load_pdb_string`.
- Add a sphere or alpha-sphere set.
- Clear by tag.
- Export the scene with `MolSysView.write_html("_static/views/quickstart.html")`.
- Embed it here with:

```python
from molsysviewer.thirds import load_html_in_jupyter_notebook
load_html_in_jupyter_notebook("_static/views/quickstart.html")
```

Interactive preview (static export):

<iframe src="_static/views/quickstart.html" width="100%" height="360px"></iframe>

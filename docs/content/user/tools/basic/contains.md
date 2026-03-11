# `contains`

`molsysviewer.tools.basic.contains(view, ...)` lets you ask quick composition/presence questions about a viewer.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
tools.basic.contains(view, peptides=True)
```

Use it for inspection-style checks while staying in the MolSysViewer surface.

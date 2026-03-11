# `is_composed_of`

`molsysviewer.tools.basic.is_composed_of(view, ...)` lets you ask whether a selected part of a view is composed exclusively of certain classes/counts.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
tools.basic.is_composed_of(view, n_molecules=1, n_peptides=1)
```

This is useful in inspection workflows where you want composition checks directly on the loaded viewer.

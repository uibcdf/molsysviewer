# `select`

`molsysviewer.tools.basic.select(view, ...)` is the functional counterpart of `view.select(...)`.

Use it when you prefer a MolSysMT-like call style while working directly with a `MolSysView`.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
atom_indices = tools.basic.select(view, selection="group_index==0")
```

This does not create a new viewer. It returns the selected indices.

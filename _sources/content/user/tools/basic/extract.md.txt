# `extract`

`molsysviewer.tools.basic.extract(view, ...)` builds a **new** `MolSysView` from a subset of another view.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
subset = tools.basic.extract(view, selection="group_index==0")
subset
```

Use it when you want to spin off a focused inspection view without mutating the original one.

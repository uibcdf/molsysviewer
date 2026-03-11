# `remove`

`molsysviewer.tools.basic.remove(view, ...)` is the functional counterpart of `view.remove(...)`.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
tools.basic.remove(view, selection=[0, 1, 2])
```

This is a **live** operation. The current view is rebuilt and region/shape state is reconciled.

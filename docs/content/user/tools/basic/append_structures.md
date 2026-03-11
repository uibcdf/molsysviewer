# `append_structures`

`molsysviewer.tools.basic.append_structures(view, from_molecular_system, ...)` is the functional counterpart of `view.append_structures(...)`.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
tools.basic.append_structures(view, demo["dialanine"].molsys)
```

This is a **live** operation that appends structures/frames to the current view.

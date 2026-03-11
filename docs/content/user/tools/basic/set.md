# `set`

`molsysviewer.tools.basic.set(view, ...)` is the functional counterpart of `view.set(...)`.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
tools.basic.set(view, element="group", selection=[0], group_name="ACE2")
```

This is a **live** operation: it mutates the loaded system and refreshes the viewer state.

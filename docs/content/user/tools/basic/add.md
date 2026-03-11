# `add`

`molsysviewer.tools.basic.add(view, from_molecular_system, ...)` is the functional counterpart of `view.add(...)`.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
tools.basic.add(view, demo["dialanine"].molsys)
```

Use it to extend an existing view with atoms/elements from another molecular system.

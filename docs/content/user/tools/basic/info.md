# `info`

`molsysviewer.tools.basic.info(view, ...)` is the functional counterpart of `view.info(...)`.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
tools.basic.info(view, element="group", selection=[0, 1, 2])
```

It returns the same styled summary table that you would get from the method form.

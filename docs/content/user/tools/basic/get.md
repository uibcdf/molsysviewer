# `get`

`molsysviewer.tools.basic.get(view, ...)` is the functional counterpart of `view.get(...)`.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
n_atoms = tools.basic.get(view, element="system", n_atoms=True)
```

Use it when you want MolSysMT-style attribute queries directly on a `MolSysView`.

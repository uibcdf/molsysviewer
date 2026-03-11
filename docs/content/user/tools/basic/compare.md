# `compare`

`molsysviewer.tools.basic.compare(view_a, view_b, ...)` compares the **loaded molecular systems** of two views.

It does **not** currently compare visual scene state such as:

- regions,
- layers,
- shapes,
- camera,
- or visibility masks.

```python
from molsysviewer import demo, tools

view_a = demo["dialanine"]
view_b = demo["dialanine"]

tools.basic.compare(view_a, view_b)
```

This follows the semantics of `molsysmt.compare(...)`, but applied to the molecular systems held by `MolSysView`.

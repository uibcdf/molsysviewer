# `copy`

`molsysviewer.tools.basic.copy(view)` returns an independent copy of a viewer.

Current contract:

- it copies the loaded molecular system,
- and it also recreates useful scene state:
  - whole representation and colour scheme,
  - whole visibility state,
  - regions,
  - layers,
  - shapes,
  - atom visibility,
  - controls configuration,
  - last camera snapshot.

```python
from molsysviewer import demo, tools

view = demo["dialanine"]
clone = tools.basic.copy(view)
```

Use it when you want to branch an inspection workflow without mutating the original view.

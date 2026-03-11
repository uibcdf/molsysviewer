# `concatenate_structures`

`molsysviewer.tools.basic.concatenate_structures(...)` builds a new view by concatenating the **structure axis** of multiple compatible inputs.

Use it when:

- the topology is the same,
- you want more structures/frames in one viewer,
- and you do **not** want to mutate an existing view in place.

## Minimal example

```python
from molsysviewer import demo, tools

view_a = demo["dialanine"]
view_b = demo["dialanine"]

result = tools.basic.concatenate_structures([view_a, view_b])
result
```

The resulting viewer contains the topology of the first input and the structures from both inputs.

## Notes

- Inputs may be `MolSysView` objects or MolSysMT-compatible molecular systems.
- This is a pure operation: it returns a new viewer.
- It delegates structural concatenation to `molsysmt.concatenate_structures(...)`.

## When not to use it

Do not use `concatenate_structures(...)` when you want to combine different systems into one larger topology. For that case, use {doc}`merge`.

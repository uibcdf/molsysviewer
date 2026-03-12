# Labels

Labels are text annotations you add on top of the scene.

The first label slice is intentionally narrow:

- labels are persistent,
- they are anchored to one `group`,
- they belong to `annotations`, not `shapes`,
- and they are controlled through `layers`.

## Add a label to one group

```python
from molsysviewer import demo

view = demo["dialanine"]
view.annotations.add_label(
    text="N-terminus",
    group_index=0,
    tag="notes",
)
view
```

## Layers and cleanup

Labels participate in normal layer semantics:

```python
view.layers["notes"].hide()
view.layers["notes"].show()
```

You can also clear all labels without touching the molecular system:

```python
view.clear_decorations(shapes=False, styles=False, labels=True)
```

## Current limits

The current implementation does not yet cover:

- atom-attached labels,
- free point labels,
- shape-attached labels,
- or rich label editing.

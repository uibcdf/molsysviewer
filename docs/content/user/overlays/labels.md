# Labels

Labels are persistent text annotations anchored to atoms in the scene.
They belong to `annotations`, not `shapes`, and are controlled through `layers`.

## Add a label

Use `add_annotation()` to attach a label to any set of atoms.
The anchor position is the geometric centroid of the selected atoms.

```python
from molsysviewer import demo

view = demo["dialanine"]
view.annotations.add_annotation(
    text="N-terminus",
    selection="group_index==0",
    tag="n-term-label",
)
view
```

You can also pass explicit atom indices:

```python
view.annotations.add_annotation(
    text="Catalytic site",
    atom_indices=[4, 5, 6, 7, 8],
    tag="site-label",
)
```

## Label style

Control color and size with `label_style`:

```python
view.annotations.add_annotation(
    text="Active site",
    selection="group_index==3",
    tag="active-label",
    label_style={"color": "#ff4444", "size_em": 1.4},
)
```

Supported keys: `color` (CSS hex string), `size_em` (float, default 1.0).

## Multi-group labels

`selection` (or `atom_indices`) can span multiple residues — the anchor
will be placed at their centroid:

```python
view.annotations.add_annotation(
    text="Backbone",
    selection="group_index in [0, 1, 2]",
    tag="backbone-label",
)
```

## Label from active canvas selection

After clicking one or more residues on the canvas, add a label at that selection:

```python
view.annotations.add_label_from_active_selection(
    text="Selected residues",
    label_style={"color": "#40c0e0", "size_em": 1.2},
)
```

This is the same operation exposed by **Add Label** in the canvas context menu,
which additionally provides a color picker and size slider in the inline composer.

## Layers and cleanup

Labels participate in normal layer semantics:

```python
view.annotations.hide("n-term-label")
view.annotations.show("n-term-label")
view.annotations.delete("n-term-label")

# Clear all labels at once
view.annotations.clear()
```

Or via the layer directly:

```python
view.layers["n-term-label"].hide()
```

## Update text or anchor

```python
view.annotations.set_text("n-term-label", "New text")
view.annotations.set_anchor("n-term-label", selection="group_index==1")
```

## Inspect annotations

```python
view.annotations.info()          # list of all annotation summaries
view.annotations.info("n-term-label")  # single annotation
view.annotations.tags()          # list of active tags
```

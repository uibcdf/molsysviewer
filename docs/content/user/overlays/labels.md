# Labels

Labels are persistent text annotations anchored to atoms or an absolute coordinate.
They belong to `annotations`, not `shapes`, and are controlled through `layers`.

## Add a label

Use `add()` to attach a label to any set of atoms.
The anchor position is the geometric centroid of the selected atoms.

```python
from molsysviewer import demo

view = demo["dialanine"]
view.annotations.add(
    text="N-terminus",
    selection="group_index==0",
    tag="n-term-label",
)
view
```

You can also pass explicit atom indices:

```python
view.annotations.add(
    text="Catalytic site",
    atom_indices=[4, 5, 6, 7, 8],
    tag="site-label",
)
```

## Label style

Control color and size with `label_style`:

```python
view.annotations.add(
    text="Active site",
    selection="group_index==1",
    tag="active-label",
    label_style={"color": "#ff4444", "size_em": 1.4},
)
```

Supported keys: `color` (CSS hex string), `size_em` (float, default 1.0).

## Multi-group labels

`selection` (or `atom_indices`) can span multiple residues — the anchor
will be placed at their centroid:

```python
view.annotations.add(
    text="Backbone",
    selection="group_index in [0, 1]",
    tag="backbone-label",
)
```

## Label from active canvas selection

After clicking one or more residues on the canvas, add a label at that selection.
You can also set the active atoms from Python:

```python
view.active_selection.set([0, 1])
view.annotations.add_label_from_active_selection(
    text="Selected residues",
    label_style={"color": "#40c0e0", "size_em": 1.2},
)
```

This is the same operation exposed by **Add Label** in the canvas context menu,
which additionally provides a color picker and size slider in the inline composer.

## Anchoring to a coordinate

Use an absolute coordinate for a marker that stays fixed while atoms move.
Supply explicit length units for positions and world offsets:

```python
import pyunitwizard as puw

note = view.annotations.add(
    "Reference point",
    position=puw.quantity([1, 2, 3], "nm"),
    offset_mode="world",
    offset=puw.quantity([2, 0, 0], "angstrom"),
    leader_line=True,
    leader_line_style="dotted",
    tag="reference-label",
)
note.set_coordinates(puw.quantity([4, 5, 6], "angstrom"))
```

Legacy bare triples mean nm for positions and world offsets, independently of
your session's standard units. With `offset_mode="camera"`, offsets instead
use dimensionless renderer units along camera right, up and toward the viewer.
World offsets stay fixed when the camera rotates. Leaders accept `solid`,
`dashed` and `dotted` styles.

You can switch between anchor kinds without recreating the annotation:

```python
view.annotations.set_anchor("reference-label", atom_indices=[0, 1])
view.annotations.set_anchor(
    "reference-label", position=puw.quantity([1, 2, 3], "nm"),
)
```

Text/style edits, hiding, undo/redo, state/session saving, copying and extraction
preserve coordinate anchors. Coordinates in exported state carry explicit
angstrom units. Coordinate anchors stay at their absolute position across frames;
atom anchors follow their participants.

## Showing and hiding

Labels participate in normal layer semantics:

```python
view.annotations.hide("n-term-label")
view.annotations.show("n-term-label")
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

## Cleaning up

Delete one annotation or clear all labels:

```python
view.annotations.delete("n-term-label")
view.annotations.clear()
```

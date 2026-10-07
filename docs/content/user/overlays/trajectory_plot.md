# Trajectory plot

The trajectory plot is a 2D overlay linked to the trajectory: you push one or
more per-frame scalar series and the viewer draws them with a playhead marker
that stays synced to the structure on screen. Clicking a point in the plot moves
the molecular system to that frame.

It is a generic viewer primitive with no add-on dependency, so anything you can
compute per frame works: an end-to-end distance, RMSD, radius of gyration, a
channel bottleneck radius, an energy term.

## A first plot

Any per-frame series will do. This one measures how stretched the peptide is at
each frame — the distance between its two end atoms:

```python
import numpy as np
import molsysmt as msm
import pyunitwizard as puw
from molsysviewer import demo

view = demo["pentalanine"]      # 5000 structures

xyz = np.asarray(puw.get_value(
    msm.get(view.molsys, element="atom", structure_indices="all", coordinates=True)
))
end_to_end = np.linalg.norm(xyz[:, 0, :] - xyz[:, -1, :], axis=1)

view.trajectory_plot.show(end_to_end, y_label="end-to-end (nm)", title="Pentalanine")
view
```

Play the trajectory and the playhead follows along:

```python
view.play(fps=30, mode="loop")
```

## Several series at once

Pass a mapping to label each series, or a 2D array for unlabelled ones:

```python
centroid = xyz.mean(axis=1, keepdims=True)
radius_of_gyration = np.sqrt(((xyz - centroid) ** 2).sum(axis=2).mean(axis=1))

view.trajectory_plot.show(
    {"end-to-end": end_to_end, "Rg": radius_of_gyration},
    colors="okabe_ito",     # colour-vision-deficiency safe palette
    y_label="nm",
)
```

Series must all have one value per frame. NumPy arrays, plain lists and mappings
of either are accepted.

## Marking events

Use `events` to draw vertical markers at specific frames:

```python
view.trajectory_plot.show(
    end_to_end,
    events=[{"frame": 1200, "label": "unfolds"}, {"frame": 3800, "label": "refolds"}],
    y_label="end-to-end (nm)",
)
```

## Custom x axis

By default the x axis is the frame index. Pass `x` to use physical time instead:

```python
time_ps = np.arange(len(end_to_end)) * 0.2      # 0.2 ps per frame

view.trajectory_plot.show(end_to_end, x=time_ps, x_label="time (ps)", y_label="end-to-end (nm)")
```

The supplied numeric `x` values determine the horizontal positions of samples,
event markers and the playhead. Uneven spacing, reversed order and repeated
values preserve the order of the loaded structures. Clicking chooses the
nearest sample; ties keep the current structure if it is among the nearest,
otherwise they choose the earliest matching structure in the loaded order.

For example, these supplied dimensionless scores belong to three structures
loaded from nonconsecutive source indices:

```python
import molsysviewer as msv

view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 2, 8])
view.trajectory_plot.show(
    [0.1, 0.4, 0.9],
    x=[0, 2, 8],
    x_label="source structure index",
    y_label="score",
    events=[{"frame": 1, "label": "second loaded structure"}],
)
```

Event `frame` values and click results use the local loaded order: the marker
above belongs to local frame 1, displayed at `x=2`. Each series and `x` must
contain one finite value per loaded structure. NaN and positive or negative
infinity are refused before changing the plot or importing scene state.

## Hide and clear

Use a different `tag` for each card you want to keep. For example, these two
dimensionless score series belong to the same three loaded structures:

```python
import molsysviewer as msv

view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 2, 8])
view.trajectory_plot.show([0.1, 0.4, 0.9], tag="score_a", title="Score A")
view.trajectory_plot.show([0.8, 0.5, 0.2], tag="score_b", title="Score B")

view.trajectory_plot.hide("score_a")   # Score B stays visible
view.trajectory_plot.show(tag="score_a")  # restore its retained data
view.trajectory_plot.clear("score_b")  # remove only Score B
```

Closing a card in the canvas also hides it and retains its data. Restore it with
`show(tag=...)`. After `clear(tag)`, supply a new series to create that card again.
`records()` returns detached records of all retained cards, including hidden ones;
editing these records does not change the plots.

Without a tag, `hide()` and `clear()` affect every card:

```python
view.trajectory_plot.hide()      # retain every card's data, hide all cards
view.trajectory_plot.show(tag="score_a")  # restore one retained card
view.trajectory_plot.clear()     # remove every card and its data
```

`update()` is an alias of `show()`: supplying a new series replaces the card
with that tag and leaves other tags unchanged.

## Keeping plots with the system

Cards and their visibility survive scene-state and session saving, copying a
view and extracting structures. Extraction keeps values and `x` in the selected
local order, including repeated structures, and remaps event markers to that
order.

Clear the cards before appending structures or applying a system edit that
changes the number of loaded structures. Hidden cards still retain a series
for the original structure axis, so hiding them does not remove this check.
Plot data is supplied by you and is not recalculated after coordinate edits.
Keeping cards when replacing a system with the same structure count declares
that their values still correspond to its local structure order.

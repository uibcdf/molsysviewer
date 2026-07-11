(User_Cookbook_Workbench_Scientific_Workflow)=
# Navigate, annotate, measure, and export

This tutorial shows how to use the Navigate and Workbench panels together
with Python to build an annotated, measured view of a molecular structure.

The key idea is that **the Python API and the workbench panels are two views
of the same reproducible state**:

- what you create from Python appears immediately in the panels
- what you see in the panels reflects the current Python-accessible state
- everything you build survives an HTML export

## Goal

You will:

1. open a viewer and explore the structure through the Navigate panel
2. create two regions to differentiate structural parts
3. add persistent annotations on specific residues
4. measure a backbone bond distance
5. inspect the collected state from Python and from the Workbench panel
6. export the annotated view as a self-contained HTML file

## 1. Open the viewer and the Navigate panel

```python
from molsysviewer import demo

view = demo["dialanine"]
view.set_panel_mode(panel="navigate", expanded=True)
view
```

The Navigate panel opens on the right side of the canvas.
The **GroupStrip** shows a horizontal lane of residue groups along chain A
(here: ACE, ALA, NME).

Click any group cell to focus the camera on that residue.
Hover over a cell to see the residue name and index in a tooltip.

## 2. Create two regions

Regions let you apply different representations to different parts of the
structure.
Here we isolate the central ALA residue and leave the rest as-is:

```python
# Atom indices for the ALA residue (group_index 1 in dialanine)
ala_atoms = list(view.select(selection="group_index==1"))

# ALA residue: ball-and-stick to highlight it
region_ala = view.regions.add(
    atom_indices=ala_atoms,
    tag="ala",
    representation="ball_and_stick",
)

# Everything else: sticks
region_caps = view.regions.add(
    complement_of_regions="ala",
    tag="caps",
    representation="sticks",
)
```

The two regions appear in the scene immediately.
No panel interaction is needed — regions are Python-first.

## 3. Add persistent annotations

Add a label on the ACE cap (N-terminal side):

```python
ace_atoms = list(view.select(selection="group_index==0"))
view.annotations.add_annotation(
    text="ACE cap",
    atom_indices=ace_atoms,
    tag="label_ace",
    label_style={"color": "#E04060", "background": True, "background_opacity": 0.6},
)
```

Add a label on the ALA residue itself:

```python
view.annotations.add_annotation(
    text="Ala",
    atom_indices=ala_atoms,
    tag="label_ala",
    label_style={"color": "#4080E0", "background": True, "background_opacity": 0.6},
)
```

After both calls, look at the Navigate panel.
Each annotated residue now shows a small **L** badge on its GroupStrip cell.
That badge confirms the annotation is anchored to those atoms and registered
in the workbench.

## 4. Measure a backbone bond

Add a distance measurement between the backbone nitrogen and alpha-carbon
of the ALA residue:

```python
n_atom  = list(view.select(selection="group_index==1 and atom_name=='N'"))
ca_atom = list(view.select(selection="group_index==1 and atom_name=='CA'"))

dist = view.measurements.add_distance(
    selection_a=n_atom,
    selection_b=ca_atom,
    tag="n_ca",
    measurement_style={"color": "#40B060"},
)
```

A dotted line between the two atoms appears in the canvas.
The value is the N–Cα bond length in the current conformation.

## 5. Inspect the workbench state

Switch to the Workbench panel:

```python
view.set_panel_mode(panel="workbench", expanded=True)
```

Navigate to the **Annotations** section — both labels are listed with their
tags, text, and anchoring atoms.
Navigate to the **Measurements** section — the distance measurement is listed
with its current value.

The same state is accessible from Python at any time, without touching the UI:

```python
view.annotations.records()
```

```python
view.measurements.records()
```

Both return the same information as the workbench sections, confirming that
the panel and the Python state are always synchronized.

## 6. Export the annotated view

All the regions, labels, and measurements you created are part of the
reproducible message history.
Export them to a self-contained HTML file:

```python
view.export.html("dialanine_annotated.html", title="Annotated dialanine")
```

Open that file in any browser — it replays the full sequence:
load → regions → annotations → measurement → camera — with no running
Jupyter session required.

## Why this workflow matters

Annotations and measurements created this way are not ephemeral overlays.
They are:

- **replay-safe**: stored in the message history and replayed by any export
- **rebuild-safe**: atom indices are remapped correctly after MolSysMT-addon
  live edits or loader sugar such as `view.load(..., mode="append_structures")`
- **panel-visible**: immediately reflected in Navigate GroupStrip badges and
  Workbench panel sections

This means you can hand an exported HTML to a colleague and they will see
exactly what you built, with no dependency on the original notebook.

## API surfaces used

- `view.set_panel_mode(panel=...)`
- `view.select(selection=...)`
- `view.regions.add(atom_indices=..., tag=..., representation=...)`
- `view.regions.add(complement_of_regions=..., tag=..., representation=...)`
- `view.annotations.add_annotation(text=..., atom_indices=..., tag=..., label_style=...)`
- `view.measurements.add_distance(selection_a=..., selection_b=..., tag=...)`
- `view.annotations.records()`
- `view.measurements.records()`
- `view.export.html(...)`

## See also

- {doc}`../viewer/panel_mode`
- {doc}`../scene_management/regions`
- {doc}`../overlays/labels`
- {doc}`figure_export_workbench`

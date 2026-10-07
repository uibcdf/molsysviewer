# Measurements

A measurement draws a distance, angle or dihedral between points in the scene and reports
its value. It is an overlay: it has a tag, it can be hidden and deleted, and it belongs to
a layer.

For a worked example inside a full workflow, see
{doc}`../cookbook/workbench_scientific_workflow`.

## Adding one

Each endpoint is a selection. A distance takes two, an angle three, a dihedral four:

```python
import molsysviewer as msv

view = msv.demo["1TCD"]

view.measurements.add_distance(
    selection_a="atom_index==[0]",
    selection_b="atom_index==[10]",
    tag="d1",
)
```

```python
view.measurements.add_angle(
    selection_a="atom_index==[0]",
    selection_b="atom_index==[10]",
    selection_c="atom_index==[20]",
    tag="a1",
)
```

If you already have the indices, pass `atom_indices_a=[…]` instead of a selection
expression. The two forms are interchangeable and you can mix them between endpoints.

## When an endpoint is more than one atom

A selection that resolves to several atoms is not an error. What happens then is the
**endpoint policy**: it decides which single point the endpoint stands for.

```python
view.measurements.set_endpoint_policy("centroid")
```

Set it per measurement with `endpoint_policy=`, or change the default for the view as
above. `set_representative_atom` refines it per molecule class — `protein`, `nucleic`, `lipid` or
`other` — for example making every protein group measure from its `CA`:

```python
view.measurements.set_representative_atom(target="protein", atom_name="CA")
```

This is the part worth getting right before you read numbers off a picture. A distance
between two residues means nothing until you have said which atoms it runs between.

## Reading the values

```python
view.measurements.info("d1")
view.measurements.records()
```

`info` gives one measurement in full, including the atoms each endpoint resolved to and
whether it is `broken` — a measurement whose endpoints no longer exist after an edit says
so rather than reporting a stale number.

For a trajectory, `series` gives the value per structure:

```python
view.measurements.series("d1")
```

## Managing

```python
view.measurements.tags()
view.measurements.count()

view.measurements.hide("d1")
view.measurements.show("d1")
view.measurements.set_tag("d1", "catalytic-pair")
view.measurements.delete("catalytic-pair")
view.measurements.clear()
```

`view.measurements.settings()` reports the current endpoint policy and representative
atoms, which is what you want when a value looks wrong and you are not sure which
convention produced it.

## What survives a save

Measurements are part of `view.export_state()`, with their endpoint selections rather than
resolved indices, so they come back with {doc}`../export/state` on a compatible structure.
The endpoint policy and representative atoms travel with them.

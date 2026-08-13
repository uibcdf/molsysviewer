# Selections

A selection is a **set of atoms you have named**. It changes nothing on screen by itself:
it is what you point other operations at.

That is the difference from a region. A region is drawn — it has a representation, a
colour, and a visibility. A selection is only the set. Use a selection when you want to
keep a group of atoms to reuse; turn it into a region when you want to *see* it
differently.

## The active selection

There is exactly one active selection per view. It is what clicking in the canvas fills,
and what the panels act on.

```python
import molsysviewer as msv

view = msv.demo["1TCD"]
view.active_selection.set('molecule_type=="protein" and group_index<5')

view.active_selection.is_empty()
```

`set` takes a MolSysMT selection expression, so anything you can write for
`view.select(...)` works here. It replaces whatever was active; `clear()` empties it.

## Keeping one

The active selection is transient — the next click replaces it. `save` gives it a tag and
puts it in `view.selections`:

```python
view.active_selection.set('molecule_type=="protein" and group_index<5')
view.active_selection.save(tag="core")

view.selections.tags()
```

You can also store one without going through the active selection:

```python
view.selections.add_selection(tag="waters", selection='molecule_type=="water"')
```

## Using one

A stored selection is an object with its own operations:

```python
selection = view.selections["core"]

selection.activate()                 # make it the active selection again
selection.focus()                    # move the camera to it
```

`add_label` is available too, with one constraint worth knowing before you reach for it:
the label needs somewhere definite to sit, so the selection must resolve to **exactly one
group**.

```python
view.selections.add_selection(tag="res10", selection="group_index==10")
view.selections["res10"].add_label(text="catalytic")
```

The one that changes the picture is `new_region`, which turns the set into something drawn:

```python
region = view.selections["core"].new_region(tag="core-region", representation="cartoon")
```

From there it is a region like any other — see {doc}`regions`.

## Inspecting

```python
view.selections.count()
view.selections.records()
view.selections.info("core")
```

`info` describes one selection: how it was built (`source_kind`), at which element level,
and which atoms it resolved to.

## Managing

```python
view.selections.set_tag("core", "active-site")
view.selections.delete("active-site")
view.selections.clear()                 # every stored selection
```

## What survives a save

Stored selections **are** part of `view.export_state()`, so they come back with
{doc}`../export/state`. The active selection is saved too, as a convenience — it is
runtime state rather than scene content, and restoring it is not a promise about what a
click will do next.

## Tips

- A selection is cheap; a region draws. If you are only computing, do not make a region.
- Selection expressions are MolSysMT's, not MolSysViewer's. When one does not resolve the
  way you expect, the syntax question belongs upstream — see
  {doc}`../troubleshooting/selection_issues`.
- `view.select(...)` returns atom indices without storing anything. Use it when you want
  the numbers, not a named set.

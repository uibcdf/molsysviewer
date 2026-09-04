# Migrating to 0.22

0.22 removes methods from `view`. Everything they did is still available, and mostly one
object over: **the molecular system is asked of `view.whole` or of a region, not of the
view.**

The reasoning is in `uibcdf/molsysviewer#71`; what follows is the translation.

## Asking about the molecular system

The whole *is* the system, so it answers for all of it. A region answers for its own atoms.

| before | now |
| --- | --- |
| `view.get(...)` | `view.whole.get(...)` — or `region.get(...)` for a subset |
| `view.select(...)` | `view.whole.select(...)` / `region.select(...)` |
| `view.convert(...)` | `view.whole.convert(...)` / `region.convert(...)` |

These are thin wrappers over MolSysMT, so `msm.get(view, ...)`, `msm.select(view, ...)` and
`msm.convert(view, ...)` work too, and always did.

### `contains` and `is_composed_of` are gone

`get` already carries what they answered:

```python
view.contains(water=True)                       # before
view.whole.get(n_waters=True) > 0               # now

view.is_composed_of(protein=True, water=True)   # before
set(view.whole.get(element='molecule', molecule_type=True)) == {"protein", "water"}
```

`msm.contains(view, water=True)` and `msm.is_composed_of(view, ...)` also still work if you
want the direct question.

## `info` now means one thing per object

It used to mean either the scene or the system, depending on a `source` argument.

| call | answers |
| --- | --- |
| `view.info()` | **the scene** — one row per object: whole, loads, styles, regions, annotations, layers, active selection |
| `view.whole.info(...)` | **the molecular system** |
| `region.info(...)` | the system, masked to that region's atoms |

`view.info(element=..., selection=..., source=...)` now raises rather than quietly answering
a different question. Those arguments moved with the half they belonged to:

```python
view.info(element="molecule")          # before
view.whole.info(element="molecule")    # now
```

## Choosing what is drawn

`view.hide(selection)`, `view.isolate(selection)` and `view.show(selection)` are gone,
together with `view.atom_mask`. They wrote a cross-cutting atom-visibility mask, and that
mask **never travelled with a saved scene**: hiding atoms, saving and reloading brought them
back with nothing to warn you.

Visibility is now a property of the objects that a saved scene does carry:

```python
view.hide('molecule_type=="water"')              # before

view.whole.hide()                                # now
waters = view.regions.add(selection='molecule_type=="water"', tag="waters")
waters.hide()
```

{doc}`../scene_management/atom_masking` covers the model and the remaining cases.

**`view.show()` stays**, and is now only what its name says: the notebook display trigger,
like `pyplot.show()`. It no longer resets visibility on its way there, so what the whole and
the regions decided survives it.

## Smaller removals

- `ViewerInfo` and `RegionInfo` are gone with the two-section output they existed to hold;
  each `info` now returns a single table.
- `apply_system_edit(..., visible_atom_indices=...)` no longer takes that argument.

## What did not change

`view.extract(...)` still returns a new **view** of a structural subset, with the scene
migrated — it is about the viewer, not about the molecular system, which is why it stayed.
`view.regions`, `view.layers`, `view.styles`, `view.annotations`, `view.measurements`,
`view.shapes`, `view.camera`, `view.player`, `view.movie` and `view.export` are untouched.

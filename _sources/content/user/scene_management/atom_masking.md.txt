# Choosing what is drawn

MolSysViewer has one mechanism for this, and it is regions.

The viewer used to carry a second one — an atom-visibility mask behind `view.hide(...)`,
`view.show(selection)` and `view.isolate(...)` — which subtracted atoms from every
representation at once. It was removed before 1.0 for a reason worth knowing, because it
explains why the replacement is shaped the way it is: **the mask never travelled with a
saved scene.** You could hide the waters, save your work, reload it, and find them back,
with nothing to warn you. See {doc}`../export/state` for what a state document does carry.

## The model: the whole paints, or the regions do

```python
import molsysviewer as msv

view = msv.demo["1TCD"]

view.whole.hide()                                        # nothing painted by default
protein = view.regions.add(selection='molecule_type=="protein"',
                           tag="protein", representation="cartoon")
```

From here, showing and hiding is per object, and each object knows what it is:

```python
protein.hide()      # the protein disappears
protein.show()      # and comes back
view.whole.show()   # the baseline paints everything again
```

## The three old calls, and what they are now

| before | now |
| --- | --- |
| `view.hide('molecule_type=="water"')` | make a region for the waters and `hide()` it, with `view.whole.hide()` so nothing else paints them |
| `view.isolate('chain_name=="A"')` | `view.whole.hide()` and a region for chain A |
| `view.show()` (to reset) | `view.whole.show()` |
| `view.show()` (to display the widget) | unchanged — that half stayed |

The difference that is not just spelling: a region is a **named, saved thing**. It appears
in `view.info()`, it survives `save_state`, and it can be recoloured, layered and reused.
The mask was none of those.

## Selections

Regions take the same MolSysMT selection language the old calls did — see
{doc}`../molecular_system/selection`.

See also {doc}`visibility` for how visibility composes across the whole, regions and layers.

# Regions

Regions are structural subsets (selections) you can represent, hide/show, and delete independently.

Use regions when you need multiple representations at once (for example, protein as cartoon and ligand as ball-and-stick).
Use presets from {doc}`../representations/index` to stay consistent across regions.

Each region has one of three visual states:

- **None**: no own visual representation. The region still exists as a
  structural subset, but it is visible only through the whole baseline.
- **Inherit**: the region has its own visual component, but follows the live
  representation type of the whole.
- **Own**: the region has an explicit representation or preset of its own.

This distinction matters when the whole baseline is hidden. Regions in state
None disappear because they do not draw anything independently. Inherit and Own
regions remain visible while their own region visibility is on.

## Create a region from a selection

```python
import molsysviewer as viewer

view = viewer.MolSysView()
view.load("1CRN")
view.show()

protein = view.regions.add("protein", tag="protein", representation="cartoon")
ligand = view.regions.add("hetero", tag="ligand", representation="ball-and-stick")
```

## Update a region representation

```python
ligand.set_representation("spacefill", alpha=0.5)
```

You can also apply a Mol* preset (or a user preset if configured):

```python
protein.set_representation(preset="polymer-cartoon")
```

Use the reserved `"inherit"` sentinel when you want the region to stay visible
as a region while following the whole representation:

```python
protein.set_representation("inherit")
```

Changing `view.whole.set_representation(...)` later repaints inheriting regions
with the new whole representation type.

Use `None` when you intentionally want to remove the region's own visual:

```python
ligand.set_representation(None)
```

Extra representation parameters are ignored in state None. If you want to pass
parameters while following the whole representation, use `"inherit"` instead.

## Reset representation and colours

```python
ligand.reset_representation()
ligand.reset_colors()
view.reset_all_colors()
```

`region.reset_representation()` removes the region's own visual and returns it
to state None. It does not create a cartoon representation.

`region.reset_colors()` clears only that region's colour layer. Atoms not
coloured by the region keep the structural theme or whatever lower layer is
visible underneath. Colouring one region no longer turns the rest of the system
grey. Use `view.reset_all_colors()` only when you intentionally want to clear
every whole and region colour layer.

## Hide/show and delete

```python
ligand.hide()
ligand.show()
ligand.delete()
```

## Rename a region

```python
protein.rename("main-chain")
# view.regions["main-chain"] now resolves to the same region
```

Renaming updates Python state and JS state simultaneously, and the new name
is used in export/replay messages.

## Complementary regions

If you want “everything except X”, create a new region from the complement:

```python
binding_site = view.regions.add("resid 10:20", tag="site", representation="ball-and-stick")
rest = binding_site.new_complementary_region(tag="not-site", representation="cartoon")
```

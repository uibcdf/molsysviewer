# Regions

Regions are structural subsets (selections) you can represent, hide/show, and delete independently.

Use regions when you need multiple representations at once (for example, protein as cartoon and ligand as ball-and-stick).
Use presets from {doc}`../representations/index` to stay consistent across regions.

## Create a region from a selection

```python
import molsysviewer as viewer

view = viewer.MolSysView()
view.load("1CRN")
view.show()

protein = view.new_region("protein", tag="protein", representation="cartoon")
ligand = view.new_region("hetero", tag="ligand", representation="ball-and-stick")
```

## Update a region representation

```python
ligand.set_representation("spacefill", alpha=0.5)
```

You can also apply a Mol* preset (or a user preset if configured):

```python
protein.set_representation(preset="polymer-cartoon")
```

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
binding_site = view.new_region("resid 10:20", tag="site", representation="ball-and-stick")
rest = binding_site.new_complementary_region(tag="not-site", representation="cartoon")
```


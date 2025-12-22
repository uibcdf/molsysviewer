# Regions

Regions are structural subsets (selections) you can represent, hide/show, and delete independently.

Use regions when you need multiple representations at once (for example, protein as cartoon and ligand as ball-and-stick).
The global view is still useful as a baseline style for the whole system.

## Create a region from a selection

```python
import molsysviewer as mv

v = mv.MolSysView()
v.load_pdb_id("1CRN")
v.show()

protein = v.new_region("protein", tag="protein", representation="cartoon")
ligand = v.new_region("hetero", tag="ligand", representation="ball-and-stick")
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

## Complementary regions

If you want “everything except X”, create a new region from the complement:

```python
binding_site = v.new_region("resid 10:20", tag="site", representation="ball-and-stick")
rest = binding_site.new_complementary_region(tag="not-site", representation="cartoon")
```

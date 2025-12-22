# Whole

`Whole` controls the baseline representation for the whole molecular system.

Use it when you want a single default style (for example, cartoon for the full protein).
If you want different representations for different atom selections, use {doc}`regions` instead.

## Set a baseline representation

```python
import molsysviewer as mv

v = mv.MolSysView()
v.load_pdb_id("1CRN")
v.show()

v.whole.set_representation("cartoon")
v.whole.set_representation("ball-and-stick")
```

You can also apply a Mol* preset:

```python
v.whole.set_representation(preset="polymer-and-ligand")
```

## Hide/show the whole representation

```python
v.whole.hide()
v.whole.show()
```

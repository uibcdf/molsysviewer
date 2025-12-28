# Whole

`Whole` controls the baseline representation for the whole molecular system.

Use it when you want a single default style (for example, cartoon for the full protein).
If you want different representations for different selections, use {doc}`regions`.

## Set a baseline representation

```python
import molsysviewer as viewer

view = viewer.MolSysView()
view.load("1CRN")
view.show()

view.whole.set_representation("cartoon")
view.whole.set_representation("ball-and-stick")
```

You can also apply a Mol* preset:

```python
view.whole.set_representation(preset="polymer-and-ligand")
```

## Hide/show the whole representation

```python
view.whole.hide()
view.whole.show()
```


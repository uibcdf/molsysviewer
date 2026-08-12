# Whole

`Whole` controls the baseline representation for the whole molecular system.

Use it when you want a single default style (for example, cartoon for the full protein).
If you want different representations for different selections, use {doc}`regions`.

## Set a baseline representation

```python
import molsysviewer as msv

view = msv.MolSysView()
view.load("1CRN")
view.show()

view.whole.set_representation("cartoon")
view.whole.set_representation("ball-and-stick")
```

You can also apply a Mol* preset:

```python
view.whole.set_representation(preset="polymer-and-ligand")
```

The whole also owns the baseline structural colour scheme:

```python
view.whole.set_color_scheme("secondary_structure_default")
```

For one uniform color, use the base per-atom color layer:

```python
view.whole.set_color("cornflowerblue")
```

Changing the whole representation updates regions that explicitly inherit from
it (`region.set_representation("inherit")`). Regions with their own
representation keep their own visual state.

## Hide/show the whole representation

```python
view.whole.hide()
view.whole.show()
```

Hiding the whole hides only the baseline. Regions with their own representation
remain governed by their region visibility. Regions in the base/None state have
no own visual and therefore disappear while the whole is hidden.

## Reset representation and colours

```python
view.whole.reset_representation()
view.whole.reset_colors()
view.reset_all_colors()
```

`whole.reset_representation()` restores the load-time baseline style.
`whole.reset_colors()` clears only the whole/base colour layer and restores the
structural theme underneath region colour layers. Use `view.reset_all_colors()`
when you intentionally want to clear every whole and region colour layer.

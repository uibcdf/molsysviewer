# Visibility

MolSysViewer tracks visibility at three independent levels:

| Level | Object | Controls |
|---|---|---|
| **Whole** | the baseline representation | `view.whole.show()`, `view.whole.hide()` |
| **Region** | a named structural subset | `region.show()`, `region.hide()` |
| **Layer** | a non-structural visual group (shapes, overlays) | `layer.show()`, `layer.hide()` |

---

## Whole visibility

`view.whole.show()` and `view.whole.hide()` operate on the baseline
representation — the one created automatically when you load a system or by
`view.whole.set_representation(...)`.

```python
# Hide the baseline representation
view.whole.hide()

# Show it again
view.whole.show()
```

There is no second, selection-level mechanism. `view.hide(...)`, `view.show(selection)` and
`view.isolate(...)` wrote an atom-visibility mask and were removed before 1.0: the mask
never travelled with a saved scene, so anything hidden that way came back on reload with no
warning. {doc}`atom_masking` has the migration and the reasoning.

To take a selection out of the picture, make it a region and hide that:

```python
view.whole.hide()                                       # nothing painted by default
waters = view.regions.add(selection='molecule_type=="water"', tag="waters")
waters.hide()
```

---

## Region visibility

Each `Region` object has independent `hide()` and `show()` methods.
These do not affect other regions or the baseline.

```python
view.make_regions_by(element="chain")

view.regions["chain-A"].hide()   # hide chain A
view.regions["chain-B"].show()   # show chain B (already visible by default)
```

Regions created from explicit atom indices also respond to the same calls:

```python
pocket = view.regions.add(atom_indices=[10, 11, 12, 13], tag="pocket")
pocket.hide()
pocket.show()
```

---

## Layer visibility

Layers group non-structural shapes (overlays, vectors, links, etc.) and can
be toggled without touching the molecular representation.

```python
layer = view.layers["hbonds"]
layer.hide()
layer.show()
```

---

## Interaction between levels

- Hiding the whole (`view.whole.hide()`) hides only the baseline. Regions with
  own visuals remain controlled by their region visibility.
- A region in state None (no own representation or preset) is painted by the
  whole, so it disappears while the whole is hidden.
- `view.show()` displays the widget and nothing else. It does not touch what the
  whole and the regions decided — that was the atom-mask half, and it is gone.
- A region hidden explicitly with `region.hide()` stays hidden until
  `region.show()` is called — region-level intent is preserved.

---

## Common patterns

**Hide solvent before export:**

```python
view.whole.hide()
view.regions.add(selection='not (molecule_type=="water" or molecule_type=="ion")',
                 tag="dry", representation="cartoon")
view.export.html("dry_scene.html")
```

The region is the thing that gets exported, saved and restored — which the mask never was.

**Focus on a ligand:**

```python
view.whole.hide()
view.regions.add(selection='group_name=="LIG"', tag="ligand",
                 representation="ball-and-stick")
```

**Toggle an overlay layer during exploration:**

```python
view.layers["anm-mode-0"].hide()
# ... inspect ...
view.layers["anm-mode-0"].show()
```

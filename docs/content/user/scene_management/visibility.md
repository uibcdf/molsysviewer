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

Atom-mask visibility is a separate selection-level operation:

```python
# Hide only a selection (MolSysMT syntax)
view.hide('molecule_type == "water"')

# Show only a selection — everything else stays as-is
view.show('group_name == "LIG"')
```

`view.isolate()` is a combined hide-all + show-selection in one call:

```python
# Show only chain A, hide everything else
view.isolate('chain_name == "A"')

# Restore full visibility
view.isolate("all")
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
- `view.show(...)`, `view.hide(...)`, and `view.isolate(...)` operate on the
  atom mask. They compose with whole and region visibility rather than deleting
  regions.
- A region hidden explicitly with `region.hide()` stays hidden until
  `region.show()` is called — region-level intent is preserved.

---

## Common patterns

**Hide solvent before export:**

```python
view.hide('molecule_type == "water" or molecule_type == "ion"')
view.export.html("dry_scene.html")
```

**Focus on a ligand:**

```python
view.isolate('group_name == "LIG"')
```

**Toggle an overlay layer during exploration:**

```python
view.layers["anm-mode-0"].hide()
# ... inspect ...
view.layers["anm-mode-0"].show()
```

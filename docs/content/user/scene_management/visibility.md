# Visibility

MolSysViewer tracks visibility at three independent levels:

| Level | Object | Controls |
|---|---|---|
| **Whole** | the baseline global representation | `view.show()`, `view.hide()`, `view.isolate()` |
| **Region** | a named structural subset | `region.show()`, `region.hide()` |
| **Layer** | a non-structural visual group (shapes, overlays) | `layer.show()`, `layer.hide()` |

---

## Whole visibility

`view.show()` and `view.hide()` operate on the baseline representation —
the one created automatically when you load a system.

```python
# Hide the entire structure
view.hide("all")

# Show it again
view.show("all")

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

Regions created from an active canvas selection also respond to the same calls:

```python
pocket = view.new_region(atom_indices=[10, 11, 12, 13], tag="pocket")
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

- Hiding the whole (`view.hide("all")`) also hides all region representations
  but does **not** clear the region registry — regions are still accessible in Python.
- `view.show("all")` restores the baseline and all previously visible regions.
- A region hidden explicitly with `region.hide()` stays hidden even after
  `view.show("all")` — region-level intent is preserved.

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

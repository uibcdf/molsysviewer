# Tags

Tags are identifiers you reuse to group and manage parts of the scene.

They are not limited to shapes. In MolSysViewer, the same tag string can be used in different registries:

- **Regions** use tags as their stable identifier.
- **Layers** use tags as their stable identifier.
- **Shapes** use the tag as the *layer tag* where the created visuals are registered.

This means a tag is a handle you can keep in your workflow, even when you build the scene incrementally.

## Tag shapes (layer tag)

When you add shapes, reuse a tag to group them:

```python
view.shapes.add_pocket_blob(..., tag="pockets")
view.shapes.add_channel_tube(..., tag="pockets")
```

Clear by tag:

```python
# Remove only shapes tagged "pockets"
view.shapes.clear(tag="pockets")

# Remove all shapes
view.shapes.clear()
```

## Tag regions (region tag)

When you create a region, the tag identifies that region:

```python
site = view.new_region("resid 10:20", tag="site", representation="ball-and-stick")
site.hide()
```

Tip
- Use short, stable tags (e.g. `protein`, `ligand`, `pockets`) so you can hide/show/clear consistently.

Note
- You can rename a layer tag with `Layer.set_tag(...)`. This is useful when a tag becomes part of a workflow or naming convention.

# Layers

Layers are tag-based groups you can hide/show or delete as a unit. They are useful to manage overlays (shapes) that belong together.

## Create a layer

```python
import molsysviewer as mv

v = mv.MolSysView()
v.load_pdb_id("1CRN")
v.show()

pockets = v.new_layer(tag="pockets", kind="shapes")
```

## Add content to a layer

When you add shapes, reuse the same `tag` as the layer tag:

```python
v.shapes.add_pocket_blob(..., tag="pockets")
v.shapes.add_channel_tube(..., tag="pockets")
```

## Hide/show and delete

```python
pockets.hide()
pockets.show()
pockets.delete()
```

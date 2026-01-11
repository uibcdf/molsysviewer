# Layers

Layers are tag-based groups you can hide/show or delete as a unit.

Use layers to manage non-structural visuals (shapes, overlays) that belong together.

## Create a layer

```python
import molsysviewer as viewer

view = viewer.new_view("1CRN")
view.show()

pockets = view.new_layer(tag="pockets", kind="shapes")
```

## Add content to a layer

When you add shapes, reuse the same tag as the layer tag:

```python
view.shapes.add_pocket_blob(..., tag="pockets")
view.shapes.add_channel_tube(..., tag="pockets")
```

## Hide/show and delete

```python
pockets.hide()
pockets.show()
pockets.delete()
```

## Rename a layer tag

```python
pockets.set_tag("pockets-v2")
```

Notes
- You can hide a layer before it has content. When you later add shapes with that tag, they inherit the hidden state.


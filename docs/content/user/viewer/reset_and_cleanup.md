# Reset & cleanup

Use these helpers when you want to clear part of the scene without reloading the structure.

## Clear decorations

You can clear shapes/styles/labels without touching the loaded structure:

```python
view.clear_decorations(shapes=True, styles=True, labels=True)
```

## Fully reset the viewer

Use this when you want a clean state and plan to call `load(...)` again:

```python
view.reset_viewer()
```

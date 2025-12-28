# Camera & controls

Use these helpers to focus the view and control the on-canvas UI.

## Zoom to a selection

```python
import molsysviewer as viewer

view = viewer.MolSysView()
view.load("1CRN")
view.show()

view.zoom("protein", duration_ms="250 ms", extra_radius="4 angstroms")
```

## Reset the camera

```python
view.reset_camera()
```

## Save and restore a camera view

```python
snap = view.get_camera_snapshot()
view.set_camera_snapshot(snap)

# Pretty-print the snapshot (for notes or config files)
print(view.get_camera_snapshot(pretty=True))
```

## Show/hide the on-canvas controls

```python
view.set_controls_visible(True, autohide=True)
view.set_controls_visible(False)
```

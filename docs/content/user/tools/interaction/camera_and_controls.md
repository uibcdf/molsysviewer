# Camera & controls

Use these helpers to focus the view and control the on-canvas UI.

## Zoom to a selection

```python
import molsysviewer as mv

v = mv.MolSysView()
v.load_pdb_id("1CRN")
v.show()

v.zoom("protein", duration_ms="250 ms", extra_radius="4 angstroms")
```

## Reset the camera

```python
v.reset_camera()
```

## Save and restore a camera view

```python
snap = v.get_camera_snapshot()
v.set_camera_snapshot(snap)

# Pretty-print the snapshot (for notes or config files)
print(v.get_camera_snapshot(pretty=True))
```

## Show/hide the on-canvas controls

```python
v.set_controls_visible(True, autohide=True)
v.set_controls_visible(False)
```

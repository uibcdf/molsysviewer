# Atom masking

MolSysViewer uses MolSysMT selections to control what is visible in the scene.

## Hide/show/isolate

```python
import molsysviewer as viewer

view = viewer.MolSysView()
view.load("1CRN")
view.show()

view.hide("water")
view.show("protein")
view.isolate("protein")
view.show()  # reset to show all
```

## Selection syntax

Selections are interpreted by MolSysMT (default `syntax="MolSysMT"`).
See {doc}`../molecular_system/selection` for the selection basics.

See also {doc}`../scene_management/visibility` for how visibility works across whole, regions, and layers.

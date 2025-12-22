# Visibility & selections

MolSysViewer uses MolSysMT selections to control what is visible.

## Hide/show/isolate

```python
import molsysviewer as mv

v = mv.MolSysView()
v.load_pdb_id("1CRN")
v.show()

v.hide("water")
v.show("protein")
v.isolate("protein")
v.show()  # reset to show all
```

## Selection syntax

Selections are interpreted by MolSysMT (default `syntax="MolSysMT"`). Keep selection expressions consistent with your MolSysMT workflow.


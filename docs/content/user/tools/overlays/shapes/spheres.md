# Spheres

Spheres are the simplest overlay primitives.

```python
import molsysviewer as mv

v = mv.MolSysView()
v.load_pdb_id("1CRN")
v.show()

v.shapes.add_sphere(center=(0, 0, 0), radius=3.0, color=0x00FF00, alpha=0.4, tag="demo")
```


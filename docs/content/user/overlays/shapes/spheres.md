# Spheres

Spheres are the simplest overlay primitives.

```python
import molsysviewer as msv

view = msv.MolSysView()
view.load("1CRN")
view.show()

view.shapes.add_sphere(center=(0, 0, 0), radius=3.0, color=0x00FF00, alpha=0.4, tag="demo")
```

```python
import molsysviewer as msv
view = msv.MolSysView()
view.show()

# Transparent sphere
view.shapes.add_sphere(center=(0, 0, 0), radius=3.0, color=0x00ff00, alpha=0.4)

# Alpha-sphere set with optional atom spheres (single message)
view.shapes.add_set_alpha_spheres(
    centers=[(0, 0, 0), (4, 0, 0)],
    radii=[2.0, 1.5],
    atom_centers=[(0, 0, 0), (4, 0, 0)],
    atom_radius=0.8,
    color_alpha_spheres=0xff8800,
    alpha_alpha_spheres=0.3,
    color_atoms=0x0055ff,
    alpha_atoms=0.6,
    tag="alpha-demo",
)
```

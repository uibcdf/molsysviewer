# Shapes & overlays

Add basic shapes

```python
import molsysviewer as mv
v = mv.MolSysView()
v.show()

# Transparent sphere
v.add_sphere(center=(0, 0, 0), radius=3.0, color=0x00ff00, alpha=0.4)

# Alpha-sphere set with optional atom spheres
v.shapes.add_set_alpha_spheres(
    alpha_spheres={"centers": [[0,0,0],[4,0,0]], "radii": [2.0, 1.5], "color": 0xff8800, "alpha": 0.3},
    atom_spheres={"centers": [[0,0,0],[4,0,0]], "radius": 0.8, "color": 0x0055ff, "alpha": 0.6},
    tag="alpha-demo",
)
```

Pockets and blobs

```python
# Pocket blob (Gaussian field from alpha-spheres)
v.shapes.add_pocket_blob(
    centers=[(0,0,0), (3,0,0), (1.5,2,0)],
    radii=[2.0, 1.8, 1.2],
    iso_levels=[0.08, 0.15],
    iso_colors=[0x44ccff, 0x003366],
    smoothing=1.0,
    tag="pocket-blob",
)
```

Channel tubes

```python
centers = [(0,0,0), (2,0.5,0.2), (4,1,0.5), (6,1.5,1.0)]
radii   = [1.2, 1.0, 0.9, 1.1]
v.shapes.add_channel_tube(
    centers=centers,
    radii=radii,
    color_mode="segment",  # or "distance"
    smoothing=0.5,
    tag="channel-demo",
)
```

Pharmacophore glyphs

```python
v.shapes.add_pharmacophore_features(
    centers=[(0,0,0), (3,0,0), (6,0,0)],
    kinds=["aromatic", "hydrophobic", "hbond_acceptor"],
    alphas=[0.5, 0.4, 0.6],
    tag="ph4-demo",
)
```

Anisotropy ellipsoids/disks

```python
v.shapes.add_anisotropy_ellipsoids(
    centers=[(0,0,0), (3,0,0)],
    eigenvalues=[[3,2,1],[2,1.5,0.8]],
    eigenvectors=[
        [[1,0,0],[0,1,0],[0,0,1]],
        [[0,1,0],[0,0,1],[1,0,0]],
    ],
    scale=1.0,
    max_eccentricity=5.0,
    color_mode="anisotropy",
    tag="ellipsoid-demo",
)
```

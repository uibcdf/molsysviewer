# Anisotropy (ellipsoids/disks)

Anisotropy overlays can be rendered as ellipsoids or disks driven by eigenvalues/eigenvectors.

See also the cookbook:
- {doc}`../../../cookbook/anisotropy_ellipsoids`

```python
view.shapes.add_anisotropy_ellipsoids(
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
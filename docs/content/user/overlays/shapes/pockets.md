# Pockets (surfaces and blobs)

Pocket overlays are typically built from alpha spheres and rendered as surfaces or volumetric blobs.

See also the cookbook:
- {doc}`../../../cookbook/pocket_surface`
- {doc}`../../../cookbook/pocket_blob`

```python
# Pocket blob (Gaussian field from alpha-spheres)
view.shapes.add_pocket_blob(
    centers=[(0,0,0), (3,0,0), (1.5,2,0)],
    radii=[2.0, 1.8, 1.2],
    iso_levels=[0.08, 0.15],
    iso_colors=[0x44ccff, 0x003366],
    smoothing=1.0,
    tag="pocket-blob",
)
```
# Pharmacophore overlays

Pharmacophore overlays render feature glyphs (donor/acceptor/aromatic, etc.) on top of a structure.

See also the cookbook:
- {doc}`../../cookbook/pharmacophore_overlay`

```python
view.shapes.add_pharmacophore_features(
    centers=[(0,0,0), (3,0,0), (6,0,0)],
    kinds=["aromatic", "hydrophobic", "hbond_acceptor"],
    alphas=[0.5, 0.4, 0.6],
    tag="ph4-demo",
)
```

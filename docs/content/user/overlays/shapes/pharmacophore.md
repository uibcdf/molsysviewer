# Pharmacophore overlays

Pharmacophore overlays render interaction-site glyphs (spheres, disks, arrows)
at specified positions in the scene. Use them to mark donor/acceptor positions,
hydrophobic patches, aromatic rings, or any other feature type you want to
annotate spatially.

## Quick start

```python
from molsysviewer import demo

view = demo["181L"]
view.styles.apply(tag="polymer-and-ligand")

layer = view.shapes.add_interaction_sites(
    centers=[(2.1, 5.3, 0.8), (5.4, 3.1, 2.0), (8.0, 6.0, 1.5)],
    kinds=["aromatic", "hydrophobe", "hbond_acceptor"],
    tag="ph4-demo",
)
view
```

## Supported feature kinds

| Kind | Default color | Typical glyph |
|---|---|---|
| `"donor"` | blue | sphere |
| `"acceptor"` | red | sphere |
| `"hydrophobe"` | amber | sphere |
| `"aromatic"` | purple | disk |
| `"positive"` | deep blue | sphere |
| `"negative"` | pink/red | sphere |
| `"metal"` | green | sphere |

Any string is accepted; unknown kinds render in grey (`0xcccccc`).

## Main entry-point

```python
layer = view.shapes.add_interaction_sites(
    centers=centers,          # list of (x, y, z) in Ångstroms
    kinds=kinds,              # one str per center
    radii=1.5,                # float or list — optional
    directions=None,          # for arrow/disk glyphs — optional
    alphas=0.7,               # float or list — optional
    colors=None,              # hex int list — overrides per-kind defaults
    color_scheme=None,        # named palette — alternative to per-kind defaults
    color_table=None,         # custom {kind: hex_int} mapping
    tag="my-ph4",             # optional label
    layer_tag="overlays",     # optional layer group
)
```

All lengths must be equal: `centers`, `kinds`, and (if provided) `radii`,
`directions`, `alphas`, `colors`.

## Color control

Three ways to set colors (in decreasing specificity):

1. **`colors`** — one hex integer per feature; ignores kind defaults.
2. **`color_table`** — maps kind strings to hex integers; falls back to built-in palette for missing kinds.
3. **`color_scheme`** — a named palette string (alternative to per-feature control).

```python
# Per-feature colors
view.shapes.add_interaction_sites(
    centers=[(0,0,0), (3,0,0)],
    kinds=["donor", "acceptor"],
    colors=[0x0000ff, 0xff0000],
    tag="custom-colors",
)

# Custom kind table
view.shapes.add_interaction_sites(
    centers=[(0,0,0)],
    kinds=["donor"],
    color_table={"donor": 0x00ff88},
    tag="custom-table",
)
```

## Opacity and size

```python
view.shapes.add_interaction_sites(
    centers=[(0,0,0), (3,0,0)],
    kinds=["donor", "acceptor"],
    radii=[1.8, 1.5],      # individual radii in Å
    alphas=[0.9, 0.6],     # individual alpha values
    tag="styled-sites",
)
```

## Layer visibility

`add_interaction_sites()` returns a `ShapeLayer`. Use it to toggle the overlay
without touching the rest of the scene:

```python
layer = view.shapes.add_interaction_sites(...)
layer.hide()
layer.show()
layer.delete()
```

## Cookbook

- {doc}`../../cookbook/pharmacophore_overlay` — complete scientific workflow
  combining pocket detection and pharmacophore rendering.

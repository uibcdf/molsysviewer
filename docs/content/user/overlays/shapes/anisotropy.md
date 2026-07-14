# Anisotropy (ellipsoids)

Anisotropy ellipsoids overlay oriented glyphs at atom or residue positions.
They are commonly used to show B-factor anisotropy tensors (from X-ray
crystallography) or normal-mode displacement ellipsoids from an elastic network
model.

## Quick start

```python
from molsysviewer import demo
import numpy as np

view = demo["1TCD"]
view.styles.apply(tag="cartoon-secondary-structure")

# Place an ellipsoid at each Cα of the first five residues
# (coordinates and eigenvalues are illustrative)
centers = [(10.0, 5.0, 3.0), (13.5, 6.0, 3.5), (17.0, 7.0, 4.0)]
eigenvalues = [[3.0, 1.5, 0.8], [2.5, 1.2, 0.6], [4.0, 2.0, 1.0]]
eigenvectors = [
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    [[0.9, 0.4, 0], [-0.4, 0.9, 0], [0, 0, 1]],
    [[0.7, 0.7, 0], [-0.7, 0.7, 0], [0, 0, 1]],
]

layer = view.shapes.add_anisotropy_ellipsoids(
    centers=centers,
    eigenvalues=eigenvalues,
    eigenvectors=eigenvectors,
    scale=1.5,
    color_mode="anisotropy",
    alpha=0.7,
    tag="bfactor-ellipsoids",
)
view
```

## API

```python
layer = view.shapes.add_anisotropy_ellipsoids(
    centers=centers,              # (x, y, z) per ellipsoid in Å
    eigenvalues=eigenvalues,      # [[λ1, λ2, λ3], ...] — drives axis lengths
    eigenvectors=eigenvectors,    # [[[v1x,v1y,v1z],[v2...],[v3...]], ...]
    tensors=None,                 # 3×3 matrix per site — alternative to eigen*
    principal_directions=None,    # simplified: one direction per site
    scale=1.0,                    # uniform scale factor
    max_eccentricity=5.0,         # clamps axis-length ratio
    color_mode="anisotropy",      # "anisotropy", "value", or None
    colors=None,                  # hex int per ellipsoid — overrides color_mode
    color_map=None,               # palette for value-based coloring
    values=None,                  # float per ellipsoid — drives value coloring
    alpha=0.7,
    tag="ellipsoids",
    layer_tag="anisotropy",
    name=None,
)
```

## Input modes

You can provide anisotropy in three equivalent forms:

| Parameter | Format | Typical source |
|---|---|---|
| `eigenvalues` + `eigenvectors` | diagonalized form | ANM/NMA output |
| `tensors` | 3×3 matrices | crystallographic U tensors |
| `principal_directions` | one vector per site | simplified directional indicator |

## Color modes

| `color_mode` | What drives the color |
|---|---|
| `"anisotropy"` | ratio of largest to smallest eigenvalue |
| `"value"` | per-site scalar passed via `values=` |
| `None` | single flat color (from `colors[0]` or palette default) |

```python
# Color by a per-residue scalar (e.g. B-factor)
layer = view.shapes.add_anisotropy_ellipsoids(
    centers=centers,
    eigenvalues=eigenvalues,
    eigenvectors=eigenvectors,
    color_mode="value",
    values=b_factors,
    color_map=[0x0000ff, 0xffffff, 0xff0000],
    tag="bfactor-colored",
)
```

## Eccentricity clamping

Very elongated ellipsoids are clamped at `max_eccentricity` so the overlay
stays readable even for highly anisotropic sites:

```python
layer = view.shapes.add_anisotropy_ellipsoids(
    centers=centers,
    eigenvalues=eigenvalues,
    eigenvectors=eigenvectors,
    max_eccentricity=3.0,   # limit the longest-to-shortest ratio
    tag="clamped",
)
```

## Layer visibility

```python
layer.hide()
layer.show()
layer.delete()
```

## Cookbook

- {doc}`../../cookbook/anisotropy_ellipsoids` — ANM mode ellipsoids from ElastNetMT.

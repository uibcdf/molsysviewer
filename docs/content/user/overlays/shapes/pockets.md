# Pockets (surfaces and blobs)

MolSysViewer provides two complementary pocket overlays:

- **`add_pocket_surface`** — builds an iso-surface from per-atom scalars (e.g.,
  electrostatic potential values on alpha-sphere atoms).
- **`add_pocket_blob`** — builds a volumetric Gaussian blob from alpha-sphere
  centers and radii, useful when you have a pocket from a simple sphere model.

## Pocket blob

A Gaussian field is computed from the alpha-sphere centers and radii, then
iso-surfaces are extracted.

```python
from molsysviewer import demo

view = demo["181L"]
view.styles.apply(tag="polymer-and-ligand")

layer = view.shapes.add_pocket_blob(
    centers=[(14.0, 8.0, 3.0), (16.0, 9.0, 4.0), (15.0, 11.0, 3.5)],
    radii=[2.0, 1.8, 1.5],
    iso_level=0.1,
    smoothing=1.0,
    alpha=0.5,
    tag="pocket-blob",
)
view
```

### Blob API

```python
layer = view.shapes.add_pocket_blob(
    centers=centers,        # (x, y, z) list in Å
    radii=radii,            # radius per center in Å
    radius_scale=1.0,       # uniform scale applied to all radii
    resolution=0.5,         # grid resolution in Å (smaller = finer)
    iso_level=0.1,          # iso-surface threshold
    smoothing=1.0,          # Gaussian smoothing sigma
    values=None,            # float per center for color mapping
    color_map=None,         # palette for value mapping
    alpha=0.5,
    tag="pocket-blob",
    layer_tag="pockets",
    name=None,
)
```

### Multi-level iso-surfaces

Pass `iso_levels` (list) to extract several nested surfaces:

```python
layer = view.shapes.add_pocket_blob(
    centers=centers,
    radii=radii,
    # NOTE: iso_levels / iso_colors are passed through the frontend
    # for blobs that support multi-level rendering
    tag="nested-pocket",
)
```

## Pocket surface

Builds a surface directly from per-atom scalar values (e.g., electrostatic
potential or solvent-accessibility computed on alpha-sphere positions).

```python
layer = view.shapes.add_pocket_surface(
    atom_indices=[10, 11, 12, 13, 14, 15],   # atoms that define the surface
    scalars=[0.2, -0.1, 0.5, -0.3, 0.1, 0.4],   # per-atom values
    iso_levels=[0.0],
    iso_colors=[0x4488ff],
    alpha=0.6,
    tag="ep-surface",
)
```

### Surface API

```python
layer = view.shapes.add_pocket_surface(
    atom_indices=atom_indices,    # required — defines the surface support
    scalars=None,                 # float per atom — drives color/iso
    grid=None,                    # explicit volumetric grid dict
    alpha=None,
    iso_levels=None,              # list of iso-values
    iso_colors=None,              # hex int per iso-level
    iso_alphas=None,              # alpha per iso-level
    color_map=None,               # palette string or hex list
    mouth_atom_indices=None,      # atoms at the pocket mouth — clips the surface
    clip_plane=None,              # alternative to mouth_atom_indices
    tag="my-surface",
    layer_tag="pockets",
)
```

### Mouth clipping

`mouth_atom_indices` marks the opening of the pocket so the surface is clipped
at the solvent-accessible entrance:

```python
layer = view.shapes.add_pocket_surface(
    atom_indices=pocket_atoms,
    mouth_atom_indices=mouth_atoms,
    tag="clipped-pocket",
)
```

## Layer visibility

Both calls return a `ShapeLayer`:

```python
layer.hide()
layer.show()
layer.delete()
```

## Cookbook

- {doc}`../../../cookbook/pocket_surface` — `add_pocket_surface` with scalar mapping.
- {doc}`../../../cookbook/pocket_blob` — `add_pocket_blob` workflow from alpha spheres.

# Representation types

Representation types control how atoms and polymers are drawn (cartoon, ball-and-stick, surface, etc.).

Use this page to pick a representation type name you can pass to:

- `view.whole.set_representation(representation=...)`
- `region.set_representation(representation=...)`

Supported types (normalized)
- `backbone`
- `ball-and-stick`
- `carbohydrate`
- `cartoon`
- `ellipsoid`
- `gaussian-surface`
- `gaussian-volume`
- `line`
- `molecular-surface`
- `point`
- `putty`
- `spacefill`

Common aliases
- `sticks`, `ballstick`, `ball_and_stick`, `licorice`, `cylinders` → `ball-and-stick`
- `lines`, `wire`, `wireframe` → `line`
- `dots` → `point`
- `ribbon` → `backbone`
- `surface` → `molecular-surface`
- `vdw` → `spacefill`

Not representation types

Three capabilities are sometimes expected here and do not belong to
`set_representation`. Each has its own entry point, and passing its name as a
representation type raises:

- **labels** — use {doc}`../overlays/labels` (`view.annotations.add(...)`).
  A label is text placed in the scene, not a way of drawing atoms, and it has its own
  lifecycle.
- **orientation axes** — use `view.show_orientation_axes(selection)`. It returns a
  `Region` with the usual `hide` / `show` / `delete`.
- **best-fit plane** — use `view.show_best_fit_plane(selection)`, likewise.

The last two draw Mol\* representations that are geometric rather than structural: they
describe where a selection *is*, not what its atoms look like. They are public, and they
are reached through their own helper rather than through the type name.

Tips
- Start with a preset if you are unsure (see {doc}`presets`).
- Use a region when you want different styles for different selections.

## Curated parameters

Inspect `view.styles.representation_param_schema("ball-and-stick")` to find
the curated options for a type. Whole, regions and inline styles digest these
values with the same contract. For example:

```python
view.whole.set_representation(
    "ball-and-stick", sizeFactor=0.7, ignoreHydrogens=True, multipleBonds="symmetric"
)
```

Scale factors are finite, dimensionless numbers. `sizeFactor` and
`terminalLinkSizeFactor` admit zero; `sizeAspectRatio` must be positive.
Hydrogen and tubular-helix switches require booleans. Profile, multiple-bond
and quality options use the values listed in the schema. Surrounding whitespace
and letter case are normalized for these enums. Rendering slider maxima are
not hard limits on the accepted scales.
Molecular `alpha` is one scalar opacity in [0, 1]; shape opacity batches keep
their separate API.

The native Mol* `probeRadius` and `resolution` controls use the molecular
payload's fixed **ångström** coordinate space. Their schema records declare
`unit="angstrom"`. Existing bare native numbers keep that meaning; quantities
with explicit length units are converted to ångströms before forwarding:

```python
view.whole.set_representation("surface", probeRadius="0.14 nm", resolution="0.05 nm")
# Native parameters are probeRadius=1.4 and resolution=0.5, in angstroms.
```

`probeRadius` is nonnegative; grid `resolution` must be positive. Both require
finite scalar values. The session unit policy does not change their native
meaning. This renderer contract is separate from pocket-grid options.

Invalid curated values leave the scene and its Undo history unchanged. Core
owner checks also protect delegated styles and trusted internal calls.
`skip_digestion=True` bypasses ArgDigest, not the representation owner's
semantic checks.

Advanced Mol* options remain available through the existing escape route.
A directly forwarded name outside the curated catalogue retains its
missing-digester warning; it is not thereby a validated public option.
The catalogue is intentionally a subset of Mol*'s runtime parameter domain.

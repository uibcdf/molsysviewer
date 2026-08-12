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

- **labels** — use {doc}`../annotations/index` (`view.annotations.add_annotation(...)`).
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

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
- `label`
- `line`
- `molecular-surface`
- `orientation`
- `plane`
- `point`
- `putty`
- `spacefill`

Common aliases
- `sticks`, `ballstick`, `ball_and_stick` → `ball-and-stick`
- `licorice`, `lines`, `wire`, `wireframe` → `line`
- `ribbon` → `backbone`
- `surface` → `molecular-surface`
- `vdw` → `spacefill`

Tips
- Start with a preset if you are unsure (see {doc}`presets`).
- Use a region when you want different styles for different selections.

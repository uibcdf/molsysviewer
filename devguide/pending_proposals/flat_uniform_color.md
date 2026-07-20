# Flat/uniform color for whole and regions (`set_color`)

**Status:** Proposal — requested by the maintainer during dogfooding (recorrido 2)
**Priority:** medium — closes an obvious gap in the coloring API

## Motivation

Today a region or the whole can only be colored:

- by a structural scheme (`set_color_scheme("chain-id")`),
- by a scalar attribute (`set_color_by_attribute("b_factor")`), or
- by an explicit per-atom value array (`set_color_by_values([...])`).

There is **no direct way to paint everything a single flat color** (e.g. "make
this region red"). The user has to fake it via `set_color_by_values` with a
constant array, which is unintuitive and needs the right length.

## Proposal

Add `set_color(color)` on both `Whole` and `Region`:

- `color` accepts the same color forms already digested elsewhere (an int
  `0xRRGGBB`, a `"#rrggbb"`/named string — reuse the existing `color` digester).
- Applies a uniform color to the target's own representation (region must have an
  own representation, same precondition and error message as `set_color_scheme`).
- Emits the existing `set_atom_colors` wire op with a constant color broadcast to
  the target's atoms, `replace=True`.

This is a thin convenience over the machinery that already exists (the per-atom
color path), so it should be small once the render path for per-atom colors is
confirmed working (see `pending_bugs/region_color_by_attribute_not_rendered.md`
— that bug must be resolved first, or a flat color would be invisible too).

## Tests

- Unit: `set_color(0xFF0000)` on whole and region emits `set_atom_colors` with a
  single distinct color broadcast to all target atoms.
- Invalid color values rejected at the public boundary.
- E2E: flat color visibly applied and distinct from the structural theme.

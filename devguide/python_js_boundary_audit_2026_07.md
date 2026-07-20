# Python ↔ JS boundary audit (2026-07)

Motivated by a pattern that appeared four times during dogfooding: a public
argument that Python accepts and validates, and that something downstream then
ignores in silence. Rather than keep catching them one at a time, this is a
systematic sweep of the boundary.

Three sweeps were run, each scriptable and repeatable.

## Sweep 1 — public arguments with no digester

Every function decorated with `@digest()` was parsed with `ast`, its argument
names collected, and checked against
`molsysviewer/_private/arg_digestion/argument/*.py`.

**Result: 26 arguments have no digester** (out of 483 digesters available). Each
one emits `DigestNotDigestedWarning` on every ordinary call, so the public
contract is not validated. Confirmed on real calls:

```
view.focus_region('A')      -> No digester for region
view.layers.add(meta=...)   -> No digester for meta
view.shapes.add_rings(...)  -> No digester for segments
```

Grouped by area:

- **Shapes (20)**: `draw_edges`, `edge_color`, `show_normals`, `normal_color`,
  `atom_quads`, `exterior_only`, `draw_faces`, `faces_pickable`, `atom_triplets`,
  `normals`, `segments`, `kinds`, `directions`, `length_scale`,
  `color_component`, `structures_atom_indices`, `color_alpha_spheres`,
  `color_atoms`, `alpha_alpha_spheres`, `alpha_atoms`.
- **Viewer/scene (6)**: `region` (`focus_region`), `fade` (`focus_with_fade`),
  `transaction_id` (`partial_coordinates_update`), `meta` (`layers.add`),
  `layer` (`regions.set_layer`), `target` (`measurements.set_representative_atom`).

Most are simple contracts (booleans, colors, index lists), so they are mechanical
to write; the volume is the cost, not the difficulty.

## Sweep 2 — ops emitted by Python that nobody reads

All `{"op": "..."}` literals emitted from Python were compared against every
handler form in the frontend (`case "x"`, `op === "x"`, `op !== "x"`), across
`js/src/**/*.ts` **and** the JS embedded in `widget.py`.

**Result: 1 real orphan** out of 89 ops.

- `dynamic_region_evaluation_warning` — emitted from `viewer/regions.py` through
  `_send_runtime_only` when a dynamic region blows its evaluation budget and is
  frozen to static. No frontend handler exists, so the warning never reaches the
  user; the region silently stops updating.

Five further candidates were false positives, worth recording so the sweep is not
re-run naively: `popup_source`, `request_camera_snapshot` and
`request_image_export` are intercepted in `index.ts` before the controller;
`widget_runtime_source` is handled by the JS embedded in `widget.py`; and
`set_figure_spec` is handled with an `if (op === ...)` rather than a `case`.

## Sweep 3 — values Python accepts that the frontend does not know

Literal values accepted by each digester (`in [...]`, `in (...)`) were searched
for in the frontend sources. This is the sweep that would have caught the
playback-mode bug (Python said `ping-pong`, the frontend called it `palindrome`).

**Result: no outstanding mismatch.** `ping-pong` is now resolved. The remaining
hits are noise from arguments that never cross the boundary (`output_type`,
`keys`, file/write modes) or values resolved on the Python side before sending
(`licorice`, mapped to `ball-and-stick` in `viewer/representations.py`).

This sweep has a low signal-to-noise ratio and needs manual verification of each
hit; it is worth re-running when a new enum-like argument is added.

## Side finding — orphan digesters

`color_values_scale` (and its `_2` variant) have digesters but no method uses
them: dead code in the opposite direction. A reverse sweep (digesters with no
consumer) would find more.

## Status

The six non-shape digesters are **done** (`region`, `fade`, `meta`, `layer`,
`target`, `transaction_id`), each mutation-verified. Re-running sweep 1 now
reports 20 missing arguments instead of 26, all of them in `shapes`.

## Recommendation

1. Fill the remaining 20 digesters, all in `shapes`. The group is homogeneous and
   can be done in one pass.
2. Decide on `dynamic_region_evaluation_warning`: surface it in the frontend, or
   stop emitting it. A performance warning that reaches nobody is worse than no
   warning, because the region silently degrades.
3. Re-run sweeps 1 and 2 in CI. Both are cheap and deterministic, and would have
   caught every instance of this pattern found during dogfooding.

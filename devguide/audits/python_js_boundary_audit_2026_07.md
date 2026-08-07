# Python ↔ JS boundary audit (2026-07)

**Status:** closed audit. Retained as evidence; not active work.

Motivated by a pattern that appeared four times during dogfooding: a public
argument that Python accepts and validates, and that something downstream then
ignores in silence. Rather than keep catching them one at a time, this is a
systematic sweep of the boundary.

Three sweeps were run, each scriptable and repeatable.

## Sweep 1 — public arguments with no digester

Every function decorated with `@digest()` was parsed with `ast`, its argument
names collected, and checked against
`molsysviewer/_private/argdigest/argument/*.py`.

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

## Status: closed

All three findings are resolved.

- **26 missing digesters → 0.** The six non-shape ones came first (`region`,
  `fade`, `meta`, `layer`, `target`, `transaction_id`), then the twenty in
  `shapes`. Contracts follow their call sites, and booleans are rejected wherever
  they would masquerade as a number or an index.
- **The orphan op now has a handler.** `dynamic_region_evaluation_warning` is
  surfaced as a canvas toast naming the region and the timing that blew the
  budget. The first attempt was to stop emitting it, on the grounds that the
  freeze already reaches the user through the message catalog — but the suite
  rejected that: `test_over_budget_dynamic_region_freezes_to_static_and_reports_runtime`
  asserts the message is sent. The emission was deliberate and tested; what was
  missing was the other half. Worth remembering when this sweep flags an orphan:
  check for a test asserting the emission before assuming it is dead weight.
- **Sweeps 1 and 2 now run in CI** as `tests/test_python_js_boundary.py`. Both
  are mutation-verified: removing a digester or adding an unread op fails them.

Sweep 3 (values Python accepts that the frontend does not know) is **not**
automated: its signal-to-noise ratio is poor and every hit needs manual reading.
Re-run it by hand when adding an enum-like argument that crosses the boundary.

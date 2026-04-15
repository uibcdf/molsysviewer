# Pending Closure Checkpoint (2026-04-08)

This note closes the previous contents of:

- `devguide/pending_bugs/`
- `devguide/pending_proposals/`

Those documents are no longer treated as active pending items.

## Closed Items

### `BUG_whole_set_representation.md`

Closed.

The initial default/global representations are now brought under the same
managed path used by the public `whole` API, so:

- `view.whole.set_representation(...)`
- `view.whole.show()`
- `view.whole.hide()`

operate on the same visible global state the user sees after loading.

### `BUG_measurement_persistence_ux.md`

Closed.

The old public persistence step is gone.

Current behavior:

- completed interactive measurements are registered automatically,
- they are immediately visible in `view.measurements`,
- they survive export/replay,
- they expose endpoint metadata,
- representative-atom policy is supported,
- measurement context actions support hide/delete.

Residual work in this area is no longer a bug.
It belongs to normal product evolution of UI/detail views.

### `BUG_shape_api_identity_and_mutability.md`

Closed as a pending bug.

The original failure mode has been addressed:

- shapes are retrievable via `view.shapes[...]`,
- shapes are no longer just anonymous create-and-forget layers,
- `tag` is unique in the shapes collection,
- `layer_tag` is explicit,
- `Layer` is now the grouping abstraction,
- `Shape` objects already support a first rich mutability slice for spheres:
  - `get_center()`
  - `set_center(...)`
  - `set_radius(...)`
  - `set_color(...)`
  - `set_alpha(...)`

What remains is extension of rich mutability to additional shape families.
That is future feature work, not the original architectural bug.

### `BUG_shape_interaction_lack.md`

Closed as a pending bug.

Shapes now participate in the interaction model with:

- click/hover/context targets of kind `shape`,
- context-menu support,
- Python-side `context_target.tag`,
- shape-aware `active_selection` payloads (`source_kind="shape"`),
- delete/focus-style workflows through the existing interaction channels.

Future refinement can still improve UX, but the old "visual ghosts" condition
is no longer the operative state of the project.

### `PROPOSAL_shape_layer_registry_hierarchy.md`

Closed as a pending proposal.

Its main direction has already been adopted in the live refactor:

- object identity separated from grouping,
- `tag` as public identity per collection,
- `layer_tag` for grouping,
- `view.shapes`, `view.annotations`, `view.measurements`, `view.layers`,
- `Layer` as grouping abstraction,
- reproducible `layer_tag` state in export/history.

Remaining work is implementation breadth, not architecture indecision.

## Current Follow-Up Work

The refactor is still ongoing, but the remaining tasks belong to active
development, not to the old pending buckets.

The main follow-up areas are:

- extend rich mutability beyond spheres,
- enrich workbench/detail views around `layer_tag`,
- continue reducing legacy compatibility paths,
- decide whether more shape families should get dedicated runtime update
  messages instead of recreate-and-sync behavior.

## Source Of Truth After Closure

For the current shape/layer/tag refactor state, use:

- `devguide/TMP_shape_layer_tag_checkpoint.md`
- `devguide/checkpoints.md`


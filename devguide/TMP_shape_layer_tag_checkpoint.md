# Temporary Checkpoint: Viewer / Shapes / Layers / Tags

This file is the current handoff checkpoint for the ongoing refactor around:

- `molsysviewer/viewer/`
- `view.shapes`
- `view.annotations`
- `view.measurements`
- `view.layers`
- `tag` and `layer_tag`

It is not the final design document.
It is the operational checkpoint for continuing implementation without having to
reconstruct decisions from chat history.

This front is no longer the only active refactor hotspot.
Use this file as a stable handoff checkpoint if work returns to scene-object /
layer semantics later.

## What Is Already Closed

These earlier pending items are no longer open design questions:

- `whole.set_representation()` now acts on the same managed baseline/global
  state the user sees after load.
- interactive measurements are registered automatically and survive export/replay.
- public `persist_last_measurement()` is gone.
- measurement endpoint metadata is exposed and `representative_atom` is
  supported.
- measurements participate in context actions (`Hide`, `Delete`).
- `tag` is unique per public collection.
- `layer_tag` is explicit and reproducible.
- the old pending bug/proposal buckets were closed into
  `devguide/pending_closure_2026_04_08.md`.

## Current Implementation Status

### Scene-object model

Implemented and usable now:

- `view.shapes[...]`, `view.annotations[...]`, and `view.measurements[...]`
  retrieve scene objects directly by unique `tag`.
- scene objects carry explicit `layer_tag`.
- `view.layers[...]` is backed by a real grouping abstraction exposing:
  - `.members`
  - `.shapes`
  - `.annotations`
  - `.measurements`
- `Layer` now represents grouping semantics in the current Python model.
- `GroupLayer` remains only as a compatibility alias during the transition.
- shapes, annotations, and measurements support public `set_layer_tag(...)`.
- regrouping updates the Python scene registry and the layer view consistently.
- export/replay preserves `layer_tag`.
- workbench/UI now shows `layer_tag` as a secondary label when it differs from
  the object `tag`.

### Rich mutability

Implemented now:

- `Sphere`
  - `get_center()`
  - `set_center(...)`
  - `set_radius(...)`
  - `set_color(...)`
  - `set_alpha(...)`
- `Link`
  - `set_alpha(...)`
  - `set_colors(...)`
  - `set_radii(...)`
- `TriangleFaces`
  - `set_alpha(...)`
  - `set_colors(...)`
- `Tetrahedra`
  - `set_alpha(...)`
  - `set_colors(...)`
- `ChannelTube`
  - `set_alpha(...)`
  - `set_radii(...)`
  - `set_colors(...)`
- `AnisotropyEllipsoids`
  - `set_alpha(...)`
  - `set_colors(...)`
- `Pharmacophore`
  - `set_alpha(...)`
  - `set_colors(...)`
  - `set_radii(...)`
- `DisplacementVectors`
  - `set_length_scale(...)`
  - `set_radius_scale(...)`
- `PocketBlob`
  - `set_alpha(...)`
  - `set_radii(...)`
  - `set_radius_scale(...)`
- `PocketSurface`
  - `set_alpha(...)`

Current implementation strategy:

- the Python-side reproducible state is rewritten to the final object state;
- the frontend is refreshed accordingly;
- export/replay does not accumulate intermediate edit noise.

### Viewer package split

The old `molsysviewer/viewer.py` monolith has been split into
`molsysviewer/viewer/`.

Current package layout:

- `viewer/__init__.py`
  - preserves the public import path `molsysviewer.viewer.MolSysView`
- `viewer/core.py`
  - high-level `MolSysView` facade/orchestration and frontend event handling
- `viewer/history.py`
  - replayable history recording and message rewriting
- `viewer/export.py`
  - export message assembly and HTML serialization helpers
- `viewer/scene_registry.py`
  - non-structural scene-object and layer registries
- `viewer/representations.py`
  - representation normalization
- `viewer/presets.py`
  - preset normalization and user-preset resolution
- `viewer/signals.py`
  - SMonitor/signal helper functions

Compatibility currently preserved:

- `from molsysviewer import MolSysView`
- `from molsysviewer.viewer import MolSysView`

Also already done:

- `arg_digestion` now has a shared normalization helper so
  `molsysviewer.viewer.core.*` keeps behaving like the historical public caller
  path `molsysviewer.viewer.*` where older digesters depend on exact strings.

### Small UX/UI items already handled

- annotation auto-tags now use `annotation1`, `annotation2`, ...
- the panel-shell tabs/toggles are visually lighter and more integrated with
  the canvas
- collapsed side panels no longer bleed shadow onto the canvas

## Closed Decisions

### 1. `tag` is unique per class

`tag` is unique inside each public collection:

- `view.shapes`
- `view.annotations`
- `view.measurements`
- `view.layers`

The same text may still exist across different collections.

### 2. `tag` is public object identity

`tag` identifies the object in its collection.
It is not the grouping mechanism.

Grouping is handled through `layer_tag`.

### 3. Each scene object belongs to exactly one layer

For the current design:

- one shape belongs to one layer
- one annotation belongs to one layer
- one measurement belongs to one layer
- one layer may contain many objects

### 4. `layer_tag` is the grouping channel

When creating an object:

- if `layer_tag` is explicitly provided, use it
- if `layer_tag is None`, fall back to the object's own `tag`

### 5. Layers are flat

Layers contain scene objects, not other layers.

Nested layers are intentionally out of scope for this slice.

### 6. Camera/geometry naming

Use:

- `get_center()` for object geometry
- `focus()` for camera focus + framing
- `recenter_view()` for changing the view center without a full refocus

## Public Model In Practice

The intended feel of the public API is now materially in place:

- `view.shapes["s1"].hide()`
- `view.shapes["s1"].show()`
- `view.shapes["s1"].delete()`
- `view.shapes["s1"].focus()`
- `view.annotations["a1"].hide()`
- `view.measurements["m1"].delete()`
- `view.layers["group1"].hide()`

These are no longer just design aspirations; they are the working direction of
the live codebase.

## What Still Remains

### 1. Extend rich mutability to more shape families

Still pending:

- review whether any remaining shape families still need first-class mutability
  rather than the current create/delete/recreate path
- decide whether the next worthwhile slice should be:
  - richer geometric setters,
  - stronger frontend object identity,
  - or color-system migration on top of the new scene-object model

### 2. Reduce legacy compatibility paths

Still pending:

- continue removing assumptions from the old monolithic/layer-first model
- reduce remaining fallback behavior where a single object still implicitly
  behaves like an old-style layer
- keep tightening `arg_digestion` only where real exact-caller dependencies
  still exist

### 3. Frontend identity model can still improve

Current state is already much better, but still not the final form:

- object interaction works through the current bridge,
- grouping semantics are stronger in Python,
- but the frontend can still move further toward explicit scene-object identity
  rather than historical tag-oriented assumptions.

### 4. Viewer package extraction is not “finished forever”

The package split is in place and stable, but there is still follow-up work:

- continue trimming `core.py` when a clean conceptual boundary appears
- keep docs aligned with the package layout
- avoid re-growing a new monolith inside `core.py`

## Recommended Next Steps

If continuing this refactor, the recommended order is:

1. extend rich mutability to the next most useful shape family
2. keep consolidating frontend identity/interaction semantics for shapes
3. continue reducing leftover legacy compatibility paths
4. only then evaluate whether another structural split inside `viewer/` is
   justified

## Source of Truth Around This Refactor

Use these files together:

- `devguide/TMP_shape_layer_tag_checkpoint.md`
- `devguide/pending_closure_2026_04_08.md`
- `devguide/checkpoints.md`

And in code:

- `molsysviewer/viewer/`
- `molsysviewer/layers.py`
- `molsysviewer/annotations.py`
- `molsysviewer/measurements.py`
- `molsysviewer/shapes/`

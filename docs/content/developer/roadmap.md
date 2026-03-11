# Roadmap

This page is public on purpose.
It captures current engineering direction toward `1.0`, not a frozen promise list.

## Current Position

MolSysViewer already has a solid core:

- Python facade centered on `MolSysView`
- TypeScript runtime split into handlers
- native MolSys payload loading
- regions / layers / whole abstractions
- live structural editing (`append_structures`, `set`, `add`, `remove`)
- replayable HTML export
- popup host + popup baseline synchronization
- major scientific overlay families

The main work is no longer “make the basic viewer exist”.
The main work is:

- expanding product capability,
- stabilizing feature breadth,
- and keeping runtime contracts solid while that surface grows.

## Priority Toward 1.0

### 1. Advanced Operations via `molsysviewer.tools`

Direction:

- keep `MolSysView` relatively small;
- grow advanced operations in `molsysviewer.tools`.

Current state:

- `molsysviewer.tools.basic.concatenate_structures(...)` exists as the first pure composition primitive.

Planned next:

- `merge_views(...)`
- additional `tools.basic` composition helpers
- later, analysis / structure / topology / hbonds-oriented tool modules as their responsibilities become concrete

### 2. Richer Interaction on the Canvas

High-value 1.0 direction:

- hover behavior for atoms / regions / overlays
- pointer semantics and picking
- tooltips / lightweight UI feedback
- callbacks or event bridges for interaction-driven workflows
- shared highlight / selection flows

### 3. Overlay Maturity

Important for 1.0:

- pockets
- pharmacophore features
- channel tubes
- labels
- additional primitives such as points / arrows / cylinders

This means both:

- rendering quality,
- and reliable behavior across replay / export / rebuild flows.

### 4. Visibility / Export / Popup Breadth

The baseline contracts are already in place.
What remains is broader coverage and more edge-case confidence for:

- visibility combinations,
- export continuity,
- popup synchronization,
- and interaction between these systems.

### 5. Incremental Runtime Improvements

Longer-range, but already part of the design direction:

- more Mol*-native incremental updates
- better trajectory/update handling
- eventual Level B state-tree integration instead of full reload/replay in some paths

This is not the immediate `1.0` blocker.

## What Is Already Done

These are no longer roadmap wishes; they are implemented realities:

- loading MolSysMT-compatible systems into the viewer
- trajectory-capable MolSys payload path
- tag-based regions / layers / shape registration
- core camera helpers and HTML export
- pocket / blob / tube / ellipsoid / pharmacophore / tetrahedra / triangle-face overlays
- live editing with rebuild/replay contracts

## What Is Still Missing or Incomplete

- broader `tools` surface
- richer interaction and picking
- some overlay families still need visual/behavioral refinement
- public docs still lag behind current implementation in several places
- JS tests still do not cover the full runtime surface

## Non-Goals for the Immediate Next Step

These are valuable, but not the next move:

- broad support-library hardening for its own sake
- full Mol* incremental architecture rewrite
- performance/engine expansion before the feature surface is mature

## Immediate Next Step

The immediate direction is:

1. keep roadmap/docs aligned with real repository state
2. continue growing `molsysviewer.tools`
3. move next into user-facing product features such as interaction and overlay maturity

## Long-Term Vision

MolSysViewer should become the visualization layer of the UIBCDF ecosystem:

- viewer-centric
- MolSysMT-aware
- strong in scientific overlays
- robust in notebooks, exports, and synchronized multi-view workflows

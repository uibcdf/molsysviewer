# The view opens zoomed in and the wheel will not zoom out

**Reported by hand, 2026-07-31, JupyterLab. Diagnosed and measured 2026-08-01.
Fix designed, not yet implemented.**

The mechanism, the conditions that hide it, and the shape of the fix are written
up as **`scene_contracts.md` Contract S9**. This file tracks only what is left to
do and what is still unknown.

## Symptom

```python
v = demo["181L"]
v.whole.set_representation("cartoon")          # <- removing this line fixes the camera
v.regions.add("molecule_type=='protein' and group_index<40",
              tag="helice", representation="cartoon", color="orange")
v.measurements.add_distance(selection_a=[434], selection_b=[975], tag="larga")
v.annotations.add_annotation("extremo", atom_indices=[434], tag="nota")
v
```

Everything renders correctly, but the view opens inside the molecule and the
wheel will only zoom in. Right-click → "Reset view" recovers it.

## Cause, in one line

The representation swap leaves the scene empty long enough for Mol\* to collapse
`camera.state.radiusMax` to 0.01, and the trackball then clamps the camera to
`radiusMax * 1000` on the next frame it draws — permanently, because the clamp
writes `camera.position`. Full chain and measurements: Contract S9.

## Work remaining

1. **DONE — take camera authority at plugin init** (S9 mechanism B):
   `camera.manualReset: true` and `trackball.autoAdjustMinMaxDistance: off`, plus
   one explicit `requestCameraReset()` once a load has content, with a re-request
   if `radiusMax` is still 0. Measured: trackball bound 1e150 instead of 305,
   `radiusMax` immovable at 30.534 through a swap that otherwise collapses it, and
   framing after load identical to the default configuration (79.79).
   Supersedes the per-mutation guard, which was the third wrong-shaped answer to
   this defect: it needed a definition of "finished" nothing supplies, had to be
   remembered at every call site, and did not close the `requestCameraReset` hole.
   Judge the behaviour change explicitly: Mol\*'s opportunistic re-framing is lost,
   and `minDistance` reverts from 5 to 0.01.
2. **DONE — in-place representation update.** Update the existing
   `StructureRepresentation3D` transform's `type` (with its colour and size
   themes) instead of removing and rebuilding, for the case where the state tree
   shape is unchanged: `msg.representation` set, no `preset`, no `user_preset`.
   Measured, both arms building *cartoon*: 760 ms empty rebuilding, **0 ms** in
   place; by mutation, removing the branch takes that 0 back to 2960 ms.

   Its reach is narrower than it looked: the loader's preset registers **four**
   global representations (polymer, ligand, water, …), so the *first*
   `set_whole_representation` after a load collapses four nodes into one — a change
   of tree shape no parameter edit can express, and the reported case. **Closed by
   add-before-remove**, below.
3. **DONE — `repairCameraAfterSwap` was never committed.** Discarded once camera
   authority made it unnecessary; S9 records why repair is the wrong shape.
4. ~~Make camera resets wait for the scene.~~ **No longer needed** if item 1
   lands: with `autoAdjustMinMaxDistance` off, `resolveCameraReset` is a no-op on
   an empty scene, so a `reset_view` arriving mid-mutation is harmless instead of
   a trap. Kept here as a record of why the ordering machinery was dropped.
5. **DONE — audited the other scene-emptying and scene-hiding paths.**

   The audit's answer is that there is nothing to fix, and *why* is the point:
   camera authority is taken once per controller, at creation, so it covers every
   path that exists and every path that will exist. Had the per-mutation guard been
   chosen instead, this item would have been a list of call sites to edit and a
   standing obligation to remember — which is the drift pattern S9 rejects.

   Paths confirmed to empty or hide the scene, all now harmless: the four loader
   entry points, `clear_scene` / `clearAll` / `clearShapesByTag`, region
   representation changes, `handleShowHideGlobal` (hide the whole while its regions
   have not drawn), layer and scene-object visibility, and annotation/measurement
   removal. Hiding matters as much as emptying, because the `p.maxDistance` vector
   keys on `boundingSphereVisible` rather than on existence.

   One incidental finding, filed separately below: the loader's
   `clearGlobalRepresentations` callback is a **no-op**
   (`viewer-controller.ts:1487`), with a comment that admits it was never resolved
   — `/* handled by state via events usually, but direct call needed? */`. It is
   called on all four load paths. Harmless today, because replacing the structure
   node removes its descendants and `currentGlobalRepresentationRefs()` filters
   refs whose cells are gone. But a callback that does nothing, named for something
   important, is a trap for whoever next assumes it works.

8. **Resolve the no-op `clearGlobalRepresentations`.** Either implement it or delete
   it and the callback from `LoaderHandlers`. Leaving a question mark in a comment
   is not a decision.
6. **DONE — signal when the invariant breaks** (`CATALOG` + `CODES`). Not a repair — the
   camera is never moved behind the user — but a camera left inside the scene
   bounding sphere after a mutation is never a framing anyone chose, and saying so
   turns a silent, unexplainable viewer into a diagnosable one. The same imprecise
   condition that made *repair* unacceptable is fine for *detection*: a false
   positive costs a log line instead of a camera that jumps. It also guards the
   guard, which depends on Mol\* internals that will change.

7. **DRAFTED — report upstream to Mol\*.** Ready to file at `molstar/molstar`:
   `upstream_molstar_empty_scene_camera_bounds.md`, with both patches, the
   measurements and runnable reproductions. The case is stronger than "we disagree with a
   design choice": **Mol\* already encodes the right rule, in two places, and
   skips it in two others.**

   - `Camera.update()` opens with `if (snapshot.radiusMax === 0) return false`
     (`camera.js:22`) — an empty scene means *do not act*. The trackball's
     `checkDistances()` (`controls/trackball.js:404`) does not honour it and
     clamps anyway, writing `camera.position` irreversibly.
   - In `resolveCameraReset`, `camera.setState` is guarded by `if (radius > 0)`
     while `controls.setProps({ minDistance, maxDistance })` three lines above it
     is not (`canvas3d.js:678-691`), so an empty scene still pins the trackball
     bound at `maxDistanceMin` (20).

   The fix to propose is **not** a `=== 0` test downstream — the bound reaches 0.01
   rather than exactly 0, so such a test would miss this very case. It is to stop
   deriving the bound from an empty scene at all: gate the `radiusMax` update in
   `commitScene` (`canvas3d.js:744`) on the scene having content, and move the
   `autoAdjustMinMaxDistance` block inside the `radius > 0` guard that its
   neighbour already uses.

   A patch with a reproduction lands far more often than prose, and the
   reproduction exists: `probe:representation-swap-emptiness` and
   `probe:camera-authority`. Precedent for the format: the MolSysMT
   `viewer_json_conversion_deep_copies_twice` report.

## Still unknown

In the headless harness Mol\* rescues the camera on its own: emptying the scene
makes `commitScene` request a camera reset, and that reset re-frames the
structure. **Something suppresses that rescue in a real session** — a camera
transition in progress or a pending reset snapshot both cancel it
(`canvas3d.js:702`), and a real session has camera traffic the harness has none
of (widget bootstrap, popup camera sync).

This does not block the fix — layer 2 prevents the damage whether or not the
rescue would have fired — but it is worth knowing, because anything that suppresses
Mol\*'s auto-reset will also suppress it in cases we have not thought about.

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

1. **Take camera authority at plugin init** (S9 mechanism B):
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
2. **Layer 1 — in-place representation update.** Update the existing
   `StructureRepresentation3D` transform's `type` (with its colour and size
   themes) instead of removing and rebuilding, for the case where the state tree
   shape is unchanged: `msg.representation` set, no `preset`, no `user_preset`.
   Measured at 0 ms empty in every condition tested, and it produced a scene
   identical to the current path (bounding radius 31.142038731724032 from both).
   Keep remove-then-add as the fallback for the preset branches.
3. **Remove `repairCameraAfterSwap`** from `state-handlers.ts`. It was the first
   attempt and is superseded by both layers above; S9 records why repair is the
   wrong shape. The e2e `camera-survives-representation-swap.e2e.ts` should be
   rewritten with it, asserting `radiusMax` during the window rather than where
   the camera ended up.
4. ~~Make camera resets wait for the scene.~~ **No longer needed** if item 1
   lands: with `autoAdjustMinMaxDistance` off, `resolveCameraReset` is a no-op on
   an empty scene, so a `reset_view` arriving mid-mutation is harmless instead of
   a trap. Kept here as a record of why the ordering machinery was dropped.
5. **Audit the other scene-emptying *and scene-hiding* paths**:
   `clearGlobalRepresentations()` on the load path, `clear_scene`, the rebuild
   after `apply_system_edit`, region representation changes, and layer visibility.
   Hiding matters as much as emptying: the `p.maxDistance` vector keys on
   `boundingSphereVisible`, so a scene that is fully present but fully hidden does
   the same damage.
6. **Signal when the invariant breaks** (`CATALOG` + `CODES`). Not a repair — the
   camera is never moved behind the user — but a camera left inside the scene
   bounding sphere after a mutation is never a framing anyone chose, and saying so
   turns a silent, unexplainable viewer into a diagnosable one. The same imprecise
   condition that made *repair* unacceptable is fine for *detection*: a false
   positive costs a log line instead of a camera that jumps. It also guards the
   guard, which depends on Mol\* internals that will change.

7. **Report upstream to Mol\*.** The case is stronger than "we disagree with a
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

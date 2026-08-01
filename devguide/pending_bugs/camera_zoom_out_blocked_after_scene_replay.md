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

1. **Layer 2 — the camera-authority guard.** Hold `camera.manualReset` for the
   duration of a scene mutation, and on exit set the bound once from the finished
   scene. Verified in a probe to keep `radiusMax` at 31.14 where it otherwise
   collapses to 0.01. Needs a real answer to "when has the mutation finished"
   (see S9, *The open question*), including a deadline so a failed mutation cannot
   leave camera authority suspended forever.
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
4. **Audit the other scene-emptying paths** against layer 2:
   `clearGlobalRepresentations()` on the load path, `clear_scene`, the rebuild
   after `apply_system_edit`, region representation changes, layer visibility.

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

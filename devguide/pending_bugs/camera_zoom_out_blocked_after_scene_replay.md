# The view opens zoomed in and the wheel will not zoom out

**Reported by hand, 2026-07-31, JupyterLab.** Not reproduced in the headless
harness yet — this file records what was measured so the next attempt starts
from evidence rather than from the same three hypotheses.

## Symptom

Building a scene and *then* displaying the view:

```python
v = demo["181L"]
v.whole.set_representation("cartoon")
v.regions.add("molecule_type=='protein' and group_index<40",
              tag="helice", representation="cartoon", color="orange")
v.measurements.add_distance(selection_a=[434], selection_b=[975], tag="larga")
v.annotations.add_annotation("extremo", atom_indices=[434], tag="nota")
v
```

Everything renders correctly, but the camera opens zoomed into the middle of the
system. The scroll wheel only zooms **in**; it will not zoom out. Right-click →
"Reset view" recovers the whole system.

Noticed immediately after Contract S8 (`scene_contracts.md`) made these messages
arrive at all, so the scene now lands in a burst right behind the structure —
which is the obvious suspect and, so far, is *not* supported by measurement.

## What was measured

`camera.state.radiusMax` is what bounds zoom-out in Mol\*. Three probes were run
against a real browser (Playwright + Chromium), on the real 181L structure:

**1. Spaced messages, 300 ms apart.** After `set_whole_representation("cartoon")`
the camera bound collapses:

| step | radiusMax | sceneRadius | drawn |
|---|---:|---:|---:|
| after load | 30.53 | 30.53 | 4 |
| after set_whole_representation | **0.01** | null | **0** |
| after create_region | **0.01** | null | **0** |
| after add_distance_measurement | 30.93 | 30.93 | 3 |

**2. Does it recover on its own?** Yes. Sampling every 500 ms with nothing else
sent, `radiusMax` returns to 31.14 at **+1.5 s**, when the cartoon finishes
building. The collapse is the window in which the swap has removed the old
representation and the new one has not drawn yet — transient, self-healing, and
therefore **not** the reported defect on its own.

**3. The exact Python sequence, back to back, no delays.** The camera settles at
`radiusMax 30.93, distance 80.82`, identical to what `reset_view` produces. **The
burst does not reproduce it.**

A first probe using a synthetic poly-ALA chain showed the same collapse for
`cartoon` but not for `ball_and_stick` or `spacefill` — that was the fixture, not
the code: residues 1 Å apart are not a traceable backbone, so cartoon drew
nothing. Recorded because it is exactly the kind of result that would have been
published as a finding.

## What is therefore still unexplained

The harness reproduces neither the persistent bound nor the zoomed-in camera.
What the harness does **not** exercise, and what the user's path does:

- the **array-native load** (`load_molsys_array_payload`) rather than
  `load_structure_from_string` — structurally identical in the loader
  (`loader-handlers.ts`, no camera call in either), but not verified end to end;
- the real widget bootstrap: `initial_messages`, the `ready` handshake, and the
  camera snapshot traffic that exists once a popup is or has been open;
- a canvas that is resized by the notebook layout after first paint.

## Leads worth pulling first

- `state-handlers.ts:1518` restores a camera snapshot after a representation swap
  when `intentionalViewpoint && shouldRestoreCameraSnapshot(snap)`. The guard
  rejects `radius === 0` (Mol\*'s never-framed default) but **accepts 0.01**,
  which is exactly the value a collapsed empty scene produces. The snapshot is
  captured at the *start* of the swap (`:1387`), so it should be healthy — but a
  *second* swap that begins during the collapse window would capture 0.01 and
  restore it. The user's scene contains two swaps (`set_whole_representation`
  then `set_region_representation`).
- Whether `intentionalViewpoint` is already true at bootstrap: the wheel
  subscription in `ensureCameraInputTracking` marks it on the user's *first*
  scroll, which is also the moment they discover they cannot zoom out.

## Acceptance

An e2e that drives the widget seam (not the bare controller), replays this exact
scene, and asserts `camera.state.radiusMax` is within a few percent of
`canvas3d.boundingSphere.radius` once the scene is idle — plus the mutation check
that it fails when the guard at `:1518` is loosened.

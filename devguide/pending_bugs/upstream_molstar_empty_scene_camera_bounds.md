# Upstream (Mol\*): an empty scene is treated as a scene of radius zero

**Ready to file at `molstar/molstar`. Written 2026-08-01 from the investigation in
`camera_zoom_out_blocked_after_scene_replay.md` and `scene_contracts.md` Contract
S9. Not yet submitted.**

Our own fix is in place and does not depend on this being accepted; what upstream
acceptance would retire is the two `isHidden` params we now rely on, and with them
the runtime detection that exists only because those params could change semantics
silently.

---

## Title

Camera is permanently displaced when the scene is transiently empty during a
representation swap

## Summary

While a representation is being replaced, the scene is momentarily empty. Mol\*
derives the camera bounds from that empty scene and the trackball then clamps the
camera against them — writing `camera.position`, so the move survives the scene
coming back. The user is left inside the structure with the wheel unable to zoom
out, and only "Reset view" recovers.

**Mol\* already has the right rule and applies it in two places while skipping it
in two others**, which is why this reads as an inconsistency rather than a design
choice.

## Where

- `Camera.update()` opens with `if (snapshot.radiusMax === 0) return false;`
  (`mol-canvas3d/camera.ts`) — an empty scene means *do not act*.
- `TrackballControls.checkDistances()` (`mol-canvas3d/controls/trackball.ts`) does
  **not** honour it. It clamps to
  `min(max(camera.state.radiusMax * 1000, 0.01), p.maxDistance)` on every
  `update(t)` — every frame, not only on input — and assigns `camera.position`.
- `Canvas3D.commitScene()` re-derives the bound unconditionally:
  `camera.setState({ radiusMax: getSceneRadius() })`, where
  `getSceneRadius() = scene.boundingSphere.radius * sceneRadiusFactor` is ~0 for an
  empty scene.
- `Canvas3D.resolveCameraReset()` guards `camera.setState` with `if (radius > 0)`
  but leaves `controls.setProps({ minDistance, maxDistance })` three lines above it
  **ungated**, so an empty or fully hidden scene pins the trackball bound at
  `maxDistanceMin` (20).

## Measured

On 181L (bounding radius ~30.5, camera framed at ~80), swapping the global
representation to cartoon while the viewer is still settling from the load:

| | value during the window |
|---|---:|
| `camera.state.radiusMax` | **0.01** (from 30.5) |
| trackball `p.maxDistance` | **20** (from 305) |
| effective bound | 10 |

With `radiusMax` forced to 0.01 on an otherwise untouched scene, the camera moved
from **79.79 to exactly 10** — `radiusMax * 1000` — within five frames. The bounds
recover when the geometry lands. The camera does not.

## Suggested fix

Two small changes, each restoring a rule the surrounding code already applies:

1. In `commitScene`, do not derive the bound from a scene that has no content:

   ```diff
   -    if (!p.camera.manualReset)
   +    if (!p.camera.manualReset && scene.boundingSphere.radius > 0)
            camera.setState({ radiusMax: getSceneRadius() }, 0);
   ```

2. In `resolveCameraReset`, move the `autoAdjustMinMaxDistance` block inside the
   `if (radius > 0)` guard its neighbour already uses.

**Please do not add a `radiusMax === 0` test downstream in `checkDistances`.** It
would miss this case: the bound reaches **0.01**, not exactly 0, because
`Camera.setState` floors the radius. The problem is deriving a bound from an empty
scene at all, not the exact value that comes out.

## Reproduction

Both probes live in this repository and run against Chromium via Playwright:

```bash
cd molsysviewer/js
npm run probe:representation-swap-emptiness   # the empty window itself
npm run probe:camera-authority                # the bounds collapsing, and holding
```

The condition matters: the window only opens when the representation change lands
while the viewer is **still settling from the load**. On a settled viewer the swap
is clean, which is why this is easy to miss by hand.

It also needs a canvas that is actually drawing — the clamp runs per frame, so a
headless harness that draws once when idle will not show it.

## Our workaround

Set at plugin init, so no call site has to remember it:

```ts
canvas3d.setProps({
    camera: { manualReset: true },
    trackball: { autoAdjustMinMaxDistance: { name: "off", params: {} } },
});
```

with framing then requested explicitly once a load has content. Both params are
`isHidden`, which is the reason for filing this: a release that changes their
meaning would remove our protection silently.

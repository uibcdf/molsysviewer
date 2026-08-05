# Report the empty-scene camera bounds defect to Mol\*

**Filed 2026-08-05 as [molstar/molstar#1903](https://github.com/molstar/molstar/issues/1903).
Waiting for a maintainer's answer before offering the patch.**

Verified against `master` at `26216e9b1` (5.11.0) on the day it was filed: all
three links in the chain are unchanged — `commitScene`'s unguarded
`camera.setState({ radiusMax: getSceneRadius() })` (`canvas3d.ts:959`), the
`autoAdjustMinMaxDistance` block outside the `if (radius > 0)` guard beside it
(`canvas3d.ts:886-893`), and `checkDistances` assigning `camera.position` every
frame (`trackball.ts:493, 543`), while `Camera.update()` still refuses to act on
`radiusMax === 0` (`camera.ts:99`).

**Next step is theirs.** If the direction is accepted, the two-line patch is
ready and the prize is not the fix — we already carry Contract S9 — but retiring
the workaround: today it depends on two parameters Mol\* marks `isHidden`, and a
change in their *semantics* would remove our protection silently, compiling and
green. `camera_stranded_inside_scene` in the smonitor catalog exists for exactly
that. If they decline, that detector becomes permanent and should be documented
as such rather than left looking temporary.

## Why this is a proposal and not a bug of ours

The defect is Mol\*'s. We already carry a fix — `scene_contracts.md` Contract S9,
implemented in `takeCameraAuthority` — and it works. But it works by setting two
parameters Mol\* declares `isHidden`:

```ts
canvas3d.setProps({
    camera: { manualReset: true },
    trackball: { autoAdjustMinMaxDistance: { name: "off", params: {} } },
});
```

They are typed, so a Mol\* release that *removes* either breaks our build loudly. A
release that changes their *semantics* — say `manualReset` stops gating the
`radiusMax` derivation — would remove our protection **silently, with everything
still compiling and every test still green**. That risk is the whole reason
`camera_stranded_inside_scene` exists in the smonitor catalog.

So this is not about fixing something for us. It is about retiring a workaround
that currently has to be permanent, along with the runtime detection that only
exists to guard it. If upstream takes the patch, we delete both.

The case is unusually strong, and that is worth saying when filing: **Mol\* already
applies the rule in two places and skips it in two others.** It is an internal
inconsistency, not a design disagreement, which is the form most likely to be
accepted quickly.

Our own investigation is in `devguide/archive/camera_zoom_out_blocked_after_scene_replay.md`
and Contract S9. Everything a maintainer needs is reproduced self-contained in the
issue body below — deliberately, since nobody upstream can run our probes.

---

## Title

```
Camera is permanently displaced when the scene is momentarily empty (bounds derived from an empty scene)
```

## Body

````markdown
### Summary

While a representation is being replaced, the scene is momentarily empty. Mol*
derives the camera bounds from that empty scene, and `TrackballControls` then
clamps the camera against them — assigning `camera.position`, so the displacement
survives the scene coming back. The user is left inside the structure with the
wheel unable to zoom out; only "Reset view" recovers.

Mol* already applies the right rule in two places and skips it in two others, so
this reads as an inconsistency rather than a design choice:

- `Camera.update()` opens with `if (snapshot.radiusMax === 0) return false;` — an
  empty scene means *do not act*.
- `Canvas3D.resolveCameraReset()` guards `camera.setState` with `if (radius > 0)`.

but

- `TrackballControls.checkDistances()` clamps regardless, on **every** `update(t)`
  — every frame, not only on user input — and writes `camera.position`.
- `Canvas3D.commitScene()` re-derives the bound unconditionally with
  `camera.setState({ radiusMax: getSceneRadius() })`, and
  `getSceneRadius() = scene.boundingSphere.radius * sceneRadiusFactor` is ~0 for an
  empty scene.
- In `resolveCameraReset`, the `controls.setProps({ minDistance, maxDistance })`
  three lines *above* that guard is not covered by it, so an empty or fully hidden
  scene pins the trackball bound at `maxDistanceMin` (20).

### Minimal reproduction

No timing luck required — this isolates the mechanism from the swap that triggers
it. In the console of any Mol* viewer with a structure loaded and framed:

```js
const c3d = viewer.plugin.canvas3d;
const d = () => {
    const s = c3d.camera.state;
    return Math.hypot(s.position[0] - s.target[0],
                      s.position[1] - s.target[1],
                      s.position[2] - s.target[2]);
};

d();                                        // e.g. 79.79, correctly framed
c3d.camera.state.radiusMax;                 // e.g. 30.53

// Exactly what an empty scene produces, with the scene left untouched:
c3d.camera.setState({ radiusMax: 0.01 });

// after a few rendered frames:
d();                                        // 10  — camera moved, permanently
```

10 is `max(radiusMax * 1000, 0.01)`. Restoring `radiusMax` afterwards does not
bring the camera back, because `checkDistances` assigned `camera.position`.

### How it happens for real

Replace the global representation of a ~1500-atom structure with `cartoon` while
the viewer is **still settling from the load**. Measured on 181L:

| | during the window |
|---|---:|
| scene empty | 20–1020 ms (varies per run) |
| `camera.state.radiusMax` | **0.01**, from 30.5 |
| trackball `p.maxDistance` | **20**, from 305 |
| effective bound | 10, where the framed distance is ~80 |

Two conditions make it easy to miss:

- On a **settled** viewer the swap is clean — the removal and the build coalesce
  and there is no empty commit. It only reproduces when the change lands while the
  viewer is still building from the load.
- The clamp runs per frame, so a canvas that is idle or offscreen never shows it.
  A headless harness that draws once when idle will report everything fine.

### Suggested fix

Two small changes, each restoring a rule the surrounding code already applies:

1. `Canvas3D.commitScene()` — do not derive the bound from a scene with no content:

   ```diff
   -    if (!p.camera.manualReset)
   +    if (!p.camera.manualReset && scene.boundingSphere.radius > 0)
            camera.setState({ radiusMax: getSceneRadius() }, 0);
   ```

2. `Canvas3D.resolveCameraReset()` — move the `autoAdjustMinMaxDistance` block
   inside the `if (radius > 0)` guard its neighbour already uses.

Please **not** a `radiusMax === 0` test downstream in `checkDistances`: it would
miss this case, because `Camera.setState` floors the radius and the bound reaches
**0.01**, not exactly 0. The problem is deriving a bound from an empty scene at
all, not the particular value that comes out of it.

### Workaround, for anyone hitting this before a fix lands

```js
canvas3d.setProps({
    camera: { manualReset: true },
    trackball: { autoAdjustMinMaxDistance: { name: 'off', params: {} } },
});
```

with framing then requested explicitly (`canvas3d.requestCameraReset()`) once a
load has content. Note that `manualReset` also disables Mol*'s own camera reset,
which is otherwise what quietly recovers from this — so the explicit request
becomes required, not optional.
````

---

## After filing

- Record the issue number here.
- When it lands, `takeCameraAuthority` and the `camera_stranded_inside_scene`
  catalog entry can both go, together with the note in Contract S9 about hidden
  parameters — but only once the minimum supported Mol\* version includes the fix.
  That version floor is a deliberate decision, not something to inherit silently.

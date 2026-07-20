# Camera jumps (or view goes blank) when applying a representation

**Status:** Root mechanism located, fix pending (needs visual iteration)
**Severity:** high — one symptom leaves the viewer apparently empty

## Symptoms (dogfooding, recorrido 2, on the `.bcif.gz` demos)

**1. Unexpected zoom/focus.** With the widget already displayed:

```python
v = msv.demo["1TCD"]
v            # cell 1 — renders fine
# cell 2
v.whole.set_representation("cartoon")
v.whole.set_color_scheme("chain-id")
```

Both chains render in cartoon with correct colors, but the camera zooms/focuses
unexpectedly. Only *Reset view* brings back the previous framing.

**2. Nothing visible at all.** Same calls, but issued *before* displaying the
widget (the natural notebook flow of configuring and then showing):

```python
v = msv.demo["1TCD"]
v.whole.set_representation("cartoon")
v.whole.set_color_scheme("chain-id")
v            # nothing is shown
```

## Mechanism

`StateHandlers.setWholeRepresentation` (`src/managers/handlers/state-handlers.ts`)
already tries to protect the camera:

```ts
// line ~1236, before the swap
const cameraSnap = this.plugin.canvas3d?.camera.getSnapshot?.();
// ... removes and re-adds the global representations ...
// line ~1356
if (cameraSnap) {
    await PluginCommands.Camera.SetSnapshot(this.plugin, { snapshot: cameraSnap, durationMs: 0 });
}
```

Its own comment states that removing then re-adding representations *"can trigger
Mol*-internal camera adjustments"*. Two ways this safeguard falls short:

- **Symptom 1:** if the Mol*-internal adjustment happens *after* `SetSnapshot`
  (on a later render tick), it overwrites the restore. Note the user flow calls
  `setWholeRepresentation` twice (`set_representation`, then `set_color_scheme`,
  which re-applies the representation), so the second call snapshots an
  already-perturbed camera.
- **Symptom 2:** in the configure-before-display flow the calls are replayed
  through `initial_messages` during init, so `getSnapshot()` runs with the camera
  **not yet initialized** (no canvas size, no structure bounding box). Restoring
  that snapshot pins the camera to a meaningless state — the structure is
  rendered but never in view.

Message ordering was **ruled out** as a cause: `enqueueMessage` in `src/index.ts`
serializes messages through a promise chain (`await controller.handleMessage`),
and `initial_messages` are awaited before `ready` is emitted.

## Fix directions (to evaluate with a visual run)

- Do not restore a snapshot that is not a valid, initialized camera state (guard
  on canvas size / structure bounding box / non-zero radius). In the init path
  there is no user view worth preserving — let Mol* frame the structure.
- Restore the camera *after* Mol*'s own adjustment settles (e.g. after the next
  render tick) rather than immediately after the state commit.
- Consider not re-applying the whole representation at all for a pure color
  change — see `restyle_toggles_water_visibility.md`, where `set_color_scheme`
  rebuilding the representation also causes visibility side effects. Fixing that
  would remove one of the two swaps in this flow.

## Related

- `restyle_toggles_water_visibility.md` — same root habit: `set_color_scheme`
  re-applies the representation instead of only recoloring.

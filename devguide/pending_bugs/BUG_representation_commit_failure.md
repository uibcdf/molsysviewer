# BUG: `set_representation` fails to render due to missing State Commit in frontend

## Description
Any attempt to change the representation of a region or the whole system (using manual types like `licorice`, `spacefill`, etc.) fails to update the canvas. The old representations are removed, but the new ones are never displayed, eventually leading to an empty viewer if the baseline is hidden.

## Steps to Reproduce
1. Load a structure: `view.load('1CRN')`.
2. Create a region: `core = view.new_region(selection='1<=group_id<10', tag='nucleo')`.
3. Set representation: `core.set_representation(representation='spacefill')`.
4. Hide the global view: `view.whole.hide()`.
5. **Observed Result:** The viewer is empty. The `spacefill` representation was never rendered.

## Technical Analysis
In `molsysviewer/viewer.js`, the methods `setGlobalRepresentation` and `setRegionRepresentation` construct a state update using `this.plugin.state.data.build()`.

However, in the branch that handles manual representations (non-presets), the code performs:
```javascript
const repr = this.plugin.builders.structure.representation.buildRepresentation(
  update,
  { ref: componentRef },
  { type: reprType, ... },
  { tag }
);
// MISSING: await update.commit();
```
Without the `await update.commit()`, Mol* never applies the changes to the actual render tree. Interestingly, the code *does* call `commit()` in the `createRegion` method, which is why initial regions might work if created with a representation, but fail when updated via `set_representation`.

## Proposed Solution
Add `await update.commit({ revertOnError: false });` after building the representation in both `setGlobalRepresentation` and `setRegionRepresentation` branches in `viewer.js`.

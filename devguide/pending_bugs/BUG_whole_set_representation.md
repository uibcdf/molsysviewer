# BUG: `view.whole.set_representation()` fails to update global visualization after initial load

## Description
After loading a molecular system using `view.load()`, the Mol* viewer automatically applies a default representation (typically `cartoon`). Any subsequent attempt to change this global representation using `view.whole.set_representation(representation='...')` has no visual effect in the viewer, even though the internal Python state is updated correctly.

## Steps to Reproduce
1. Initialize the viewer: `view = msv.MolSysView()`
2. Load a structure: `view.load('1CRN')` -> Visualized in `cartoon` (Mol* default preset).
3. Attempt to change global representation: `view.whole.set_representation(representation='spacefill')`
4. **Observed Result:** The protein remains in `cartoon` style.
5. Test visibility: `view.whole.hide()` -> The viewer becomes empty.
6. Show again: `view.whole.show()` -> The `cartoon` reappears, but never the `spacefill`.

## Expected Behavior
The global representation should immediately replace the default style (`cartoon`) with the newly requested style (`spacefill`, `point`, etc.).

## Technical Analysis & Hypothesis
After auditing the `viewer.js` code (specifically `setGlobalRepresentation`) and `load_molsysmt.py`, the following has been identified:

1. **Initialization Orphans:** The initial loading method (`loadStructureFromMolSysPayload` in JS) uses `applyPreset(trajectory, "default")`. This preset creates Mol* representations (like the cartoon) that are **not registered** in the `this.globalReprs` collection.
2. **Cleanup Failure:** The `setGlobalRepresentation` method attempts to clear the scene by iterating over `this.globalReprs`. Since the initial representations are not there, the original `cartoon` is never removed.
3. **State Tree Persistence:** When adding the new global representation (e.g., `spacefill`) to the same structure node, Mol* keeps both representations alive. Due to priority in the graphics engine or errors in state commitment, the initial representation (`cartoon`) prevails or the new one fails to coexist with the original preset.
4. **Indiscriminate Visibility:** `view.whole.hide()` works because the `handleShowHideGlobal` method in JS iterates over all non-region representations of the structure node, capturing both the "orphans" and the new ones, hiding them all. However, upon calling `show()`, the state returns to the original conflict point.

## Possible Solution
- Ensure that representations created by the "default" preset during `load` are added to `this.globalReprs`.
- Alternatively, modify `setGlobalRepresentation` to perform a deep clean of all non-region representations before applying the new style.
- Review if the structure node returned by the preset is suitable for attaching new manual representations.

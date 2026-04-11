# BUG: UX "Remove Selection" action does not work

## Description
The user-facing action to "Remove" a selection (via context menu or UI button) fails to modify the scene or the underlying molecular system.

## Steps to Reproduce
1. Load a system and select a set of atoms interactively.
2. Trigger the "Remove" action from the viewer's UI.
3. Observe the canvas and `view._molsys.n_atoms`.
4. **Observed Result:** No atoms are removed from the view or the system.

## Potential Cause
There may be a disconnect between the frontend event message and the Python handler for structural removal, or the `view.remove()` logic is not being correctly invoked from the UI layer.

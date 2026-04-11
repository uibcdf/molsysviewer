# BUG: picking/selection fails for atoms added via second `load()` (additive)

## Description
When a second molecular system is loaded into an existing viewer session (triggering the additive/add logic), the atoms from the new system are visible in the canvas but cannot be selected via mouse clicks. Only the atoms from the first load remain interactive.

## Steps to Reproduce
1. Load first structure: `view.load('1CRN', label='A')`.
2. Select an atom from 'A' -> **Success**.
3. Load second structure: `view.load('1BNA', label='B')`.
4. Attempt to click an atom from 'B' in the viewer.
5. Check `view.active_selection.info()` -> **Observed Result:** Remains empty or refers to previous selection.

## Hypothesis
The Mol* "Picking" and "Selection" states are not being fully rebuilt or synchronized when new atoms are appended to the structure state. The frontend might still be using the atom index map from the initial load.

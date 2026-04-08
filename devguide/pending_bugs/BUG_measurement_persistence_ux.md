# BUG/UX: Interactive measurements lack automatic persistence and clarity on atom selection

## Description
When creating measurements (distances, angles, etc.) via the viewer's context menu or keyboard shortcuts, the resulting visual elements (lines and labels) are "volatile". They do not appear in `view.measurements.info()` or the internal message history until explicitly saved using `view.measurements.persist_last_measurement()`. Furthermore, there is no visual or API feedback indicating which atoms are being used for the calculation when selecting hierarchical elements (like residues in cartoon mode).

## Steps to Reproduce
1. Load a structure in cartoon mode: `view.load('1CRN')`.
2. Interactively create a distance measurement between two residues (Right-click -> Distance).
3. Check the measurements in Python: `view.measurements.info()` -> **Observed Result:** Returns an empty list `[]`.
4. Persist the measurement: `view.measurements.persist_last_measurement()`.
5. Check again: `view.measurements.info()` -> **Observed Result:** Now shows the measurement, but the `picks_atom_indices` contains full lists of atoms for each residue.

## Identified Issues
1. **Lack of WYSIWYG Persistence:** Users expect that if a measurement is visible on the canvas, it is part of the state. Volatile measurements are lost upon notebook reload or HTML export.
2. **Computational Ambiguity:** In `cartoon` mode, selecting a residue calculates the distance between **centroids** of all atoms in that residue. There is no indication to the user that they are not measuring specific atoms (like Alpha Carbons), nor a way to toggle this behavior easily.

## Proposed Improvements
1. **Automatic Persistence:** Every measurement created in the UI should be automatically registered in the Python `measurements` history.
2. **Transparency in Selection:**
   - Defaulting to centroids for group selections is a reasonable default, but the viewer should provide a way to specify "Representative Atom" (e.g., CA for proteins, P for DNA) for measurements.
   - The API should clearly distinguish if a measurement endpoint is a single atom or a centroid.
3. **Interactive Metadata:** Add a property or method to `info()` (e.g., `view.measurements.active_interactive_measurements`) to see current canvas-only elements before they are "hardened" into the state, or simply unify them.

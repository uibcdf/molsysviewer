# BUG: `new_region` fails to render even with initial representation

## Description
The creation of new regions via `view.new_region()` does not produce any visual output in the canvas, even when a valid representation (e.g., `spacefill`) is provided at creation time. This occurs both with MolSysMT selections and with manual `atom_indices`.

## Steps to Reproduce
1. Load a structure: `view.load('1CRN')`.
2. Create a region with manual indices and style: `view.new_region(atom_indices=list(range(50)), tag='test', representation='spacefill')`.
3. Observe the canvas.
4. **Observed Result:** No spheres or changes are visible. The original `cartoon` remains.

## Technical Analysis
Although `Region.atom_indices` is correctly populated in Python (e.g., 59 atoms for a selection), and the message is sent to the frontend, Mol* fails to render the new `StructureComponent`. This could be due to:
1. An issue in the `Bundle.fromSelection` logic in `viewer.js`.
2. The component being created but marked as invisible or having 0 opacity by default.
3. A failure in the `addRepresentation` call within `createRegion`.

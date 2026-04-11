# PROPOSAL: Comprehensive Overhaul of `view.info()`

## Problem Statement
The current implementation of `view.info()` is a first draft that needs refinement to become a truly useful diagnostic tool. It currently lacks clarity and does not adequately distinguish between the **Molecular System Data** and the **Viewer's Visual State**.

## Proposed Changes
1.  **Tabular/Structured Output:** Ensure the output is formatted as a clean summary (using DataFrames or similar if available) that clearly lists:
    *   Structural blocks (Loads) and their labels.
    *   Active regions and their corresponding atom counts.
    *   Current global representation and visibility.
2.  **Dual-Context Reporting:** Explicitly separate "Molecular Metadata" (n_atoms, n_residues) from "Viewer Metadata" (active layers, camera focus, active selection).
3.  **Active Structure Tracking:** Include the current structure index (frame) in the viewer metadata section to synchronize Python's awareness with the frontend slider.
4.  **Argument for Source:** Support `source='molsys'`, `source='view'`, or `source='all'` to allow users to filter the amount of information displayed.
4.  **Integration with Additive Loading:** `info()` should reflect the `_n_atoms_per_load` history to show how the system was built.

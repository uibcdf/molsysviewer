# Proposal: Studio Subpanels Refactoring

**Status:** proposed (design discussion).

**Scope:** The organization and taxonomy of the **Studio** sidebar subpanels in MolSysViewer. This document defines the refactored 10-subpanel sidebar, the interaction delegation between sidebar tabs and the canvas right-click context menu, and outlines a roadmap for post-1.0 features.

---

## 1. The Refactored Studio Taxonomy (10 Subpanels)

To prevent subpanels from becoming catch-all groups (such as the old "Overlays" and "Viewport") and to expose baseline system styling (`view.whole`), the Studio navigation sidebar (180px width, vertical scrolling) is reorganized into 10 focused subpanels:

1.  **System:** Structural metadata, loaded workspaces, and the chain-level list with visibility toggles.
2.  **Global (Whole):** Visual configuration (`view.whole`) of the baseline molecular structure: presets, 12 representation styles, base opacity (alpha), quality, and base coloring.
3.  **Selection:** Atom selections and query composition. Includes the manual-validation query composer (`Check`/`Enter`), predefined selection chips, naming forms, and the selection history (`Undo`/`Redo`).
4.  **Regions:** Card list of represented custom regions (`view.regions`), per-card styling composers, complementary regions, z-fighting overlap warnings, and the boolean region composer (Union, Intersection, Difference).
5.  **Measures:** Inspector and manager of quantitative geometry metrics (`view.measurements`). Shows list of active distances, angles, and dihedrals.
6.  **Annotations:** Qualitative text labels (`view.annotations`) pointing to specific atoms or residues.
7.  **Shapes:** Analytical and decorative 3D geometric primitives (arrows, spheres, cylinders, best-fit planes, orientation axes) placed in the scene.
8.  **Layers:** Logical group tag organizer (`view.layers`). Lists active grouping tags (`layer_tag`) and provides bulk actions (bulk visibility toggle, bulk delete).
9.  **Viewport:** Live camera and render configurations: perspective vs. orthographic projection, background color presets, and camera spin/swing animations.
10. **Export:** Publication-quality file output generator: PNG snapshot parameters (transparency, resolution scale) and standalone HTML webpage export.

---

## 2. Context Menu Delegation & Refinement Resolutions

### A. Selection Picking Level (Clicking Granularity)
*   **Decision:** Move mouse selection granularity controls (select by Atom, Residue, Chain, or Entity) to the **canvas right-click context menu** rather than the Selection sidebar.
*   **Detailed Proposal:** See [canvas_picking_level.md](file:///home/diego/repos@uibcdf/molsysviewer/devguide/pending_proposals/canvas_picking_level.md).

### B. Interactive Measurements Builder
*   **Decision:** Keep 3D interactive measurement creation (Distance, Angle, Dihedral) mapped to the **canvas right-click context menu** (where it is already implemented).
*   **Interaction Flow:**
    1.  The user right-clicks an atom on the canvas and selects `Distance`, `Angle`, or `Dihedral`.
    2.  This activates the visual tool status overlay (e.g., "Distance Tool: Click endpoint 2").
    3.  Once the user clicks the endpoint atoms in the 3D viewport, the measurement is created on the backend.
    4.  The new measurement is registered and automatically appears in the **Measures** sidebar subpanel for inspection, renaming, layering, and deletion.
*   **Sidebar Role:** The **Measures** subpanel functions purely as a manager/inspector (non-interactive registry), avoiding the need to write complex 3D raycasting events in the sidebar itself.

### C. Split-Screen Viewport Sinking (Multi-View Sync)
*   **Decision:** Split-screen viewport synchronization is moved out of the Studio subpanels scope.
*   **Detailed Proposal (Post-1.0):** See [multiview_split_screen.md](file:///home/diego/repos@uibcdf/molsysviewer/devguide/pending_proposals/multiview_split_screen.md).

---

## 3. Post-1.0 Roadmap

1.  **Movie Keyframe timeline Editor (Movie Factory):** An interactive keyframe composition timeline for camera paths, zooms, and custom molecular movies.
2.  **Advanced Overlay styling:** Customizing label fonts, line thicknesses, dashed rendering styles for hydrogen bonds, and custom measurement coloring.

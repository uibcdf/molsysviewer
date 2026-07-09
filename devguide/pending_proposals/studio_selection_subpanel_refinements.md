# Proposal: Selection Subpanel Refinements (Manual Checking & Context Menu Expanders)

**Status:** Proposed — **paused** (2026-07-08), deferred while the Regions subpanel is
prioritized (`studio_region_subpanel.md`).  
**Author:** Antigravity AI & Diego  
**Date:** 2026-07-08  

---

## 1. Context & Objectives (Why)

Based on real-world smoke tests of the Studio Selection subpanel in Jupyter notebooks, two major design bottlenecks have been identified:

1.  **Noise during query typing:** The query composer previously validated the search string on every keystroke via a 250ms debounce. Because a query is syntactically incomplete while typing, this led to constant red error badges ("✗ invalid syntax") and kernel overhead, disrupting the user's typing flow.
2.  **Cluttered and misallocated expanders:** The Supra-atomic supra-atomic levels (`group`, `component`, etc.) and the Spatial expander (`within Å`) were placed inside the static sidebar. This cluttered the layout and deviated from direct-canvas interaction. These operations naturally belong in the 3D viewer's context menu (right-click).

This proposal outlines the design changes and a step-by-step implementation plan to resolve both issues.

---

## 2. Proposed Changes (What & How)

### Part A: Manual Query Verification ("Check" Button)

Instead of checking the query string on every keystroke, verification is triggered explicitly by the user.

*   **UI Changes:**
    *   Add a `Check` button next to the query composer input.
    *   **Layout:**  
        `[ Selection Query Input               ] [Check] [Syntax ▾] [?]`
*   **Behavioral Flow:**
    1.  **Draft State:** While typing, no preview requests are sent to the Python kernel. The preview status remains at a neutral `idle` state (e.g., showing *"Press Enter or Check to verify"* in muted text).
    2.  **Explicit Verification:** The query check is dispatched only when:
        *   The user clicks the `Check` button.
        *   The user presses the `Enter` key while focused on the query input.
    3.  **Typing Reset:** If the user resumes typing after a check, the preview status returns to `idle` (or a minor "dirty" indicator) to avoid displaying stale counts or error messages.

---

### Part B: Context Menu Selection Expanders

Remove the expansion controls from the sidebar and place them in the canvas context menu (right-click).

*   **UI Changes:**
    *   Remove the `data-molsysviewer-selection-expander-panel` (supra-atomic buttons and spatial expander row) from the `GroupPanel` Selection tab.
    *   Extend [context-menu.ts](file:///home/diego/repos@uibcdf/molsysviewer/molsysviewer/js/src/ui/context-menu.ts) to display a new section of selection actions.
*   **Contextual Scenarios:**
    1.  **Right-click on a Structure Target (Atom/Residue):**
        *   Show an **"Expand Selection to..."** group containing:
            *   `Group` (Residue)
            *   `Component`
            *   `Molecule`
            *   `Chain`
            *   `Entity`
        *   Show a **"Spatial Expansion..."** option:
            *   `Select within 5 Å` (with common quick-presets like 3 Å, 5 Å, 8 Å, or an option triggering a prompt/inline dialog).
    2.  **Right-click on Empty Canvas (if `active_selection` is non-empty):**
        *   Show the same **"Expand Selection to..."** and **"Spatial Expansion..."** options relative to the currently active selection, along with a `Clear Active Selection` action.
*   **Action Routing:**
    *   Context menu click handlers will emit the existing `expand_selection` action with the respective payload (`{ level: "group" | "chain" | ... }` or `{ level: "spatial", distance_angstroms: X }`), reusing the backend controller logic.

---

## 3. Step-by-Step Implementation Plan

### Phase 1: Manual Check Button & Input Form Keypress Handler
1.  In `GroupPanel.renderSelectionSection` ([group-panel.ts](file:///home/diego/repos@uibcdf/molsysviewer/molsysviewer/js/src/ui/group-panel.ts)), create a `Check` button styled with secondary variables.
2.  Append it to the `inputRow` flex layout.
3.  Remove `scheduleSelectionQueryPreview()` and the `input` event listener from the text field.
4.  Add a `keypress` event listener to the text input that triggers the preview request on `Enter`.
5.  Wire the `Check` button click event to trigger the preview request.
6.  Add an `input` listener to set the preview status back to `idle` when typing resumes.

### Phase 2: Relocate Expanders to the Context Menu
1.  Remove the code generating `expandPanel` in `GroupPanel.renderSelectionSection` ([group-panel.ts](file:///home/diego/repos@uibcdf/molsysviewer/molsysviewer/js/src/ui/group-panel.ts)).
2.  In [context-menu.ts](file:///home/diego/repos@uibcdf/molsysviewer/molsysviewer/js/src/ui/context-menu.ts), update the `open()` method:
    *   For target `structure`, append buttons for expanding to group, chain, molecule, and spatial contacts.
    *   For target `empty`, if the current active selection has `count_atoms > 0`, append the same selection expander buttons.
3.  Verify that clicking these buttons dispatches the correct `expand_selection` actions to Python.

### Phase 3: Update Test Suite & Walkthroughs
1.  Update the unit tests in [group-panel.test.ts](file:///home/diego/repos@uibcdf/molsysviewer/molsysviewer/js/tests/unit/group-panel.test.ts):
    *   Change test actions that relied on keypress debouncing to click the `Check` button instead.
    *   Verify the check button trigger matches the expected `selection_query_preview_request` output.
2.  Update context menu unit tests to cover the new expansion buttons.
3.  Verify that all Python tests in `tests/test_active_selection.py` still pass.

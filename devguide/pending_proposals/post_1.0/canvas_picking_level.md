---
summary: Configurable canvas picking granularity via the context menu.
issue: uibcdf/molsysviewer#45
status: open
opened: 2026-07-30
closed:
verification: inspected
area: [interaction]
guard:
normative:
blocked_by: []
supersedes: []
---

# Proposal: Canvas Picking Level Selection via Context Menu

**Status:** post-1.0 design.

**Scope:** Canvas right-click context menu integration for toggling mouse interaction picking granularity.

---

## 0. Verified current behavior

The correctness concern that originally raised this proposal is resolved.
`ActiveSelectionController.setFromAtomIndices()` restricts each group item to
the exact incoming atom indices. The unit test
`ActiveSelectionController can rebuild a group-centric selection from atom
indices` requires `[3, 4]` to remain `[3, 4]`.

Picking granularity is therefore only a mouse-interaction preference. It does
not rewrite a selection stated by Python, and this proposal is no longer a
scientific-correctness blocker.

---

## 1. Why

Currently, clicking on the 3D canvas selects atoms or residues based on the viewer's default interaction mode. However, users often need to select different structural granularities on the fly—for example, clicking to select a single **Atom** (e.g., for detailed distance measurement), a **Residue** (for standard binding pocket highlighting), or a whole **Chain** / **Entity** (for global component adjustments).

To make this granularity setting highly interactive and context-aware, this proposal places the picking level selector directly in the **canvas right-click context menu**, rather than inside the sidebar.

---

## 2. Interaction Design (UI/UX)

1.  **Context Menu Entry:** When the user right-clicks anywhere on the canvas (on an atom, shape, measurement, or empty space), the context menu displays a **Selection Level** cascading submenu:
    ```
    ┌──────────────────────────────────────────────┐
    │ Focus Target                                 │
    │ Selection Level ▸  ( ) Atom                  │
    │ Distance           (•) Residue (default)     │
    │ Angle              ( ) Chain                 │
    │ ...                ( ) Entity                │
    └──────────────────────────────────────────────┘
    ```
2.  **Visual State:** The submenu options display radio buttons showing the active picking level.
3.  **Behavior:** Clicking a level (e.g., *Chain*) instantly updates the cursor's interaction behavior. Subsequent left-clicks on the canvas will select the entire chain associated with the clicked atom.

---

## 3. Implementation Details (How)

1.  **Frontend (`js/src/ui/context-menu.ts`):**
    *   Add a `selection_level` option to the context menu action builders.
    *   Render a nested list of radio buttons for the options: `atom`, `residue`, `chain`, `entity`.
    *   On selection, dispatch a message to the Mol* plugin controller to set the picking level.
2.  **Mol\* Controller Integration:**
    *   Access the Mol* selection manager: `this.plugin.managers.structure.selection`.
    *   Set the picking granularity by modifying the target element selection level in Mol* (e.g., setting the active focus/interaction granularity).
3.  **Python Integration:**
    *   Since mouse picking is a pure frontend layout state, no Python IPC message is required for the act of clicking itself. However, the resulting indices of the selection event will be broadcast to the Python backend via the existing `active_selection` channels, automatically respecting the chosen granularity.

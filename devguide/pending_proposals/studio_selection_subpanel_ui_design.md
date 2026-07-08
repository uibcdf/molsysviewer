# Proposal: Studio → Selection Subpanel UI Design & Implementation Spec

**Status:** implemented (retained as the UI/UX reference).
**Scope:** UI/UX styling, layout structure, and frontend-backend synchronization for the **Selection Subpanel** of the **Studio** panel in MolSysViewer.

This document serves as the high-fidelity visual and UX specification, supplementing the core architectural blueprint in `studio_selection_subpanel.md`.

---

## 1. Motivation & Design Goals

The Selection subpanel is a central, visual tool for managing the viewer's active and saved selections. Since MolSysMT query expressions (`molecule_type == "protein"`, `group_index in [10, 15]`) are powerful but have a learning curve, the interface must be **self-documenting, visual, and highly responsive**.

Key Objectives:
1.  **Ergonomics:** Clear hierarchical layout with glassmorphic accents.
2.  **Education:** Preset chips and inline helper sheets that teach the query grammar dynamically.
3.  **Efficiency:** Immediate action buttons (Union, Subtract, Intersect) instead of sticky global modes.
4.  **Network-Safety:** Optimized communication paths to prevent kernel/WebSocket flooding in remote JupyterHub sessions.

---

## 2. Interface Layout (ASCII Blueprint)

A developer implementing the subpanel should construct the HTML/TS hierarchy matching the following visual layout:

```
================================================================================
                    STUDIO workspace -> Subpanel: SELECTION
================================================================================

┌── [Section A] ACTIVE SELECTION CARD (Glassmorphic Card) ──────────────────────┐
│  Toolbar:  [ All ]  [ None ]  [ Invert ]                                      │
│                                                                               │
│  ● 22 atoms selected                                                          │
│    group level                                                                │
│                                                                               │
│  [ ↶ Undo ]  [ ↷ Redo ]                                [ → Region ] [ → Label]│
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section B] SELECT BY QUERY (Query Composer & Helpers) ─────────────────────┐
│                                                                               │
│  🔍 [ Enter MolSysMT query...                                            ] ❓  │
│       Syntax: [ MolSysMT | Indices ▼ ]                                        │
│                                                                               │
│  Presets: (protein ✕) (water ✕) (backbone ✕) (sidechain ✕) (ligand ✕)         │
│                                                                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐  │
│  │     + Union     │ │   - Subtract    │ │   ∩ Intersect   │ │  ⤩ Invert   │  │
│  │ Add matching to │ │ Remove matching │ │ Keep only comm. │ │ Select other│  │
│  │ current selection││  from current   │ │  with current   │ │    atoms    │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────┘  │
│                                                                               │
│  Validation Status: "✓ Matches: 45 atoms" (Updates dynamically on debounce)   │
│                                                                               │
│  Hierarchical Expanders:                                                      │
│  [ Group ]  [ Component ]  [ Molecule ]  [ Chain ]  [ Entity ]                │
│                                                                               │
│  Spatial Expander:                                                            │
│  Distance: [ 5.0 ] Å   [ Expand Selection ]                                   │
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section C] SAVED SELECTIONS (Gestor de Favoritos) ─────────────────────────┐
│                                                                               │
│  ■ Cys-62 Ligand (14 atoms · group level)                                     │
│    [ Activate ]  [+ Union]  [- Sub]  [∩ Int]  [ Rename ] [→ Region] [→ Label] [🗑]
│  ───────────────────────────────────────────────────────────────────────────  │
│  ■ Active Site Residues (82 atoms · group level)                              │
│    [ Activate ]  [+ Union]  [- Sub]  [∩ Int]  [ Rename ] [→ Region] [→ Label] [🗑]
│  ───────────────────────────────────────────────────────────────────────────  │
│  ■ Bound Water (9 atoms · atom level)                                         │
│    [ Activate ]  [+ Union]  [- Sub]  [∩ Int]  [ Rename ] [→ Region] [→ Label] [🗑]
│└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details & Interactions

### A. Active Selection Card
*   **Stats:** Dynamically bound to `active_selection` properties. Displays the number of atoms, groups, and the selection level (e.g. `group level` derived from `element_level`).
*   **Quick Toolbar:** Actions for `All` (selects everything), `None` (clears active selection), and `Invert` (selects the inverse).
*   **Undo/Redo History:** Managed **entirely in the TS frontend** to guarantee zero-latency recovery from misclicks, avoiding round-trips to the Python kernel.
*   **History Invalidation:** When the molecular system is rebuilt or edited (via `apply_system_edit` or load actions), the frontend selection history stack must be **cleared immediately** to prevent restoring invalid or corrupted atom indices.
*   **Promote Buttons:** `[→ Region]` and `[→ Label]` (for 3D text annotation) are explicitly named text-anchored buttons to prevent icon collisions with the system color-scheme toggle.

### B. Query Composer (Select by Query)
*   **Syntax Selector:** Dropdown letting the user switch between `MolSysMT` query strings and explicit `Indices` list formats.
*   **Validation Badge:** Debounces query input (250ms delay). Sends a preview message to the backend. If valid, displays the green checkmark and matching count. If invalid, displays a red cross and "Invalid syntax" without throwing console exceptions.
*   **Preset Chips:** Includes `protein`, `water`, `backbone`, `sidechain`, and `ligand`. Clicking a chip injects its exact string representation into the query input field.
*   **Cheat Sheet (`[?]`):** Expands a sliding list showing syntax examples for quick copy-pasting.
*   **Expansion buttons:** 
    *   *Hierarchical:* Expand active selection to whole groups/components/chains.
    *   *Spatial:* Perform a distance expander. The input distance (in Ångstroms) is evaluated as a native MolSysMT selection query (e.g., `all within X of selection`) routed through `view.select()` as defined in the core proposal (avoiding separate backend contact calculations).

### C. Saved Selections Manager
*   **Saved Rows:** Displays named selections sorted alphabetically.
*   **Composition Controls:** Each saved row exposes buttons for:
    *   `[Activate]`: Replaces the current active selection with the saved selection's indices.
    *   `[+ Union]`: Combines the saved selection with the active selection.
    *   `[- Sub]`: Subtracts the saved selection from the active selection.
    *   `[∩ Int]`: Intersects the saved selection with the active selection.
*   **Management Controls:** Each row includes inline buttons for `[Rename]`, `[→ Region]`, `[→ Label]`, and `[🗑]` (Delete), matching the promotion capabilities of the active card.
*   **Name Collision Handling:** When saving a selection, if the tag already exists, the panel prompts the user with `[Rename]`, `[Overwrite]`, or `[Cancel]`.

---

## 4. Graphic Style & CSS Design System

To match the dark-mode aesthetic of MolSysViewer, the subpanel should use the following tokens and rules:

```css
/* Color Palette */
--bg-sidebar: #12131a;
--bg-card: rgba(255, 255, 255, 0.03);
--bg-card-hover: rgba(255, 255, 255, 0.06);
--border-subtle: rgba(255, 255, 255, 0.08);
--accent-indigo: #6366f1;
--accent-indigo-glow: 0 0 12px rgba(99, 102, 241, 0.25);

/* Active Selection Card Glassmorphism */
.active-selection-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
  border: 1px solid var(--border-subtle);
  backdrop-filter: blur(12px);
  border-radius: 8px;
  padding: 12px;
}

/* Glowing input fields on focus */
.query-input:focus {
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: var(--accent-indigo-glow);
  outline: none;
}

/* Row animations */
.saved-row {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.saved-row:hover {
  background-color: var(--bg-card-hover);
}
.saved-row.is-active {
  border-left: 3px solid var(--accent-indigo);
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.05) 0%, transparent 100%);
}
```

---

## 5. Programming & Backend Synchronization

To keep the application highly responsive and prevent code duplication, the subpanel's frontend triggers actions that map to the molsysviewer public APIs and MolSysMT backend adapters.

1.  **Backend Method Contracts:** All operations (Replace, Union, Subtract, Intersect, Invert, Expansion, and Distance Queries) must route through the verified python methods detailed in **§6 (Architecture / How)** of the main proposal (`studio_selection_subpanel.md`).
2.  **Opt-in Hover Telemetry:** Hover target updates are a global contract concern (as noted in `interaction_targets_and_selection.md`). They must not be turned on by default for the subpanel to prevent remote WebSocket flooding unless a python callback or flag is actively listening.

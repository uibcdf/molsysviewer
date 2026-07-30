# Studio Subpanel — Interactions (UI Design Specification)

**Status:** Post-1.0 UI specification (2026-07-24). Companion to [the Interactions domain spec](interactions_domain.md).
**Visual Language:** Standard Studio Workbench design system (`panels/ui-helpers.ts`).  

---

## 1. Overview & Core Purpose

The **Interactions** subpanel manages scientifically derived atom–atom relations (hydrogen bonds, salt bridges, $\pi$-stacking, hydrophobic contacts, halogen bonds) across single structures and multi-frame trajectories.

Unlike anonymous geometric shapes, an **`InteractionSet`** is a scientific object defined by a **reproducible criterion** (or explicit pair mapping), tracking per-frame topology, contact persistence ($\%$, $0.0\text{–}1.0$), and count series over time.

This document specifies the UX/UI layout, interaction flow, and frontend-to-backend seam contracts for **`InteractionsPanel`**.

---

## 2. Layout & Structure

The subpanel follows the established 3-part Studio layout:

```
┌─ Interactions ────────────────────────────────────── [3] ─┐
│                                                           │
│  • 2 of 3 interaction sets visible   [ Show all ] [ Hide ]│
│                                                           │
│  New interaction set                                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Mode: (•) Criterion   ( ) Explicit   ( ) File/DF    │  │
│  │ Kind: [ Hydrogen Bond (H-Bond)                  ▼ ] │  │
│  │ Target A: [ Anchor A ] (Ligand / 12 atoms)          │  │
│  │ Target B: [ Anchor B ] (Active Site / 45 atoms)     │  │
│  │ Criterion: [ Luzar-Chandler                     ▼ ] │  │
│  │ Cutoffs: Dist: [ 0.35 ] nm   Angle: [ 30 ] °        │  │
│  │ [ Calculate & Create Interactions ]                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  Saved interaction sets                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ • site_hbonds                                       │  │
│  │   hbond · 4 active edges · 85% avg persistence      │  │
│  │   [ Focus ] [ 👁 ] [ Edit ] [ 🗑 ]                   │  │
│  │   Timeline: [ ██████████░░░████████ ] 3/4 (85%)     │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## 3. Section 1: Top Status & Visibility Card

Located immediately below the `Interactions` header:

```
┌────────────────────────────────────────────────────────┐
│  • 2 of 3 interaction sets visible   [ Show all] [Hide]│
└────────────────────────────────────────────────────────┘
```

*   **Status Indicator Dot:** Green (`#34d399`) with subtle glow when at least one interaction set is visible; neutral gray (`rgba(244,244,245,0.28)`) when empty or all hidden.
*   **Readout:** `X of Y interaction sets visible`.
*   **Global Actions:** Compact **`[ Show all ]`** and **`[ Hide all ]`** buttons dispatching `show_all_interactions` and `hide_all_interactions`.

---

## 4. Section 2: `New interaction set` Form

The creation card provides a tabbed/mode-driven creation flow matching the three data sources defined in `interactions_domain.md`:

### 4.1 Mode A: Criterion-Based (Calculated via MolSysMT or Mol*)
Used for automatic calculation of hydrogen bonds, salt bridges, or $\pi$-stacking based on scientific criteria:

*   **Kind Dropdown:** Select interaction type (`Hydrogen Bond`, `Salt Bridge`, `Pi-Stacking`, `Hydrophobic Contact`, `Halogen Bond`).
*   **Engine Radio:** `(•) MolSysMT (Exact)` vs `( ) Mol* (GPU/Fast)`.
*   **Target Staging Buttons:**
    *   **`[ Anchor A ]`**: Captures selection for group A (e.g. `Ligand (12 atoms)`).
    *   **`[ Anchor B ]`**: Captures selection for group B (e.g. `Active Site (45 atoms)`).
*   **Criterion & Cutoffs:**
    *   Criterion selector (e.g. `Luzar-Chandler`, `Buch`).
    *   Distance cutoff input (in `nm`, e.g. `0.35 nm`).
    *   Angle cutoff input (in degrees, e.g. `30 °`).
*   **Initial Style Parameters:**
    *   Color picker (`#34d399`).
    *   Line pattern (`Solid` / `Dashed`).
    *   Opacity slider ($0.0\text{–}1.0$).
*   **Creation Button:** **`[ Calculate & Create Interactions ]`** dispatches `create_interaction`.

### 4.2 Mode B: Explicit Pair Mapping
Used when a Python script pre-calculates atom pairs per frame (`0: [(3, 105), (12, 204)]`).

### 4.3 Mode C: File / Third-Party Data
Used when importing interaction tables directly from Pandas DataFrames or external analysis pipelines (ProLIF, PLIP, GetContacts).

---

## 5. Section 3: `Saved interaction sets` Cards

Each saved `InteractionSet` renders as a card in the list:

### 5.1 Collapsed Card (Clean View)
```
┌────────────────────────────────────────────────────────┐
│  • site_hbonds                                         │
│    hbond · 4 active edges · 85% avg persistence       │
│    [ Focus ] [ 👁 ] [ Edit ] [ 🗑 ]                    │
│                                                        │
│  Persistence timeline:                                 │
│  [  ██████████░░░████████  ] (Frame 12/50: 3 bonds)    │
└────────────────────────────────────────────────────────┘
```

*   **Primary Identity:** Name/tag (`site_hbonds`), kind (`hbond`), active edge count, and average persistence ($\%$ of trajectory frames where contacts exist).
*   **Button Bar (`btnRow`):**
    *   **`[ Focus ]`**: Centers the 3D camera on the interaction network centroid.
    *   **`[ 👁 / ⦻ ]`**: Toggles visibility of the interaction set.
    *   **`[ Edit ]`**: Expands/collapses the inline edit sub-form.
    *   **`[ 🗑 ]`**: Deletes the interaction set.
*   **Persistence Timeline Sparkline:** Visual bar showing contact frequency across frames. Hovering or scrubbing displays per-frame bond counts.

### 5.2 Expanded Card (`[ Edit ]` Clicked)
```
┌────────────────────────────────────────────────────────┐
│  • site_hbonds                                         │
│    hbond · 4 active edges · 85% avg persistence       │
│    [ Focus ] [ 👁 ] [ Edit ] [ 🗑 ]                    │
│ ────────────────────────────────────────────────────── │
│  [ Input: site_hbonds____________ ] [ Rename ]         │
│  [ Input: user-layer_____________ ] [ Set layer ]      │
│                                                        │
│  Style & Thresholds:                                   │
│  Colour:    [ █ #34d399 ]   Pattern: [ Dashed ▼ ]      │
│  Radius:    [ 0.05 ] nm     Alpha:   [======o==] 0.85  │
│  Min Persistence Filter: [====o========] >= 50%       │
└────────────────────────────────────────────────────────┘
```

---

## 6. Action Seam & Message Contracts

`InteractionsPanel` communicates with the Python backend (`molsysviewer/viewer/panel_actions/scene_objects.py`) via the standard action seam:

| Frontend Action | Target Backend Handler | Payload Arguments |
| :--- | :--- | :--- |
| `create_interaction` | `create_interaction` | `kind`, `mode`, `atom_indices_a`, `atom_indices_b`, `criterion`, `cutoffs`, `color`, `pattern`, `alpha`, `tag` |
| `toggle_interaction_visibility` | `toggle_interaction_visibility` | `tag` |
| `rename_interaction` | `rename_interaction` | `tag`, `new_tag` |
| `set_interaction_layer` | `set_interaction_layer` | `tag`, `layer` |
| `delete_interaction` | `delete_interaction` | `tag` |
| `set_interaction_style` | `set_interaction_style` | `tag`, `color`, `pattern`, `radius`, `alpha` |
| `set_interaction_filter` | `set_interaction_filter` | `tag`, `min_persistence` |
| `show_all_interactions` | `show_all_interactions` | — |
| `hide_all_interactions` | `hide_all_interactions` | — |

---

## 7. History & Coalescing Discipline

*   Slider modifications (`Alpha`, `Radius`, `Min Persistence Filter`) invoke `begin_scene_history_coalescing` on `focus`/`pointerdown` and `end_scene_history_coalescing` on `change`/`blur`.
*   This ensures that continuous slider drags produce a single undo/redo transaction in scene history (Contract S6).

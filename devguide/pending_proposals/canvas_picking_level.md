# Proposal: Canvas Picking Level Selection via Context Menu

**Status:** proposed (design).

**Scope:** Canvas right-click context menu integration for toggling mouse interaction picking granularity.

---

## 0. The granularity is not only a picking preference — it is lossy today

Found while validating the scene contracts in a real browser (2026-07-11), and it raises the
stakes of this proposal.

The active selection is not held as a set of atoms. It is held as **group-level items**:
`ActiveSelectionController.setFromAtomIndices()` builds a Mol\* loci and immediately passes it
through `lociToGroupItems()`. So an atom-level selection coming **from Python** is snapped up to
whole groups.

Concretely: `view.active_selection.set([0, 1])`, where atoms 0, 1, 2 are one residue, comes back
from the frontend as a **three-atom** selection. Python asked for two atoms and the canvas selected
three. (`js/tests/e2e/selection-subpanel.e2e.ts` documents this at the point where a shift-click
composes to six atoms rather than five.)

That is defensible as a *canvas* interaction default — you rarely want to click half a residue —
but it is applied to the backend echo too, where nobody chose it. Whatever this proposal decides,
it should decide **whether a picking level is a canvas-interaction setting or a property of the
active selection itself**, and whether a Python-set selection is allowed to be rewritten by it.

### 0.1 Proposed answer (2026-07-12): snapping is a *mouse* rule, not a *selection* rule

The picking level exists to make **clicking** pleasant — nobody wants to click half a residue.
It has no business rewriting a selection that **Python stated exactly**.

> `view.active_selection.set([0, 1])` must come back as **two** atoms.

So: `lociToGroupItems()` applies to **pointer input only**. A selection arriving from the API is
taken literally, and the picking level is what it always should have been — a property of the
*canvas interaction*, not of the *active selection*.

**Cost, stated honestly.** The active selection is currently *held* as group-level items, so this
is not a one-line change: the model becomes atom-level and the snapping moves to the input edge.
The visible consequence is that a Python-set selection may highlight **part of a residue**, which
is exactly what was asked for and will look unfamiliar.

**Not in the scene-objects block.** It touches the active-selection model, which that block does
not open. Flagged here so the decision is taken deliberately rather than inherited.

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

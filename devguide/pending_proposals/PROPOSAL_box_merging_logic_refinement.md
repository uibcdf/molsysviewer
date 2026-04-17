> **TEMPORALMENTE IGNORADA** — Esta propuesta depende de una API de MolSysMT
> que aún no existe (acceso por-frame a los vectores de caja). No se puede
> implementar en MolSysViewer hasta que MolSysMT exponga esa interfaz.
> Ignorar en las sesiones de desarrollo hasta nueva orden.

# PROPOSAL: Refine Box Merging and Appending Logic

## Problem Statement
When merging multiple molecular systems or adding frames to a trajectory, the handling of the unit cell (box) must be consistent and deterministic. Currently, it is not explicitly defined which box should be displayed when multiple systems with different unit cells are combined.

## Proposed Rules

### 1. Merging / Additive Loading (`add()`)
Follow MolSysMT's convention:
- The **first loaded system's box** takes precedence and becomes the active box for the merged view.
- If the first system lacks a box but the second has one, the second's box is adopted.
- If both have boxes, only the first is kept.

### 2. Appending Structures (`append_structures()`)
Maintain frame-specific boxes:
- Each structure (frame) should carry its own unit cell data.
- The `view.show_box()` method should render the box corresponding to the currently displayed structure (frame).
- This is vital for NPT ensemble simulations where the box volume fluctuates over time.

## Benefits
- **Consistency:** Aligns the viewer's visual context with the underlying data model's hierarchy.
- **Scientific Accuracy:** Ensures that dynamic box information is correctly represented during trajectory playback.

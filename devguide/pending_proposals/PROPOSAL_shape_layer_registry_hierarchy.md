# PROPOSAL: Dual Shape/Layer Registry Hierarchy and Shape Mutability

## Problem Statement
The current architecture in `molsysviewer` collapses the identity of geometric objects (`Shapes`) into visibility groups (`Layers`). When multiple shapes are added with the same tag, they become an indistinguishable part of a single `Layer` object. Python loses the ability to address, modify, or query individual shapes once they are sent to the frontend.

## Proposed Architecture

1.  **Global Shape Registry:**
    *   Implement a central registry for all geometric objects (`view.shapes.registry`).
    *   Each shape (sphere, link, etc.) must have its own unique `tag`.
    *   Example: `view.shapes['s1']` returns a specialized object with properties (color, center, radius).

2.  **Global Layer Registry:**
    *   Maintain the existing `view.layers` as a management system for visibility and logical grouping.
    *   Each `Layer` can contain one or more `Shapes`.

3.  **Association at Creation:**
    *   When adding a shape, users can specify both its own `tag` and a `layer` tag.
    *   Example: `view.shapes.add_sphere(center=[0,0,0], tag='s1', layer='l1')`.
    *   If `layer` is not provided, it defaults to the shape's `tag` (legacy behavior) or a global "default" layer.

4.  **Hierarchical Access:**
    *   A `Layer` object should expose its members: `view.layers['l1'].shapes` returns a list or dictionary of `Shape` objects.
    *   This allows users to reason about "visibility groups" while still having access to individual geometric entities.

5.  **Dynamic Mutability (Live Update):**
    *   Shape objects should implement setter methods: `view.shapes['s1'].set_color(0xFF0000)`.
    *   These methods should emit a specific "update" operation (e.g., `update_shape_property`) to the frontend without requiring the deletion and recreation of the entire layer or shape.

## Benefits
- **Granular Control:** Users can change the appearance of one specific item within a complex scene (e.g., highlighting a specific interaction site).
- **Logical Grouping:** Complex objects made of multiple shapes (like a pharmacophore feature or a channel tube) can be hidden/shown as a single unit via the `Layer` API while remaining individually editable.
- **Efficiency:** Sending partial updates to the frontend (color, opacity) is significantly faster than a full "delete and re-create" cycle.
- **Improved UX:** Avoids the confusion of "orphaned" or "ghost" visual elements that cannot be interacted with from Python.

## Implementation Path
- Refactor `ShapesManager` to maintain a registry of shape instances.
- Enhance the `Layer` class to track its associated shape tags.
- Update `viewer.js` to handle property updates for existing scene objects by their tag.
- Ensure `_shape_history` is updated when a shape's property is modified for replayability/export.

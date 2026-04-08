# BUG/UX: Geometric shapes (Spheres, etc.) are non-interactive "visual ghosts"

## Description
Geometric shapes added to the scene via `view.shapes` (e.g., `add_sphere`) are rendered in the Mol* viewer but do not participate in the interaction system. Clicking or right-clicking on these objects does not update `active_selection` or `context_target`, making it impossible to retrieve their tags or metadata interactively.

## Steps to Reproduce
1. Load a structure: `view.load('1CRN')`.
2. Add a geometric sphere: `view.shapes.add_sphere(center=[0,0,0], radius=1.0, tag='my_sphere')`.
3. Perform a click or right-click directly on the green sphere in the viewer.
4. Check the interaction state in Python:
   - `view.active_selection.is_empty()` -> **Observed Result:** `True`.
   - `view.context_target.kind` -> **Observed Result:** `'empty'`.
   - `view.context_target.tag` -> **Observed Result:** `None`.

## Identified Issues
1. **Lack of Object Selection:** Unlike atoms and residues, geometric shapes cannot be "selected" to perform operations (like centering the camera, hiding them via a context menu, or identifying them).
2. **Inconsistency with Layers:** Since shapes are registered in `view.layers`, the user expects them to behave as first-class objects in the scene, similar to structural components.
3. **No Event Emission:** The frontend (JS) does not seem to emit `interaction_click` or `interaction_context_menu` events for non-structural Pickable objects (Shapes).

## Proposed Improvements
1. **Enable Picking for Shapes:** Ensure that the Mol* renderer treats geometric shapes as pickable objects and emits the corresponding `tag` in the interaction events.
2. **Integration with `ActiveSelection`:** Allow `ActiveSelection` to hold a `tag` (the shape's ID) when no atoms are selected but a shape is clicked.
3. **Context Menu Support:** Enable standard context menu actions (Hide, Focus, Delete) for shapes when right-clicked.

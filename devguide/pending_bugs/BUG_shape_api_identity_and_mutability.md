# BUG/DESIGN: Shape API lacks object identity, registration, and mutability

## Description
The current implementation of geometric shapes (via `view.shapes`) follows a "create-and-forget" pattern. When a shape is added (e.g., `view.shapes.add_sphere`), the manager returns a generic `Layer` object. This design leads to a loss of geometric identity and makes it impossible to update shape properties (color, radius, position) after creation without deleting and recreating the object.

## Steps to Reproduce
1. Create a sphere: `sphere = view.shapes.add_sphere(center=[0,0,0], radius=1.0, color=0x00FF00, tag='my_vol')`.
2. Inspect the returned object: `type(sphere)` -> **Observed Result:** `<class 'molsysviewer.layers.Layer'>`.
3. Attempt to change color: `sphere.set_color(0xFF0000)` -> **Observed Result:** `AttributeError` (Layer has no such method).
4. Attempt to retrieve via a shapes registry: `view.shapes['my_vol']` -> **Observed Result:** `TypeError` (ShapesManager is not subscriptable).

## Identified Issues
1. **Loss of Geometric Identity:** The `Layer` class only manages visibility (`show`, `hide`, `delete`). Once a sphere is created, Python "forgets" it is a sphere, losing access to its specific parameters.
2. **Missing Shapes Registry:** While `view.layers` exists for visibility management, there is no corresponding `view.shapes` registry to access shapes as specialized objects.
3. **Immutability of Appearance:** There is no mechanism to send "update" messages to the frontend for existing shapes. Operations like changing a site color during an interactive session require a full delete/create cycle, which is inefficient and breaks UX flow.
4. **API Inconsistency:** Structural elements (Regions) have their own specialized class and registry, but geometric elements are downgraded to generic layers immediately upon creation.

## Proposed Improvements
1. **Specialized Shape Classes:** Create classes like `Sphere`, `Link`, etc., that inherit from `Layer` but retain their geometric metadata.
2. **Shapes Registry:** Implement a subscriptable registry in `ShapesManager` (e.g., `view.shapes['tag']`) to retrieve these specialized objects.
3. **Update Methods:** Implement `set_color()`, `set_radius()`, and `set_position()` methods in the shape classes that trigger specific "update" operations in the frontend.
4. **Frontend Synchronization:** Update `viewer.js` to handle property updates for existing scene objects by their tag.

# Proposal: Multi-View Split-Screen Viewport Synchronization

**Status:** proposed (post-1.0 design).

**Scope:** Viewport splitting and camera synchronization in MolSysViewer to compare multiple structures or frames side-by-side.

---

## 1. Why

In structural biology, comparing two or more molecular systems is a frequent task. Examples include:
*   Comparing a wild-type protein against a mutant.
*   Analyzing different ligand docking poses in the same binding pocket.
*   Comparing different frames/steps of a molecular dynamics trajectory side-by-side.

Relying on overlaying structures in a single viewport often causes visual clutter (overlapping cartoon shapes, z-fighting). A **Split-Screen Viewport** solves this by rendering the systems in separate viewport panels side-by-side while keeping their camera movements synchronized, allowing the user to rotate, pan, and zoom all models simultaneously.

---

## 2. Interaction Design (UI/UX)

1.  **Split Controls:** Placed in the **Viewport** subpanel. The user can select the split layout:
    *   `Single` (default full canvas)
    *   `Split Horizontal` (2 viewports, left/right)
    *   `Split Vertical` (2 viewports, top/bottom)
    *   `Grid` (4 viewports, quadrants)
2.  **Model Assignment:** Each viewport segment has a structure selector (e.g., `Viewport 1: structureA`, `Viewport 2: structureB`).
3.  **Camera Sync Toggle:** A checkbox `[x] Sync Cameras` (enabled by default). When checked:
    *   Interacting with any viewport (rotating/panning/zooming) applies the exact same transformation matrix to the other viewports.
    *   When unchecked, the user can orient the viewports independently.

---

## 3. Technical Implementation Details (How)

1.  **Mol\* Multi-Viewport Configuration:**
    *   Mol* natively supports rendering multiple viewports within the same WebGL canvas using viewport regions or by instantiating multiple sub-renderers.
    *   Alternatively, the frontend can mount multiple canvas elements next to each other, each running a separate Mol* plugin instance or a shared WebGL context.
2.  **Camera Sync Pipeline:**
    *   Listen to camera change events on each viewport.
    *   When a transformation change occurs (rotation, translate, zoom), copy the camera parameters (target, position, up vector) to the peer viewports.
    *   Add a lock-guard to prevent infinite feedback loops during camera synchronization.
3.  **Python API Integration:**
    *   Expose viewport split commands:
        *   `view.split_viewport(mode='horizontal'|'vertical'|'grid'|'none')`
        *   `view.assign_structure_to_viewport(structure_index, viewport_index)`
        *   `view.set_camera_sync(bool)`

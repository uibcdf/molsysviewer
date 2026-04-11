# PROPOSAL: Strict Separation of Shapes and Layers with Semantic Naming

## Problem Statement
The current implementation of geometric shapes conflates the concept of an individual object (Shape) with its visibility group (Layer). Calls to `add_spheres` currently generate multiple independent layers instead of a single layer containing multiple shapes. Additionally, there is no central registry to query shapes by their own identity.

## Proposed Changes

### 1. Shape Identity vs. Layer Grouping
- **Shape Tag:** Every geometric object must have a unique identifier. Default: `shape1`, `shape2`, etc.
- **Layer Tag:** A logical grouping for visibility. 
- **Behavior of `add_spheres` (plural):**
  - If a `layer` tag is provided, all created spheres are added to that single layer.
  - If no `layer` tag is provided, a new layer is created automatically (e.g., `layerN`).
  - Each individual sphere in the batch gets its own unique shape tag.

### 2. `ShapesManager` as a Registry
Refactor `view.shapes` (ShapesManager) to behave as a dictionary-like registry:
- Implement `view.shapes.keys()`, `view.shapes.values()`, and `view.shapes.items()`.
- Implement `__getitem__`: `view.shapes['shape_tag']` should return the specific Shape object.

### 3. Navigation and Camera Control
- Implement a `focus()` method for all Shape objects: `view.shapes['shape1'].focus()`.
- **Logic:** The camera should center on the geometric center of the shape (retrieved from its properties) with a suitable zoom level.

### 4. API Signature Update
Update `add_sphere` and `add_spheres` to accept both tags:
```python
view.shapes.add_spheres(
    centers=..., 
    tag=['s1', 's2', 's3'], # Individual shape tags
    layer='my_cluster'      # Common layer tag
)
```

## Benefits
- **Clean Scene Hierarchy:** Users can hide a whole "cluster" of shapes by toggling one layer, but still edit the color of a single sphere by accessing its shape tag.
- **Semantic Clarity:** `view.layers` tells you what is being drawn; `view.shapes` tells you what geometric entities exist.
- **Consistency:** Aligns the shapes API with the proposed improvements for measurements and labels.

## Implementation Path
- Update `ShapesManager` to maintain an internal map of all created shapes.
- Modify `SphereShapes` (and others) to register shapes into the central manager.
- Ensure the frontend `viewer.js` can handle the `tag` (object) vs `layer_tag` (group) distinction in its internal `tagIndex`.

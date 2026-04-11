# PROPOSAL: Semantic prefixes for automatic object tags

## Problem Statement
Currently, many objects created in the viewer (especially measurements and shapes) default to a generic tag like `layer1`, `layer2`, etc. This makes it difficult for users to:
1. Identify the nature of an object in `view.layers.keys()`.
2. Script actions specifically for measurements vs. shapes.
3. Understand the scene hierarchy at a glance.

## Proposed Solution
Implement specialized tag counters in `MolSysView` (or within each manager) to provide semantic prefixes:

1.  **Measurements:** Default tag prefix should be `measurement` (e.g., `measurement1`).
2.  **Shapes:** Default tag prefix should be `shape` (e.g., `shape1`).
3.  **Annotations:** Ensure the prefix is consistently `annotation` (e.g., `annotation1`).

### Implementation detail
Refactor `_next_layer_tag()` to accept a prefix or create sibling methods:
- `_next_measurement_tag()`
- `_next_shape_tag()`
- `_next_annotation_tag()`

## Benefits
- **Readability:** `view.measurements.info()` will show tags like `measurement1` which is much more intuitive than `layer1`.
- **Debugging:** Easier to trace which part of the code created an object.
- **UX Consistency:** Aligns with the object-oriented nature of the library.

# PROPOSAL: `Layer.info()` and Semantic `attach`/`detach`

## Problem Statement
The `Layer` class (grouping manager) is currently missing a summary method, making it difficult to inspect its members programmatically. Additionally, the method name `add()` is too generic and can be confused with object creation.

## Proposed Changes

### 1. Implement `Layer.info()`
Add a summary method to `molsysviewer/layers.py` that returns a list of dictionaries or a Pandas Styler containing:
- `kind`: (shape, annotation, measurement, region).
- `tag`: The unique object ID.
- `type`: Specific geometry (e.g., sphere, label).
- `visible`: Visibility status of the member.

### 2. Rename Membership Methods
To improve semantic clarity, rename the top-down management methods:
- **`layer.add()`** → **`layer.attach()`**: Indicates linking an existing object to the group.
- **`layer.detach()`**: (Keep or rename to `release()` for symmetry).

## Benefits
- **Transparency:** Users can easily audit the composition of a visibility group: `view.layers['my_analysis'].info()`.
- **API Elegance:** Distinguishes between "Creating" (`view.shapes.add_sphere`) and "Grouping" (`view.layers['X'].attach(obj)`).
- **Consistency:** Aligns with the professional tone of the library.

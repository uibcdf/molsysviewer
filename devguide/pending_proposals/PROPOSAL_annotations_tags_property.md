# PROPOSAL: Convert `AnnotationsManager.tags()` to a property

## Problem Statement
Currently, `view.annotations.tags()` is a method. Users expecting to inspect the list of active annotation tags often try to access it as an attribute (e.g., `view.annotations.tags`), which returns the method object itself instead of the list of strings. This is inconsistent with how other registries are evolving in the library.

## Proposed Changes
Refactor the `tags()` method in `molsysviewer/annotations.py` to use the `@property` decorator.

### New Implementation
```python
@property
def tags(self) -> list[str]:
    """Return a list of active annotation tags."""
    return [tag for tag, layer in self._view._scene_objects.items() if getattr(layer, "kind", None) == "annotation"]
```

## Benefits
- **Intuitiveness:** Aligns the API with common Python patterns for registries.
- **Consistency:** Matches the proposed `keys()` property in `ShapesManager` and other collection-like objects.
- **Jupyter UX:** Allows for easier inspection of tags via tab-completion and direct printing.

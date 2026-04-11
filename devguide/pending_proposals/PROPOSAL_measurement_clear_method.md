# PROPOSAL: Add `clear()` method to `MeasurementsManager`

## Problem Statement
Currently, there is no simple way to remove all measurements from the viewer. Users must either delete them one by one using their tags (`view.measurements.delete(tag)`) or use the generic `view.clear_decorations()` which might remove more than intended (like shapes or labels).

## Proposed Solution
Implement a `clear()` method in `molsysviewer/measurements.py`:

```python
def clear(self, tag: str | None = None, skip_digestion: bool = False):
    """Remove all measurements or a specific one by tag."""
```

### Logic
1. If `tag` is provided, call `self.delete(tag)`.
2. If `tag` is `None`, iterate over all active measurement tags and delete them.
3. Emit a single signal or a batch of signals to update the frontend.

## Benefits
- **Consistency:** Aligns the measurements API with `annotations` and `shapes` (which already have or should have clear methods).
- **UX:** Provides a quick "reset" for measurements during an interactive session.

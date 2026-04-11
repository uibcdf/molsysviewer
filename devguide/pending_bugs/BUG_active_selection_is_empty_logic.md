# BUG: `active_selection.is_empty()` returns contradictory or inverted values

## Description
The method `view.active_selection.is_empty()` does not reliably reflect whether the user has selected something in the viewer. In some cases, it returns `True` when atoms are selected and `False` when clicking on empty space, which is the exact opposite of the expected behavior.

## Steps to Reproduce
1. Load a structure.
2. Click on a residue in the viewer (indices should be populated).
3. Check `view.active_selection.is_empty()` -> **Observed Result:** `True` (Expected `False`).
4. Click on the empty background (indices become `[]`).
5. Check `view.active_selection.is_empty()` -> **Observed Result:** `False` (Expected `True`).

## Technical Analysis
The current implementation in `molsysviewer/active_selection.py` is:
```python
return self.source_kind == "empty" or len(self.atom_indices) == 0 and len(self.items) == 0
```
Due to Python operator precedence, this is evaluated as:
`source_kind == "empty" OR (len(atom_indices) == 0 AND len(items) == 0)`

If `source_kind` is anything other than `"empty"`, the result depends on the second block. Furthermore, the logic seems to be inverted or improperly capturing the "empty" state of the frontend payload.

## Proposed Solution
Refactor the logic to be more robust and use explicit parentheses:
```python
return (self.source_kind == "empty") or (len(self.atom_indices) == 0 and len(self.items) == 0)
```
And verify that the frontend actually sends `source_kind: "empty"` when the selection is cleared.

(User_Troubleshooting_SelectionIssues)=
# Selection issues

## Empty selection

If `view.select(...)` returns an empty list:

1. **Check that the system is loaded.** `view.molsys` must not be `None`.
2. **Check the selection string syntax.** MolSysViewer delegates selection
   parsing to MolSysMT. A typo in a residue name or chain id returns an empty
   result silently.

```python
# Quick validation — print the atom count
indices = view.select("chain A")
print(len(indices), "atoms selected")
```

3. **Chain ids are case-sensitive.** `chain A` and `chain a` are different.
4. **Residue indices vs residue numbers.** MolSysMT uses 0-based residue
   *indices* internally. If you are mixing 1-based PDB residue *numbers*,
   convert first.

## Unexpected matches

If your selection matches more atoms than expected:

- Use a more specific selector: `"chain A and resname LIG"` instead of `"resname LIG"`.
- Inspect what you selected:

```python
indices = view.select("resname HOH")
print(f"Selected {len(indices)} water atoms")
```

## Selection does not create a region

`view.create_region(selection=..., tag=...)` requires a non-empty atom-index
list. Check that `view.select(selection)` is non-empty first.

## Active selection out of sync

If `view.active_selection` does not match what you see highlighted in the canvas:

```python
view.active_selection.clear()   # reset both Python and frontend state
```

## Selection after `remove()` or `set()`

After a structural edit, atom indices are remapped. Re-run `view.select(...)`
after the edit rather than reusing a cached index list.

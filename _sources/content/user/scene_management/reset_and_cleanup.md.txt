# Reset & cleanup

Use these helpers when you want to clear part of the scene without reloading the structure.

## Clear decorations

You can clear shapes/styles/labels without touching the loaded structure:

```python
view.clear_decorations(shapes=True, styles=True, labels=True)
```

## Inspect and edit the loaded system (live)

MolSysViewer keeps the currently loaded molecular system inside the viewer.

If you want a quick, practical workflow, prefer these methods over mutating `view.molsys` directly:

```python
# Query helpers (MolSysMT under the hood)
view.select("atom_name == 'CA'")
view.get(element="system", n_atoms=True)
view.info(element="system")
```

Some operations mutate the loaded system and then refresh the frontend so the change becomes visible:

```python
# Live operations (experimental)
view.set(selection="group_index == 0", group_name="XXX")
view.remove(selection="water")
view.add(other_system)
view.append_structures(other_system, structure_indices=0)
```

These operations are designed to preserve regions, layers, visibility, and shapes whenever possible.

## Fully reset the viewer

Use this when you want a clean state and plan to call `load(...)` again:

```python
view.reset_viewer()
```

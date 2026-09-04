# Reset & cleanup

Use these helpers when you want to clear part of the scene without reloading the structure.

## Clear decorations

You can clear shapes/styles/labels without touching the loaded structure:

```python
view.clear_decorations(shapes=True, styles=True, labels=True)
```

## Inspect the loaded system

MolSysViewer keeps the currently loaded molecular system inside the viewer.

If you want a quick, practical workflow, prefer these methods over mutating `view.molsys` directly:

```python
# Query helpers (MolSysMT under the hood)
view.select("atom_name == 'CA'")
view.get(element="system", n_atoms=True)
view.whole.info(element="system")
```

## Edit the loaded system (MolSysMT addon)

Live molecular edits are provided by the MolSysMT addon. The addon mutates the
molecular system through MolSysMT and then asks the viewer to reconcile the
scene:

```python
view.addons.molsysmt.basic.set(selection="group_index == 0", group_name="XXX")
view.addons.molsysmt.basic.remove(selection="water")
view.addons.molsysmt.basic.add(other_system)
view.addons.molsysmt.basic.append_structures(other_system, structure_indices=0)
```

These operations are designed to preserve regions, layers, visibility, and shapes whenever possible.

For loading-only add/append workflows, you can also use the viewer loader:

```python
view.load(other_system, mode="add")
view.load(other_system, mode="append_structures")
```

## Fully reset the viewer

Use this when you want a clean state and plan to call `load(...)` again:

```python
view.reset_viewer()
```

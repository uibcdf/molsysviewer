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
view.whole.select("atom_name == 'CA'")
view.whole.get(element="system", n_atoms=True)
view.whole.info(element="system")
```

## Edit the loaded system

MolSysMT is the native scientific backend. Its former addon namespace has been
retired. Calculate a modified system with MolSysMT, then use
`view.load(molsys, mode="replace")` to replace the scene. Replacement resets
scene objects. For integrations that retain scene objects, use
`view.apply_system_edit(...)` with explicit index correspondence; see the
[developer API contract](../../developer/public_api.md).

Native loading supports adding independent sources and appending compatible
structures through `view.load(...)`. It does not require addon registration.

## Fully reset the viewer

Use this when you want a clean state and plan to call `load(...)` again:

```python
view.reset_viewer()
```

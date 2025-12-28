# What is MolSysViewer?

MolSysViewer is a Python library that lets you control a Mol* 3D scene from Python.

You typically use it in Jupyter.
You load a molecular system with MolSysMT, then add overlays and export a shareable view.

What you can do
- Load molecular systems via `view.load(...)`.
- Control visibility, camera, and scene state.
- Apply representations to the whole system or to regions.
- Add overlays (pockets, channels, pharmacophore features, anisotropy, meshes).
- Export lightweight HTML embeds with `write_html(..., mode="lite")`.


# Ecosystem add-ons

MolSysViewer is being shaped as the shared visual workbench of MolSysSuite.

That means the core viewer should stay strong and reusable, while
domain-specific capabilities can arrive as optional add-ons.

This showcase page is a placeholder for future add-on-shaped scientific
stories, such as:

- `TopoMT` panels for cavities, channels, and topographic accidents
- `PharmacophoreMT` overlays and pharmacophore workbench flows
- `ElasNetMT` network or elastic-model overlays

The important product direction is already fixed:

- the resting canvas should stay clean
- add-ons should mainly surface themselves through panel/workbench growth
- users who do not need those domains should not have to carry their visual
  complexity

Teams that want to start now already have a starter pack:

- [`minimal_topomt.py`](https://github.com/uibcdf/molsysviewer/blob/main/molsysviewer/addon_templates/minimal_topomt.py)
- {doc}`../user/cookbook/addon_development`
- {doc}`../user/cookbook/addon_workspace_workbench`
- [`IMPLEMENTATION_CONTRACT.md`](https://github.com/uibcdf/molsysviewer/blob/main/standards/addons/IMPLEMENTATION_CONTRACT.md)

There is now also a single supported smoke/demo path for external teams:

```python
import molsysviewer

view = molsysviewer.addon_templates.build_reference_demo_view("topomt")
view.workspace_runtime()
view
```

That gives `MolSysMT`, `TopoMT`, `PharmacophoreMT`, and similar teams a shared
starting point for discussions:

- one real demo molecular system
- one credible reference workspace
- one visible add-on lifecycle/runtime path
- one entry-panel landing inside that workspace
- one notebook-facing runtime snapshot of that same workspace
- one reproducible snippet everyone can run before writing their own package
- one short recipe that shows how that workspace actually sits inside the shared
  workbench

As real MolSysSuite add-ons arrive, this section should become a gallery of
focused scientific workflows built on top of the same MolSysViewer core.

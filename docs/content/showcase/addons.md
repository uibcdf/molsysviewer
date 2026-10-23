(Addon_Catalogue)=
# Add-on catalogue

Find add-on projects here, then follow the owning component's documentation for
installation, available tools, Python and graphical use, and compatible versions.
MolSysViewer documents the shared
{doc}`discovery and management model <../user/introduction/addons>` and
{doc}`how to create an add-on <../developer/addons>`.

## Projects and integrations

| Project | Scientific area | Documentation and availability |
| --- | --- | --- |
| TopoMT | Molecular topography | [TopoMT documentation](https://www.uibcdf.org/topomt). Consult the provider for the scope of `molsysviewer_topomt` and its compatible versions. |
| PharmacophoreMT | Pharmacophores | [PharmacophoreMT documentation](https://www.uibcdf.org/pharmacophoremt). Consult the provider for the scope of `molsysviewer_pharmacophoremt` and its compatible versions. |
| ElastNetMT | Elastic networks | [ElastNetMT documentation](https://www.uibcdf.org/elastnetmt). Consult the provider for the scope of `molsysviewer_elastnetmt` and its compatible versions. |
| MolSysMT tools | Additional molecular analysis, preparation and editing | **Planned redesign; not currently available.** The retired integration is rejected by the current Viewer. Follow {doc}`../user/introduction/molsysmt` for current backend integration. |

A catalogue entry identifies the project; it does not certify every scientific
workflow or package/version combination. Follow each provider's published
availability and compatibility information.

## Requesting an entry

If you develop an independent add-on, request inclusion by opening an issue in
the [MolSysViewer issue tracker](https://github.com/uibcdf/molsysviewer/issues/new).
Include:

- its name, purpose and maintainer;
- package/source and installation instructions;
- the documentation explaining its tools and use;
- declared compatible MolSysViewer versions and any platform requirements.

The maintainers review the request and add the documentation link to this
catalogue. Listing is independent of runtime discovery: use package entry points
or explicit registration as described in the creation guide. The catalogue
does not install or activate packages.

## Creating an add-on

Teams that want to start now already have a starter pack:

- [`dummy_addon.py`](https://github.com/uibcdf/molsysviewer/blob/main/molsysviewer/addon_templates/dummy_addon.py)
- {doc}`../user/cookbook/addon_development`
- {doc}`../user/cookbook/addon_workspace_workbench`
- {doc}`../developer/addons`

There is now also a single supported smoke/demo path for external teams:

```python
import molsysviewer

view = molsysviewer.addon_templates.build_reference_demo_view("dummy")
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

Keep the add-on's usage guide in the owning project's documentation. Viewer
showcases can illustrate complete visualization workflows and link to that
guide for the add-on's API and scientific options.

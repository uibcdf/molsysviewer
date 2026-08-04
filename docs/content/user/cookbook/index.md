# Cookbook

Recipes for common tasks (to be filled with concrete examples):

- Quick pocket surface from alpha-spheres (multi-iso, color maps).
- Pocket blob overlays with custom iso thresholds and smoothing.
- Channel tubes from TopoMT routes with segment coloring.
- Pharmacophore glyph overlays with standard colors and transparency.
- Anisotropy ellipsoids/disks from ANM tensors/eigenvectors.

Each recipe will include: minimal code, expected visuals (static HTML via `view.export.html(..., shared_runtime=...)`), and option tweaks.

Scientific tutorials (provisional):

- {doc}`tutorial_trajectory_analysis` — RMSF colouring, region annotation, movie export

Exporting a view and putting it on a website is documented once, in
{doc}`../export/index`. This chapter does not repeat it.

High-value runtime recipes:

- {doc}`figure_export_workbench`
- {doc}`addon_workspace_workbench`
- {doc}`panel_mode_notebook`
- {doc}`workbench_scientific_workflow`
- {doc}`movie_recipes`

```{toctree}
:maxdepth: 2
:hidden:

tutorial_trajectory_analysis
pocket_surface
pocket_blob
channel_tube
pharmacophore_overlay
anisotropy_ellipsoids
figure_export_workbench
addon_workspace_workbench
panel_mode_notebook
addon_development
workbench_scientific_workflow
movie_recipes
```

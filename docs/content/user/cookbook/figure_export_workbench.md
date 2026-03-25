(User_Cookbook_Figure_Export_Workbench)=
# Build figure exports from the workbench

This recipe shows how to turn the current state of a viewer into a small,
reusable figure-export workflow.

The important idea is that figure export in MolSysViewer is no longer just
"save a screenshot".
You can now:

- inspect the figure baseline from `Workbench -> Scene`
- inspect the same export baseline from notebook/runtime state
- capture the current camera into a reusable `FigureSpec`
- derive small variants from that recipe
- and export a publication-oriented bundle in one pass

This is a good pattern when you want the interactive exploration phase and the
final figure-export phase to stay connected.

## Goal

You will:

1. open a demo viewer
2. inspect the scene from the shared workbench
3. capture the current camera into a `FigureSpec`
4. export one figure
5. export a few named variants
6. export the standard publication bundle

## 1. Open a real viewer and expose the shared workbench

```python
import molsysviewer as mv

view = mv.demo["dialanine"]
view.set_panel_mode(panel="workbench", expanded=True)
view
```

At this point, `Workbench -> Scene` should already expose the current built-in
figure baseline:

- default figure preset
- default figure scale
- recommended figure variants

That baseline is intentionally modest, but it is useful because figure export
is now visible as part of the workbench story, not only as an API call.

From notebook code, the same workbench-facing story should already be visible
through the export API itself:

```python
view.get_camera_snapshot()
```

That means the interactive viewer state and the later export recipe can still
be discussed from Python without treating export as a disconnected subsystem.

## 2. Move the camera to the view you actually want

Use the normal viewer controls until the scene shows the orientation you want
to keep for your figures.

Once the view looks right, capture that camera into a reusable recipe:

```python
from molsysviewer.figures import FigureSpec

base_figure = FigureSpec.from_view(
    view,
    preset="publication-light",
    scale=2.0,
)
```

This is the key step.
You are not exporting yet.
You are turning the current interactive view into an explicit figure recipe.

## 3. Export one figure from the recipe

```python
view.export.figure(
    "dialanine_publication_light.png",
    figure_spec=base_figure,
)
```

This keeps the chosen camera and figure settings explicit.

## 4. Derive small named variants

If you want a few closely related outputs, derive them from the same base
recipe instead of rebuilding everything by hand:

```python
variants = base_figure.build_variants(
    {
        "light": {},
        "dark": {"background": "dark", "preset": "publication-dark"},
        "transparent": {"background": "transparent"},
    }
)
```

Then export them to one directory:

```python
view.export.figure_variants(
    output_directory="dialanine_figures",
    stem="dialanine",
    variants=variants,
)
```

This gives you a small named batch without losing the connection to the same
base camera/state choice.

## 5. Use the standard publication bundle

If you do not want to define the variants yourself, use the built-in
publication bundle:

```python
view.export.figure_publication_set(
    output_directory="dialanine_publication_set",
    stem="dialanine",
    figure_spec=base_figure,
)
```

This currently exports the small standard bundle:

- `light`
- `dark`
- `transparent`

You can optionally also include the current-view variant:

```python
view.export.figure_publication_set(
    output_directory="dialanine_publication_set_with_current",
    stem="dialanine",
    figure_spec=base_figure,
    include_current=True,
)
```

## 6. Keep the recipe reusable

You can also derive a small override without mutating the base recipe:

```python
transparent_figure = base_figure.with_overrides(background="transparent")

view.export.figure(
    "dialanine_transparent.png",
    figure_spec=transparent_figure,
)
```

This is useful when one figure should stay the canonical baseline and the
others are just controlled deviations from it.

## Why this workflow is worth using

This pattern is better than taking ad hoc screenshots because:

- the chosen camera becomes explicit
- small figure variants stay traceable to the same recipe
- publication outputs can be generated in batches
- figure export stays tied to the same reproducible viewer state you explored
  interactively

That is exactly the kind of workflow MolSysViewer should encourage before
`1.0.0`:

- interactive exploration first
- explicit figure recipe second
- reproducible exports last

## API surfaces used in this recipe

- `view.set_panel_mode(...)`
- `view.get_camera_snapshot()`
- `FigureSpec.from_view(...)`
- `FigureSpec.with_overrides(...)`
- `FigureSpec.build_variants(...)`
- `view.export.figure(...)`
- `view.export.figure_variants(...)`
- `view.export.figure_publication_set(...)`

## See also

- {doc}`../export/index`
- {doc}`addon_development`

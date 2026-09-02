# Export & embedding

Export the current state of a viewer to share it or embed it in web documentation.

Three different things live here. {doc}`html_export` produces a page that *shows* the
scene. {doc}`state` writes what you built to JSON so you can put it back on a viewer
later, without the molecular system. {doc}`session` writes the scene *and* the system into
one file that reopens on its own.

If you want a workbench-oriented figure-export workflow, start with:

- {doc}`../cookbook/figure_export_workbench`

If you are trying to connect scripted export to the shared runtime, also see:

- {doc}`../viewer/panel_mode`
- {doc}`../cookbook/panel_mode_notebook`

```{toctree}
:hidden:
:maxdepth: 2

html_export
state
session
sphinx_html_embedding
```

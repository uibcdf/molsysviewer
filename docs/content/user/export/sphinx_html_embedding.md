# Sphinx and HTML embedding

Use this page when you want to embed an interactive viewer in a documentation
page, a notebook rendered as HTML, or a static website.

## Recommended workflow

1. Export the scene to `docs/_static/views/` using `mode="lite"`.
2. Embed the file in a Sphinx page with a `raw` directive or an `<iframe>`.

```python
# In a notebook or script — generate the static view
view.export.html("docs/_static/views/my_scene.html", mode="lite")
```

## Embedding with `{raw}` in MyST

```{raw} html
<iframe
  src="../../../_static/views/my_scene.html"
  width="100%"
  height="480px"
  style="border:none;"
></iframe>
```

Adjust the relative path as needed for your page's location in the doc tree.

## Embedding in a Jupyter notebook cell

If you are working in a notebook that will be rendered by Sphinx/MyST-NB:

```python
from IPython.display import IFrame

IFrame("../../../_static/views/my_scene.html", width="100%", height=480)
```

Or use MolSysViewer's helper:

```python
import molsysviewer as msv

msv.thirds.jupyter.load_html_in_notebook(
    "docs/_static/views/my_scene.html"
)
```

## Generating views at docs-build time

Static HTML views should be generated **outside** the Sphinx build, so the
build remains reproducible without a running Jupyter kernel.

A typical pattern is a small script under `docs/generate_static_views/`:

```python
# docs/generate_static_views/01_1tcd_scene.py
import molsysviewer as msv

view = msv.demo["1TCD"]
view.styles.apply(tag="polymer-and-ligand")
view.export.html("docs/_static/views/1tcd_scene.html", mode="lite",
                 include_controls=True, include_popout=False)
```

Run all generation scripts manually before pushing the docs:

```bash
python docs/generate_static_views/01_1tcd_scene.py
```

Do not run these inside notebooks that the Sphinx build executes, because
`nb_execution_mode = "off"` is the project default and the output would be
stale.

## `mode="lite"` vs `mode="standalone"` for docs

| | `"lite"` | `"standalone"` |
|---|---|---|
| File size | small | larger |
| Offline | no (needs CDN) | yes |
| Docs embeds | preferred | works but heavy |

For Read the Docs and GitHub Pages, `"lite"` is the right choice.

## Path conventions

Store all exported views under `docs/_static/views/`. This directory is treated
as a build artifact by version control (do not diff or edit files there). See
{doc}`../../developer/documentation/web/build_and_layout` for the full layout.

## See also

- {doc}`html_export` — export options reference.
- {doc}`../../developer/documentation/web/build_and_layout` — Sphinx config and docs layout.

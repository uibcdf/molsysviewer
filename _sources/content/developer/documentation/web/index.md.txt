# Documentation for the web

This section collects guidelines and examples for writing MolSysViewer’s web
documentation with MyST and Sphinx. It is aimed at contributors who edit
the User Guide, Showcase, Cookbook, and developer documentation.

- Use `myst.ipynb` to see concrete examples of MyST admonitions and how to
  structure tutorial notebooks.
- Use `editorial_guidelines.md` as the source of truth for file types, section roles, and the HTML lite workflow.
- Use `build_and_layout.md` when you need to change the docs build or layout conventions.
- If you execute docs notebooks to freeze outputs, use `docs/execute_notebooks.py`. It strips ipywidgets/AnyWidget state by default. Tag a cell with `keep-widget-state` only if you need to preserve a widget-based output.
- Use `references.md` as the reference for cross-links between pages and
  API objects (labels, `{ref}`, `{func}`, `{class}`, etc.).

```{toctree}
:maxdepth: 2

editorial_guidelines.md
build_and_layout.md
myst.ipynb
references.md
```

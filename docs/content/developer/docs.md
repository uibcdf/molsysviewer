# Documentation

- We mirror MolSysMT’s docs style (pydata_sphinx_theme, MyST, notebooks off by default).
- Writing style: second person, short sentences, “why” before “how”, scannable headings/lists.
- Assets go to `_static/`; layout overrides in `_templates/`.
- API pages use autosummary and must match the public Python surface; run `clean_api.py` after regenerating.
- Build with `make html` (use `make clean` if artifacts conflict). Keep `_build/` out of commits.
- For interactive showcases, export static views with `MolSysView.write_html` into `_static/views/` and embed them via `molsysviewer.thirds.load_html_in_jupyter_notebook`.
- Stub pages in `content/user/cookbook/` and `content/showcase/` should be filled with real code and static exports when ready.

See also `Provisional_Docs_Guidelines.md` for the full checklist.

```{toctree}
:hidden:
:maxdepth: 1
```

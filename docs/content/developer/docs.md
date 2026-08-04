# Documentation

- We mirror MolSysMT’s docs tooling and style (pydata_sphinx_theme, MyST, notebooks off by default).
- Writing style: second person, short sentences, “why” before “how”, scannable headings/lists.
- Assets go to `_static/`; layout overrides in `_templates/`.
- API Reference pages use autosummary allowlists (`docs/api/public/api_public.rst`, `docs/api/internal/api_internal.rst`) and render from docstrings; run `python docs/clean_api.py` if you need to remove stale generated pages.
- Build with `make -C docs html` (use `make -C docs clean` if artifacts conflict). Keep `_build/` out of commits.
- When reviewing docs with embedded views, serve the build: `python -m molsysviewer.preview docs/_build/html`. Opening `index.html` from disk shows every embed blank, because a page with no origin may not load the shared runtime beside it.
- Execute notebooks manually with `docs/execute_notebooks.py` when you want frozen outputs in tutorials; it strips ipywidgets/AnyWidget state by default to keep `.ipynb` files small. Add the cell tag `keep-widget-state` if you really need a widget-based output to survive the strip.
- Runtime: this site's embedded views load `_static/viewer.js`, placed at build time by `docs/conf.py` from the installed package. No network, no registry. The npm package `@uibcdf/molsysviewer` (Trusted Publisher workflow in `.github/workflows/npm-publish.yml`) serves only authors who opt into `shared_runtime="cdn"`.
- For interactive showcases, export docs-light views into `_static/views/`. The mechanism, including where the runtime comes from, is documented once in {doc}`../user/export/sphinx_html_embedding`; this project uses it unchanged, so do not describe it again here.
- Stub pages in `content/user/cookbook/` and `content/showcase/` should be filled with real code and static exports when ready.

See also:
- `docs/content/developer/documentation/web/editorial_guidelines.md` for the editorial rules used across the web docs.
- `docs/content/developer/documentation/web/build_and_layout.md` for the docs build and layout conventions.

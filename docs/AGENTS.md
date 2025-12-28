# Instructions for AI assistants (docs/)

- Keep the writing style: second person, short sentences, “why” before “how”,
  scannable headings/lists. Code/docstrings in English.
- Do not edit generated artifacts (`_build/`). Use `_static/` for assets and
  `_templates/` for layout overrides.
- Notebooks execute off (`nb_execution_mode="off"`). For interactive demos,
  export docs-light views with `MolSysView.write_html(..., mode="lite")` into
  `_static/views/` and embed via
  `molsysviewer.thirds.jupyter.load_html_in_notebook`.
- Respect the existing structure (`content/`, `api/`, `_static/`,
  `_templates/`). Keep new pages consistent with
  `docs/content/developer/documentation/web/build_and_layout.md`.
- Do not suggest running `npm run build` for TypeScript; the JS bundle is
  maintained separately.

## Documentation guide (where to look first)

- Docs workflow checklist: `docs/content/developer/docs_workflow.md`
- Web docs editorial rules: `docs/content/developer/documentation/web/editorial_guidelines.md`
- Web docs build/layout conventions: `docs/content/developer/documentation/web/build_and_layout.md`
- Cross-linking patterns: `docs/content/developer/documentation/web/references.md`
- API Reference workflow: `docs/content/developer/documentation/api/index.md`

## Notebook policy (important)

- Sphinx does not execute notebooks (`nb_execution_mode="off"`).
- Freeze tutorial outputs with `docs/execute_notebooks.py`.
- The executor strips ipywidgets/AnyWidget state by default; tag cells with `keep-widget-state` only when you truly need widget state preserved.

## Docs build prerequisites (important)

- When building docs locally, set `NUMBA_CACHE_DIR=/tmp/numba_cache` to avoid Numba caching errors if `molsysmt` is used from a local checkout.

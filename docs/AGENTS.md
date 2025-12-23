# Instructions for AI assistants (docs/)

- Keep the writing style: second person, short sentences, “why” before “how”,
  scannable headings/lists. Code/docstrings in English.
- Do not edit generated artifacts (`_build/`). Use `_static/` for assets and
  `_templates/` for layout overrides.
- Notebooks execute off (`nb_execution_mode="off"`). For interactive demos,
  export docs-light views with `MolSysView.write_html(..., mode="lite")` into
  `_static/views/` and embed via
  `molsysviewer.thirds.load_html_in_jupyter_notebook`.
- Respect the existing structure (`content/`, `api/`, `_static/`,
  `_templates/`, `_bibtex/`). Keep new pages consistent with
  `docs/Provisional_Docs_Guidelines.md`.
- Do not suggest running `npm run build` for TypeScript; the JS bundle is
  maintained separately.

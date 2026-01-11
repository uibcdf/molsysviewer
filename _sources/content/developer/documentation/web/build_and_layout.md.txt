# Web docs build & layout

Use this page when you need to change the documentation build, the Sphinx configuration, or the docs layout.

## Objectives

- Reuse the MolSysMT documentation layout (Sphinx + pydata-sphinx-theme + MyST + notebooks) with minimal friction.
- Keep tone and narrative consistent: short, action-oriented sentences in the second person, “why” before “how”, and API-accurate terminology.
- Make pages scannable: headings + lists, small code/examples, consistent capitalization.
- Build cleanly locally and on Read the Docs; keep assets organized in `_static/` and `_templates/`.

## Build & tooling

- Sphinx with `pydata_sphinx_theme`.
- Extensions: autodoc, autosummary, napoleon, viewcode, intersphinx, mathjax, todo, bibtex, extlinks, copybutton, remove_toctrees, sphinx_design, sphinx_tabs, sphinx_favicon, myst_nb.
- MyST config: `dollarmath`, `amsmath`, `colon_fence`, `deflist`; heading anchors to level 3.
- Notebook execution: `nb_execution_mode = "off"` (do not run during build).
- When you want frozen outputs, execute notebooks manually with `docs/execute_notebooks.py` (see {doc}`editorial_guidelines`).
- Sources: `.md`, `.rst`, `.ipynb`; `master_doc`/`root_doc` = `index`.
- Theme options: GitHub icon link; no edit button; no source link in HTML; favicons/logo from `_static/`.
- Custom assets: `_static/custom.css` (sidebar widths, colors, Jupyter cell styling), `_templates/` overrides.

Commands
- `make html` (and `make clean` if needed).

## Directory layout

- `docs/`
  - `index.ipynb` landing page.
  - `content/` for authored pages.
  - `api/` for autosummary-generated reference.
  - `_static/` for assets and `_static/views/` for exported HTML lite views.
  - `_templates/` for layout overrides.
  - Utility scripts: `execute_notebooks.py`, `clean_api.py`.

## Assets and hygiene

- Place reusable assets in `_static/` or `_templates/`.
- Do not edit generated artifacts under `_build/`.
- Do not edit or read exported HTML under `_static/views/` (treat them as build artifacts).
- Generate HTML lite views via scripts in `docs/generate_static_views/` (do not generate them inside notebooks).

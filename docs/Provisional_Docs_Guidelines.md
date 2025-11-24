# MolSysViewer Documentation — Provisional Guidelines

This document captures the style, structure, and build conventions we will mirror from the MolSysMT docs for MolSysViewer (and, later, TopoMT/PharmacophoreMT).

## Objectives
- Reuse the MolSysMT documentation layout (Sphinx + pydata-sphinx-theme + MyST + notebooks) with minimal friction.
- Keep tone and narrative consistent: short, action-oriented sentences in the second person, “why” before “how”, and API-accurate terminology.
- Make pages scannable: headings + lists, small code/examples, consistent capitalization.
- Build cleanly locally and on Read the Docs; keep assets organized in `_static`/`_templates`.

## Build & Tooling
- Sphinx with `pydata_sphinx_theme`.
- Extensions: autodoc, autosummary, napoleon, viewcode, intersphinx, mathjax, todo, bibtex, extlinks, copybutton, remove_toctrees, sphinx_design, sphinx_tabs, sphinx_favicon, myst_nb.
- MyST config: `dollarmath`, `amsmath`, `colon_fence`, `deflist`; heading anchors to level 3.
- Notebook execution: `nb_execution_mode = "off"` (do not run during build).
- Sources: `.md`, `.rst`, `.ipynb`; `master_doc`/`root_doc` = `index`.
- Theme options: GitHub icon link; no edit button; no source link in HTML; favicons/logo from `_static`.
- Custom assets: `_static/custom.css` (sidebar widths, colors, Jupyter cell styling), `_templates/` overrides (copyright, theme-version).
- Commands: `make html` (and `make clean` if needed). If using RTD, keep `.readthedocs.yaml` aligned and add optional deps to a docs requirements file when needed.

## Directory Layout (to mirror MolSysMT)
- `docs/`
  - `index.ipynb` landing page (logo + badges, install snippet, short “Use it” example, hidden secondary sidebar).
  - `content/`
    - `about/` (what, installation, who, citation).
    - `user/` (user guide index with cards/grids to intro/tools/cookbook; AI Assistants link).
    - `developer/` (intro/fork/env, warnings/logging, tests, docs authoring).
    - `showcase/` (notebooks/demos/quickstart; HTML exports optional).
  - `api/` (autosummary-generated reference grouped by functional areas; helper script `clean_api.py` to tidy titles/order).
  - `_static/` (logo, favicons, css, tabs css, any exported HTML assets).
  - `_templates/` (layout overrides).
  - `_bibtex/` + `bibliography.bib` for citations.
  - Utility scripts: `execute_notebooks.py`, `clean_api.py`, Makefile/make.bat.

## Writing Style & Tone
- Second person (“you”), short sentences, direct instructions.
- Start with the “why” before the “how”; follow with minimal, reproducible examples.
- Use headings and bullet lists instead of dense paragraphs; keep sections scannable.
- Match API names exactly (case-sensitive) and avoid inventing new terms.
- When adding scientific context, give a brief rationale and cite `bibliography.bib` when relevant.
- Keep heading hierarchy consistent (`##` then `###`).

## Visual/Structural Patterns
- pydata-sphinx-theme with widened main content and sidebars (see `_static/custom.css`).
- `sphinx_design` grids/cards on index pages (user guide, showcase) to navigate sections.
- Badges on the landing page; logo centered; install snippet prominently placed.
- Hidden secondary sidebar on landing page via `:html_theme.sidebar_secondary.remove:`.
- Notebook cells: styling for input/output scroll regions via CSS; execution disabled by default.

## API Docs Expectations
- `autosummary_generate = True`; type hints shown in descriptions.
- Group APIs by domain (basic, build, form, structure, topology, etc.); keep order stable across regenerations.
- Use `clean_api.py` (or equivalent) after regenerating to enforce naming/ordering consistency.

## Assets & Content Hygiene
- Place reusable assets in `_static` or `_templates`; avoid embedding large binaries in markdown.
- Keep `_build/` out of versioned edits (use `.gitignore`); clean before major rebuilds if artifacts conflict.
- If new optional doc dependencies are required, list them in a docs-specific requirements file and mention them in the dev guide.

## Porting Checklist (for MolSysViewer and siblings)
1. Copy/adapt the layout above; update branding in `conf.py`, `index.ipynb`, and `content/about`.
2. Create user/developer/showcase pages with `sphinx_design` cards and concise toctrees.
3. Set up API autosummary pages grouped by MolSysViewer domains; wire `clean_api.py` to the package.
4. Keep MyST + notebook settings aligned (execution off, math extensions on).
5. Apply consistent tone and heading structure; reuse CSS colors/widths unless a new palette is defined.
6. Validate with `make html` locally; align RTD config if publishing.

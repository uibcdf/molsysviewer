# API documentation guidelines

This section collects guidelines for documenting MolSysViewer’s public API and for
testing examples embedded in docstrings.

- `docstrings.md` describes the structure, style, and required sections for
  docstrings on functions, methods, classes, modules, and attributes.
- `doctests.md` explains how we use `pytest --doctest-modules` to keep all
  `Examples` up to date and executable.

Docstrings are written in NumPy style with Sphinx roles (such as `:ref:` and
`:func:`), while the surrounding documentation uses MyST and the cross-linking
patterns described in `docs/content/developer/documentation/web/`.

## API Reference pages (autosummary)

The API Reference under `docs/api/` is generated from docstrings using Sphinx
`autosummary` + `autodoc`:

- `docs/api/public/api_public.rst` defines the allowlist for the **Public API**.
- `docs/api/internal/api_internal.rst` defines the allowlist for the **Internal API**.

These files are the sources of truth for what appears in the reference.
They should include only the supported surface. In particular:

- Do not include `molsysviewer._private.*` in Public API.
- Prefer documenting user-facing entrypoints even if they are not imported from
  the top-level package (for example `molsysviewer.regions.Region`).

### Generated files

Sphinx generates per-object stub pages under:

- `docs/api/public/autosummary/`
- `docs/api/internal/autosummary/`

Do not edit those generated files manually.
When you change the allowlist or docstrings, regenerate the reference by building
the docs (see below).

### Regeneration workflow

1. (Optional) Remove stale autosummary outputs:
   - `python docs/clean_api.py`
2. Build the docs:
   - `make -C docs html`

If a local MolSysMT/Numba environment shows cache failures, document the exact
traceback before adding a workaround to the docs.

```{toctree}
:maxdepth: 2

docstrings.md
doctests.md
```

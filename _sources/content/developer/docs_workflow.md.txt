# Docs workflow (local build and RTD parity)

Use this page as a checklist when you change documentation.
It helps you keep local builds consistent with Read the Docs.

## Before you build

- Work under `docs/content/`.
- Follow the editorial rules in {doc}`documentation/web/editorial_guidelines`.
- Prefer HTML lite exports for 3D visuals.

## Build locally

From the repo root:

```bash
make -C docs html
```

If you have stale artifacts:

```bash
make -C docs clean
make -C docs html
```

## Review locally

Open the built site:

```bash
python -m molsysviewer.preview docs/_build/html
```

Serve it; do not open `index.html` from disk. This site's views share one
runtime, and a page opened from a disk is refused when it tries to load the file
beside it.

## Notebook outputs

Sphinx does not execute notebooks (`nb_execution_mode = "off"`).
If you want frozen outputs in `.ipynb` tutorials:

```bash
python docs/execute_notebooks.py -f -r docs/content/
```

The executor strips ipywidgets/AnyWidget state by default.
If you truly need a widget-based output to survive, tag the cell with:

- `keep-widget-state`

## RTD parity checklist

- Do not rely on local-only paths or local browsers to load assets.
- Keep external downloads optional or clearly documented (network access may be restricted).
- Keep notebooks reproducible from a clean environment.
- If you add new docs dependencies, update the docs environment files under `devtools/conda-envs/`.

## Coordinated source and installed-package evidence

The `Python 3.14 source pair` workflow installs and audits an exact MolSysMT
commit together with the current Viewer source. Its Linux job registers that
environment's interpreter as the notebook kernel, then executes every notebook
under `docs/content` with `--force` and all core browser suites. Documentation
changes trigger this lane as well as library changes. Notebook failure logs are
retained even if an earlier browser check fails.

This is development integration evidence. The separate `Documentation notebooks`
and `CI_e2e` workflows continue to use released dependencies on normal pushes,
or an explicitly selected coordinated staging version on manual dispatch. They
must pass with compatible installed packages before release qualification.
Passing the source lane does not clear a missing published provider, an
installed-artifact gate or the strict 1.0 gate.

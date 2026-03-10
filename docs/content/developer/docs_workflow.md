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
google-chrome docs/_build/html/index.html
```

For lite embeds, you do not need a local HTTP server if assets load from the CDN.

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

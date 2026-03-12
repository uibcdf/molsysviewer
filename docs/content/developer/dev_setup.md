# Developer setup

MolSysViewer has two toolchains:

1. Python (the `molsysviewer/` package, demos, and tests).
2. Node.js (the `molsysviewer/js/` TypeScript runtime and tests).

You keep them separate on purpose.
You do not install Node.js inside conda.

## Requirements

You need these installed at the system level:

- Python >= 3.10
- Node.js >= 18
- npm >= 9
- Git

## Recommended Node installation (NVM)

### Linux / macOS

```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# Install Node.js LTS
nvm install --lts
```

### Windows

Use nvm-windows:
`https://github.com/coreybutler/nvm-windows`

## Python environment

You can use conda/mamba.
An environment definition exists at `devtools/conda-envs/development_env.yaml`.

Install the project in editable mode:

```bash
pip install -e .[dev]
```

## TypeScript environment

All JS/TS work happens under `molsysviewer/js/`:

```bash
cd molsysviewer/js
npm install
```

Build the widget bundle when you need to test TypeScript changes locally:

```bash
npm run build
```

This produces `molsysviewer/viewer.js` and `molsysviewer/viewer.js.map`.
Do not edit these generated files by hand.

See also

- {doc}`js_workflow`

## Typical dev loop

Python changes
- Edit Python code under `molsysviewer/`.
- Restart your kernel/session if needed (editable install picks up changes).

TypeScript changes
- Edit TypeScript under `molsysviewer/js/src/`.
- Run `npm run build` when you need to test locally.
- Reload the Jupyter frontend to pick up the new bundle.

## Tests

Python
```bash
pytest
```

JS unit tests
```bash
cd molsysviewer/js
npm run test:js
```

JS E2E tests (Playwright)
```bash
cd molsysviewer/js
npm run test:e2e
```

E2E requires a local Chrome/Chromium with WebGL.

On this workstation, the verified recipe is:

```bash
PW_CHROMIUM_BIN=/usr/bin/google-chrome npm --prefix molsysviewer/js run test:e2e
```

## Using Codex or other AI tools (optional)

If you want to use Codex CLI as a development assistant:

```bash
npm install -g @openai/codex
```

Launch it from the root of the repository:

```bash
cd /path/to/molsysviewer
codex
```

## Documentation workflow

Docs live under `docs/` and build with Sphinx + MyST.
Notebook execution is off during the Sphinx build.

See also

- {doc}`docs_workflow`

If you want frozen outputs in `.ipynb`, execute notebooks manually:

```bash
python docs/execute_notebooks.py -f -r docs/content/
```

For 3D visuals, prefer HTML lite exports:

- Export with `MolSysView.write_html(..., mode="lite")` into `docs/_static/views/`.
- Embed via iframe or `molsysviewer.thirds.jupyter.load_html_in_notebook`.

## Troubleshooting

Node is not found
```bash
node --version
```

If you installed Node via NVM, re-load it:
```bash
source ~/.bashrc
nvm use --lts
```

Widget does not update in Jupyter
- Rebuild (`npm run build`).
- Restart the kernel and refresh the browser tab.

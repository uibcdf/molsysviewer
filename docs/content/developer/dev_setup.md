# Developer setup

MolSysViewer has two toolchains:

1. Python (the `molsysviewer/` package, demos, and tests).
2. Node.js (the `molsysviewer/js/` TypeScript runtime and tests).

The maintained Conda recipes provide both toolchains. You can also use a
system Node.js installation when it meets the requirements below.

## Requirements

Use these tools (the Conda recipe supplies Python, Node.js and npm):

- Python 3.14 for development; the package supports Python 3.11–3.14
- Node.js >= 18
- npm >= 9
- Git

## Optional system Node installation (NVM)

### Linux / macOS arm64

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

For routine Linux development in MolSysSuite, activate the qualified shared
`molsyssuite@uibcdf_3.14` environment. Its canonical recipe and eligibility rules
are maintained by MolSysSuite; see `MOLSYSSUITE_GUIDE.md` at the repository root.

For an isolated component environment, use the maintained Python 3.14 recipe:

```bash
conda env create -n molsysviewer-dev -f devtools/conda-envs/development_env.yaml
conda activate molsysviewer-dev
```

Install the checkout with Conda supplying dependencies:

```bash
python -m pip install --no-deps --editable .
python -m pip check
```

Use that interpreter for tests (`python -m pytest --receptor=llm`). The main
Linux/macOS matrix retains Python 3.11–3.13 comparison cells and adds 3.14;
JS/coverage, documentation and core browser jobs use 3.14. The exact-source
three-host 3.14 pair and experimental Qt lane keep their separate scopes.

### Standalone Qt host note

The final standalone packaging story is still open.

For current Qt-host development, use the working recipe recorded in:

- `devguide/standalone_supported_environment.md`

The current candidate is the official, matching conda-forge stack:

```bash
mamba install -c conda-forge \
  "pyside6=6.11.2" "qt6-webengine=6.11.2" "qt6-positioning=6.11.2"
```

Keep a clean derived environment for native Qt diagnosis. The UIBCDF Qt
family remains available for deliberate rollback with
`MOLSYSVIEWER_QT_BINDING=uibcdf`; it is no longer the default. See the linked
recipe for platform-specific evidence limits. macOS Intel is outside the
supported matrix (`uibcdf/molsyssuite#59`).

## TypeScript environment

All JS/TS work happens under `molsysviewer/js/`:

```bash
cd molsysviewer/js
npm install
```

Build the widget bundle when you need to test TypeScript changes locally:

```bash
npm run build:runtime
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

To test an already installed MolSysMT–MolSysViewer pair, install both packages
in a clean environment and run the integration tests from a directory outside
either checkout:

```bash
MOLSYSVIEWER_TEST_INSTALLED=1 python -m pytest --receptor=llm --import-mode=importlib /path/to/molsysviewer/tests/integration/test_molsysmt_integration.py
```

This mode retains the normal test fixtures but refuses to load either package
from a source checkout. Running the command from inside a checkout is an error;
that prevents a source import from masquerading as an installed-package result.

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

E2E requires a local Chrome/Chromium with WebGL2. The default command runs the complete suite and
fails if the browser or WebGL2 is unavailable. Use `E2E_ALLOW_SKIP=1` only when intentionally
opting out of E2E validation.

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

- Export into `docs/_static/views/` as described in {doc}`../user/export/sphinx_html_embedding`.
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

# MolSysViewer — Developer Guide

This document describes how to set up a local development environment for
MolSysViewer, work on the Python and TypeScript code, and run the viewer
inside JupyterLab.

## 1. Overview

MolSysViewer is split into two main layers:

- **Python layer** (`molsysviewer/`):
  - Public API (`MolSysView`)
  - Anywidget wrapper (`widget.py`)
  - Message queue and high-level behavior

- **TypeScript / Mol\* layer** (`js/src/`):
  - `widget.ts`: anywidget renderer + Mol* plugin initialization
  - `shapes.ts`: custom shapes (spheres, future primitives)
  - `structure.ts`: structure loading utilities

The JavaScript bundle (`molsysviewer/viewer.js`) is generated from the
TypeScript sources and is **not committed** to the repository. It is built
automatically during packaging (conda build) and manually during development.

---

## 2. Create and activate the development environment

A dedicated conda environment is defined in:

```text
devtools/conda_envs/development_env.yaml
```

To create or update it, run from the repository root:

```bash
bash devtools/dev.sh
```

This script will:

- use **mamba** if available, otherwise **conda**
- create or update the `molsysviewer_dev` environment

Then activate it:

```bash
conda activate molsysviewer_dev
```

---

## 3. JavaScript / TypeScript build

The JS bundle is built from `js/src/*.ts` using `esbuild`. All configuration is
in `js/package.json`.

From the repository root:

```bash
cd js
npm install        # or npm ci if you prefer
npm run build      # generates ../molsysviewer/viewer.js
cd ..
```

You should rerun `npm run build` whenever you change the TypeScript sources.

---

## 4. Installing MolSysViewer in editable mode

After building the JS bundle at least once, install the Python package in
editable mode:

```bash
pip install -e .
```

This makes your local edits to the Python code immediately visible in the
environment.

---

## 5. Running JupyterLab and testing the viewer

With the `molsysviewer_dev` environment active:

```bash
jupyter lab
```

In a notebook:

```python
import molsysviewer as mv

pdb_text = """ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
"""

v = mv.MolSysView()
v.show()
v.load_pdb_string(pdb_text)
v.add_sphere(center=(12.0, 12.0, 8.0), radius=3.0, color=0x00ff00, alpha=0.4)
```

You should see the Mol* viewer with the molecule and a transparent sphere.

---

## 6. Testing, linting, and formatting

If you add tests and tooling, typical commands in this environment would be:

```bash
pytest
pytest --cov=molsysviewer
black molsysviewer js
ruff check molsysviewer js
```

(Adjust the paths as your test and lint configuration evolves.)

---

## 7. Building and testing the conda package locally

To build the conda package using the recipe:

```bash
conda build devtools/conda-build
```

This will:

- create a build environment (using `build_env.yaml`)
- run the JS build step (`npm run build`) via `build.sh`
- run `pip install .` to build the final package
- leave a `molsysviewer-*.tar.bz2` file in your local conda-bld directory

Install it locally with:

```bash
conda install molsysviewer --use-local
```

and test it again in JupyterLab.

---

## 8. General guidelines

- Keep Python and TypeScript changes small and well-scoped.
- Whenever you change TypeScript, rebuild the bundle (`npm run build`).
- Prefer the conda package for “user-level” environments; reserve the editable
  install for development.
- Update `CHECKPOINT.md` and `ROADMAP.md` when you reach meaningful milestones.

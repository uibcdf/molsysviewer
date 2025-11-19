# **DEV_SETUP.md**

# Developer Setup Guide for **MolSysViewer**

This document describes how to set up a clean and reliable development environment for working on **MolSysViewer**, including both the Python side (AnyWidget/Jupyter integration) and the TypeScript side (Mol* + ESBuild toolchain).
The instructions apply to Linux, macOS, and Windows (with minor adjustments noted below).

---

# 1. Overview

MolSysViewer consists of two major parts:

1. **Python package**

   * Jupyter widget wrapper
   * Communication layer with AnyWidget
   * Integrated API for MolSysMT and related libraries

2. **JavaScript / TypeScript widget backend**

   * Mol* viewer integration
   * TS → JS build pipeline (via ESBuild)
   * Runs inside the Jupyter front-end and in browser contexts

Both sides must be set up correctly for full development capability.

---

# 2. Requirements

## 2.1 System Requirements

You must have the following installed **at the system level** (not inside conda):

* **Python ≥ 3.10**
* **Node.js ≥ 18**
  (Recommended installation method: `nvm`)
* **npm ≥ 9**
* **Git**

> ❗ **Do NOT install Node.js or npm inside the conda environment**.
> Node is a global development tool, just like Git.

---

## 2.2 Recommended Node Installation (NVM)

### Linux / macOS

```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# Install Node.js LTS
nvm install --lts
```

### Windows

Use **nvm-windows**:
[https://github.com/coreybutler/nvm-windows](https://github.com/coreybutler/nvm-windows)

---

# 3. Python Environment Setup

Create and activate the development environment:

```bash
conda create -n molsysviewer-dev python=3.12
conda activate molsysviewer-dev
```

Install development dependencies:

```bash
pip install -e .[dev]
```

This includes testing tools, formatting, anywidget dependencies, etc.

---

# 4. JavaScript / TypeScript Environment Setup

All JS/TS development occurs inside the `js/` directory:

```
molsysviewer/
    js/
        package.json
        src/
        ...
```

Install JS dependencies:

```bash
cd js
npm install
```

Build the widget code:

```bash
npm run build
```

This produces:

* `viewer.js`
* `viewer.js.map`

which are loaded by the Python widget via AnyWidget.

---

# 5. Development Workflow

## 5.1 Editing the Python Side

Make changes anywhere in the Python package:

```
molsysviewer/
    widget.py
    view.py
    ...
```

Reload Jupyter Lab / Notebook to test changes.

---

## 5.2 Editing the TypeScript Side

Modify files in:

```
molsysviewer/js/src/
```

Rebuild:

```bash
npm run build
```

Reload the Jupyter environment to see the effect.

---

# 6. Using Codex or Other AI Tools

If you wish to use **Codex CLI** for development assistance:

* Install Codex globally (not inside conda):

```bash
npm install -g @openai/codex
```

* Launch it from the root of the repository:

```bash
cd ~/path/to/molsysviewer
codex
```

Codex will read and operate on the entire repository.

---

# 7. Project Structure

```
molsysviewer/
│
├── js/                     # TypeScript sources
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── ... (build artifacts)
│
├── molsysviewer/           # Python package
│   ├── viewer.py
│   ├── widget.py
│   ├── _version.py
│   └── ...
│
├── tests/
├── examples/
└── setup.cfg / pyproject.toml
```

---

# 8. Best Practices

* Keep Python and JS toolchains **separate**.
* Do not commit `node_modules/`.
* Run tests regularly:

```bash
pytest
```

* Stick to a clean branch structure (`dev`, feature branches, etc.)
* When modifying JS, always rebuild before testing in Jupyter.

---

# 9. Troubleshooting

### **Node is not found**

You may need to re-load NVM:

```bash
source ~/.bashrc
nvm use --lts
```

### **Widget does not update in Jupyter**

Try:

```bash
npm run build
```

Then restart the Jupyter kernel and refresh the browser.

### **Python import errors**

Ensure your environment is active:

```bash
conda activate molsysviewer-dev
```

And reinstall editable mode:

```bash
pip install -e .
```

---

# 10. Contributing

Please ensure your PRs include:

* Clear commit messages
* Updated TypeScript build
* Working example in Jupyter
* Passing tests
* No stray `viewer.js` edits unless they come from the build

---

# 11. Contact / Maintainer Notes

For architecture discussions, cross-library integration (MolSysMT, TopoMT), or roadmap questions, contact the maintainers or open an issue on GitHub.


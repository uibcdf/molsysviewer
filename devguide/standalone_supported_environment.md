# Standalone Supported Environment

This document records the currently supported development-time environment
recipe for the standalone Qt host.

It is intentionally narrower than the final `1.0.0` packaging story.

The goal here is:

- make the current Qt host reproducible for development and QA
- keep the recipe explicit
- avoid rediscovering the same conda/pip boundary by trial and error

## Current Position (2026-04-04)

The standalone Qt host is **technically complete and packaging-validated**.

The supported recipe is now **conda-native** from the `uibcdf` channel.
The previous `pip install PySide6==6.9.2` recipe is **obsolete**.

## Supported Development Recipe

### Conda-native recipe (current)

Add the `uibcdf` channel to your environment and install the three Python-binding
packages. The two Qt helper packages (`qt6-positioning-uibcdf`,
`qt6-webengine-uibcdf`) are pulled in as run dependencies automatically.

```bash
conda install -c uibcdf -c conda-forge \
    "shiboken6-uibcdf=6.9.2=*_3" \
    "pyside6-essentials-uibcdf=6.9.2=*_3" \
    "pyside6-addons-uibcdf=6.9.2=*_3"
```

If the conda solver has trouble (common in complex envs), install from direct
file paths instead:

```bash
conda install -n <env> \
    /path/to/conda-bld/linux-64/shiboken6-uibcdf-6.9.2-*_3.conda \
    /path/to/conda-bld/linux-64/pyside6-essentials-uibcdf-6.9.2-*_3.conda \
    /path/to/conda-bld/linux-64/pyside6-addons-uibcdf-6.9.2-*_3.conda
```

### Validation smoke

```python
from PySide6_uibcdf.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QMessageBox
)
from PySide6_uibcdf.QtWebEngineWidgets import QWebEngineView
print("OK")
```

## What Was Learned

- A coherent `pip` Qt stack worked in practice as a prototype path.
- Mixing conda `pyside6` + pip `PySide6-Addons` was not reliable.
- The correct long-term path was a source-built, namespace-separated
  (`PySide6_uibcdf`) family published to a UIBCDF conda channel.
- The pip recipe is retained here only as historical context.

## Why Not The Main Environment

The main day-to-day development environment should stay conservative.

The Qt host spike has different constraints:

- Qt WebEngine availability
- binary compatibility
- Linux platform plugin support

So the supported practice is:

- keep the normal development environment for general MolSysViewer work
- use a derived Qt-spike environment for standalone-host work

## Linux Note

On Debian/Ubuntu-like systems, the tested Qt host also needed:

```bash
sudo apt install libxcb-cursor0
```

Without that, the Qt `xcb` platform plugin may fail to initialize.

## What This Recipe Is For

Use this recipe when you need to work on:

- `molsysviewer-qt`
- `python -m molsysviewer.standalone_qt`
- Qt-host behavior
- Qt-host smoke/QA

This recipe is not yet the final answer for:

- conda packaging
- end-user standalone installation
- release distribution

## What Still Remains Open

The remaining standalone environment questions are:

- whether the final supported recipe is:
  - conda-only
  - or a supported conda+pip combination
- how that recipe should be distributed
- whether final release packaging should remain environment-driven or become a
  more app-like distribution

Those are Phase E / pre-`1.0.0` questions.

They should not block continued host development now that a supported prototype
recipe exists.

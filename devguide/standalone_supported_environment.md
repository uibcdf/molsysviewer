# Standalone Development Environment

This document records the currently reproducible development-time environment
recipe for the experimental standalone Qt host. The host is outside the 1.0
support promise and its visible-window observations do not block the 1.0 tag.

It is intentionally narrower than a future supported-host packaging story.

The goal here is:

- make the current Qt host reproducible for development and QA
- keep the recipe explicit
- avoid rediscovering the same conda/pip boundary by trial and error

## Current candidate recipe (2026-09-27)

The standalone host now prefers canonical `PySide6`. It uses
`PySide6_uibcdf` only when the canonical namespace is absent, retaining the
existing UIBCDF packages as a fallback. Do not install both stacks into a
new environment: Qt native libraries and WebEngine resource paths must remain
coherent.

For a deliberate rollback in an existing UIBCDF environment, set
`MOLSYSVIEWER_QT_BINDING=uibcdf`. The default `auto` selects canonical PySide6
if present and selects UIBCDF only when the canonical namespace is absent.
`MOLSYSVIEWER_QT_BINDING=canonical` forces the official binding. A broken
canonical installation does not silently switch to the fallback.

For Linux development and CI, use the matching conda-forge stack:

```bash
mamba install -c conda-forge \
    "pyside6=6.11.2" "qt6-webengine=6.11.2" "qt6-positioning=6.11.2"
```

The coordinated public MolSysMT 0.22.4 / MolSysViewer 0.23.4 pair plus this
stack resolved and passed real WebEngine transport and two-generation payload
smokes in clean Linux Conda environments on Python 3.11, 3.12, 3.13 and 3.14.
The real-window probe reached bridge readiness and completed payload delivery
under Xvfb/SwiftShader; this is not a visible-window rendering certificate.

| Platform | Conda resolution with canonical Qt 6.11.2 | Qt host runtime evidence |
| --- | --- | --- |
| `linux-64` | Solved and installed | Transport and payload smokes passed on Python 3.11–3.14; visible-window observation still pending |
| `win-64` | Dry-run solved on Python 3.14 | Not run on Windows yet |
| `osx-arm64` | Dry-run solved on Python 3.14 with macOS 14 override | Not run on macOS yet |
| `osx-64` | Outside the supported platform matrix | No support claim or required runtime gate |

Solver success does not confer supported-platform status. The experimental
standalone Qt host is currently runtime-tested on Linux only; Windows and macOS arm64
have solver-only evidence. The support boundary and user-facing wording remain
tracked in `uibcdf/molsysviewer#97`. The suite-wide macOS architecture decision
is tracked in `uibcdf/molsyssuite#59`.

macOS support is currently limited to Apple Silicon (arm64). Intel-based macOS
(x86_64) is not part of the supported platform matrix. Support may be
reconsidered if there is demonstrated user demand.

### Historical UIBCDF 6.9.2 recipe (superseded as the default)

The standalone Qt host was **technically complete and packaging-validated**
with the custom 6.9.2 stack.

That recipe was **conda-native** from the `uibcdf` channel. It is a
historical reference, not the current recommendation or the current
6.10.1 local rollback recipe. The latter is documented in
`uibcdf/molsyssuite#52`.

## Supported Development Recipe

### Conda-native recipe (historical fallback)

The full conda family is **5 packages**:

| Package | Version | Build | Role | How it arrives |
|---------|---------|-------|------|----------------|
| `shiboken6-uibcdf` | `6.9.2` | `_3` or newer | Python/C++ bridge | install explicitly |
| `pyside6-essentials-uibcdf` | `6.9.2` | `_3` or newer | Core Qt bindings | install explicitly |
| `pyside6-addons-uibcdf` | `6.9.2` | `_5` or newer | Add-on Qt bindings (includes WebEngine; exposes `QWebEngineUrlScheme.setFlags`) | install explicitly |
| `qt6-positioning-uibcdf` | `6.9.2` | `_0` | Qt Positioning native runtime | auto-pulled as dependency of `addons` |
| `qt6-webengine-uibcdf` | `6.9.2` | `_1` or newer | Qt WebEngine native runtime, resources, locales, activation scripts | auto-pulled as dependency of `addons` |

You only need to name the three Python-binding packages explicitly.
The two Qt native-runtime packages are declared as `run` dependencies of
`pyside6-addons-uibcdf` and are resolved automatically by the solver.

```bash
mamba install -c uibcdf -c conda-forge \
    "shiboken6-uibcdf=6.9.2" \
    "pyside6-essentials-uibcdf=6.9.2" \
    "pyside6-addons-uibcdf=6.9.2"
```

If the solver has trouble (common in complex envs), install all five from direct
file paths instead:

```bash
mamba install -n <env> \
    /path/to/conda-bld/linux-64/shiboken6-uibcdf-6.9.2-*_3.conda \
    /path/to/conda-bld/linux-64/pyside6-essentials-uibcdf-6.9.2-*_3.conda \
    /path/to/conda-bld/linux-64/pyside6-addons-uibcdf-6.9.2-*_3.conda \
    /path/to/conda-bld/linux-64/qt6-positioning-uibcdf-6.9.2-*.conda \
    /path/to/conda-bld/linux-64/qt6-webengine-uibcdf-6.9.2-*.conda
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

Current package-level fixes also include:

- `qt6-webengine-uibcdf` exports the Qt WebEngine resource paths and Chromium
  sandbox override through conda activation/deactivation scripts.
- `pyside6-addons-uibcdf` exposes `QWebEngineUrlScheme.flags()` and
  `setFlags(...)`, which MolSysViewer needs for fetchable custom schemes.

- A coherent `pip` Qt stack worked in practice as a prototype path.
- Mixing conda `pyside6` + pip `PySide6-Addons` was not reliable.
- The source-built, namespace-separated (`PySide6_uibcdf`) family was
  published to a UIBCDF conda channel. The canonical 6.11.2 stack has since
  passed the Linux clean-environment probes above, so this is no longer the
  only viable path.
- The pip recipe is retained here only as historical context.

## Main Development Environment And Isolated Qt Probes

The shared Linux `molsyssuite@uibcdf_3.14` development environment now
uses the official conda-forge 6.11.2 family after a clean Qt-pinned
solve and targeted runtime tests (`uibcdf/molsyssuite#52`). A separate
clean Qt environment remains useful for isolating native-runtime
problems or comparing a newer candidate before changing the shared
environment.

The Qt host spike has different constraints:

- Qt WebEngine availability
- binary compatibility
- Linux platform plugin support

So the supported practice is:

- keep the normal development environment for general MolSysViewer work
- use a clean derived Qt environment to reproduce native-runtime failures

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

- runtime certification of Windows and macOS ARM
- whether the final supported recipe is conda-only or also includes pip
- how that recipe should be distributed
- whether final release packaging should remain environment-driven or become a
  more app-like distribution

Those are Phase E / pre-`1.0.0` questions.

They should not block continued host development now that a supported prototype
recipe exists.

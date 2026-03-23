# Standalone Qt Prototype Plan

This document defines the first technical prototype for the final standalone
host direction already chosen in:

- `devguide/standalone_host_plan.md`

The goal here is narrower than "build the final standalone product".

The goal is:

- prove that MolSysViewer can live inside a real app window
- keep the same runtime and workbench model
- avoid moving viewer logic into the host

## Prototype Goal

The first Qt prototype should demonstrate:

- one native application window
- one embedded MolSysViewer runtime
- one minimal menu bar
- one minimal startup path
- the same `Core` workspace and `panel mode` already used in notebook/popup

If that works and still feels like MolSysViewer, then the final standalone host
becomes much more concrete.

## Scope Of Prototype 1

Prototype 1 should include:

- `PySide6`
- `QMainWindow`
- `QWebEngineView`
- load the existing standalone/runtime HTML into the embedded webview
- window title + app identity placeholder
- minimal menus:
  - `File`
  - `View`
  - `Export`
- one startup action:
  - load demo

Prototype 1 does **not** need yet:

- full file-open support
- session/project management
- recent files
- preferences
- multi-window mode
- add-on-specific host chrome
- custom export dialogs

## Recommended Technical Shape

The host should be kept thin.

### Host layer

Owns:

- window
- menu bar
- host shortcuts
- native dialogs later
- startup flow later

### Viewer layer

Owns:

- canvas
- workspaces
- panel stacks
- add-on runtime projection
- context menu semantics
- figure export semantics
- scene/state logic

The Qt host should not become a second controller for viewer semantics.

## Loading Strategy

For the first prototype, prefer the simplest path:

1. reuse the current standalone HTML generation path
2. write/load that HTML in a `QWebEngineView`
3. confirm that the embedded runtime behaves like the current browser-hosted
   `standalone 0`

That keeps the first prototype honest:

- same runtime
- new host shell

Only later should we optimize whether the final host loads from:

- generated temporary HTML
- a local mini server
- or another controlled runtime source

## Minimal Menu Contract

Prototype 1 menus should stay intentionally small.

### File

- `Load Demo`
- `Close`

### View

- `Open Navigate`
- `Open Workbench`
- `Close Panel Mode`

### Export

- `Export HTML`
- `Export Figure`

At this stage, these can be placeholders or thin wrappers if needed.
What matters is host ownership of app-level affordances.

## First Validation Criteria

Prototype 1 is successful if:

- the window feels like an app, not a browser tab
- the embedded runtime still behaves like MolSysViewer
- `Core` and `panel mode` survive unchanged in meaning
- the host code remains thin and clearly separated
- the next iteration naturally suggests:
  - local file open
  - better startup flow
  - standalone-native export affordances

## Expected First Dependency

The first dependency to add for this prototype is:

- `pyside6`
- `PySide6-Addons` when `PySide6.QtWebEngineWidgets` is missing from the
  conda environment

Current recommendation for developers is:

```bash
conda install -c conda-forge pyside6
```

In the current development track, that may still be insufficient on some
platform/Python combinations because `conda-forge::pyside6` does not always
expose `PySide6.QtWebEngineWidgets`.

When that happens, install the matching PyPI addons package after `pyside6`,
for example:

```bash
pip install PySide6-Addons==$(python -c "import PySide6; print(PySide6.__version__)")
```

This is a development-time fallback for the prototype. It is not yet the final
conda packaging strategy for MolSysViewer 1.0.

## What Not To Do In Prototype 1

Do not:

- redesign the viewer UI for Qt
- create standalone-only panel behavior
- move workbench logic into menus
- create a separate add-on loading system
- overbuild startup/project/session chrome

Prototype 1 should answer one question only:

- can the current MolSysViewer runtime live convincingly inside a real Qt app
  window?

## Immediate Next Step

After this document, the next implementation slice should be:

1. add `pyside6` as an optional development dependency
2. document the temporary `PySide6-Addons` fallback for `QtWebEngineWidgets`
3. create a tiny standalone Qt launcher module
4. open one `QMainWindow` + `QWebEngineView`
5. load the existing standalone HTML path
6. verify that `Core` and `panel mode` remain intact

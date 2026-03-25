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
- multi-window mode
- add-on-specific host chrome
- custom export dialogs

Those two bullets are now outdated:

- recent files are already present in the thin host
- a very small amount of shell persistence is already justified:
  - recent sources
  - last source
  - last window size

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

1. reuse the current standalone export path
2. in the Qt host, prefer the `lite` runtime route rather than the AMD widget
   manager route
3. prefer local packaged `viewer.js` first, with CDN only as fallback
4. write/load that HTML in a `QWebEngineView`
5. confirm that the embedded runtime behaves like the current browser-hosted
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

## Dependency Findings From The First Spike

The first Qt spike already established several concrete facts:

- `conda-forge::pyside6` alone was not sufficient in the tested Python 3.13
  environments because `PySide6.QtWebEngineWidgets` was not exposed.
- Mixing:
  - conda-forge `pyside6`
  - pip `PySide6-Addons`
  was not reliable in the tested environment because the resulting binary stack
  failed to resolve `libshiboken6`.
- A coherent `pip` Qt stack **did** work:
  - `PySide6==6.9.2`
  - `PySide6-Addons==6.9.2`
- On Linux, the tested prototype also required the native `xcb` cursor support
  so the Qt platform plugin could load cleanly.
- Once the Qt host stopped loading the AMD widget-manager HTML and used the
  `lite` runtime path with local `viewer.js`, the prototype could open:
  - the empty host
  - and `dialanine --demo`

### Current development recipe

The current working development recipe for the Qt prototype should be treated
as:

```bash
pip install PySide6==6.9.2 PySide6-Addons==6.9.2
```

This should be done in a dedicated Qt-spike environment derived from a working
MolSysSuite environment, not in the main day-to-day environment.

On Debian/Ubuntu-like Linux systems, the tested prototype also needed:

```bash
sudo apt install libxcb-cursor0
```

This is a development-time recipe for the prototype. It is **not** yet the
final standalone packaging story for MolSysViewer `1.0.0`.

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

1. keep the working Qt-spike recipe explicit in `devguide`
2. keep the Qt host on the `lite` runtime path with local `viewer.js` first
3. continue improving the thin Qt launcher and menu contract
4. keep host-level persistence deliberately small and shell-only
5. verify that `Core` and `panel mode` remain intact
6. treat final conda/release packaging as a later standalone release question

## Pre-1.0 Host Sufficiency Gate

The Qt host should not stay in endless "prototype polish".

Before the final packaging decision, the host should be treated as
pre-`1.0.0` sufficient once it can honestly provide:

- a clear empty/startup path
- credible shell-owned load flows:
  - demo
  - file
  - PDB ID
  - generic source
- a clean return to empty host state
- app-level navigation/export affordances that feel intentional
- small but useful persistence:
  - recent sources
  - last source
  - window size
- non-silent, understandable host-side error handling

That gate should still preserve the thin-host rule:

- no duplicate viewer semantics
- no standalone-only add-on/runtime model
- no project/session manager detour before it is truly needed

The following should **not** be required before judging the host sufficient:

- final packaging closure
- multi-window support
- full project/session management
- more shell chrome that does not improve credibility of the host itself

Current reading after the latest slices:

- that sufficiency gate is now materially met by the thin Qt host
- so the next standalone uncertainty is no longer "can the host feel real?"
- it is now mainly:
  - packaging/distribution strategy
  - and any future host work should be justified by a real QA/runtime gap

# Standalone Supported Environment

This document records the currently supported development-time environment
recipe for the standalone Qt host.

It is intentionally narrower than the final `1.0.0` packaging story.

The goal here is:

- make the current Qt host reproducible for development and QA
- keep the recipe explicit
- avoid rediscovering the same conda/pip boundary by trial and error

## Current Position

The standalone Qt host is already technically viable.

What is **not** yet final is the packaging/distribution strategy.

So this document should be read as:

- supported prototype/development recipe
- not final end-user installation guidance

## What Was Learned

The current evidence says:

- the browser-hosted standalone bridge is fine as a teaching bridge
- the final standalone host direction remains:
  - `PySide6 + Qt WebEngine`
- a coherent `pip` Qt stack worked in practice
- the tested conda-only path did **not** expose
  `PySide6.QtWebEngineWidgets` reliably enough in the development environment
- mixing:
  - conda `pyside6`
  - pip `PySide6-Addons`
  inside the same main development environment was not reliable

## Supported Development Recipe

The currently supported recipe for Qt-host development is:

1. start from a working MolSysSuite-capable environment
2. derive a dedicated Qt-spike environment from it
3. install a coherent Qt stack from `pip`
4. keep the rest of the scientific/runtime stack intact

### Practical shape

The recommended approach is:

1. clone the main working environment
2. in that derived environment, install:

```bash
pip install PySide6==6.9.2 PySide6-Addons==6.9.2
```

This should be treated as the supported prototype recipe unless a new validated
recipe replaces it in `devguide`.

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

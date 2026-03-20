# Develop a minimal add-on

This recipe shows the current minimal contract for developing an add-on for
MolSysViewer.

It is aimed at developers extending the viewer with domain-specific MolSysSuite
capabilities.

## Goal

Build a tiny add-on that contributes one panel and can be registered either:

- directly as an `AddonSpec`
- or through an importable module

## 1. Create the spec

```python
from molsysviewer import AddonPanelSpec, AddonSpec

addon = AddonSpec(
    name="myaddon",
    package="molsysviewer-myaddon",
    version="0.1.0",
    description="Minimal example add-on.",
    panels=(
        AddonPanelSpec(
            id="my-panel",
            title="My Panel",
            entry="molsysviewer_myaddon.panel.main",
        ),
    ),
)
```

## 2. Register it directly during development

```python
import molsysviewer

molsysviewer.addons.register(addon)
```

New views now inherit that host-level add-on availability:

```python
view = molsysviewer.new_view()
view.addons.available()
view.addons.panel_specs()
```

## 3. Turn it into an importable add-on module

Recommended package split:

- scientific/domain package:
  - `myaddon`
- MolSysViewer integration package:
  - `molsysviewer-myaddon`

Recommended import name:

- `molsysviewer_myaddon`

The module should expose one of:

- `addon`
- `ADDON`
- `get_addon()`

Example:

```python
from molsysviewer import AddonPanelSpec, AddonSpec

addon = AddonSpec(
    name="myaddon",
    package="molsysviewer-myaddon",
    panels=(
        AddonPanelSpec(
            id="my-panel",
            title="My Panel",
            entry="molsysviewer_myaddon.panel.main",
        ),
    ),
)
```

## 4. Register the module explicitly

For local development or unpublished work:

```python
import molsysviewer

molsysviewer.addons.register_module("molsysviewer_myaddon")
```

If you want a concrete reference inside MolSysViewer itself, inspect:

- `molsysviewer.addon_templates.minimal_topomt`

That module exists only to demonstrate the add-on contract in a stable,
importable form.

## 5. Discovery

MolSysViewer also has a simple discovery path:

```python
import molsysviewer

molsysviewer.addons.discover()
```

Today this only checks a maintained list of known module names.
It is intentionally conservative.

## 6. Optional minimal lifecycle

If your add-on needs small Python-side setup or teardown when it becomes active
in a view, you can provide:

- `on_enable(view)`
- `on_disable(view)`

either through an explicit lifecycle object at registration time or directly in
the add-on module.

This lifecycle is intentionally minimal.
It is not yet a broad runtime hook system.

## Contract summary

The important pieces to keep stable are:

- host registry:
  - `molsysviewer.addons`
- per-view projection:
  - `view.addons`
- add-on object:
  - `AddonSpec`
- optional lifecycle:
  - `AddonLifecycleSpec`
- importable module contract:
  - `addon`
  - `ADDON`
  - or `get_addon()`

## Project defaults during development

If you want a local project to enable or disable add-ons by default, define in
`_molsysviewer.py`:

```python
ADDONS_ENABLED = ["topomt"]
ADDONS_DISABLED = ["pharmacophoremt"]
```

and apply those defaults explicitly:

```python
import molsysviewer

molsysviewer.addons.load_project_config("_molsysviewer.py")
```

New views will inherit that host-level baseline, while `view.addons` can still
override it locally for debugging.

## What not to assume yet

Do not assume that `1.0` already standardizes:

- entry-point metadata discovery
- persisted add-on preferences
- frontend runtime lifecycle hooks
- complex automatic loading of arbitrary packages

The current goal is a small, explicit, stable extension contract.

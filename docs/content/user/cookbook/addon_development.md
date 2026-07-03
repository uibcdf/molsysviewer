# Develop a minimal add-on

This recipe shows the current minimal contract for developing an add-on for
MolSysViewer.

It is aimed at developers extending the viewer with domain-specific MolSysSuite
capabilities.

## Goal

Build a tiny add-on that contributes one panel and can be registered either:

- directly as an `AddonSpec`
- or through an importable module

If it is a larger add-on, it may also declare a workspace.

For real MolSysSuite teams, a better first milestone is:

- one workspace if the add-on is large enough
- one panel
- one addon section
- one context action
- optional minimal lifecycle hooks

## 1. Create the spec

```python
from molsysviewer import AddonPanelSpec, AddonSpec, AddonWorkspaceSpec

addon = AddonSpec(
    name="myaddon",
    package="molsysviewer-myaddon",
    version="0.1.0",
    description="Minimal example add-on.",
    workspaces=(
        AddonWorkspaceSpec(
            id="myaddon",
            title="My Add-on",
            entry_panel="my-panel",
        ),
    ),
    panels=(
        AddonPanelSpec(
            id="my-panel",
            title="My Panel",
            entry="molsysviewer_myaddon.panel.main",
        ),
    ),
)
```

If you prefer to start from the bundled reference example instead of from
scratch, use:

- [`minimal_topomt.py`](https://github.com/uibcdf/molsysviewer/blob/main/molsysviewer/addon_templates/minimal_topomt.py)

That template is now more than declarative and more than single-panel:

- its lifecycle leaves visible markers on the `view`
- its context action records the last handled payload
- it models a small but credible workspace:
  - multiple panels
  - multiple addon sections
  - more than one context action
  - one export helper

That makes it useful as an end-to-end starter, not only as a static spec sample.

You can also activate that bundled reference without memorizing module names:

```python
import molsysviewer

molsysviewer.addon_templates.list_reference_addons()
molsysviewer.addon_templates.register_reference_addon("topomt")
```

If you want the shortest end-to-end smoke path for a downstream team demo, use:

```python
import molsysviewer

view = molsysviewer.addon_templates.build_reference_demo_view("topomt")
view
```

That helper currently does three things for you:

- registers the bundled reference add-on
- opens the `dialanine` demo system
- opens the shared `Add-ons` panel so the reference workspace is visible

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

If the add-on needs lifecycle hooks, it may also expose:

- `lifecycle`
- `LIFECYCLE`
- or plain functions:
  - `on_enable`
  - `on_disable`
  - `on_context_action`

Example:

```python
from molsysviewer import AddonPanelSpec, AddonSpec, AddonWorkspaceSpec

addon = AddonSpec(
    name="myaddon",
    package="molsysviewer-myaddon",
    workspaces=(
        AddonWorkspaceSpec(
            id="myaddon",
            title="My Add-on",
            entry_panel="my-panel",
        ),
    ),
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

Recommended use:

- `on_enable(view)`:
  - prepare small per-view state
- `on_disable(view)`:
  - clean it up
- `on_context_action(view, action_id, payload)`:
  - connect one visible context-menu action back to Python-side behavior

## Contract summary

The important pieces to keep stable are:

- host registry:
  - `molsysviewer.addons`
- per-view projection:
  - `view.addons`
- add-on object:
  - `AddonSpec`
- optional workspace:
  - `AddonWorkspaceSpec`
- optional lifecycle:
  - `AddonLifecycleSpec`
- importable module contract:
  - `addon`
  - `ADDON`
  - or `get_addon()`
- reference smoke helper:
  - `molsysviewer.addon_templates.build_reference_demo_view(...)`

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

## Recommended checklist before sharing your add-on with the MolSysViewer team

1. the package imports as `molsysviewer_<name>`
2. it exposes `addon`, `ADDON`, or `get_addon()`
3. if it exposes lifecycle, the hooks are small and explicit
4. if it is a large add-on, it defines a workspace
5. it can be registered both:
   - manually via `molsysviewer.addons.register_module(...)`
   - and through discovery once its module name is added to the maintained list

For the more normative version of this contract, also see:

- [`standards/addons/README.md`](https://github.com/uibcdf/molsysviewer/blob/main/standards/addons/README.md)
- [`standards/addons/IMPLEMENTATION_CONTRACT.md`](https://github.com/uibcdf/molsysviewer/blob/main/standards/addons/IMPLEMENTATION_CONTRACT.md)

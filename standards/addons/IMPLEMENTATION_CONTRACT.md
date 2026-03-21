# Add-on Implementation Contract

This file defines the implementation contract that downstream MolSysViewer
add-ons should follow.

It is intentionally conservative.
The goal is to let ecosystem teams start now without forcing repeated rewrites
of package shape and registration semantics.

## Public Vocabulary

Use **add-on** consistently.

Public names:

- `molsysviewer.addons`
- `view.addons`
- `AddonSpec`
- `AddonWorkspaceSpec`
- `AddonPanelSpec`
- `AddonContextActionSpec`
- `AddonWorkbenchSectionSpec`
- `AddonShapeProviderSpec`
- `AddonExportHelperSpec`
- `AddonLifecycleSpec`

Do not introduce `plugin` as a parallel public vocabulary.

## Host vs View

The contract is split in two levels:

- `molsysviewer.addons`
  - host-level registry
- `view.addons`
  - per-view projection of the host registry

Add-ons belong to the host, not to a single view instance.

## Package Shape

Recommended split for larger integrations:

- domain/scientific package:
  - `topomt`
- MolSysViewer integration package:
  - `molsysviewer-topomt`

Recommended Python import path:

- `molsysviewer_topomt`

## Importable Module Contract

An importable add-on module must expose one of:

- `addon`
- `ADDON`
- `get_addon()`

and it must resolve to an `AddonSpec`.

## Lifecycle Contract

If lifecycle is needed, the module may expose:

- `lifecycle`
- `LIFECYCLE`
- or plain functions:
  - `on_enable`
  - `on_disable`
  - `on_context_action`

Lifecycle must remain small and explicit:

- `on_enable(view)`
- `on_disable(view)`
- `on_context_action(view, action_id, payload)`

Do not assume broader frontend hook contracts yet.

## Contribution Types

An add-on may currently declare:

- workspaces
- panels
- context actions
- workbench sections
- shape providers
- style helpers
- export helpers
- tool modes

## Workspace Guidance

- `Core` is the native workspace
- large add-ons may define one or more workspaces
- small add-ons should be allowed to remain lighter and not define a workspace

Do not treat “every add-on” and “workspace” as synonyms.

## Discovery and Registration

There are two supported paths:

### 1. Manual coupling

For local development or unpublished add-ons:

```python
import molsysviewer

molsysviewer.addons.register_module("molsysviewer_topomt")
```

### 2. Discovery

For known packages added to MolSysViewer's maintained discovery list:

```python
import molsysviewer

molsysviewer.addons.discover()
```

Discovery is intentionally conservative.
Do not assume arbitrary package scanning or final entry-point metadata yet.

## First Milestone for External Teams

The recommended first milestone is:

1. one workspace if the add-on is large enough
2. at least one panel
3. at least one workbench section
4. at least one context action
5. one small lifecycle-driven behavior

That is enough to validate:

- packaging
- registration
- discovery
- activation
- runtime summary
- Python-side action handling

## Reference Implementation

Start from:

- [`minimal_topomt.py`](/home/diego/repos@uibcdf/molsysviewer/molsysviewer/addon_templates/minimal_topomt.py)

That reference template is intentionally small but already demonstrates:

- workspace contribution
- multi-panel contribution
- multi-section workbench contribution
- more than one context-action contribution
- shape-provider contribution
- export-helper contribution
- lifecycle export
- a visible lifecycle effect on the `view`

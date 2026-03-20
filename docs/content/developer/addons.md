# Add-ons

MolSysViewer now exposes a first explicit add-on platform aimed at the broader
MolSysSuite ecosystem.

This page describes the current contract that downstream packages should target.

## Mental model

The add-on model is split into two levels:

- `molsysviewer.addons`
  - host-level registry
- `view.addons`
  - per-view projection of the host registry

This is intentional.

Add-ons belong to the MolSysViewer host, not to one single view instance.
Each view inherits what the host knows and can still enable or disable add-ons
locally.

## Public vocabulary

Use **add-ons** consistently.

The public API avoids parallel terminology such as `plugins`.

Current public surfaces include:

- `molsysviewer.addons`
- `view.addons`
- `AddonSpec`
- `AddonPanelSpec`
- `AddonContextActionSpec`
- `AddonWorkbenchSectionSpec`
- `AddonShapeProviderSpec`
- `AddonStyleHelperSpec`
- `AddonExportHelperSpec`
- `AddonToolModeSpec`

## Current contribution types

An add-on may currently declare:

- panels
- context-menu actions
- workbench sections
- shape providers
- style helpers
- export helpers
- tool modes

These contributions are intentionally typed and explicit.

## Discovery

The current discovery strategy is deliberately conservative.

MolSysViewer maintains a small list of known add-on module names and can try to
discover them with:

```python
import molsysviewer

molsysviewer.addons.discover()
```

Missing known modules are ignored without error.

You can inspect the maintained known-module list with:

```python
molsysviewer.addons.known_modules()
```

This is a pragmatic first step.
It avoids a large dynamic plugin system before the first real ecosystem add-ons
exist.

## Manual coupling for development

For local or unpublished work, explicit registration is supported and expected.

Registering a spec directly:

```python
import molsysviewer
from molsysviewer import AddonPanelSpec, AddonSpec

molsysviewer.addons.register(
    AddonSpec(
        name="my-addon",
        panels=(
            AddonPanelSpec(
                id="my-panel",
                title="My Panel",
                entry="my_addon.panel.main",
            ),
        ),
    )
)
```

Registering an importable module that exposes a valid add-on contract:

```python
import molsysviewer

molsysviewer.addons.register_module("molsysviewer_myaddon")
```

## Packaging contract

The current packaging contract is lightweight.

Recommended split:

- scientific/domain package:
  - `topomt`
- MolSysViewer integration package:
  - `molsysviewer-topomt`

Recommended Python import name:

- `molsysviewer_topomt`

The module should expose one of:

- `addon`
- `ADDON`
- `get_addon()`

and that object/factory must resolve to an `AddonSpec`.

## View-local behavior

New views inherit the globally registered add-ons:

```python
import molsysviewer

view = molsysviewer.new_view()
```

The local projection can then be inspected or overridden:

```python
view.addons.available()
view.addons.enabled()
view.addons.disable("topomt")
view.addons.reset()
```

## What is still intentionally missing

This first slice does **not** yet try to standardize:

- entry-point metadata discovery
- persisted enable/disable preferences
- full runtime lifecycle hooks
- execution of arbitrary add-on code in the frontend
- a marketplace-like plugin model

That is deliberate.
The current goal is a stable connection platform for the first real MolSysSuite
add-ons, not a maximal extension framework.

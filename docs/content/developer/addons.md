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
- `AddonLifecycleSpec`

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

MolSysViewer also ships a tiny reference template module you can inspect:

- `molsysviewer.addon_templates.minimal_topomt`

It is intentionally small and only demonstrates the registration contract, not
the full runtime behavior of a real scientific add-on.

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

The bundled reference template follows exactly that rule.

## Project-level defaults

Add-on enable/disable can now also be configured through `_molsysviewer.py`.

Supported names there are:

- `ADDONS_ENABLED`
- `ADDONS_DISABLED`

Those names define host-level defaults, not per-view overrides.

Apply them explicitly with:

```python
import molsysviewer

molsysviewer.addons.load_project_config("_molsysviewer.py")
```

The host registry updates its default enabled/disabled set, and new views
inherit that baseline automatically.
Existing `view.addons` overrides remain local.

## Minimal lifecycle

MolSysViewer now also supports a deliberately small per-view lifecycle:

- `on_enable(view)`
- `on_disable(view)`
- `on_context_action(view, action_id, payload)`

This lifecycle is Python-side and view-local.
It is intended for light runtime wiring when an add-on becomes active in a
specific view.

You can provide it explicitly:

```python
import molsysviewer
from molsysviewer.addons import AddonLifecycleSpec

molsysviewer.addons.register(
    my_addon_spec,
    lifecycle=AddonLifecycleSpec(
        on_enable=my_on_enable,
        on_disable=my_on_disable,
        on_context_action=my_on_context_action,
    ),
)
```

or expose it from an importable add-on module through:

- `lifecycle`
- `LIFECYCLE`
- or plain module functions:
  - `on_enable`
  - `on_disable`
  - `on_context_action`

This remains intentionally small:

- no persisted lifecycle state
- no frontend runtime code execution contract
- no broad hook surface yet

The new `on_context_action(...)` hook is the first real runtime bridge from
visible add-on UI back into Python-side behavior.

When an enabled add-on contributes a compatible context-menu action and the
user activates it, MolSysViewer can now call:

- `on_context_action(view, action_id, payload)`

with a structured payload containing, for example:

- `addon`
- `addon_action_id`
- `addon_action_title`
- `context`

This keeps the first real add-on runtime behavior explicit and testable without
opening arbitrary frontend execution.

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

MolSysViewer also now mirrors a minimal add-on runtime summary into the current
Workbench runtime.

The first visible slice is intentionally modest:

- enabled add-ons appear in a dedicated `Add-ons` section
- panel titles and workbench-section titles are summarized there
- context-action titles and export-helper titles are now also summarized there

This is not full add-on UI execution yet.
It is only the first visible runtime proof that the add-on platform can reach
the viewer surface.

The next visible slice is now also present in the context menu:

- compatible add-on context actions can appear in an `Add-ons` section
- clicking one emits a structured Python-side `interaction_context_action`

This still does **not** mean that add-ons already execute arbitrary frontend
logic.
At this stage the menu action is mainly a clean runtime bridge for future
domain-specific behavior.

## What is still intentionally missing

This first slice does **not** yet try to standardize:

- entry-point metadata discovery
- persisted enable/disable preferences
- rich runtime lifecycle hooks beyond `on_enable(view)` / `on_disable(view)`
- execution of arbitrary add-on code in the frontend
- a marketplace-like plugin model

That is deliberate.
The current goal is a stable connection platform for the first real MolSysSuite
add-ons, not a maximal extension framework.

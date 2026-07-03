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

## What external add-on teams can rely on now

The current platform is ready enough for MolSysSuite teams to start prototyping
against it.

The stable surface to target today is:

- host-level registration:
  - `molsysviewer.addons`
- view-local projection:
  - `view.addons`
- typed contribution specs:
  - workspaces
  - panels
  - addon sections
  - context actions
  - shape providers
  - export helpers
- minimal lifecycle:
  - `on_enable(view)`
  - `on_disable(view)`
  - `on_context_action(view, action_id, payload)`

What downstream teams should not assume yet:

- a final workspace launcher/mosaic
- persisted add-on preferences
- broad frontend runtime hooks
- standalone as a finished product

For the most stable normative references, also see:

- [`standards/addons/README.md`](https://github.com/uibcdf/molsysviewer/blob/main/standards/addons/README.md)
- [`standards/addons/IMPLEMENTATION_CONTRACT.md`](https://github.com/uibcdf/molsysviewer/blob/main/standards/addons/IMPLEMENTATION_CONTRACT.md)

## Public vocabulary

Use **add-ons** consistently.

The public API avoids parallel terminology such as `plugins`.

Current public surfaces include:

- `molsysviewer.addons`
- `view.addons`
- `AddonSpec`
- `AddonWorkspaceSpec`
- `AddonPanelSpec`
- `AddonContextActionSpec`
- `AddonSectionSpec`
- `AddonShapeProviderSpec`
- `AddonStyleHelperSpec`
- `AddonExportHelperSpec`
- `AddonToolModeSpec`
- `AddonLifecycleSpec`

## Current contribution types

An add-on may currently declare:

- workspace specs
- panels
- context-menu actions
- addon sections
- shape providers
- style helpers
- export helpers
- tool modes

These contributions are intentionally typed and explicit.

Important clarification:

- not every add-on should become a workspace
- `Core` remains the native workspace
- larger add-ons may later contribute a workspace plus its own panel stack
- smaller add-ons may remain lighter and only contribute local surfaces

That workspace layer is already part of the typed add-on contract and now also
travels through the current runtime summary path, even though a dedicated
workspace selector UI has not been built yet.

## Discovery

The current discovery strategy is deliberately conservative.

By default, `molsysviewer.addons.discover()` loads add-ons exposed through the
standard Python entry point group `molsysviewer.addons`. This avoids importing
large scientific add-on stacks just because `molsysviewer` was imported.

Legacy add-ons that have not yet published entry points can still be discovered
from the maintained fallback module list by opting in explicitly:

```python
import molsysviewer

molsysviewer.addons.discover(include_known_modules=True)
```

Missing known modules are ignored without error. You can inspect the maintained
known-module list with:

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
from molsysviewer import AddonPanelSpec, AddonSpec, AddonWorkspaceSpec

molsysviewer.addons.register(
    AddonSpec(
        name="my-addon",
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

It is intentionally bounded, but it now demonstrates more than the bare
registration contract:

- one workspace
- several panels
- several addon/runtime contributions
- a minimal but visible lifecycle flow

So it is a better starter for downstream teams than a purely declarative
one-panel example.

For onboarding and demos, MolSysViewer also exposes a small helper surface:

```python
import molsysviewer

molsysviewer.addon_templates.list_reference_addons()
molsysviewer.addon_templates.register_reference_addon("topomt")
molsysviewer.addon_templates.build_reference_demo_view("topomt")
```

That avoids hardcoding internal module strings when teams just want to inspect
the bundled references.

`build_reference_demo_view("topomt")` is now the shortest supported smoke path
for external teams:

- register one bundled reference add-on
- open a real demo system
- land directly in the shared `Add-ons` surface
- activate the add-on workspace
- and open its entry panel so the add-on runtime can be inspected immediately

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

`AddonSpec` metadata should include stable package/version information when the
add-on is distributed separately. Add-ons may also declare a MolSysViewer runtime
requirement with `requires_molsysviewer`, using standard Python version
specifiers such as `">=0.14,<1"`. Registration rejects incompatible add-ons
before mutating the registry.

Registry namespaces are strict. Registering two add-ons with the same
`AddonSpec.name` raises `ValueError`, and add-on workspace IDs must also be
globally unique because workspaces are selected by ID in the viewer runtime.
Panel IDs and context-action IDs remain scoped by add-on.

The bundled reference template follows exactly that rule.

Recommended lifecycle exports, when needed:

- `lifecycle`
- `LIFECYCLE`
- or plain functions:
  - `on_enable`
  - `on_disable`
  - `on_context_action`

## Recommended package layout

For larger MolSysSuite integrations, prefer:

- domain/scientific package:
  - `topomt`
- MolSysViewer integration package:
  - `molsysviewer-topomt`

Typical import path:

- `molsysviewer_topomt`

This keeps domain logic and viewer integration decoupled while still allowing a
first-class add-on story.

## Reference template and first milestone

MolSysViewer now ships an importable reference template:

- [`minimal_topomt.py`](https://github.com/uibcdf/molsysviewer/blob/main/molsysviewer/addon_templates/minimal_topomt.py)

That template already includes:

- one workspace
- several panels
- several addon sections
- more than one context action
- one shape provider
- one export helper
- a minimal lifecycle object
- and a visible reference lifecycle flow:
  - `on_enable(view)` leaves a marker on the view
  - `on_context_action(...)` records the handled action payload
  - `on_disable(view)` flips that runtime marker back

Recommended first milestone for external teams:

1. define one workspace if the add-on is large enough
2. contribute one panel
3. contribute one addon section
4. contribute one context action
5. implement at most one real lifecycle-driven behavior

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
specific view. Lifecycle callback exceptions are isolated: MolSysViewer records
the failure, keeps the viewer running, and exposes the diagnostic in the Add-ons panel. If `on_enable(view)` fails, that add-on is left
disabled for the affected view so runtime state remains coherent.

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

### Frontend panel cleanup

An add-on panel ESM `render({ model, el })` function may return a cleanup
function. MolSysViewer calls it before removing the panel element when the user
navigates away or another add-on panel is mounted. Use this for timers, charts,
secondary canvases, subscriptions, or other browser resources:

```javascript
export function render({ model, el }) {
    const interval = window.setInterval(() => {
        model.send({ type: "action", id: "heartbeat" });
    }, 1000);

    return () => {
        window.clearInterval(interval);
    };
}
```

### Panel state isolation

`AddonPanelWidget.state` and `AddonPanelWidget.set_state(...)` are scoped to
the add-on that created that widget instance. The namespace is bound when the
panel widget is resolved, so background work can safely update its own panel
state even if the user navigates to a different add-on panel before the update
finishes.

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
Add-ons panel.

The first visible slice is intentionally modest:

- enabled add-ons appear in a dedicated `Add-ons` section
- panel titles and addon-section titles are summarized there
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

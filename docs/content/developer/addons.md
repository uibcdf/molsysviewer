(Developer_Addons)=
# Add-ons

MolSysViewer exposes an explicit add-on platform aimed at the broader MolSysSuite ecosystem.

This page is the centralized source of truth for downstream teams implementing MolSysViewer add-ons.

## Documentation responsibilities

Use this guide to create an add-on against the public host API. MolSysViewer
documents the shared concepts, discovery, registration, activation,
configuration, lifecycle and extension contracts. The user introduction is
{doc}`../user/introduction/addons`.

Keep documentation of your add-on's capabilities and use in its owning project:
the Python API, graphical tools, installation requirements, scientific methods,
examples and limitations. Link to that reference from the Viewer catalogue;
avoid maintaining a second copy of signatures and scientific options here.

Independent authors can request inclusion in the
{doc}`../showcase/addons` catalogue through a MolSysViewer issue. Catalogue
inclusion is separate from package discovery: prefer the entry-point mechanism
below for installed discovery, or document explicit registration.

## Core and add-on responsibilities

The core serves molecular visualization and exploration. It may offer qualified
scientific calculations directly to create or configure visual content, such as
displaying calculated hydrogen bonds. Additional analysis, molecular preparation
and editing tools, and specialized scientific models belong to the owning
add-on/library. Classify by user intent and scientific effects, rather than by
which provider module contains an algorithm or whether its output can be plotted.

Keep scientific options explicit and reuse public provider tools. A visual action
must not silently repair, protonate or transform a molecular system. Results and
representations retain separate lifetimes; removing a visual object must not
implicitly delete scientific data. Python remains the headless, composable
foundation shared by Studio and add-on panels. The user explanation is
{doc}`../user/introduction/what`.

---

## Mental Model: Host vs View

The add-on model is split into two levels:

- `molsysviewer.addons`: Host-level registry.
- `view.addons`: Per-view projection of the host registry.

Add-ons belong to the MolSysViewer host, not to a single view instance. Each view inherits what the host knows and can still enable or disable add-ons locally.

---

## Public Vocabulary

Use **add-on** consistently. The public API avoids parallel terminology such as `plugin`.

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

---

## Where an add-on lives

**MolSysViewer owns the host contract; each scientific toolkit owns its own integration.**
The integration is a top-level package inside the toolkit's repository, not a separate
distribution:

| Toolkit repository | Ships | Imported as |
|---|---|---|
| `topomt` | `molsysviewer_topomt/` | `molsysviewer_topomt` |
| `elastnetmt` | `molsysviewer_elastnetmt/` | `molsysviewer_elastnetmt` |
| `pharmacophoremt` | `molsysviewer_pharmacophoremt/` | `molsysviewer_pharmacophoremt` |

There is no `molsysviewer-topomt` distribution to install. Installing the toolkit installs
its integration, which is the point: the team that owns the science owns the panel that
presents it, and MolSysViewer never has to be edited to add one.

An external add-on is free to be its own distribution. The pattern above is what the
MolSysSuite toolkits do, not a requirement of the host contract.

MolSysMT is the required native backend. The former
`molsysviewer_molsysmt` root entry point is ignored before loading and explicit
registration of its legacy modules is rejected. The redesigned source integration
uses `molsysviewer_molsysmt.tools`, with `molsysmt` as its view namespace. Native loading,
selection, interactions and H5MSM workflows remain available without registration.
Optional domain extensions keep this addon contract. See uibcdf/molsysviewer#186.

The experimental source integration provides qualified bound queries,
independent molecular outputs and retained-axis edits with synchronization
controls. The provider owns the exact capability inventory and usage reference.
Broader scientific coverage, other edit families, panels and installed-package
compatibility remain pending. The new route does
not enable retired packages. General automatic observation of arbitrary
external molecular edits is not required; integrated tools coordinate their own
edits through the shared Viewer reconciliation boundary.

A `state_factory` failure is recorded in `view.addons.manager.lifecycle_failures()`
and its original exception propagates. It does not produce an empty cached
namespace. A later access retries initialization; successful creation clears
that failure record. Addons without a factory still receive an empty namespace.
Use `view.closed` to reject bound operations after explicit view closure;
closing a popup alone does not close the view.

### Coordinating scientific edits

`view.addons.manager.system_edits` is a host integration service shared by
addons. A reviewed provider adapter passes `execute(callback, name=...,
update_view=True, rejection_check=None, axis_growth=None)` a read-only preparation callback on the bound target. Its
plan declares the native `run` callable, whether science changes the target,
operation-relative retained atom/structure correspondence, interaction validity
and any qualified atomic-rejection guarantee. Scientific semantics and map
correctness remain the provider's responsibility. `read(callback)` serializes
readers against managed writes while preserving native values and aliasing.

`update_view=False` defers projection only. Compatible edits compose their maps;
old-index scene actions are rejected at Python and paused in live windows.
`get_status()` returns detached metadata. `synchronize()` rebuilds from retained
scene metadata without repeating science. A synchronization failure after
science exposes `SystemEditSyncError.science_completed`, `operation_id` and
`scientific_result`; providers should propagate it and instruct callers to retry
synchronization. A potentially partial scientific write instead needs explicit
recovery through `replace(molecular_system)`, which discards pending scene
reconciliation without undoing the scientific mutation.

Receiving supports retained nonempty axes and qualified native prefix additions.
The explicit axis_growth="atoms" or "structures" keyword requires a plan
added_count; old hosts reject the keyword before executing science. Providers
declare retained prefix identities; counts only check that declaration. This
does not certify arbitrary provider mutators, raw external writes or molecular
Undo. Coordinate/analysis arrays and arbitrary user extension attributes are not
copied into its scene checkpoint. Ordinary `view.load` cannot discard unresolved
managed edits silently. Scientific usage belongs in the provider documentation.

For nested writes, a provider may supply `rejection_check(target)` as a read-only
immutable token reader. The host compares before/after-error tokens in addition
to target/state identity; unchanged counts alone cannot certify rejection. This
is an explicit executor keyword, so an old host fails before executing science.
It does not make multi-attribute scientific operations atomic. Source receiving
of geometry setting presently rebuilds the scene on synchronization; do not
promise bounded or incremental trajectory transfer for that route.

## How the host finds it

Three routes, in decreasing order of preference. They are not equivalent, and the
MolSysSuite add-ons do not all use the same one:

1. **An entry point** in the toolkit's `pyproject.toml` — installed means discovered:

   ```toml
   [project.entry-points."molsysviewer.addons"]
   topomt = "molsysviewer_topomt"
   ```

2. **`KNOWN_ADDON_MODULES`** in `molsysviewer/addons.py`, which names the optional domain
   modules explicitly. This is a courtesy for known siblings, not a mechanism external
   add-ons should rely on: it requires editing MolSysViewer.
3. **`molsysviewer.addons.register_module("…")`**, always available, always explicit.

An add-on that offers only route 3 works; it just will not appear until someone asks for
it by name.

---

## Importable Module Contract

An importable add-on module must expose one of:
- `addon`
- `ADDON`
- `get_addon()`

and it must resolve to an `AddonSpec`.

---

## Contribution Types

An add-on may currently declare:
- **workspaces** (`AddonWorkspaceSpec`): Defines a top-level workspace with sidebar tabs.
- **panels** (`AddonPanelSpec`): Subpaneles rendered inside the workspace.
- **context_actions** (`AddonContextActionSpec`): Injects items into the 3D context menu (right click) for specific kinds (e.g. `structure`, `shape`).
- **addon_sections** (`AddonSectionSpec`): Injects cards into the workbench sidebar.
- **shape_providers** (`AddonShapeProviderSpec`): Adds custom 3D geometries to the renderer.
- **export_helpers** (`AddonExportHelperSpec`): Provides export formats (e.g. PNG, HTML).

---

## Workspace Guidance

- `Core` is the native workspace.
- Large add-ons may define one or more workspaces.
- Small add-ons should remain lighter and not define a workspace (they only contribute sections or context actions).
- Do not treat "every add-on" and "workspace" as synonyms.

---

## Discovery and Registration

There are two supported paths:

### 1. Manual Coupling
For local development or unpublished add-ons, register the module explicitly:
```python
import molsysviewer

molsysviewer.addons.register_module("molsysviewer_topomt")
```

### 2. Discovery
For known packages added to MolSysViewer's entry points group `molsysviewer.addons`:
```python
import molsysviewer

molsysviewer.addons.discover(include_known_modules=True)
```

Importing public `AddonSpec`, panel/widget specs or `MolSysView` declares types
without discovering providers. Automatic discovery happens on first use of
`molsysviewer.addons` or construction of a view. A provider still initializing
is deferred and retried on subsequent registry/view use, preserving its exact
entry point and lifecycle. Completed invalid contracts retain load diagnostics.
Explicit `discover()` remains available after installing providers. Replacing
an already registered contract requires unregistering its namespace first.
`addons.clear()` preserves an empty registry across reads and view construction;
only explicit discovery or registration restores providers afterward.

---

## Python Lifecycle Contract

If per-view behavior is needed, the module may expose a lifecycle object `AddonLifecycleSpec` or plain functions:
- `on_enable(view)`: Executed when the add-on is enabled on a view.
- `on_disable(view)`: Executed when disabled.
- `on_context_action(view, action_id, payload)`: Handles Python-side execution of 3D context-menu clicks.

---

## Add-on State and Public API Namespace

MolSysViewer provides a dedicated namespace for each enabled add-on at `view.addons.<addon_name>` (e.g., `view.addons.dummy` or `view.addons.topomt`). This namespace should hold all runtime parameters, data models, and analytical results generated by the add-on for that specific view.

To implement this:

1.  **Define a State Dataclass:**
    Define a dataclass to store the view's add-on state. For backward compatibility with dict-based lookups, implement `__getitem__`:
    ```python
    @dataclass
    class MyAddonRuntime:
        enabled: bool = False
        workspace: str = "my_workspace"
        my_data: Any = None

        def __getitem__(self, key: str) -> Any:
            return getattr(self, key)
    ```

2.  **Define a State Factory:**
    Create a factory function that takes the `view` and returns the state object. It is recommended to check if a private attribute already exists to avoid overwriting state initialized during early lifecycle hooks:
    ```python
    def create_my_addon_state(view: Any) -> MyAddonRuntime:
        runtime = getattr(view, "_my_addon_runtime", None)
        if isinstance(runtime, MyAddonRuntime):
            return runtime
        state = MyAddonRuntime()
        try:
            view._my_addon_runtime = state
        except Exception:
            pass
        return state
    ```

3.  **Register `state_factory` in Python:**
    Pass the factory function to `AddonSpec`:
    ```python
    addon = AddonSpec(
        name="my_addon",
        state_factory=create_my_addon_state,
        ...
    )
    ```

4.  **Resolve State Safely (`ensure_runtime`):**
    Use a helper function inside your panels and python functions to resolve the runtime state safely:
    ```python
    def ensure_runtime(view: Any) -> MyAddonRuntime:
        addons = getattr(view, "addons", None)
        if addons is not None:
            try:
                namespace = getattr(addons, "my_addon", None)
                if isinstance(namespace, MyAddonRuntime):
                    return namespace
            except Exception:
                pass
        # Fallback for mock environments / test doubles
        ...
    ```

### Reference Implementation
Refer to the **`dummy`** reference add-on (`view.addons.dummy`) or **`topomt`** add-on (`view.addons.topomt`) for a complete, fully tested example of this state factory pattern.

`state_factory` creates live, per-view runtime state; it does not by itself make
that arbitrary state serializable or part of static HTML export. Static export
preserves add-on output registered through core scene domains (regions, layers,
shapes, annotations, and measurements) and materialized runtime/export-helper
specifications. Add-ons must not claim persistence for other runtime fields
until a versioned opt-in projection/state contract is introduced.

---

## Frontend Panel Guidelines

Add-on panels are loaded dynamically by the frontend as ES modules.

### 1. ESM Signature
The panel entry script must export a `render` function:
```javascript
export function render({ model, el }) {
    el.innerHTML = `<div>Hello from my Add-on Panel</div>`;
    
    // Optional: Return a cleanup callback
    return () => {
        console.log("Unmounting panel...");
    };
}
```

### 2. Frontend Cleanup (Critical)
Always return a cleanup function from `render` if you register window event listeners, intervals, secondary canvas contexts, or subscriptions. MolSysViewer executes this callback before removing the panel element from the DOM.

### 3. Panel State Isolation
Use `model.get()`, `model.set()`, and `model.send()` to sync state. State properties are isolated and namespace-bound to the active add-on.

### 4. Panel Subsections and Tab Navigation (Nivel 3)
Add-ons can organize panels into multiple sub-sections or tabs. MolSysViewer automatically renders tab buttons and manages visibility transitions when the following rules are met:

1.  **Define Sections in Python:**
    Register sections via `addon_sections` (using `AddonSectionSpec` with `target_panel="addons"`).
2.  **Target Specific Panels:**
    To display a section only when a particular panel is active, set the panel ID in the section's metadata:
    ```python
    AddonSectionSpec(
        id="interactive",
        title="Interactive Controls",
        entry="...",
        target_panel="addons",
        meta={"panel": "main"},  # Only visible when panel 'main' is selected
    )
    ```
3.  **Decorate HTML Elements in JavaScript:**
    Inside your panel's ESM `render` function, assign the matching `data-molsysviewer-addon-section` attribute to the container element of that subsection. The attribute value must follow the format `<addon_name>:<section_id>`:
    ```html
    <div data-molsysviewer-addon-section="my-addon:interactive" style="...">
        <!-- Interactive content here -->
    </div>
    ```
    Any elements without this attribute will remain visible at all times (like headers or shared controls).

### 5. Aesthetics and CSS Guidelines
*   **Color Palette**: Use CSS variables or coordinate with the dark mode system. Avoid hardcoded light backgrounds. Use `rgba(255, 255, 255, 0.08)` for borders/hover, and `#f4f4f5` for primary text.
*   **Typography**: Use inherited IBM Plex Sans / system sans-serif fonts. Do not override global fonts.
*   **CSS Isolation**: Write scoped classes or prefix selectors to avoid style leakages into the core viewer chrome.

---

## Reference Implementation: Add-on Tester

MolSysViewer ships a complete reference add-on called **`dummy_addon`** for testing and illustration purposes:

- Code: [`dummy_addon.py`](https://github.com/uibcdf/molsysviewer/blob/main/molsysviewer/addon_templates/dummy_addon.py)

You can load and inspect it immediately using the development helpers:
```python
import molsysviewer

# List bundled references
molsysviewer.addon_templates.list_reference_addons()

# Launch a ready-made demo with the dummy addon active
view = molsysviewer.addon_templates.build_reference_demo_view("dummy")
```

---

## First Milestone for Downstream Teams

To build a new add-on, follow these initial steps:
1. Define one workspace if your add-on represents a complete analytics studio.
2. Contribute one panel.
3. Contribute one workbench section.
4. Contribute one context action.
5. Implement at least one Python lifecycle callback to handle context clicks.


### Prefix additions and new structure origins

A reviewed provider may use `axis_growth="atoms"` or `"structures"` with an
integer nonnegative `added_count` in its execution plan. Native prefix identity
is an explicit provider declaration; matching counts are not identity evidence.
The other axis must remain unchanged. New atoms have unmapped upstream origins.
`structure_index_map` entries may be `None` to declare new positions explicitly;
known source runs remain sparse and retain their original indices. Composed
pending edits may subsequently retain, remove or reorder those positions.

Per-structure shapes and trajectory cards reject new origins before scientific
execution because the host cannot invent their new values. Static atom-anchored
shapes and explicit existing-structure filters retain their meaning. Source
analyses, evaluated universes and newly unevaluated structures remain the
scientific owner's responsibility. The host neither merges nor recalculates them.

Live adoption checks coordinate presence with one atom/structure query before
creating a lazy projection, without scanning a complete edited trajectory. A
valid native coordinate-free result remains available independently; an in-place
operation that drops coordinates can complete science but fail synchronization.
`SystemEditSyncError` preserves that distinction. Expert callers can supply the
missing scientific data and retry synchronization, or explicitly replace the
system. A potentially partial native write remains uncertain and requires
replacement; retry must not rerun science. This source capability does not change
published package floors or qualify every scientific mutation.

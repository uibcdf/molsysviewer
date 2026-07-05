# Add-ons

MolSysViewer exposes an explicit add-on platform aimed at the broader MolSysSuite ecosystem.

This page is the centralized source of truth for downstream teams implementing MolSysViewer add-ons.

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

## Recommended Package Shape

For larger integrations, prefer:
- Domain/scientific package: e.g. `topomt`
- MolSysViewer integration package: e.g. `molsysviewer-topomt`
- Recommended Python import path: `molsysviewer_topomt`

This keeps domain logic and viewer integration decoupled while still allowing a first-class add-on story.

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

---

## Python Lifecycle Contract

If per-view behavior is needed, the module may expose a lifecycle object `AddonLifecycleSpec` or plain functions:
- `on_enable(view)`: Executed when the add-on is enabled on a view.
- `on_disable(view)`: Executed when disabled.
- `on_context_action(view, action_id, payload)`: Handles Python-side execution of 3D context-menu clicks.

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

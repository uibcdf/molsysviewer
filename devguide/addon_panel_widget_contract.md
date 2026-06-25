# Add-On Panel Widget Contract

Last update: 2026-04-17

This document defines the architectural decision and implementation contract for
**interactive add-on panels** in MolSysViewer.

It is the answer to the question: *how does an add-on contribute a real
interactive panel — with sliders, inputs, plots, and domain controls — that
works identically from the Python API and from the canvas panel mode?*

## Status

- **Architecture**: decided and stable.
- **Contract**: defined and implemented.
- **Implementation**: complete. All three host requirements below are done and
  tested as of 2026-04-17.
- **First proof**: `ElasNetMTModelPanel` in `molsysviewer_elasnetmt/panels/model.py`
  is the first `AddonPanelWidget` subclass in production. 12 integration tests pass.

## Context

The current add-on host (`molsyssuite_addon_direction.md`) supports workspaces,
panel specs, context actions, workbench sections, and lifecycle hooks. Panel
specs register a name and an `entry` string, but the host does not yet render
their content as interactive UI. The `elasnetmt_addon_follow_up.md` already
flags "a richer parameter-editing surface" as the next open item.

This document closes that gap.

## The Core Decision: anywidget-Based Panel Embedding

Add-on panels use **anywidget** as the embedding mechanism.

Each panel contributed by an add-on is an `AddonPanelWidget` — a thin anywidget
subclass. The add-on author writes HTML/CSS/JS for the panel UI. MolSysViewer
embeds that widget in its panel host area when the user navigates to that panel.

**Why anywidget:**

- MolSysViewer is already anywidget. Same technology, no new dependencies.
- The same communication channel (JSON messages over the widget protocol)
  already exists between Python and the canvas. Panel ↔ Python uses the same
  model.
- anywidget works in every MolSysViewer host: Jupyter, JupyterLab, VS Code
  notebooks, and Qt WebEngine (standalone). The panel author does not need to
  know which host is active.
- Add-on authors only need HTML/CSS/JS — no MolSysViewer TypeScript knowledge
  required.
- Python stays the owner of all scientific logic and viewer state. The panel is
  UI only.
- The model is sandboxed and testable independently of the canvas.

**Why not a declarative schema:**

A declarative schema (describing UI as a dict/dataclass from Python) becomes a
DSL bottleneck. Every new UI pattern requires extending the schema in
MolSysViewer core. anywidget gives full expressiveness without core changes.

**Future extension — bundle JS panels:**

anywidget covers the ecosystem use case (Python developers, Jupyter context).
For future add-ons that need richer frontend integration (e.g. a 3D renderer
inside the panel), the host can later support registered JS bundles through the
same panel slot. anywidget panels and JS-bundle panels are not in conflict; the
host dispatches based on panel type. Add-ons written for anywidget panels do not
need to change. See the "Future Extension" section below.

## The AddonPanelWidget Base Class

MolSysViewer provides a base class:

```python
from molsysviewer.addons import AddonPanelWidget

class MyDomainPanel(AddonPanelWidget):
    # Standard anywidget fields
    _esm: str   # the JS module (ESM format)
    _css: str   # optional CSS

    def handle_action(self, view, action_id: str, payload: dict) -> None:
        """Called when the panel sends an action message to Python."""
        ...

    def on_mount(self, view) -> None:
        """Called when the panel is embedded in the canvas panel area."""
        ...

    def on_unmount(self, view) -> None:
        """Called when the user navigates away from this panel."""
        ...
```

`AddonPanelWidget` is a thin anywidget subclass that:

- handles the message routing from JS to `handle_action`
- holds a reference to the current `view` after mounting
- exposes the `state` property and `set_state(updates: dict)` for two-way synchronized state management (recommended)
- exposes `push_state(state: dict)` to push legacy one-way state updates to the JS side
- exposes `request_context()` to request the current viewer context snapshot

## Communication Protocol

MolSysViewer supports two communication patterns between the Python backend and the JavaScript frontend panel:
1. **Two-Way State Synchronization (Recommended)**: A reactive, Backbone-like state sync model where properties are automatically shared and synchronized, allowing direct gets, sets, and property-specific change listeners.
2. **Message-Driven Actions (Legacy / Direct)**: A message-passing model where the frontend sends explicit action intents to Python, and Python can optionally push state snapshots back.

---

### 1. Two-Way State Synchronization (Recommended)

This pattern provides a modern, reactive programming model similar to standard `anywidget` state synchronization, but with automatic namespace isolation and environment fallback.

#### The State Synchronization Mechanism
- **Backend Storage**: All active add-on states are stored in a single synchronized dictionary traitlet, `addon_states`, on the main viewer widget. This dictionary is keyed by the add-on name, e.g. `addon_states["my-addon"] = { ... }`.
- **Namespace Isolation**: The `AddonPanelWidget` in Python and the state proxy in JavaScript automatically isolate state operations. The panel only reads and writes within its own add-on namespace, preventing collisions with other add-ons.
- **Environment Fallback**: In stand-alone or popout modes where the Backbone widget connection is not active, the JavaScript state proxy automatically falls back to a local state dictionary. This ensures that panels run identically and flawlessly across all hosts (Jupyter, Standalone, exports) with zero code changes.

#### Python API (Backend)
The Python panel class can read, update, and react to state changes using the `state` property and `set_state` method:

```python
# Reading state
current_cutoff = self.state.get("cutoff", 7.0)

# Updating state (triggers automatic synchronization and reactive JS listeners)
self.set_state({
    "cutoff": 7.5,
    "n_nodes": 247,
    "active_mode_index": 2
})
```

#### JavaScript/TypeScript API (Frontend)
The frontend receives a mock Backbone `model` proxy that matches standard `anywidget` syntax. Panel developers can use `get`, `set`, and reactive `on("change:key")` listeners:

```js
// Inside the ESM render function
export function render({ model, el }) {
    // 1. Read state
    const currentCutoff = model.get("cutoff") || 7.0;

    // 2. React to specific state changes (from Python or JS)
    model.on("change:cutoff", (model, value) => {
        console.log("Cutoff changed to:", value);
        updateCutoffUI(value);
    });

    // 3. Update state (synchronizes back to Python automatically)
    el.querySelector("input.cutoff").addEventListener("input", (e) => {
        model.set("cutoff", parseFloat(e.target.value));
    });
}
```

#### 1.1 Local Frontend Event Bus (Zero-Latency Notifications)

For high-frequency or interactive synchronization (such as updating an energy plot during trajectory playback or coordinate displays on camera movement), panels can subscribe directly to the local event bus of the viewer without going through Python.

The proxy `model` forwards the following local event triggers under the `"viewer:"` namespace:

- `"viewer:frame-changed"`: Fired when the active conformation structure/frame changes. Receives the `frameIndex` (number) as the argument.
- `"viewer:selection-changed"`: Fired when the active selection changes. Receives the list of selected atom indices (number[]) as the argument.
- `"viewer:camera-moved"`: Fired when the camera position, focus, or zoom changes. Receives the camera state object (snapshot).

```js
export function render({ model, el }) {
    // Zero-latency local subscription (runs in the browser at 60 FPS, < 1ms latency)
    model.on("viewer:frame-changed", (frameIndex) => {
        updateInteractivePlot(frameIndex);
    });

    model.on("viewer:camera-moved", (cameraState) => {
        updateCameraCoordinateDisplay(cameraState.position);
    });
}
```

> [!IMPORTANT]
> **Automatic Cleanup**: To prevent memory leaks in persistent Jupyter environments, the MolSysViewer controller automatically purges all `"viewer:*"` subscriptions registered on the proxy `model` when the panel is unmounted or the active workspace is switched. Panel developers do not need to manually write clean-up logic for these local event listeners.

---

### 2. Message-Driven Actions & Message Passing

For explicit operations or calling specific scientific methods in Python, the message-driven pattern is highly appropriate.

#### Panel → Python: Actions
The panel sends a standardized action message using the model proxy:

```js
// Inside _esm
model.send({
    type: "action",
    id: "compute-gnm",           // action identifier
    payload: { cutoff: 7.5 }    // action-specific data
});
```

MolSysViewer routes this to `handle_action(view, "compute-gnm", {"cutoff": 7.5})`.

The action handler calls viewer APIs and/or add-on runtime methods directly:

```python
def handle_action(self, view, action_id, payload):
    if action_id == "compute-gnm":
        from molsysviewer_elasnetmt.adapters.contacts import render_contact_network
        render_contact_network(view, cutoff=f"{payload['cutoff']} angstroms")
        
        # Synchronize new state to the frontend
        self.set_state({
            "cutoff": payload["cutoff"],
            "contacts_rendered": True
        })
```

#### Python → Panel: Legacy State Updates (One-way)
For backward compatibility, Python can push state snapshots directly via `push_state`:

```python
self.push_state({
    "model_kind": "gnm",
    "cutoff": "7.5 angstroms",
})
```

In the frontend, these are received as custom messages:

```js
model.on("msg:custom", (msg) => {
    if (msg.type === "state") {
        render(msg.state);
    }
});
```

The state schema is owned by the add-on. MolSysViewer does not inspect it.

### Viewer Context Bridge

The panel can request a minimal viewer context snapshot:

```js
model.send({ type: "query", id: "viewer.context" });
```

Python responds with a standardized context dict:

```python
{
    "has_system": True,
    "n_structures": 1,
    "active_selection": {
        "n_atoms": 43,
        "target_level": "group"
    },
    "workspace": "elasnetmt"
}
```

The context bridge is intentionally narrow. It answers "what is loaded and
selected" without exposing MolSysViewer internals to the add-on panel.

MolSysViewer also pushes context automatically on mount so the panel can
initialize correctly without an explicit request.

## Panel Lifecycle

```
user navigates to panel
        ↓
MolSysViewer resolves AddonPanelSpec.entry
        ↓
instantiates AddonPanelWidget bound to current view
        ↓
on_mount(view) called → Python can pre-populate state
        ↓
push_state() sends initial state to JS
        ↓
MolSysViewer embeds widget in panel host area
        ↓
[user interacts — action ↔ state cycle]
        ↓
user navigates away
        ↓
on_unmount(view) called → Python can clean up
        ↓
widget removed from panel host
```

Panels are instantiated per navigation, not per session. If the add-on needs to
cache expensive computation across panel navigations, it should store that in
the `ElasNetMTAddonRuntime` (or equivalent runtime object on the view), not
inside the panel widget itself.

## Relationship with Context Actions

Context actions (`on_context_action`) and panel actions (`handle_action`) are
two independent paths to the same Python logic.

Best practice: implement the science in a shared adapter function, and call it
from both paths:

```python
# adapter function — shared
def _do_show_contact_network(view, cutoff):
    render_contact_network(view, cutoff=cutoff)

# context action path
def on_context_action(view, action_id, payload):
    if action_id == "show-contact-network":
        _do_show_contact_network(view, cutoff=runtime.cutoff)

# panel action path
def handle_action(self, view, action_id, payload):
    if action_id == "compute-gnm":
        _do_show_contact_network(view, cutoff=payload["cutoff"])
        self.push_state(self._build_state(view))
```

This ensures that the API, context actions, and the panel all produce the same
result and that the viewer state remains reproducible regardless of how the
action was triggered.

## AddonPanelSpec Changes

The existing `AddonPanelSpec` gains one new optional field:

```python
AddonPanelSpec(
    id="model",
    title="Model",
    entry="molsysviewer_elasnetmt.panels.model",   # existing
    widget_class="molsysviewer_elasnetmt.panels.ElasNetMTModelPanel",  # new
    description="Model parameters and node selection.",
    order=10,
)
```

- `entry` continues to resolve to Python callables for workbench section helpers
  (existing behavior).
- `widget_class` is the new field: a dotted path to the `AddonPanelWidget`
  subclass for this panel. When present, MolSysViewer instantiates and embeds
  that widget when the user navigates to the panel.
- `widget_class` is optional. A panel without it continues to behave as before
  (workbench section summary only).

## Host Requirements (MolSysViewer side)

The following work has been fully implemented in MolSysViewer to support this contract:

1. **`AddonPanelWidget` base class** in `molsysviewer/addons.py`: ✓
   - Subclass of anywidget's `AnyWidget`.
   - `state` property and `set_state(updates: dict)` for namespace-isolated synchronized state.
   - `push_state(state: dict)` method (legacy one-way).
   - `request_context()` method.
   - Message routing to `handle_action`.
   - `on_mount` / `on_unmount` hooks.

2. **Panel widget resolver** `ViewAddonsManager.resolve_panel_widget(addon, panel)`: ✓
   - Imports and instantiates the `widget_class` bound to the current view when a user navigates to the panel.

3. **Panel host embedding and state proxy** in the TS canvas: ✓
   - `workspaceAddonWidgetHost` div inside `WorkbenchPanel`.
   - Dynamic ESM import via Blob URL in `viewer-controller.ts`.
   - Backbone-compatible model proxy simulating `model.get()`, `model.set()`, and `model.on("change:key")` listeners.
   - Namespace-isolated state routing: maps local panel keys into `addon_states[addon_name]` and synchronizes them to Python using `model.save_changes()`.
   - Environment independence: falls back automatically to a local state store when running in standalone, popup, or exported HTML pages where the Backbone widget connection is not present.
   - Clean unmount on panel navigation or workspace switch.

4. **Viewer context response** in `viewer/core.py`: ✓
   - `panel_navigate` event → `_mount_addon_panel`
   - `panel_unmount` event → `_unmount_addon_panel`
   - `addon_panel_action` event → routes to active widget.
   - Context pushed automatically on mount.

5. **Main widget synchronization** in `molsysviewer/widget.py`: ✓
   - `addon_states` synchronized traitlet dictionary containing state for all active panels, guaranteeing two-way Python-JS synchronizations.

## Add-On Author Requirements

To contribute an interactive panel, the add-on author:

1. Subclasses `AddonPanelWidget` from `molsysviewer.addons`
2. Writes `_esm` (and optionally `_css`) for the panel UI
3. Implements `handle_action(view, action_id, payload)` (if message-driven actions are needed)
4. Uses `self.state` and `self.set_state(...)` in Python, and standard Backbone `model.get()`, `model.set()`, and `model.on("change:key")` in JavaScript to read, write, and react to state changes in a fully synchronized manner.
5. Optionally implements `on_mount` to send initial state or configure the panel
6. Registers the class via `widget_class` in `AddonPanelSpec`

No TypeScript or MolSysViewer-internal knowledge is required. The add-on author works entirely in Python + HTML/CSS/JS.

## Future Extension: Bundle JS Panels

Once the anywidget path is stable, the host can add support for panels backed by a registered JS bundle. The extension is additive:

```python
AddonPanelSpec(
    id="modes",
    title="Modes",
    entry="molsysviewer_elasnetmt.panels.modes",
    widget_class="molsysviewer_elasnetmt.panels.ElasNetMTModesPanel",  # anywidget
    # future:
    # js_bundle="molsysviewer_elasnetmt/panels/modes.js",  # JS bundle alternative
)
```

The host dispatches based on which field is present. anywidget panels and JS-bundle panels coexist without conflict. Add-ons using `widget_class` do not need changes when JS-bundle support is added.

## Design Constraints

- **Python owns the logic.** The panel sends intents (actions or state changes), never commands to the viewer directly. Python is the orchestrator.
- **State is synchronized and namespace-isolated.** The widget leverages `addon_states` to maintain two-way state synchronization. To preserve scientific reproducibility across cell executions and environments, state changes are automatically synchronized between Python and the frontend.
- **The panel must not access MolSysViewer internals directly.** All viewer interaction goes through the public Python API (`view.shapes`, `view.regions`, etc.) or through the context bridge.
- **Actions must be reproducible.** Any action a panel can trigger must also be callable from the Python API with the same effect.
- **The panel body is the only add-on-owned UI area.** Add-ons do not get permanent canvas chrome, toolbar buttons, or new context menu families outside of what `AddonContextActionSpec` already supports.

## Relationship with Other Devguide Documents

- `molsyssuite_addon_direction.md` — top-level add-on architecture and
  registration model. This document extends it with the panel widget layer.
  Several open questions listed there are answered here:
  - "when should the first add-on contribution become visibly real in the
    runtime?" → when `widget_class` is resolved and embedded by the host.
  - "should large add-ons contribute primarily as their own workspaces?" →
    yes, and this contract is how those workspaces get interactive panel content.
- `canvas_minimal_ux.md` — panel mode UX contract. The add-on panel widget is
  embedded in the same panel area described there. The UX constraints (clean
  canvas, one panel at a time, panel mode open/close) apply equally to add-on
  panels. The architectural requirement "host-agnostic panel concepts" from
  `standalone_direction.md` is satisfied by anywidget panels, which are
  host-independent by design.
- `path_to_1_0.md` — The unified release plan requires ElasNetMT to "use the workspace
  panel host" as a condition for the stable 1.0.0 release. This
  contract is the implementation path for that gap.
- `elasnetmt_addon_plan.md` — ElasNetMT add-on plan. The "richer
  parameter-editing surface" flagged there is implemented through this contract.
- `elasnetmt_addon_follow_up.md` — explicitly names "a richer
  parameter-editing surface" as the next open item. This document is the answer.
- `standalone_direction.md` — requires "host-agnostic panel concepts". anywidget
  panels satisfy this: the panel author writes HTML/CSS/JS that runs identically
  in Jupyter, JupyterLab, VS Code, and Qt WebEngine (standalone).

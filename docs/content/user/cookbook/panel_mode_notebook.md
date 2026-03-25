# Notebook control of panel mode

This recipe shows the current Python-facing control surface for the shared
panel/workspace runtime.

It is intentionally small:

- open or close panel mode
- choose a workspace
- choose the local panel inside that workspace
- inspect the effective workspace and panel catalog from Python
- inspect the last known runtime state from Python

## Core workspace

```python
import molsysviewer as mv

view = mv.demo["dialanine"]
view.workspace_catalog()
view.workspace_panels("core")
view.workspace_sections("core")
view.workspace_runtime()
view.set_panel_mode("workbench")
view.set_workspace("core")
view.get_panel_mode_state()
view
```

Typical state shape:

```python
{
    "event": "panel_mode_state",
    "panel": "workbench",
    "expanded": True,
    "workspace": "core",
    "workspace_panel": "workbench",
}
```

## Add-on workspace

```python
import molsysviewer as mv

view = mv.addon_templates.build_reference_demo_view("topomt")
view.workspace_catalog()
view.workspace_panels("topomt")
view.workspace_sections("topomt")
view.workspace_runtime()
view.set_panel_mode("workbench")
view.set_workspace("topomt")
view.set_workspace_panel("topo")
view.get_panel_mode_state()
view
```

This is the current notebook-friendly pattern:

- `view.set_panel_mode(...)`
- `view.set_workspace(...)`
- `view.set_workspace_panel(...)`
- `view.workspace_catalog()`
- `view.workspace_panels(...)`
- `view.workspace_sections(...)`
- `view.workspace_runtime()`
- `view.get_panel_mode_state()`

In practice:

- `workspace_catalog()` lets notebook code discover what can be opened
- `workspace_panels("topomt")` shows the local stack for that workspace
- `workspace_sections("topomt")` shows the workbench sections visible for that
  workspace
- `workspace_runtime()` gives one combined snapshot for notebook logic that does
  not want to recombine these queries manually
- that snapshot now also includes:
  - `current_workspace_record`
  - `current_panel`
- both helpers mark the active item once the frontend has reported runtime
  state

## Notes

- `get_panel_mode_state()` returns the last state reported by the frontend.
- it is useful for notebook flows that want to confirm the current workspace or
  panel after scripted navigation
- it should be read as runtime state, not as long-term persisted session state

## See also

- {doc}`../viewer/panel_mode`
- {doc}`addon_workspace_workbench`

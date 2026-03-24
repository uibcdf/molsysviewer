(User_Viewer_Panel_Mode)=
# Panel mode and workspaces

`Panel mode` is the current structured way to move beyond the resting canvas.

In practice, it is the shared doorway to the workbench:

- `Navigate`
- `Workbench`
- and, when larger add-ons are available, their workspaces and local panel
  stacks

The important idea is that MolSysViewer does **not** want to turn the canvas
into a busy control surface.
Instead, the canvas should stay calm, and structured work should happen through
panel mode.

## What panel mode is for

Use panel mode when you want to:

- inspect the current structural organization
- move through workbench objects such as annotations, measurements, shapes, and
  scene state
- switch to a larger add-on workspace
- keep the canvas clean while still having a real workbench available

## Core behavior

Today, the shared Python entrypoint is:

```python
view.set_panel_mode(...)
view.set_workspace(...)
view.set_workspace_panel(...)
```

The current contract is intentionally small:

```python
view.set_panel_mode("navigate")
view.set_panel_mode("workbench")
view.set_panel_mode(None, expanded=False)
view.set_workspace("core")
view.set_workspace("topomt")
view.set_workspace_panel("topo", workspace="topomt")
```

This means:

- `panel="navigate"` opens `Navigate`
- `panel="workbench"` opens `Workbench`
- `expanded=False` collapses the current panel-mode surface
- `workspace="core"` selects the native workspace
- another workspace id selects that add-on workspace when it is available
- `set_workspace_panel(...)` selects a local panel inside the current or given
  workspace

The browser side may also remember the last active panel when appropriate.

## How this relates to workspaces

The native workspace is still `Core`.

Inside `Core`, panel mode currently gives you the familiar pair:

- `Navigate`
- `Workbench`

For larger add-ons, the current direction is different:

- first choose a workspace
- then use the local panel stack inside that workspace

This scales much better than a single flat list of every future panel in the
whole ecosystem.

## What you should expect today

At the current pre-`1.0` stage, panel mode already gives you a coherent shared
workbench model, but it is still intentionally modest.

You should expect:

- one shared panel header
- one workspace-aware launcher
- one local panel stack for the active workspace
- one calm default `Core` workspace

You should **not** assume yet:

- the final launcher/mosaic
- the final standalone host
- a completely finished add-on panel UX

## Minimal example

```python
import molsysviewer as mv

view = mv.demo["dialanine"]
view.set_panel_mode(panel="workbench", expanded=True)
view.set_workspace("core")
view
```

If you also enable a larger add-on workspace, the same panel mode becomes the
place where that workspace appears.

## Notebook-oriented workspace example

```python
import molsysviewer as mv

view = mv.addon_templates.build_reference_demo_view("topomt")
view.set_panel_mode("workbench")
view.set_workspace("topomt")
view.set_workspace_panel("topo")
view
```

This is the current notebook-friendly pattern:

- open the shared panel surface
- select the workspace explicitly
- then land on the local panel you want

## Why this matters

Panel mode is one of the most important bridges between:

- interactive exploration
- structured workbench activity
- and the future standalone host

That is why the project treats it as a shared runtime concept, not as a
notebook-only convenience.

## See also

- {doc}`ui`
- {doc}`camera_and_controls`
- {doc}`../cookbook/addon_workspace_workbench`
- {doc}`../cookbook/figure_export_workbench`

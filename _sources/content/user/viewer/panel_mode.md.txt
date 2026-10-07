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
view.get_panel_mode_state()
view.workspace_catalog()
view.workspace_panels(...)
view.workspace_sections(...)
view.workspace_runtime()
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
- `get_panel_mode_state()` returns the last runtime state reported back by the
  frontend
- `workspace_catalog()` returns the effective workspace catalog visible to the
  view
- `workspace_panels(...)` returns the local panel stack for a workspace
- `workspace_sections(...)` returns the visible workbench sections for a
  workspace
- all three runtime helpers also reflect the currently active workspace/panel
  when that runtime state is already known
- `workspace_runtime()` bundles the current runtime state, visible workspace
  catalog, current workspace record, current local panel stack, current active
  panel record, and current workspace sections into one query

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

## Experimental layout modes

Two constructor arguments let you try alternative canvas layouts:

```python
view = mv.MolSysView(
    controls_mode="minimal",
    panel_mode_style="floating",
)
```

`controls_mode`:

- `"classic"` — six text buttons at the bottom of the canvas.
- `"minimal"` — three SVG icons (panel / fullscreen / popup) plus a `?` help button.
  Scene actions (reset view, background, spin, swing) move to the empty-canvas context menu.
  Keyboard shortcuts: `H` help overlay, `N` Navigate, `W` Workbench.
- `"cinema"` — the canvas alone, with the controls out of the way.

`panel_mode_style`:

- `"drawer"` — Navigate slides in from the left, Workbench from the right.
- `"floating"` — a centered overlay card that closes on backdrop click, with zero viewport shift.
- `"floating-unified"` — one shared shell instead of two separate panels.
- `"integrated"` — the unified shell, docked into the canvas rather than over it.
- `"ambient"` and `"split"` — the unified shell laid out beside the canvas.

**You rarely need either.** Both follow from `viewer_mode`, which is the one knob
worth knowing: `"classic"` gives you `classic` + `drawer`, `"integrated"` (the
default) gives `minimal` + `integrated`, and `"cinema"` gives `cinema` +
`integrated`. Setting `controls_mode` or `panel_mode_style` overrides that pair
for one of the two.

To fix a preference for every view, set it in `molsysviewer.config`:

```python
import molsysviewer as mv

mv.config.viewer_mode = "classic"        # or set the two below individually
mv.config.panel_mode_style = "drawer"
```

Leaving a configuration value as `None` — which is how it ships — means *follow
whatever `viewer_mode` implies*. That distinction matters: until 2026-08-06 the
defaults `"classic"` and `"drawer"` doubled as "not chosen", so configuring
either of them asked for the classic surface and quietly got the preset's
instead. They are requestable now.

## See also

- {doc}`ui`
- {doc}`camera_and_controls`
- {doc}`../cookbook/addon_workspace_workbench`
- {doc}`../cookbook/figure_export_workbench`
- {doc}`../cookbook/workbench_scientific_workflow`

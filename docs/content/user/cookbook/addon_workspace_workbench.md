(User_Cookbook_Addon_Workspace_Workbench)=
# Explore an add-on workspace in the shared workbench

This recipe shows how a larger add-on workspace currently appears inside the
shared MolSysViewer workbench.

It is useful for two audiences:

- downstream MolSysSuite teams that want to understand the current host/runtime
  shape before writing their own add-on
- users who want to understand how add-on workspaces relate to the native
  `Core` workspace

The example uses the bundled reference add-on because it is:

- stable
- importable
- visible in the real runtime

## Goal

You will:

1. register the reference add-on
2. open a real demo molecular system
3. land in the shared `Workbench`
4. inspect the add-on workspace, panel stack, sections, and immediate
   capabilities
5. return to `Core`

## 1. Build the reference demo view

```python
import molsysviewer

view = molsysviewer.addon_templates.build_reference_demo_view("topomt")
view
```

This is the shortest supported smoke path for an add-on workspace today.

It currently does three things:

- registers the bundled reference add-on
- opens the `dialanine` demo system
- opens the shared `Workbench` so the add-on runtime is immediately visible

## 2. Read the runtime as a shared workbench, not a separate app

The important architectural point is that the add-on does **not** open its own
viewer.

Instead, you stay inside the same MolSysViewer runtime:

- one viewer
- one workbench
- one workspace launcher
- one panel stack for the active workspace

That is the product direction the host is now designed to preserve.

## 3. Inspect the active add-on workspace

Once the reference view is open, the shared workbench should now make several
things visible:

- the active workspace
- the local panel stack for that workspace
- the generic active-panel host
- workspace-specific sections
- immediate add-on capabilities

In other words, the add-on should no longer feel like "metadata attached to the
core".
It should already feel like a domain that lives inside the shared workbench.

## 4. Use the workspace launcher

Open the workspace launcher in the shared panel header.

You should see:

- `Core`
- the reference add-on workspace

The launcher is intentionally still modest.
Its job at this stage is to make the domain boundary explicit:

- first choose the workspace
- then use the local panel stack inside it

This is already much better than flattening every future add-on panel into one
global list.

## 5. Read the add-on host surface

In the active add-on workspace, the workbench now acts as a generic host for
the active add-on panel.

The runtime can already surface:

- the active panel
- workspace-specific sections
- context-action capabilities
- export-helper capabilities

That means the host is already doing something important:

- it gives add-ons a place to feel native
- without giving them arbitrary frontend execution

This is exactly the right pre-`1.0` balance:

- real enough to design against
- still controlled enough not to destabilize the host

## 6. Return to `Core`

Use the shared header to return to `Core`.

This is an important behavioral check:

- add-on workspaces should feel first-class
- but `Core` should remain calm and legible as the native workspace

The goal is not to turn MolSysViewer into a flat launcher of unrelated
mini-apps.
The goal is to let domain workspaces grow while the host still feels like one
tool.

## What this recipe proves today

This workflow already proves several things that are easy to miss if you only
read the API reference:

- add-ons belong to the host, not to one single view instance
- larger add-ons can already project a credible workspace shape into the shared
  runtime
- the workbench is already the place where add-on workspaces become visible
- `Core` and add-on workspaces can coexist without turning panel mode into one
  giant list

## What it does not prove yet

This recipe is still intentionally modest.
It does **not** mean that `1.0` already guarantees:

- the final workspace launcher/mosaic
- rich arbitrary frontend add-on panels
- the final standalone host
- the final multi-window host layout

It proves something narrower but important:

- the shared workbench model is already strong enough that downstream teams can
  start thinking against a real runtime surface

## API surfaces used in this recipe

- `molsysviewer.addon_templates.build_reference_demo_view(...)`
- `view.set_panel_mode(...)`
- shared workbench/runtime behavior

## See also

- {doc}`addon_development`
- {doc}`../viewer/index`

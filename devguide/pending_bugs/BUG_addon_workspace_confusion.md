# BUG/UX: Addon activation causes UI confusion (Workbench disappearance)

## Description
When an author-defined add-on with a custom `Workspace` is enabled, the viewer's standard "Workbench" panel is automatically replaced or hidden by the add-on's workspace. While this is technically correct (context switching), it causes user disorientation because:
1. The standard tools disappear without warning.
2. If the add-on's `on_enable` hook does not immediately render something in the canvas, the user perceives the viewer as "broken" or "empty".

## Steps to Reproduce
1. Register a template add-on: `msv.addons.register_module(minimal_elasnetmt)`.
2. Enable the add-on: `view.addons.enable('elasnetmt-template')`.
3. Observe the UI panels.
4. **Observed Result:** The "Workbench" tab is gone, replaced by "Elastic Networks". The canvas remains unchanged.

## Identified Issues
- **Abrupt Context Switch:** There is no transition or notification indicating that the viewer has entered a specialized work mode.
- **Lack of UI Persistence:** Users might want to use both standard tools and add-on tools simultaneously.
- **Discovery Gap:** The user does not know how to return to the "Default" workspace without disabling the add-on.

## Proposed Improvements
1. **Workspace Tabs:** Instead of replacing the Workbench, add the new Workspace as a distinct tab or a clearly labeled section.
2. **Activation Toast:** Show a brief notification: *"Add-on 'ElasNetMT' activated. Switching to ENM Workspace."*
3. **Empty State Guidance:** If an add-on is active but has no data to show yet, display a placeholder in its panel with instructions (e.g., *"Select CA atoms to build the network"*).

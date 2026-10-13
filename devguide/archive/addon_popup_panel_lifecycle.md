---
summary: Addon panel lifecycle and actions are shared across independent popup windows
issue: uibcdf/molsysviewer#245
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: high
verification: reproduced
area: [addons, popup, lifecycle]
guard: molsysviewer/js/tests/e2e/panel-popup-welcome.e2e.ts
normative: devguide/addon_panel_widget_contract.md
blocked_by: []
supersedes: []
---

# Addon panel lifecycle and actions are shared across windows

**Reported:** canonical browser CI 38456046033 on 25b61e46.

## What

The real shape-only workspace renders and clears geometry in the panel popup.
After that popup closes, Render in the canvas popup stops producing geometry.
The 30-second semantic assertion fails in `panel-popup-welcome.e2e.ts`; this is
not the outer suite budget. The complete local core campaign had passed earlier.

## How

Python retains one `_active_panel_widget` for every window. Local navigation and
unmount notifications replace or close it, and actions are routed to whichever
widget is currently retained without checking addon/panel ownership. Outbound
mount/state messages also reach peer windows. Initial on_mount state precedes
ESM listener installation.

## Why

Windows have local Studio navigation and a shared scientific scene. Closing or
navigating one window must preserve another window's active addon controls.
This is independent of the empty-workspace availability fixed by #240.

## What was refuted

Raising timeouts or treating the earlier local pass as hosted evidence would not
repair the shared ownership. The failing guard draws actual Mol* geometry and
routes actions through a real Python addon; no dummy molecular system is used.

## Resolution

Window-owned widgets/actions and targeted mount/state delivery replace the shared singleton route. Initial state follows ESM mount; messages from retired widgets and wrong panel owners are ignored. Closing a popup releases only its widgets/layouts; closing the view releases every owned instance. Four real Python ownership/lifecycle tests, the replay unit guard and the final production-widget/Mol* browser scenario pass. The complete first implementation core campaign passes 43/43; final message hardening is covered by its separately retained final browser guard, not relabelled as the same exact global invocation.

Exact final-source hosted qualification is tracked separately in
[the receiving receipt](../addon_window_lifecycle_validation_20261013.json).
No candidate freeze or publication is inferred.

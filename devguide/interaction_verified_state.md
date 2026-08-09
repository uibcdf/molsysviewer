# Interaction Verified State

This page is the operational source of truth for interaction behavior that is
already implemented and has been checked in practice.

It is intentionally different from the interaction design/spec documents:

- `interaction_overview.md`
- `interaction_targets_and_selection.md`
- `interaction_gestures_and_menus.md`
- `interaction_modifiers_and_future.md`

Those documents describe the intended contract and future direction.
This page records what is actually working now, what has already been verified,
and what still needs confirmation or correction.

Update this page whenever smoke testing changes the confidence level of an
interaction behavior.

## Status Vocabulary

- `implemented`: code exists, but it has not been re-verified recently in the
  real notebook/browser flow.
- `verified`: confirmed manually in live smoke and/or by stable automated
  coverage.
- `pending`: intended behavior exists in the contract, but the implementation is
  missing or still known to be unreliable.

## Main Notebook Canvas

### Verified

- `left drag`
  - rotates the scene
- `right drag`
  - pans/translates the scene
  - does not open the JupyterLab host menu
- `right click` on empty canvas
  - opens the viewer-owned context menu
  - does not open the JupyterLab host menu
- `right click` on atoms and visible bonds/links
  - resolves to the default `group` target
  - bond/link fragments no longer fall back to `No target under cursor`
- `left click`
  - selects the clicked `group`
- `Shift + left click`
  - adds another `group`
  - toggles off a previously selected `group`
- `Esc`
  - clears `active_selection` when no measurement tool mode is active
- selection visual state
  - the current `selection` marker is visible again
  - multi-selection no longer depends on click order

### Verified

- `double left click`
  - triggers camera `focus` on the clicked `group`

## Popup Canvas

### Verified

- `left drag`
  - rotates the scene
- `right drag`
  - pans/translates the scene
- `right click`
  - opens the viewer-owned context menu
  - no host JupyterLab menu conflict appears in the popup surface

## GroupPanel / GroupStrip

### Verified

- the runtime now uses a `GroupPanel` container with one `GroupStrip` per chain
- `left click`
  - selects the corresponding `group`
- `Shift + left click`
  - adds a `group`
  - toggles off a selected `group`
- `hover`
  - mirrors into viewer highlight
- `double click`
  - triggers camera `focus`
- current visual strip states now distinguish at least:
  - active selection
  - annotation selection badges
  - context target, with a discrete marker for structure and annotation targets

### Verified

- `right click`
  - opens the same viewer-owned context menu used by the canvas

## Context Menu

### Verified

- opens on the main notebook canvas without leaking the host menu
- opens on the popup canvas
- shows the correct empty-canvas message
- on structural targets, it supports:
  - `Focus Target`
  - `Distance`
  - `Angle`
  - `Dihedral`
- on annotation targets, it now supports:
  - `Focus Target`
  - `Delete Annotation`
- on shape targets with stable tags, it now supports:
  - `Focus Target`
  - `Delete Shape`
- on active selection, it supports:
  - `Focus Selection`
  - `Save Selection`
  - `Create Region from Selection`
  - `Add Label from Selection`
  - `Clear Selection`
- for recent interactive measurements, it supports:
  - `Persist Last Measurement`
- for structural context targets, it now also exposes a first lightweight
  persistent-workbench bridge for relevant `regions`:
  - a `Regions` section appears when stored regions overlap the context target
  - the first action is intentionally narrow:
    - `Focus Region`

## Python Interaction Callbacks

### Verified (2026-06-25)

- `view.on_hover(callback)` — registers a callback fired on every
  `interaction_hover` event and enables browser-to-Python hover telemetry;
  `off_hover(callback)` removes it and the last removal disables telemetry
  unless `view.hover_telemetry_enabled` remains explicitly true
- `view.on_click(callback)` — same pattern for `interaction_click`
- `view.on_context_menu(callback)` — same pattern for `interaction_context_menu`
- Callbacks receive the raw event dict (same payload stored in
  `view.get_last_hover_event()` / `view.get_last_click_event()`)
- **Enriched Biological Metadata**: The frontend now queries the molecular hierarchy in Mol* directly and attaches a complete metadata block. The payload includes:
  - `chain_id` (string)
  - `group_name` (string, e.g. "ALA")
  - `group_id` (string, e.g. "43")
  - `group_index` (int, 0-indexed residue/group position)
  - `atom_name` (string, e.g. "CA")
  - `element` (string, e.g. "C")
  - `atom_index` (int, global 0-indexed atom index)
  - `atom_id` (int, global atom ID)
- This enrichment is resolved locally on the JS side and sent directly, avoiding round-trip latency to Python for standard hover/click inspections.
- Implementation: `_hover_callbacks`, `_click_callbacks`, `_context_callbacks`
  lists in `core.py`; fired inside the `_handle_frontend_event` dispatcher

## Interactive Measurements

### Verified

- the measurement tool modes feel clear in live smoke
- measurements appear in the scene where expected
- full state machine in `measurement-tools.ts` (`MeasurementToolController`):
  - states: started → progress → completed / cancelled
  - `Escape` key cancels via `window keydown` listener (capture phase)
  - `ToolStatusOverlay` (top-left of canvas) shows pick count and "Esc cancels" hint
- `view.get_last_measurement_created_event()` reports a coherent replay-safe
  payload:
  - `action`
  - `picked_count`
  - `picks_atom_indices`
  - `endpoint_kinds`, `endpoint_policy`, `endpoint_labels`, `endpoint_atom_indices`
  - `tag`, `value`
- `view.get_last_tool_state_event()` reports current tool progress:
  - `action`, `status`, `required_picks`, `picked_count`, `remaining_picks`
- `Persist Last Measurement` is part of the implemented reproducibility bridge
- `view.measurements` now exposes minimum inspection helpers:
  - `count()`
  - `records()`
  - `info()`

## Region-Aware Picks

### Implemented (2026-04-27)

- `kind: "structure"` payloads for `interaction_hover`, `interaction_click`, and
  `interaction_context_menu` now include `region_tags: list[str]`
- The list contains the tags of all named regions (`view._regions`) whose
  `atom_indices` intersect the `atom_indices` in the pick payload
- Empty list when no regions are defined or none overlap the pick
- Enrichment is Python-side in `_enrich_interaction_payload()` (core.py); no JS changes
- Covered by: `test_region_tags_added_to_structure_payload`,
  `test_region_tags_empty_when_no_regions_defined`

## Reproducibility Bridges

### Verified

- `active selection -> region`
  - UI action exists and executes through Python into reproducible viewer state
- `active selection -> named selection`
  - UI action exists and executes through Python into reproducible viewer state
  - automated regression exists
  - live smoke now verifies the context-menu flow both from empty-canvas context and from a structural context target
- saved selections can now be reactivated from API and the context-menu saved-selection section
- `active selection -> label`
  - UI action exists and executes through Python into reproducible viewer state
- `interactive measurement -> persisted measurement`
  - UI action exists and executes through Python into reproducible viewer state

## Active Selection API

### Verified

- `view.active_selection` now exists as a public Python wrapper
- current minimum surface:
  - `info()`
  - `is_empty()`
  - `clear()`
  - `focus(...)`
  - `new_region(...)`
  - `add_label(...)`
  - `save(...)`
- persistent selections can now be restored back into the interactive workflow via:
  - `view.selections.activate(tag)`
  - `view.selections[tag].activate()`
- `clear()` now clears both:
  - Python-side cached selection state
  - frontend runtime active selection

## Hover And Context Targets

### Verified

- `view.hover_target` now exists as a lightweight public Python wrapper
- `view.context_target` now exists as a lightweight public Python wrapper
- current minimum surface for both:
  - `info()`
  - `is_empty()`
- hover telemetry is off by default; `hover_target.info()` distinguishes
  `telemetry_disabled`, `telemetry_waiting`, and a sampled target, while
  `is_empty()` raises for the first two states
- current first slice intentionally remains query-oriented
- legacy/raw event getters still exist and remain valid:
  - `get_last_hover_event()`
  - `get_last_context_event()`

## Annotations

### Verified

- persistent labels exist as `annotations`, not `shapes`
- labels created from UI appear in the scene
- labels are reflected as overlays in `GroupStrip`
- labels participate in replay/export/rebuild
- labels can be managed by Python API:
  - `tags()`
  - `count()`
  - `contains()`
  - `get()`
  - `records()`
  - `info()`
  - `show()/hide()`
  - `delete()`
  - `set_tag()`
  - `set_text()`
  - `set_group_index()`
  - `clear()`
- UI-created labels now survive a live `hide()/show()` round-trip through the
  Python API on the notebook canvas

## Export / Replay

### Verified

- `_build_export_messages()` now has an integral regression covering a realistic
  reproducible workbench state with:
  - `create_region`
  - `set_region_representation`
  - `add_label`
  - `update_label`
  - `add_distance_measurement`
  - `add_angle_measurement`
  - `add_dihedral_measurement`
  - `set_camera_snapshot`
- `measurements` no longer emit `DigestNotDigestedWarning` for the explicit
  atom-pick arguments used by the reproducible API surface

## Known Open Points

- future discussion of a distinct `bond` target policy
- future discussion of `focus` versus optional `focus marker`
- future richer gesture policy for range selection, without overloading `Shift`

## GroupPanel Layout

### Implemented

- `GroupPanel` is now a left sliding sidebar
- when collapsed, only the chevron tab remains visible
- each `GroupStrip` is rendered as a full-height vertical column with its own scroll
- the notebook/docs embedding clips viewer overflow so sidebar motion does not create host-cell scrollbars or canvas blinking

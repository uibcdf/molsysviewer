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
  - handles an open context menu first (Back in a submenu, close at root)
  - otherwise retains tool/panel cancellation and active-selection clearing priority
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

### Automated foundation verification — 2026-10-08

The real dialanine/Mol*/Chromium `context-menu.e2e.ts` guard verifies the #179
foundation: target headings, bounded submenus, active-selection preservation,
keyboard and focus return, canvas-edge positioning, authoritative history,
section-aware Studio opening and explicit-state Python viewport echoes.
Atomless targets disable atom-based focus unless real geometry bounds are
available. Molecular creation from shape-only selections is disabled.
Escape handles the open menu before a measurement tool. Backend actions dispatch
once, and browser-owned Studio navigation sends no unsupported backend action.
The targeted GroupPanel interaction guard confirms its shared menu still creates
a label after opening the active-selection submenu.

These checks are development browser evidence. The maintainer's subsequent
notebook review confirms the contextual workflows and both reported defect
corrections. The final visual refinement remains under review as recorded below.
Molecular/object/occurrence workflows are implemented; their evidence is
recorded below. Earlier main/popup observations retain their original scope.

The implemented menu offers the existing target focus/measurement and scene
object operations, active-selection workflows and relevant-region actions through
compact pages. Saved collections open Studio. Shared View, Undo/Redo and Open
Studio are no longer restricted to empty canvas. Interactive measurements are
already managed objects; the former Persist Last Measurement entry is absent.
[The accepted plan](canvas_context_menu_pre_1_0_plan.md) records outstanding work.

### Automated molecular workflows — 2026-10-08

The extended real-demo guard verifies target inspection, target-based
region/annotation creation while preserving a different working selection,
distinct add/remove/replace actions, contextual Shapes staging and Interactions
calculation preparation without executing it. Browser-generated requests are
replayed through the real Python owners. A panel-only Studio opens the menu from
its relayed hierarchy, omits canvas measurement picking and does not send a
fictitious frame-zero identity. Measure has three actions and a separate explicit
endpoint-policy selector; its progress label names the policy. Human acceptance
of this slice remains pending together with the completed object/occurrence work.

### Automated object and occurrence workflows — 2026-10-08

Clicked occurrences carry their actual query position, occurrence ID, visible
frame and analysis/query revisions. One bounded inspector page resolves the
pick before existing participant selection/focus actions. Backend tests cover
parallel observations, compound participants, nonconsecutive structures,
skipped geometry and stale/mismatched references. Explicit Hide is idempotent
and preserves stored analysis. Object actions route to the existing Studio
editors; atomless geometry focuses real Mol* bounds. Current object ownership
comes from the registered scene, preserving type/tag across renames and collisions.

53 focused Python checks, 46 focused JS owner cases, TypeScript and runtime
regeneration pass. The final extended real-Mol*/Chromium guard passes: one-page occurrence #61
inspection, participant/set scope, object editors, free-geometry focus, rename
and same-tag kind separation, shared Help and stale-context dismissal.
The prepared human notebook is
[`../sandbox/revision_context_menu_pre_1_0.ipynb`](../sandbox/revision_context_menu_pre_1_0.ipynb).
Its public setup executes successfully (three structures evaluated for Buch,
three occurrences). The maintainer's first interactive review confirms the
reviewed workflows except for the two findings below. These are development
checks, not replacement-package or manual acceptance. #179 stays partial.

### First human review: boundary bonds and translucent picking — 2026-10-08

The maintainer observed missing peptide half-links after contextual residue
creation and an unpickable free sphere. A real-browser diagnostic reproduces
zero/two boundary halves without/with Mol* parent context, and empty/shape picks
at opacity thresholds `0.5`/`0.01`. The corrections preserve neighbor atom
exclusion and fully transparent Whole ownership masks. All three pointer paths
and active shape selection use current registered tags; free geometry does not
invent atom associations.

The expanded context-menu guard passes with real pentalanine structures
`[0, 8, 3]`, generated peptide boundary half-links through frame and style
changes, real screen hover/click/right-click on the translucent sphere, and its
persistent selection marker. The former loci-injection checks did not cover
GPU picking. Python hover telemetry is disabled in this snapshot; hover is
checked locally, and marker checks await Mol*'s render tick. The owner unit cases
pass (30 StateHandlers and six ActiveSelection); all 323 JS cases pass after
updating the existing line-default expectation. The subsequent human review
confirms both reported defects are corrected; no package or publication
qualification is inferred.

The affected shared-Chromium campaign passes 6/6 suites: context-menu,
measurements-interaction, region-hide, region-subpanel, shapes-subpanel and
scene-contracts. Runtime regeneration, TypeScript, 181 reporting guards and
generated-index checks pass. This campaign has targeted scope; the previous
40-suite evidence remains recorded with its original source and recovery limits.

### Human reconfirmation and final UX refinement — 2026-10-08

The principal maintainer confirms the two reported defects are corrected and
the reviewed contextual workflows work. The accepted vocabulary/UX pass now
uses Group in the menu, target composers, System inspector and disulfide
calculation input. Group is a native topological level, distinct from Region.
Targets with no declared group/chain membership fail before changing selection
or creating objects; 21 focused Python cases cover these contextual owners.

Selection scopes retain their headings and explicit replace/add/remove
operations with short visible labels and scope-qualified accessible names.
Shapes/measurements prioritize current user-assigned tags, including after
rename. Related-region rows retain focus, Show/Hide and Studio access; their
rename/delete controls remain in Studio. Pointer hover is soft and keyboard
focus remains outlined.

The extended real pentalanine/dialanine/Mol*/Chromium guard passes on this
runtime, including the short labels and scope values, related-region Studio
routing without changing selection, current shape/measurement titles, and the
earlier pointer/bond/occurrence guards. The menu owner passes 17 cases. The JS
regression found one old Studio subtitle expectation (322/323); its corrected
GroupPanel owner passes 35/35. This is targeted recovery, not an uninterrupted
green full campaign. TypeScript and runtime regeneration pass. Final visual
acceptance of these refinements and replacement-package qualification remain
separate; #179 remains partial.

The required full Python run outside the sandbox completes 2,938 cases:
2,907 pass, 23 skip and the eight previously recorded Qt probes fail with
OpenGL/Vulkan context creation and D-Bus errors. Native JUnit and receptor
counts agree. The full regression is not green and is not repeated; this
preserves the experimental Qt scope under #109/#113. Ruff and generated-index
checks pass.

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

## Adaptive context navigation — 2026-10-08

The final real-demo context guard verifies a persistent root plus one adjacent
secondary card, click-to-toggle/switch without hover opening, left flipping and
canvas-edge bounds. Narrow resizing uses Back and preserves an unsent form;
Cancel/Escape restores the originating submenu without changing selection.
An actual secondary browser window renders Mol* and switches from two cards
to one within its own resized bounds. Disabled history actions accept focus,
show their reason and reject Enter/Space activation. The explanatory overlay
does not reflow action positions during pointer focus.

The final focused menu owner passes 17 cases, and TypeScript/runtime build pass.
The full JS campaign passed 323 cases before that explanatory-overlay correction.
Five affected suites also pass in one shared Chromium: popup-channel,
group-panel-interaction, measurements-interaction, selection-subpanel and
scene-contracts. The 181 reporting-protocol checks and generated indexes pass.
These are development checks; the refreshed notebook visual review is pending
under `uibcdf/molsysviewer#179` and does not qualify a replacement package.

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

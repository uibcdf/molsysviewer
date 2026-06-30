# Development Checkpoint

This file is not a changelog.
Git history already covers that.

This file is the current handoff checkpoint for ongoing development work.
It should help a developer answer, quickly:

- where we are,
- what is already decided,
- what should happen next,
- why that is the right next step,
- what constraints must not be broken.

Update this file to reflect the current state.
Do not append dated historical entries unless a date is itself operationally relevant.

## Current Focus

### Phase E — Standalone App & Parity Consolidation

With Phase D (unit consistency, TopoMT integration, and high-performance WebGL coordinate updates) fully closed and validated, the current focus shifts toward the production-ready maturation of the standalone Qt-based application shell and achieving parity in all user-facing documentation/tutorials.

**Remaining steps toward `1.0.0`:**
- **Mature the Qt Standalone Host**: Integrate the PySide6/QtWebEngine app shell with our unified reproducible workspace and scene state representation.
- **Visuals and Parity**: Promote any additional curated visual schemes or custom sizes to matching public Python APIs.
- **Downstream Hardening**: Validate other add-on integrations (e.g. `pharmacophoremt`, `elasnetmt`, `topomt`) to ensure no regression or visual bugs occur during complex analysis workflows.

### Pending proposals and bugs: current state

### Reviewed: chemical metadata SDF/MOL2 downstream integration

`chemical_metadata_loss_sdf_pdb.md` remains pending, but its local scope was
cleaned up. MolSysViewer already transports `formal_charge` from ViewerJSON into
the TS payload and materializes it as Mol*/mmCIF `atom_site.pdbx_formal_charge`,
and `bonds.order` is already part of the payload when MolSysMT provides it. The
remaining work depends on the upstream MolSysMT contract for SDF/MOL2 bond
order, aromaticity/type, partial charge, molecule/component metadata, and custom
SDF property blocks.

### Recently closed: frontend backend-error acknowledgments

`silent_exception_desync.md` was implemented and removed. Interactive frontend
actions now catch backend exceptions in the `interaction_context_action` path,
emit a catalog-driven SMonitor diagnostic (`frontend_action_failed`) with
`context_extra(...)` fields for event/action/error/evidence, and send a
runtime-only `backend_error_occurred` message back to the frontend. The ack does
not enter reproducible message history. The TypeScript controller handles the
ack with a non-blocking toast so users see the backend failure instead of a
silent browser/kernel desynchronization.

### Recently closed: generic geometry payloads and final-boundary adapters

`generic_geometry_payloads_and_entity_refs.md` was implemented and removed. The
host now exposes viewer-neutral immutable payloads in `molsysviewer.geometry`
for points, spheres, segments, indexed triangles, indexed edges, and tetrahedra,
with mandatory units, JSON-serializable entity references, and explicit atom
index-space metadata. `molsysviewer.shape_adapters` provides final-boundary
adapters that normalize units with PyUnitWizard and call existing shape APIs with
`skip_digestion=True`, preserving indexed primitive references for triangle and
tetrahedron picking payloads while keeping existing shape APIs compatible.

### Closed as already implemented: shape visibility and layer group API

`shape_visibility_and_layer_group_api.md` was reviewed and removed as already
satisfied by the current scene-object/layer model. Shapes register public
`layer_tag` membership through `register_shape_layer(...)`, `view.layers` exposes
non-structural visual groups, `Layer` provides `show()`, `hide()`, `delete()`,
`set_tag()`, `attach()`, `detach()`, and `info()`, and the frontend workbench
handles `show_layer`, `hide_layer`, `delete_layer`, and `set_layer_tag` messages
for inspectable overlay management. Existing shape APIs remain compatible and
addons can use `layer_tag` without reaching into private viewer attributes.

### Recently closed: region boolean composition and overlap warnings

`region_superposition_z_fighting.md` was implemented and removed. `Region` now
supports boolean composition through `difference()` / `-`, `intersection()` /
`&`, and `union()` / `|`, returning normal reproducible `Region` objects backed
by `new_region(...)` create messages. Visualizing a region now warns with a
`UserWarning` when its atoms overlap another active visible represented region,
while logical-only and hidden regions are ignored.

### Recently closed: Jupyter AnyWidget runtime bootstrap

`jupyter_websocket_redundancy_overflow.md` was implemented and removed.
`MolSysViewerWidget._esm` is now a small bootstrap (~2.3 KB in the current
build) instead of the full generated `viewer.js` runtime (~5.9 MB). The
bootstrap requests `widget_runtime_source` once at render time, imports it
from a Blob URL, and caches the loaded module/source on `globalThis` so
additional widgets in the same frontend page reuse the already-loaded runtime
instead of resending the bundle. Popout source delivery remains runtime-only
through `request_popup_source` / `popup_source`, and standalone HTML
exports explicitly inline the full runtime because they have no live Python
backend to answer the bootstrap request.

### Recently closed: image export GPU allocation preflight

`image_export_canvas_allocation_failure.md` and the duplicate `image_export_gpu_limits.md` were implemented/covered and removed.
Frontend image export now checks the requested scaled resolution against WebGL
`MAX_RENDERBUFFER_SIZE` and `MAX_VIEWPORT_DIMS` before asking the Mol*
viewport screenshot helper to allocate the export target. Requests above hardware
limits return an immediate `image_export` failure event with
`GPU_LIMIT_EXCEEDED`, requested dimensions, detected limits, and a clear
reduction recommendation. Python converts that frontend failure into a
`ValueError` instead of waiting for timeout or reporting a generic missing
PNG URI.

### Recently closed: high-frequency hover event saturation

`high_frequency_event_saturation.md` was implemented and removed. The current
frontend has no Python-bound camera-moved event path, and trajectory playback
frame notifications were already throttled. The remaining high-frequency path
was hover: Mol* hover events still update local frontend state immediately, but
Python/AnyWidget hover notifications are now debounced in
`MolSysViewerController` with a 60 ms tail, so rapid cursor crossings
collapse to the final inspected target without starving local JS add-ons or UI
state.

### Recently closed: dynamic shape render diagnostics

`dynamic_shapes_topology_changes.md` was implemented and removed. Dynamic
trajectory-bound shapes now report runtime-only render diagnostics via
`shape_render_status`, exposed in Python through `view.shapes.render_status(...)`
without entering reproducible message/shape history. Frontend status events are
emitted only on effective state transitions to avoid playback-channel
saturation. Rebuild remapping now handles per-frame `structures_atom_indices`
and `structures_atom_pairs`, preserving live frames as remapped indices and
dropping fully orphaned dynamic shapes.

`devguide/pending_proposals/` now holds an extensive robustness/quality backlog
(12 files). It mixes earlier visualization/addon proposals with a recent
code-review pass focused on consistency, conceptual gaps, maintainability, and
performance. Highlights from that review (not yet implemented):

* `viewer_mixin_contract_and_caller_resolution.md` — the 11 `MolSysView` mixins
  share ~33 untyped attributes/methods with no Protocol/base, and the ArgDigest
  caller resolution is double-bookkept (`__name__` spoof in 8 mixins +
  `normalize_viewer_caller` string surgery).
* `payload_column_vectorization.md` — `_column` runs 13 pure-Python per-atom
  loops on the load hot path; vectorizable fast path.
* `visibility_diff_updates.md` — `update_visibility` resends the full visible
  index list on every visibility op.

`devguide/pending_bugs/` holds 0 files.

Note: `partial_coordinate_updates.md` (the previously-tracked single proposal)
was implemented and removed; in-place WebGL updates and sequence ACKs are fully
functional and integrated.

Recently closed and implemented in this session (twenty-second batch):

**Core Feature Copy, Index Mismatch Resolution, Support Geometries, TopoMT, and Bidirectional WebGL updates**:

- **Core Feature Copy Refactor**: Refactored `__copy__` and `__deepcopy__` in TopoMT's `BaseFeature.py` to dynamically clone the feature's entire `__dict__` instead of relying on a whitelist of hardcoded attributes, removing the addon-level workaround in `molsysviewer_topomt`.
- **Index Mismatch Resolution**: Implemented `IndexMapper` in `molsysviewer/viewer/index_mapper.py` to bidirectionally translate original/global atom and structure indices to local viewer indices, ensuring correct indexing in picks, hovers, selections, active selection updates, player navigation, camera zooms, and regions.
- **Unit Consistency in Support Geometries**: Standardized the `info()` outputs of both `ShapesManager` and `MeasurementsManager` to return Pint/PyUnitWizard quantities in nanometers (`nm`) by default. Intercepted picking, hover, selection, and measurement events to convert coordinate points from raw Angstroms back to `nm`.
- **TopoMT Features Support**: Added unified `add_topomt_feature(feature)` handler to automatically detect and parse Pocket, Void, Mouth, Channel, and Boundary objects from `topomt`, converting units via PyUnitWizard and registering them to representation layers.
- **In-Place WebGL Coordinate Updates & Transaction ACKs**: Implemented `partial_coordinates_update(coords_ang, atom_indices, transaction_id)` in Python and TS. The frontend mutates active conformation coordinates (`model.atomicConformation.x/y/z` Float32Array arrays) in-place and versions the conformation ID (`conformation.id = currentId + "_upd"`), triggering rapid WebGL vertex buffer modification (`gl.bufferSubData`, <10ms rendering time). Implemented transaction ACKs (`trajectory_frame_rendered` event) backpressure throttling in playbacks to prevent WebSocket queue flooding.
- **JS unit tests**: All 110 tests pass successfully.
- **Python regression suite**: All 423 tests pass successfully.

Recently closed and implemented in this session (twenty-first batch):

**Workspace UI disappearance bug — stale field name in `getWorkspaceOptions`**:

- Root cause: `viewer-controller.ts:2148` referenced `this.addonRuntimeSummary`
  (an undefined field) instead of `this.workbenchAddons`. When any addon with a
  workspace was enabled, `getWorkspaceOptions()` threw a TypeError, crashing
  `refreshPanelWorkspaceChrome()` and `refreshWorkbenchPanel()`, causing the
  right panel to go blank.
- Fix: one-line rename `addonRuntimeSummary` → `workbenchAddons` at the call site.
- TS build: `npm run build` — exit 0, `viewer.js` updated.
- `devguide/pending_bugs/BUG_addon_workspace_ui_disappearance.md` deleted.
- `devguide/pending_bugs/BUG_addon_anisotropy_scaling_mismatch.md` deleted
  (already fixed by the nm→Å shape wire format fix in the previous session).

Recently closed and implemented in this session (twentieth batch):

**Add-on panel widget contract — full implementation**:

- `AddonPanelWidget` base class added to `molsysviewer/addons.py`:
  - anywidget subclass with `push_state`, `request_context`, `handle_action`,
    `on_mount`, `on_unmount`
  - message routing from `_route_frontend_message` dispatches `action` and
    `query` (viewer context) types
  - `_build_viewer_context()` exposes `has_system`, `active_selection`,
    `workspace`
- `widget_class: str | None = None` added to `AddonPanelSpec`, exported from
  `molsysviewer.__init__`
- `ViewAddonsManager.resolve_panel_widget(addon_name, panel_id)` imports and
  instantiates the class bound to the current view
- TS canvas panel host:
  - `workspaceAddonWidgetHost` div appended to `WorkbenchPanel`
  - `mount_addon_panel` op: creates Blob URL from ESM string, dynamically
    imports it, calls `render({ model, el })` via a model proxy
  - model proxy: `model.send` → `addon_panel_action` event to Python;
    `model.on("msg:custom", cb)` → registered in `activePanelMsgListeners`
  - `addon_panel_message` op: forwards content to all registered listeners
  - `cleanupActivePanelWidget` called on workspace switch or panel navigation
- Python panel lifecycle in `viewer/core.py`:
  - `panel_navigate` JS event → `_mount_addon_panel(addon, panel)`
  - `panel_unmount` JS event → `_unmount_addon_panel()`
  - `addon_panel_action` JS event → routes content to active widget
  - `_mount_addon_panel` patches `widget.send` to route through
    `_send_runtime_only` with `op: "addon_panel_message"`, calls `on_mount`,
    pushes initial context, sends `mount_addon_panel` op to TS
- 10 new tests in `tests/test_addons.py` — all passing
- TS build: `npm run build` — exit 0, `viewer.js` updated

**ElasNetMT `ElasNetMTModelPanel` — first proof of the panel widget contract**:

- `molsysviewer_elasnetmt/panels/model.py` — subclass of `AddonPanelWidget`
- `_esm`: vanilla JS panel with GNM/ANM tab toggle, cutoff input, Compute button
- `on_mount`: pushes current runtime state to the panel
- `handle_action`: `set_model_kind`, `set_cutoff`, `compute`
  - `compute` calls `get_or_build_contact_model` (GNM) or
    `get_or_build_anm_model` (ANM) via existing adapters; reports `n_nodes`
- `widget_class` wired in `AddonPanelSpec` for the `model` panel
- 4 new integration tests in `tests/integration/test_molsysviewer_addon.py`;
  12 total, all passing

Recently closed and implemented in this session (nineteenth batch):

**Camera zoom animation bug — PyUnitWizard `api_string.is_unit` root-cause fix**:

- `view.camera.zoom(..., duration='250 ms')` was snapping instantly (no animation) because
  `duration_ms: 0` was reaching the JS frontend.
- Root cause: `pyunitwizard/forms/api_string.py::is_unit` forced `to_type="unit"` when
  parsing the string, stripping the numeric value. This made `is_unit('250 ms') = True`,
  so `puw.standardize('250 ms')` took the unit branch and returned
  `<Unit('picosecond')>` instead of `<Quantity(2.5e+11, 'picosecond')>`.
  `quantity_value_in_unit` then wrapped it as `1.0 ps → 1e-9 ms → int = 0`.
- Fix applied in **pyunitwizard** (`api_string.is_unit`): now parses the string normally
  and checks `get_value(result) == 1`, consistent with `puw.is_unit` in `introspection.py`.
- Full chain verified: `standardize('250 ms')` → `250000000000.0 ps` (Quantity) →
  `quantity_value_in_unit(..., 'ms')` → `250.0` → `int` → `250` → JS animates correctly.
- No changes needed in MolSysViewer; `digest_duration` + `quantity_value_in_unit` are correct.

**`puw.standardize` — added `to_unit=` parameter**:

- `pyunitwizard/api/standardization.py::standardize` now accepts an optional `to_unit`
  parameter; when given, converts to that unit instead of the configured standard for the
  dimensionality. Behavior unchanged when `to_unit=None`.

**`camera.set_mode` `ArgumentError` — already fixed**:

- `BUG_camera_set_mode_validation_error.md` was stale; the whitelist entry
  `"molsysviewer.viewer.camera.CameraManager.set_mode"` was already present in
  `digest_mode`. Bug report deleted.

Recently closed and implemented in this session (eighteenth batch):

**Representation taxonomy cleanup — `licorice` alias and non-molecular types**:

- `licorice` alias corrected: was mapped to `"line"` (2D flat wireframe); now
  correctly mapped to `"ball-and-stick"` (3D cylinders + spheres, which is the
  VMD/NGLview meaning of "licorice").
- Additional aliases added: `"cylinders"` → `"ball-and-stick"`, `"dots"` → `"point"`.
- `ALLOWED_REPRESENTATIONS` audited against the full Mol* built-in list (15 types):
  - `"label"` removed — not a molecular visualization style; text labels are
    exposed through `view.annotations.add_annotation()`.
  - `"orientation"` removed — structural axes helper; accessible via the
    `molstar_repr_type` escape-hatch if needed.
  - `"plane"` removed — best-fit plane helper; same escape-hatch route.
  - All 11 remaining entries are genuine molecular representation types.
- `REPRESENTATION_PARAM_SCHEMAS` entries for `label`, `orientation`, `plane`
  removed to keep the module internally consistent with `ALLOWED_REPRESENTATIONS`.
- The comment block above `ALLOWED_REPRESENTATIONS` documents the three excluded
  types and their correct alternatives.

Recently closed and implemented in this session (seventeenth batch):

**`molsysmt.basic.info()` — subset and structure_indices support**:

- `structure_indices='all'` added to the signature of `info()`.
- `element='system'` branch now has two paths:
  - `selection='all'` (default): existing behavior unchanged.
  - `selection != 'all'`: resolves atom indices with `select()`, then calls
    `get(element='atom', selection=atom_indices_resolved, n_atoms=True,
    n_groups=True, ..., n_saccharides=True)` — all these scalar-count
    `from_atom` implementations already support index subsets.
    `n_structures` is fetched separately via `get(element='system',
    n_structures=True)` since it is a trajectory attribute.
  - After either path: if `structure_indices != 'all'`, `n_structures` is
    overridden to `len(structure_indices)`.
- All other element branches (`atom`, `group`, `chain`, etc.) are unchanged.
- When `selection='all'` and `structure_indices='all'`: output identical to
  previous behavior.

**`SelectionsManager.add_selection` — aligned with `msm.select` signature**:

- Old `atom_indices` keyword removed; replaced by the `selection` positional
  arg which already accepts integer lists (interpreted at `element` level).
- New params: `element='atom'` and `mask=None`, matching `msm.select`.
- Implementation now always calls `msm.select(molsys, selection, element,
  mask, syntax)` — the molsysmt function handles all cases (string query,
  int list at any hierarchy level, `"all"`).
- Raises `ValueError` if no system is loaded (the old `atom_indices` path
  bypassed molsysmt; that bypass is no longer needed).

Recently closed and implemented in this session (sixteenth batch):

**`set_representation(color=...)` greys out other atoms**:

- Root cause: the previous fix routed through `set_atom_colors`, which is a
  global Mol* per-atom color theme.  Atoms NOT in the color map fall back to
  grey.  For a region, only its own atoms were colored, making everything else
  grey.
- Fix: instead of using `set_atom_colors`, the color is now injected as
  `molstar_color_theme = {"name": "uniform", "params": {"value": c}}` into
  `params` BEFORE the send — both in `whole.py` and `regions.py`.
- TS change: `setRegionRepresentation` in `state-handlers.ts` now calls
  `getStructuralColorThemeFromParams` (same as `setGlobalRepresentation`) and
  spreads `color` / `colorParams` into `addRepresentation` options for the
  direct-type path.  Preset paths receive the cleaned params + `theme`.
- JS rebuilt successfully.
- The per-atom `_atom_color_map` and `set_atom_colors` path is now only used
  for scalar coloring (`set_color_by_values`), not for uniform colors.

**`Region.info()` returns per-atom table instead of system summary**:

- Root cause: `molsysmt.info()` does not support returning a system-level
  summary (N atoms, N groups, N chains…) for a subset of atoms.  `Region.info()`
  falls through to `element="atom"` which returns the full per-atom table.
- This requires a MolSysMT change.
- Filed as `pending_proposals/PROPOSAL_molsysmt_info_system_subset.md`.

Recently closed and implemented in this session (fifteenth batch):

**`SelectionsManager` API cleanup** (`BUG_selections_manager_api_overhaul` /
`PROPOSAL_selections_manager_signature_alignment`):

- `add_selection(tag, selection="all", *, atom_indices=None, syntax="MolSysMT",
  skip_digestion=False)` — clean public signature; internal Mol* metadata
  (`source_kind`, `target_level`, `items`, `group_indices`, etc.) removed from
  the public surface.
- New internal `_store_selection_record(tag, atom_indices, *, source_kind, ...)`:
  builds and sends the `save_selection` message; carries all the frontend
  metadata needed for `activate()` replay without polluting the public API.
- `add_from_active_selection` now calls `_store_selection_record` directly,
  passing the full frontend event payload.
- Deprecated `add()` method removed (no external callers; already deprecated
  in the previous session).

Recently closed and implemented in this session (fourteenth batch):

**Bug fixes**

*`Region.set_representation(color='...')` fails with `ValueError: Unsupported element level 'system'` (`BUG_region_color_string_conversion_failure`):*

- Root cause: `set_representation` was delegating to `set_color_by_values(values=[color],
  element="system", ...)`.  `expand_values_to_atoms` does not accept `element="system"`,
  and even if it did, it would treat the color int as a scalar to be mapped through viridis
  rather than as a literal color.
- Fix in `regions.py`: replaced the delegation with a direct `set_atom_colors` send:
  normalise `color` with `normalize_color()`, broadcast to all `self.atom_indices`, merge
  into `_atom_color_map`, send `{"op": "set_atom_colors", ..., "replace": False}`.
- Same broken pattern fixed in `whole.py`: uniform color now broadcasts to all `n_atoms`
  with `replace: True`.
- `normalize_color` added to the import from `.colors` in both files.

*`Region.info()` fails with `ArgumentError` on `output_type` (`BUG_region_info_output_type_error`):*

- Root cause: the actual caller string emitted by `@digest()` is
  `'molsysviewer.regions.info'`, not `'molsysviewer.regions.Region.info'`.
- Fix: both `'molsysviewer.regions.info'` and `'molsysviewer.regions.Region.info'` added
  to the `caller` whitelist in `_private/arg_digestion/argument/output_type.py`.

**Devguide**

- `PROPOSAL_box_merging_logic_refinement.md` marked with a prominent
  "TEMPORALMENTE IGNORADA" notice: depends on a per-frame box API in MolSysMT
  that does not yet exist.

Recently closed and implemented in this session (thirteenth batch):

**API unification and discovery**

*Discovery API (`PROPOSAL_discovery_api`):*

- `view.representations` property — lists all active representation names on
  the whole system.
- `view.presets` property — lists available preset names.

*Direct color in `set_representation` (`PROPOSAL_direct_color_in_set_representation`):*

- `whole.set_representation(name, color=...)` and
  `region.set_representation(name, color=...)` accept a `color` keyword.
- Internally pops `color` from params and delegates to `set_color_by_values`.

*Measurement API unification (`PROPOSAL_measurement_api_unification`):*

- `add_distance`, `add_angle`, `add_dihedral` primary positional params
  renamed to `selection_a/b/c/d`.
- Old `atom_indices_a/b/c/d` names accepted as deprecated keyword-only args
  (emit `DeprecationWarning`, then set the new variable).

*Selections manager API (`PROPOSAL_selections_manager_api`):*

- `SelectionsManager.__getitem__(tag)` and `__iter__` added.
- `add_selection(tag, selection=None, *, atom_indices=None, syntax, ...)`
  as primary method; resolves selection string via `msm.select()` or uses
  `atom_indices` directly.
- `add()` deprecated alias for `add_selection()`.

*Annotation refactor (`PROPOSAL_annotation_refactor`):*

- `add_annotation(text, kind, selection=None, *, atom_indices=None, tag,
  layer_tag, syntax)` as primary method.
- `add_label()` deprecated alias; resolves `group_index` to `atom_indices`
  internally before delegating to `add_annotation()`.

*Shape API unification (remaining) (`PROPOSAL_shape_api_unification`):*

- `add_links()` gains `radius` and `color` as primary params; old `radii` /
  `colors` accepted with `DeprecationWarning`.

*Shapes info (`PROPOSAL_shapes_info`):*

- `ShapesManager.info(tag=None)` — iterates `_shape_history` and returns
  a list of dicts: `kind`, `tag`, `layer_tag`, `color` (hex), `radius` /
  `width` (when applicable), `visible`.

*Shape named colors (`PROPOSAL_shapes_named_colors`):*

- `Shape.set_color()` and `Shape.set_colors()` now delegate to
  `normalize_color()` so named strings, hex strings, and int values all work.

**Bug fixes**

*Batch shapes creating extra layers (`BUG_batch_shapes_extra_layers`):*

- `layer_ack` handler in `core.py` now checks `tag not in self._scene_objects`
  before registering into `_layers`; this prevents individual shape tags from
  polluting the layer registry after batch ops.

*Region.get_center() missing (`BUG_region_get_center_missing`):*

- `Region.get_center(structure_indices)` added: calls
  `msm.get(coordinates=True)` for the region's `atom_indices`, computes
  centroid via numpy, returns a `puw.quantity` in nm.

*Layer membership management (`PROPOSAL_layer_membership_management`):*

- `Layer.add(obj)` — calls `obj.set_layer_tag(self.tag)`; raises `TypeError`
  if not a `SceneObject`, `ValueError` if layer inactive.
- `Layer.detach(obj)` — calls `obj.set_layer_tag(obj.tag)` (reverts to
  self-tag); raises if obj not belonging to this layer.

**Devguide cleanup**

- Deleted `devguide/TMP_shape_layer_tag_checkpoint.md` (refactor notes
  absorbed into `architecture.md`).
- Deleted `devguide/pending_closure_2026_04_08.md` (served historical
  purpose; no longer needed).
- All resolved `pending_bugs/` and `pending_proposals/` files removed;
  only `PROPOSAL_box_merging_logic_refinement.md` remains.

Recently closed and implemented in this session (twelfth batch):

**Technical debt resolution (Debts 3–5)**

*Debt 3 — Box state migrated in `extract` / `merge`:*

- `MolSysView.__init__` gains `_box_record: dict | None = None`.
- `show_box` saves `{color, width, alpha, structure_indices}` to `_box_record`.
- `hide_box` sets `_box_record = None`.
- `reset_viewer` resets both `_box_visible = False` and `_box_record = None`.
- `_import_extracted_state` (extract.py): if source had `_box_record`, calls
  `result.show_box(**box_record, structure_indices=0)` after extraction.
- `_import_view_state` (merge.py): same, taking the box from the first source
  that had one.

*Debt 4 — Per-atom color map migrated in `extract` / `merge`:*

- `MolSysView.__init__` gains `_atom_color_map: dict[int, int] = {}`.
- `Whole.set_color_by_values` now: sets `_atom_color_map = dict(zip(...))` (full replace),
  sends `replace: True` to frontend.
- `Whole.reset_colors` clears `_atom_color_map`.
- `Region.set_color_by_values` now: merges or replaces `_atom_color_map` based on
  `replace` flag; passes `replace` to the frontend message.
- `Region.reset_colors` clears `_atom_color_map`.
- `reset_viewer` resets `_atom_color_map = {}`.
- `_import_extracted_state` (extract.py): remaps `_atom_color_map` through
  `atom_index_map` and replays as a single `set_atom_colors` message.
- `_import_view_state` (merge.py): accumulates offset-remapped color maps from
  all sources and sends one final `set_atom_colors` message.

*Debt 5 — NPT box auto-update on frame change:*

- `PlayerManager.go_to_structure`: after updating `_current_structure_index`,
  auto-calls `show_box(**_box_record, structure_indices=index)` when `_box_record`
  is set.
- `TrajectoryContext` interface gains `onPlaybackStopped?: (frame: number) => void`.
- `TrajectoryHandlers.stopTrajectoryPlayback`: after clearing timers, calls
  `onPlaybackStopped(getCurrentFrameIndex())` when playback was active.
- `ViewerController` wires `onPlaybackStopped` to emit `{ event: "trajectory_frame_changed", frame }`.
- `MolSysView._handle_frontend_event` handles `"trajectory_frame_changed"`:
  updates `_current_structure_index` and `player._is_playing`, then redraws box.

Recently closed and implemented in this session (eleventh batch):

**Merge gap: measurements + saved selections** (future debt from surgical_view_extraction):

- `_OffsetMap` class added to `merge.py`: proxy with `.get(key)` → `key + offset`,
  compatible with the `dict.get` protocol expected by `_remap_measurement_message`
  and `_remap_selection_message`.
- `_import_view_state` in `merge.py` now migrates `_measurement_history` and
  `_selection_history` from each source view by calling `result._remap_*_message`
  with an `_OffsetMap(atom_offset)` — all source atoms survive a merge, so
  no measurement or selection is ever dropped.

**Scalar Color Mapping API** (`PROPOSAL_scalar_color_mapping_api`):

- `colors.py`:
  - `scalar_to_color_list(values, palette, value_range)` — normalises scalars
    and maps each to a `0xRRGGBB` int.
  - `expand_values_to_atoms(molsys, values, element, palette, value_range, scope_atom_indices)`
    — supports any hierarchy level (`"atom"`, `"group"`, `"component"`, `"molecule"`,
    `"chain"`, `"entity"`); broadcasts the per-element color to all belonging atoms.
- `whole.py` and `regions.py` gain `set_color_by_values(values, element, palette, value_range)`
  and `reset_colors()` methods.  `Region.set_color_by_values` has a `replace` flag
  (default `False`) to merge with existing color assignments.
- TS messages: `set_atom_colors` (`{atom_indices, colors, replace?}`) and
  `clear_atom_colors`.
- `src/themes/per-atom-color.ts`: custom Mol* `ColorTheme.Provider` `"msv-per-atom"`,
  registered at plugin init via
  `plugin.representation.structure.themes.colorThemeRegistry.add(...)`.
- `StateHandlers.setAtomColors` / `clearAtomColors`: update the module-level
  `Map<atomIndex, Color>` then call
  `updateRepresentationsTheme(components, { color: "msv-per-atom" })`.
- `scalar_to_color_list` and `expand_values_to_atoms` exported from `__init__.py`.

**Unit Cell Visualization** (`PROPOSAL_unit_cell_visualization`):

- `MolSysView.show_box(color, width, alpha, structure_indices)` and `hide_box()`.
- Reads box vectors via `msm.get(_molsys, element="system", box=True)` (pint nm),
  converts to Å, builds 8 vertices + 12 edges, sends as `add_network_links` with
  fixed tag `"__msv_box"`.
- `_box_visible: bool` state tracks whether a box is shown; reset in `reset_viewer()`.

Recently closed and implemented in this session (tenth batch):

**Surgical view extraction** (PROPOSAL_surgical_view_extraction):

- `_build_atom_index_map(molsys, selection, syntax)` in `extract.py`: calls
  `msm.select()` and builds `{old_index: new_index}` for all surviving atoms.
- `_import_extracted_state(result, source, atom_index_map)`: migrates all
  scene state from source to result using the map:
  - Layers: always.
  - Regions: any region with ≥ 1 surviving atom, remapped to surviving indices.
  - Shapes / Annotations: via `source._remap_shape_message` (world-space
    shapes always pass; atom-anchored only if anchor atoms survive).
  - Measurements: via `source._remap_measurement_message` (all endpoints
    must survive).
  - Saved selections: via `source._remap_selection_message`.
  - Sections: always (world-space).
  - Global: whole representation, camera snapshot, widget controls.
  - Auto-tag counters propagated so new objects don't collide with migrated tags.
- `extract()` in `extract.py` rewritten to call `_build_atom_index_map` then
  `_import_extracted_state` after the structural extraction.
- `view.extract()` docstring updated to describe scene-state migration.

Recently closed and implemented in this session (ninth batch):

**Sectioning API — rotation gizmo (Part 3 complement)**:

- **Rim handle**: second DOM element (yellow square ↻) positioned at
  `center + u * discRadius * 0.75` in Å, projected to screen space.
- **Rotation math**: `_rotateVec(v, axis, angleDeg)` applies Rodrigues'
  formula.  `_onRimHandleDrag` maps screen `dx` → rotation around camera up,
  `dy` → rotation around camera right, at 0.4 deg/px.
- **Helpers**: `_computeDiscRadius`, `_computeDiscU`, `_getRimWorldPosA`
  extracted to share geometry between gizmo disc and rim handle position.
- `_syncHandles` / `_repositionHandles` / `setActiveSectionDrag` all updated
  to manage rim handles alongside the existing center handles.
- `_onHandleDrag` (translation) now also emits `normal` in the `section_moved`
  event for consistency.
- Python `core.py` `section_moved` handler extended to update both `point` and
  `normal` in `_section_history`, so `Section.get_normal()` stays live during
  interactive rotation.

Recently closed and implemented in this session (eighth batch):

**Sectioning API — Part 4: string resolution**:

- `add_section(point="centroid:<tag>", ...)` resolves to the centroid (nm) of
  the scene object with that tag by calling `obj.get_coordinates()` + mean.
- `add_section(normal="toward:<tag>", ...)` and `"mouth:<tag>"` resolve to the
  unit vector from the resolved `point_nm` toward that object's centroid.
- Helper methods `_resolve_point_string` / `_resolve_normal_string` /
  `_get_object_centroid_nm` added to `SceneManager`.
- Both string forms raise clear errors for coincident points or unknown syntax.

Recently closed and implemented in this session (seventh batch):

**Sectioning API — Part 3: interactive gizmos**:

- **3D disc gizmo**: `_buildDiscVertices` + `_updateSectionGizmos` in
  `scene-handlers.ts` render a translucent triangle-fan disc (32 segments,
  radius = `max(15, camera.radius * 0.3)` Å) at each active section plane.
  Tag prefix `__msv_sgizmo_` keeps gizmo shapes separate from user shapes.
- **2D drag handle**: `_createSectionHandle` adds a circular DOM element over
  the canvas (z-index 10).  Pointer events use `setPointerCapture` so drags
  don't trigger Mol*'s trackball.
- **Drag math**: screen `dx/dy` → world delta via `camera.getPixelSize` and
  camera right/up vectors → projected onto section normal → section point
  updated in nm.
- **Camera reprojection**: `_ensureCameraSubscription` subscribes to
  `camera.stateChanged` so handles follow the projected section center.
- **Python sync**: TS emits `section_moved`; Python `core.py` updates
  `_section_history` so `Section.get_point()` returns the live value.
- **`Section.enable_drag()` / `disable_drag()`**: send `set_section_drag` op
  to show/hide the drag handle.
- New message type `SetSectionDragMessage` added to `viewer-messages.ts`.
- `SceneCallbacks` extended with `registerShapeRef` callback.

Recently closed and implemented in this session (sixth batch):

**Context menu: "Create Section from Selection"**:

- New `ContextMenuAction` value `"create_section_from_selection"` in `context-menu.ts`.
- `ContextActionDetails` extended with `camera_forward?: [number, number, number]`.
- `ViewerContextMenu` constructor gains optional 5th param `getCameraDirection`.
- Button added in the active-selection section of the context menu, after
  "Create Region from Selection".
- `resolveActionDetails` computes `camera_forward` from the getter when the action fires.
- `viewer-controller.ts` passes `getCameraDirection` (computes normalized view vector
  from `canvas3d.camera.getSnapshot().target - position`) and lists the new action in
  the pass-through block (no local TS handling needed).
- `core.py` handler: reads `active_selection.atom_indices`, calls
  `_molsys.structures.get_coordinates` to get atom positions (nm), computes centroid,
  reads `camera_forward` from the event payload (falling back to `[0,0,-1]`), then
  calls `self.scene.add_section(point=centroid, normal=camera_forward)`.

Recently closed and implemented in this session (fifth batch):

**World-space sectioning API — parts 1 & 2** (PROPOSAL_advanced_sectioning_api):

- `view.scene.add_section(point, normal, *, invert, tag)` — adds a clipping plane
  to all structural representations; returns a `Section` object.
- `view.scene.remove_section(tag)` / `view.scene.clear_sections()`.
- `Section` class in `layers.py`: `get_point()`, `get_normal()`, `is_inverted()`,
  `set_point()`, `set_normal()`, `set_invert()`, `delete()`.  Mutations resend the
  full section list automatically.
- `_section_history: list[dict]` added to `MolSysView.__init__` and reset paths.
- TS op `set_sections` → `setSections` in `scene-handlers.ts`:
  - Converts `point` (nm) × 10 → Mol* Å.
  - Converts `normal` [nx,ny,nz] → `{axis, angle(deg)}` rotation from Mol*'s
    default plane normal [0,1,0] using cross/dot product.
  - Applies via `plugin.managers.structure.component.setOptions({ clipObjects })`.
  - Empty sections list resets clip to Mol* defaults.
- Pilot props confirmed from Mol* source:
  `Clip.Type.plane = 1`, normal computed in shader as
  `quaternionTransform(rotation, vec3(0,1,0))`.

Recently closed and implemented in this session (fourth batch):

**Fog visual sync failure** (BUG_fog_visual_sync_failure):

- Root cause: Mol* `CameraFogParams.intensity` is a 1–100 integer scale, but the Python
  API was sending 0.0–1.0 floats directly — resulting in values < 1 that Mol* treated as
  nearly zero fog.
- Fix: `setFog` in `scene-handlers.ts` now scales `intensityRaw * 100` (clamped to 1–100)
  before passing to `canvas3d.setProps({ cameraFog: ... })`.
- Python default changed from `0.5` to `0.15` to match Mol*'s built-in default (15/100).

**`view.navigation` renamed to `view.player`** (PROPOSAL_rename_navigation_manager):

- `molsysviewer/navigation.py` → `molsysviewer/player.py`; `NavigationManager` → `PlayerManager`.
- `view.navigation = NavigationManager(self)` → `view.player = PlayerManager(self)` in `__init__`.
- All internal delegate references updated. No aliases left.

**`view.camera` manager** (PROPOSAL_camera_manager_api):

- `molsysviewer/viewer/camera.py` — `CameraManager` class, wired to `view.camera`.
- `molsysviewer/viewer/utils.py` — shared `quantity_value_in_unit` helper (replaces local
  function in `core.py`).
- Methods: `zoom`, `focus_selection`, `focus_region`, `focus_on_object(tag)`, `reset`,
  `get_snapshot`, `set_snapshot`, `mode` (property), `set_mode`.
- New TS op `set_camera_mode` → `setCameraMode` in `scene-handlers.ts` via
  `canvas3d.setProps({ camera: { mode } })`.
- `view.zoom`, `view.focus_selection`, `view.focus_region`, `view.reset_camera`,
  `view.get_camera_snapshot`, `view.set_camera_snapshot` kept as one-liner delegates
  (no deprecation period — breaking change).

**Custom background colors** (PROPOSAL_custom_background_colors):

- `view.scene.set_background(color)` now accepts any value that `normalize_color()` handles:
  ``"light"``/``"dark"`` (existing presets), hex string ``"#f0f0f0"``, integer ``0xffffff``,
  named CSS/Mol* color ``"skyblue"``.
- Non-preset values send a new op `set_background_color` → `setBackgroundColor` in
  `scene-handlers.ts`, which sets `renderer.backgroundColor` directly.

**Lighting and clipping API expansion** (PROPOSAL_lighting_api_expansion):

- `view.scene.set_lighting(ambient, diffuse, specular)` — maps to `renderer.ambientIntensity`
  and `renderer.lightIntensity` via new TS op `set_lighting` → `setLighting`.
- `view.scene.set_projection(mode)` — delegates to `view.camera.set_mode(mode)`.
- `view.scene.set_clip_planes(near, far, min_near)` — maps to `cameraClipping` via new TS
  op `set_clip_planes` → `setClipPlanes`.
- JS rebuilt with all new handlers.

Recently closed and implemented in this session (third batch):

**`view.navigation` module** (PROPOSAL_navigation_module):

- `molsysviewer/navigation.py` — `NavigationManager` class, wired to `view.navigation`
- Read-only properties: `index`, `n_structures`, `is_playing`
- Mutable-default properties: `fps`, `step_size`, `mode`, `direction`
- Navigation: `go_to_structure(index)`, `go_to_first()`, `go_to_last()`,
  `step_forward(n)`, `step_backward(n)`
- Playback: `play(fps, mode, direction, step_size)`, `pause()`
- Setters: `set_fps(fps)`, `set_step_size(step_size)`, `set_mode(mode)`,
  `set_direction(direction)`
- Existing top-level methods kept as one-liner delegates:
  `view.set_structure()` → `navigation.go_to_structure()`,
  `view.play()` → `navigation.play()`,
  `view.pause()` → `navigation.pause()`,
  `view.set_play_speed()` → `navigation.set_fps()`

**`view.get_coordinates` / `view.set_coordinates`** (PROPOSAL_coordinates_api — fully closed):

- `view.get_coordinates(selection, structure_indices, syntax)` — resolves
  `selection` with `msm.select()`, then calls
  `_molsys.structures.get_coordinates(indices, structure_indices)`; returns
  puw quantity ``(n_structures, n_atoms, 3)`` in nm.
- `view.set_coordinates(coordinates, selection, structure_indices, syntax)` —
  same resolution path, calls
  `_molsys.structures.set_coordinates(indices, structure_indices, value)`,
  then rebuilds the canvas via `_rebuild_view_from_current_molsys`.
  Operates only on `_molsys`.
- `Shape.set_coordinates` now fully covers all shape types including
  `add_pocket_blob`, `add_pocket_surface`, `add_alpha_sphere_set` via a new
  `_apply_pocket_centers_update` helper (deep-merges into
  `options["alpha_spheres"]["centers"]` without losing other sub-keys).
- `Annotation.get_coordinates()` — returns the centroid of the anchor atoms
  (from `_annotation_history` options `atom_indices`) at the current frame as
  a puw ``(3,)`` in nm.
- `Annotation.set_coordinates()` — raises `NotImplementedError`; annotations
  are atom-anchored; use `view.annotations.set_group_index()` instead.
- `Measurement.get_coordinates()` — returns puw ``(n_endpoints, 3)`` in nm,
  resolving `endpoint_atom_indices` (or fallback `picks_atom_indices`) from
  `_measurement_history` at the current frame.  Read-only by design.

Recently closed and implemented in this session (second batch):

**Measurement focus overzoom** (BUG_measurement_focus_overzoom):

- `Measurement.focus()` in `layers.py` now retrieves the 3D coordinates of the
  endpoint atoms via `msm.get(coordinates=True)`, computes a bounding sphere
  with `_bounding_sphere_nm`, and sends a `zoom_to_position` op (same path as
  `Shape.focus()`).  Falls back to `view.zoom(selection=flat)` if coordinates
  are unavailable.
- The old code called `view.zoom(atom_indices=flat)` which (a) passed a
  non-existent keyword argument and (b) would have zoomed to the whole bounding
  box of all picks atoms — which for a centroid measurement can span two
  residues far apart.

**Measurement value units missing** (BUG_measurement_info_units_missing):

- `MeasurementsManager.info()` in `measurements.py` now wraps the raw float
  value from the history with `puw.quantity()`: `"angstrom"` for distances,
  `"degrees"` for angles and dihedrals.
- Added `from . import pyunitwizard as puw` to `measurements.py`.

**Region vanishes on set_representation** (BUG_region_update_vanishing):

- `setRegionRepresentation` in `state-handlers.ts` was calling
  `removeStateObject(reprRef)` with `removeParentGhosts: true` for each old
  representation.  When the last representation was removed, Mol* silently
  cascade-deleted the parent `StructureComponent` as a ghost.  The subsequent
  `buildRepresentation` call then targeted a dangling ref and failed silently
  (`revertOnError: false`), leaving the region empty.
- Fix: delete the entire component ref first (which also removes all
  representation children in one sweep), then rebuild component + representation
  from `entry.atomIndices` using `addRepresentation` — the same pattern used by
  `createRegion`.  Restores `entry.hidden` state after the rebuild.

**Camera locks after set_representation** (BUG_representation_camera_lock):

- `setGlobalRepresentation` in `state-handlers.ts` now saves the current camera
  snapshot at the start of the method and restores it with
  `PluginCommands.Camera.SetSnapshot` after `handleShowHideGlobal`.  This
  prevents Mol*-internal camera adjustments during the representation swap (e.g.
  a tight `minRadius` calculation on the new empty/licorice scene) from leaving
  the camera unable to zoom out.

**Shape API unification** (PROPOSAL_shape_api_unification):

- `SphereShapes.add_sphere` in `shapes/spheres.py` is now polymorphic:
  - Single center (3-D point): same as before, returns one `Shape`.
  - List of centers: batch path, returns `list[Shape]`; all spheres share one
    `layer_tag` so they can be managed as a group.
- Batch tag-naming rules:
  - `tag=None` → auto-generate `shapeN` names (sequential counter).
  - `tag="prefix"` → generate `prefix1`, `prefix2`, …
  - `tag=[...]` → 1:1 mapping (must have length == number of centers).
  - `layer_tag` → shared layer; auto-generates `layerN` if omitted.
- `SphereShapes.add_spheres` is now a deprecated wrapper that calls `add_sphere`
  with the list of centers and emits `DeprecationWarning`.
- `ShapesManager.add_sphere` updated to expose the unified signature.
- `viewer.js` rebuilt from updated TypeScript sources.

**`add_spheres` removed, `Shape.get_coordinates` / `set_coordinates` added**:

- `SphereShapes.add_spheres` deleted entirely (no deprecation period — no
  external users); `ShapesManager.add_spheres` entry point also removed.
- `Shape.get_coordinates()` added to `layers.py`: dispatches on the stored
  shape op and returns a `puw` quantity in nm:
  - sphere → `(3,)` center
  - channel tube / pharmacophore / anisotropy ellipsoids / displacement
    vectors → `(n, 3)` centers
  - network links → `(n, 2, 3)` coordinate pairs
  - triangle faces → `(n, 3, 3)` vertex triples
  - tetrahedra → `(n, 4, 3)` vertex quads
  - pocket blob / surface → `(n, 3)` alpha-sphere centers
- `Shape.set_coordinates(coordinates)` added: same dispatch, routes to the
  existing `_apply_*_update` helpers.

**New pending proposals**:

- `PROPOSAL_coordinates_api.md` — unified `get_coordinates` / `set_coordinates`
  for molecular system atom selections, shapes (gaps remaining), annotations,
  and measurements (read-only endpoints).
- `PROPOSAL_navigation_module.md` — `view.navigation` manager that encapsulates
  all structure-navigation state and methods (`current_index`, `go_to()`,
  `play()`, `pause()`, `fps`, `step`, `direction`, `loop`); existing top-level
  methods become thin delegates.

Recently closed and implemented in this session (first batch):

**Canvas picking for multi-chain and multi-load systems** (BUG_picking_broken_after_rebuild):

- `group_PDB` column in `createAtomSiteTable` (structure.ts) was hardcoded
  `"HETATM"` for all atoms. Mol*'s "auto" preset uses `group_PDB = "ATOM"` to
  detect polymer chains; with all-HETATM payloads it cannot build the standard
  cartoon representation, which caused one chain of a dimer to be rendered but
  not properly integrated into the pick buffer. Fix: derive `group_PDB` from
  `group_type` (atoms with `group_type` containing "protein", "aminoacid",
  "peptide", "nucleic", "dna", "rna", or "nucleotide" become `"ATOM"`;
  everything else stays `"HETATM"`).
- `buildGroupItemsFromStructure` (active-selection.ts) only iterated the
  FIRST atomic unit, so only chain A's residues ended up in `allAvailableItems`.
  Range selection and navigate-panel navigation were broken for all subsequent
  chains. Fix: collect the set of atom indices across ALL atomic units, then
  iterate the model's residue table skipping groups not present in the
  structure.
- `setFromAtomIndices` (active-selection.ts) also searched only the first
  atomic unit, silently dropping atoms from second+ chains when Python called
  `set_active_selection` (e.g. via `view.select()` or saved-selection recall).
  Fix: iterate ALL atomic units, building per-unit loci elements.
- `atomIndicesToLoci` (viewer-controller.ts) searched only the first atomic
  unit, so `syncVisualSelection`, `focusCurrentSelection`, and `focusTarget`
  all produced `null` for atoms in chain B+. The canvas received no highlight
  call even though the Python backend reported the selection correctly. Fix:
  same multi-unit pattern — iterate all `Unit.isAtomic()` units with
  `SortedArray.ofSortedArray(matched)`.
- `makeLociForItem` (group-strip.ts) same single-unit bug: hover highlights
  and Navigate-panel clicks for chain B+ residues showed nothing in the
  canvas. Fix: same multi-unit iteration.
- `load_from_molsysmt.py`: fixed stale `_get_n_atoms()` usage (private method;
  was already deleted from `core.py`); replaced with `view._molsys.get_n_atoms()`.
- `viewer.js` rebuilt from the updated TypeScript sources.

**Load accounting and additive regions** (BUG_load_accounting_failure,
BUG_add_method_missing_auto_regions):

- `_get_molsys_n_atoms()` deleted entirely — was using a private/nonexistent
  method (`_get_n_atoms()`) that failed silently inside the `@signal` decorator,
  leaving `_load_blocks` empty after the first `load()`
- All four call sites replaced with `obj.get_n_atoms()` (for `_molsys` objects)
  or `added_molsys.get_n_atoms()` (for intermediate merge targets)
- `_rebuild_view_from_current_molsys` also updated to use `get_n_atoms()`
- `registry_cleared` frontend event handler emptied to a `pass` — it was
  destructively resetting `_load_blocks` and `_regions` after Python had already
  rebuilt them synchronously during the rebuild path
- Six regression tests added in `tests/molsysviewer/test_molsysview_load.py`
  covering: first-load block accounting, no regions on first load, race condition
  survival for blocks and regions, two- and three-block additive load scenarios

**Rich display for `view.info()`** (PROPOSAL_rich_display_for_info):

- `ViewerInfo` class added to `molsysviewer/viewer/core.py` (just before
  `MolSysView`)
- `info(source='all')` now returns a `ViewerInfo` instance instead of a raw dict
- `_repr_html_()` renders both sections (Molecular system / Viewer) sequentially
  with `<h4>` headings and inline Styler HTML; plain `__repr__` preserved for
  non-notebook contexts
- `__getitem__` and `keys()` keep the old dict-like access pattern
- `ViewerInfo` exported from `molsysviewer.viewer` and `molsysviewer`
- Bug fix: `_repr_html_()` was calling `to_html()` on each section instead of
  `_repr_html_()`; `_repr_html_()` is the correct Jupyter display protocol
  method for pandas Styler objects — using `to_html()` caused sections to render
  unstyled or produce empty output in some pandas versions

Previously closed and implemented:

Recently closed and implemented in first operational slices:

**Trajectory and structure control** (`PROPOSAL_trajectory_and_structure_control`):

- `view.current_structure_id` — reads the MolSysMT structure ID at the current
  trajectory index
- `view.set_structure(index)` — sends `set_trajectory_frame` op, updates
  `_current_structure_index`
- `view.play(fps, mode, direction, step)` — starts trajectory playback
- `view.pause()` — stops trajectory playback
- `view.set_play_speed(fps)` — adjusts playback speed without restarting

**Shape registry dict-like interface** (part of `PROPOSAL_shape_layer_separation_and_naming`):

- `view.shapes.keys()` — delegates to `tags()`
- `view.shapes.values()` — iterates `get()` for each tag
- `view.shapes.items()` — returns `(tag, shape)` pairs

**Shape.focus()** (part of `PROPOSAL_shape_layer_separation_and_naming`):

- `shape.focus(duration_ms, extra_radius)` — computes a bounding sphere from
  stored shape geometry (all op families supported: spheres, pockets, channels,
  ellipsoids, pharmacophore, links, vectors, triangles, tetrahedra), converts
  nm → Å, sends `zoom_to_position` op
- `zoom_to_position` TS op added: generic camera focus taking `center` (Å) and
  `radius` (Å); dispatched through `SceneHandlers.zoomToPosition()` via
  `plugin.managers.camera.focusSphere()`

**Workspace switch toast** (`BUG_addon_workspace_confusion`):

- `ViewerController.showToast(message, durationMs)` — self-contained CSS toast
  injected into the viewer host element
- `selectWorkspace()` now calls `showToast` when the active workspace changes

**MolSysMT integration decision** (`PROP_MolSysMT_integration`):

- closed as architecture decision: MolSysMT integration stays behind a future
  dedicated addon layer; current `view.convert(...)` path is the interim bridge
- no new surface needed; the existing implementation slice satisfies the proposal

**ElasNetMT addon integration** (`PROPOSAL_elasnetmt_addon_integration`):

- closed against the existing overlay primitive set (links, displacement vectors,
  anisotropy ellipsoids); the addon plan lives in `devguide/elasnetmt_addon_plan.md`
- no new primitives needed before ElasNetMT can start using the current host

**Headless image export** (`PROPOSAL_headless_export_support`):

- `view.export.image(...)` now works without a live Jupyter frontend
- three-layer fallback in `_export_image_impl`:
  1. live frontend (anywidget event round-trip) — existing path
  2. Qt WebEngine headless backend — primary offline path, using
     `PySide6_uibcdf` or `PySide6` with `QT_QPA_PLATFORM=offscreen` +
     `QTWEBENGINE_CHROMIUM_FLAGS=--use-gl=swiftshader --disable-gpu`
  3. playwright fallback — browser binary assumed present (shared with e2e
     suite); no mandatory install; clear error message if missing
- `_build_lite_html` JS template now sets
  `data-molsysviewer-rendered` on `#molsysviewer-root` after `boot()` + 2000ms
  settle; used by both Qt polling and playwright `wait_for_selector`
- `view.export.html(mode='lite')` and `mode='standalone'` confirmed fully
  headless-capable (Python-side only, no frontend required)
- playwright is NOT a mandatory package dependency; users install it when needed

Previously closed from `pending_proposals` and `pending_bugs` (earlier sessions):

- `MolSysView.convert(...)`
- active-selection-driven removal from the canvas/context menu
- repeated `load(...)` with:
  - `mode="add"`
  - `mode="replace"`
  - `mode="append_structures"`
  - `mode="auto"`

### Additive load logic: current state

The repeated-`load()` proposal is now implemented in its first operational
slice.

Reference status document:

- `devguide/load_modes_and_append_structures_status.md`

Implemented now:

- `view.load(..., mode="add")` is the current default
- `view.load(..., mode="replace")` resets the scene before loading
- `view.load(..., mode="append_structures")` is now implemented as the
  explicit structural-append path
- `view.load(..., mode="auto")` is now implemented as a conservative
  first-version heuristic
- first load:
  - initializes `whole`
  - records block 0 in `_load_blocks`
  - does not create an automatic region
- second additive load:
  - structurally adds the new system
  - back-fills an automatic region for block 0
  - creates an automatic region for block 1
- third and later additive loads:
  - create only the new automatic load-region
- automatic load-region naming uses:
  - the load label when present
  - otherwise `Load1`, `Load2`, ...
- `view.add(...)` remains the lower-level structural primitive:
  - merges into `_molsys`
  - updates `_load_blocks`
  - does not create automatic load-regions
- `view.load(..., mode="append_structures")` follows a first-version
  conservative policy:
  - empty viewer -> clear error
  - topology-only `_molsys` -> allowed
  - topology + structures -> append frames
  - no `_load_blocks` changes
  - no automatic load-regions
- `view.load(..., mode="auto")` currently resolves as:
  - empty viewer -> `replace`
  - same atom count + no topology in the input -> `append_structures`
  - same atom count + matching topology -> `append_structures`
  - different atom count -> `add`
- reset paths now clear additive-load bookkeeping

Internal state now uses:

- `_empty`
- `_load_blocks`

Each load block currently tracks:

- `index`
- `label`
- `n_atoms`
- `start`
- `stop`
- `region_tag`

Adjacent cleanup done while landing this slice:

- `tools.basic.add(...)` now forwards `label=...`
- the minimal `load()` integration path is more robust against missing
  optional hierarchy attributes in small MolSysMT inputs
- a few `arg_digestion` callers were normalized for the `viewer/` package split
  where tests were already touching that surface

What remains for this front:

- decide whether additive-load block metadata needs explicit provenance/source
  fields
- decide how much of `_load_blocks` should become part of a public inspection
  surface later
- add broader export/replay tests for multi-load scenes beyond the first
  targeted regression slice
- refine the first-version detection/execution split for structural append if a
  lighter MolSysMT inspection path proves preferable in practice
- decide whether `mode="auto"` should consider structure-count compatibility
  more explicitly before choosing `add`

### Visual API / styling: checkpoint before switching focus

The Python-side color subsystem now has an explicit baseline module:

- `molsysviewer/colors.py`

This first slice is intended to make color handling coherent without forcing an
immediate public-API rewrite across all shape families.

Implemented now:

- named colors normalized from the Mol* color table
- flexible single-color parsing:
  - integer `0xRRGGBB`
  - hex strings
  - RGB tuples/lists
  - named strings such as `red` or `light_blue`
- continuous palette registration and resolution
- categorical scheme registration and resolution
- adaptation from Matplotlib colormaps on the Python side
- public access through:
  - `molsysviewer.colors`
  - `molsysviewer.normalize_color(...)`
  - `molsysviewer.normalize_colors(...)`
  - `view.colors`
- built-in categorical presets now available in the registry:
  - static schemes:
    - `pharmacophore_default`
    - `element_cpk`
    - `secondary_structure_default`
  - generated schemes:
    - `chain_default`
    - `pocket_default`
  - categorical base palette:
    - `categorical_default`
- first shape-family migrations on top of the new model:
  - `displacement_vectors`
    - `color_by`
    - `palette`
  - `channel_tube`
    - `color_by`
    - `palette`
  - `anisotropy_ellipsoids`
    - `color_by`
    - `palette`
  - `pharmacophore`
    - `color_scheme`
    - `color_table`
  - `links`
    - `color_by`
    - `color_table`

Development reference:

- `devguide/molstar_color_strings.md`

Status of this front:

- the color subsystem is no longer just an internal helper layer
- structural styles, curated schemes, advanced Mol* themes, and public
  discovery/catalog APIs are now all present
- this front is in a good checkpoint state and does not block switching to a
  different area of the codebase

What remains for this front, if work resumes later:

- decide how aggressively to migrate existing shape APIs from `color_mode` /
  `color_map` toward a cleaner `color_by` / `palette` / `color_scheme` model
- decide whether these built-in presets are enough as a first public set or
  whether more should be promoted now (`residue/group`, `molecule type`, etc.)
- continue the progressive migration family by family rather than rewriting the
  whole shape surface at once
- decide whether the next migration slice should focus on:
  - remaining shape families with scalar coloring,
  - built-in categorical schemes,
  - or structural representations/styles beyond the custom-shape layer

### Structural color schemes: current state

The new color model is no longer limited to custom shapes.

Implemented now:

- structural `Style` / `whole.set_representation(...)` calls can carry
  `params.color_scheme`
- structural `Style` / `whole.set_representation(...)` calls can also carry
  `params.size_scheme`
- advanced structural escape hatches are now available:
  - `params.molstar_color_theme`
  - `params.molstar_size_theme`
- advanced theme values accept either:
  - a plain Mol* theme name string
  - or a dictionary with:
    - `name`
    - `params`
- the current public structural color-scheme bridge maps:
  - `element_cpk` -> Mol* `element-symbol`
  - `secondary_structure_default` -> Mol* `secondary-structure`
  - `chain_default` -> Mol* `chain-id`
  - `residue_name` -> Mol* `residue-name`
  - `molecule_type` -> Mol* `molecule-type`
  - `entity_default` -> Mol* `entity-id`
  - `illustrative_default` -> Mol* `illustrative`
- the current public structural size-scheme bridge maps:
  - `uniform` -> Mol* `uniform`
  - `physical` -> Mol* `physical`
  - `uncertainty` -> Mol* `uncertainty`
- this already works both for direct global representations and for preset-based
  application paths for color schemes
- size schemes are currently active on the direct global-representation path
- replay/export keeps the public `color_scheme` parameter rather than leaking
  Mol* internals into the Python-side history
- replay/export also keeps the public `size_scheme` parameter
- replay/export also keeps the advanced `molstar_color_theme` and
  `molstar_size_theme` parameters when used
- `view.styles` now exposes query helpers for the curated public structural
  scheme catalogs:
  - `structural_color_schemes()`
  - `structural_color_scheme_records()`
  - `structural_size_schemes()`
  - `structural_size_scheme_records()`
- `view.styles` now also exposes public discovery catalogs for the broader
  visual surface:
  - `representation_types()`
  - `representation_type_records()`
  - `representation_param_schema(representation)`
  - `representation_param_schema_records()`
  - `representation_presets()`
  - `representation_preset_records()`
  - `molstar_color_themes()`
  - `molstar_color_theme_records()`
  - `molstar_size_themes()`
  - `molstar_size_theme_records()`
- the built-in style catalog now includes structural color variants such as:
  - `cartoon-secondary-structure`
  - `cartoon-chain`
  - `ball-and-stick-element-cpk`
  - `spacefill-element-cpk`
- curated structural schemes have priority over advanced Mol* theme escape
  hatches when both are provided

What remains for this front:

- decide which additional Mol* structural themes deserve promotion into the
  public API beyond the current curated set
- decide whether preset-based structural application should also gain explicit
  size-theme support or whether direct-representation support is sufficient
- decide how broad the curated representation-parameter schemas should become
  relative to the underlying Mol* parameter surface

### Suggested next focus

The visual/style front is now in a strong checkpoint state.

The next work does not need to continue here immediately.
If development switches to a different area, this file should be treated as the
handoff point for resuming visual/styling work later.

### MolSysMT-facing view operations: current state

Two MolSysMT-oriented viewer operations are now implemented in a first public
slice:

- `view.convert(...)`
- `view.remove(...)` through active-selection canvas interaction

Implemented now:

- `view.convert(...)` exists as a public method
- `molsysviewer.tools.basic.convert(...)` exists as the functional wrapper
- the current implementation delegates conversion to the molecular system
  currently stored in the viewer
- this is intentionally a first operational version:
  - it already matches the most common expectation for molecular and
    trajectory-like target forms
  - it does not preclude richer future conversions from `MolSysView` itself
    once MolSysMT exposes them
- the active-selection context menu now exposes:
  - `Remove Selected Atoms`
- that action now bridges to Python and executes:
  - `view.remove(selection=<active atom indices>)`
  - followed by `active_selection.clear()`

Why this is still a first slice:

- `convert(...)` is still implemented in the main viewer surface instead of a
  future dedicated MolSysMT-facing addon layer
- canvas removal is currently selection-driven, not a broader generalized
  destructive edit surface for arbitrary interaction targets

What remains for this front:

- decide whether `convert(...)` and other MolSysMT-backed operations should
  eventually move behind a dedicated integration/addon layer
- decide whether richer viewer-aware conversion targets should be promoted once
  MolSysMT supports them directly
- expand destructive canvas editing beyond active selection only if that proves
  worth the added interaction complexity

### `MolSysView.info()`: current state

`view.info()` is no longer only a direct proxy to `molsysmt.basic.info(...)`.

Implemented now:

- `view.info(source="molsys")`
  - preserves the molecular-system-oriented path
- `view.info(source="view")`
  - returns a notebook-friendly Pandas table for viewer-state inspection
- `view.info(source="all")`
  - returns both sections together as:
    - `{"molsys": ..., "view": ...}`
- `output_type` is now supported for `view.info(...)` and the
  `molsysviewer.tools.basic.info(...)` wrapper
- supported `output_type` values are:
  - `"styler"` (default)
  - `"dataframe"`
  - `"dictionary"`

The current viewer-side summary includes compact rows for:

- `whole`
- `styles`
- `regions`
- `layers`
- `shapes`
- `annotations`
- `measurements`
- `selections`
- `active_selection`

What remains for this front:

- decide whether `source="all"` should remain a mapping of two outputs or gain
  a more unified presentation later
- decide whether the viewer-side table should grow richer details for some
  sections or stay intentionally compact

### Viewer / Scene Refactor: current state

The `viewer` refactor and the `shape/layer/tag` model are no longer only an
architecture discussion. The operational base is already implemented:

- `molsysviewer/viewer.py` has been replaced by the `molsysviewer/viewer/`
  package
- `Layer` is now the grouping abstraction
- `view.shapes[...]`, `view.annotations[...]`, `view.measurements[...]`, and
  `view.layers[...]` are already part of the active public model
- `layer_tag` is explicit and reproducible
- the first rich mutability slice already exists for `sphere`, `links`, and
  `triangle_faces`
- measurements already follow the new stable, manageable object model

The operational checkpoint for this front is:

- `devguide/TMP_shape_layer_tag_checkpoint.md`

What remains is no longer “resolve the architecture”, but rather broaden
coverage and reduce inherited compatibility paths:

- extend rich mutability to more shape families
- continue removing assumptions from the old model
- keep strengthening scene-object identity/interaction semantics in the frontend

### Phase E — Standalone: current state

**Phase E in `molsysviewer` is materially complete.**

- `molsysviewer/standalone_qt.py` imports directly from `PySide6_uibcdf`.
  `QFileDialog` and `QMessageBox` are restored and functional.
- The conda-native recipe (`_3` builds) is published on the `uibcdf` channel
  and validated. The standalone opens, loads systems, and the menus work.
- `devguide/standalone_supported_environment.md` documents the 5 packages
  involved (3 explicit installs + 2 automatic dependencies).
- `standalone_packaging_strategy.md` closes A2 as a completed decision.
- The host satisfies the pre-`1.0.0` gate defined in the roadmap.

**There is no pending work in this repo for Phase E.**

The `QtQuick` blocker mentioned in older checkpoint versions is already
resolved in the sibling repo `../pyside6-essentials-uibcdf`:
`PySide6/QtQuick/typesystem_quick.xml` has the required `remove="all"`
entries for `QQuickItem::flags()`,
`QQuickRenderTarget::fromOpenGLTexture(...Flags...)`, and the other instances
of the same incorrect flag-type pattern.

If sibling repos produce improved builds in the future, the only expected
change here is updating version pins in
`standalone_supported_environment.md` and validating the smoke import.

### Familia de packaging (referencia)

| Paquete | Build | Rol | Cómo llega |
|---------|-------|-----|------------|
| `shiboken6-uibcdf 6.9.2` | `_3` | bridge Python/C++ | install explícito |
| `pyside6-essentials-uibcdf 6.9.2` | `_3` | bindings Qt core | install explícito |
| `pyside6-addons-uibcdf 6.9.2` | `_3` | bindings Qt addons (WebEngine) | install explícito |
| `qt6-positioning-uibcdf 6.9.2` | `_0` | runtime Qt Positioning | dep automática de addons |
| `qt6-webengine-uibcdf 6.9.2` | `_0` | runtime Qt WebEngine | dep automática de addons |

Sibling repos: `../shiboken6-uibcdf`, `../pyside6-essentials-uibcdf`,
`../pyside6-addons-uibcdf`, `../qt6-positioning-uibcdf`, `../qt6-webengine-uibcdf`.

- `0.16.0` should now be read as the checkpoint where:
  - the mature product stories were verified together as one coherent release
    surface
  - the JS interaction/active-selection/annotation path was hardened back to a
    green unit suite
  - the route to `1.0.0` stopped being blocked by shared-runtime hardening and
    shifted more clearly toward final standalone/distribution questions
  - Phase B should now be treated as done enough unless a new realistic add-on
    path reveals another structural host gap
  - Phase E should now be treated as the main execution focus toward `1.0.0`
  - the standalone Qt spike now also has an explicit supported development
    recipe in `devguide`, so the conda/pip boundary no longer lives partly in
    chat history
  - the remaining standalone packaging/distribution question is now also split
    out explicitly from host implementation work, so Phase E can proceed
    without pretending that the final installer story is already decided

- `0.14.0` should now be read as the checkpoint where:
  - Phase D stopped being only intention and gained first real tightening
    slices
  - the product became materially easier to teach without chat history
  - figure export, add-on workspaces, and panel mode now have both user-facing
    guidance and matching smoke/regression coverage

- `0.13.0` should now be read as the checkpoint where:
  - the shared workbench/runtime became coherent enough to stop dominating the roadmap
  - the reference add-on path became teachable end to end
  - and figure export stopped being a thin helper and became a small but real subsystem

- Continue feature implementation toward 1.0 on top of the now-hardened runtime/contracts layer.
- Treat `0.12.0` as the end of the "prove the platform exists" stage.
- Treat `0.13.0` as the end of the first serious consolidation wave across:
  - workbench/workspace runtime
  - add-on onboarding
  - figure export
- The current stage is now:
  - finish squeezing the value out of the now-stronger add-on/runtime path,
  - treat figure export as a deliberate subsystem rather than a side helper,
  - and leave standalone as the final major pre-`1.0.0` host push.
- Support-library hardening is also part of the current stage:
  - `workspace_catalog()` and `workspace_runtime()` now belong to the structured
    SMonitor contract layer, not just the thin query surface
  - `new_view(...)` and the main export paths now also emit richer structured
    SMonitor context, which makes fast QA around scripted load/export flows more
    informative
  - `molsysviewer.config` PyUnitWizard setters now follow the same
    `@digest()`/`@signal()` rule as the rest of the main public API
  - `depdigest` is now explicit in the local hard support stack rather than an
    implicit bootstrap dependency
  - `depdigest` now also has a first concrete `MAPPING` layer for primary
    MolSysMT input forms used by MolSysViewer (`molsysmt.MolSys`, `h5msm`,
    `pdb`) instead of remaining completely flat
  - the ArgDigest surface now also covers stable query/delegation wrappers such
    as `contains(...)`, `is_composed_of(...)`, and `extract(...)` in the main
    viewer path
  - the criterion is now explicit:
    - public methods with a real named contract should digest;
    - pure `*args/**kwargs` forwarders should stay observable via `@signal()`
      but should not introduce fake digestion surfaces
- The standalone question should now be treated as more concrete than before:
  - browser-hosted `standalone 0` is already good enough as a teaching bridge
  - the final pre-`1.0.0` standalone host should now be planned as a dedicated
    application shell, not just "open HTML in browser"
  - the current preferred direction is:
    - Python app shell
    - embedded webview
    - likely `PySide6 + Qt WebEngine`
  - keep that host decision explicit in:
    - `devguide/standalone_host_plan.md`
- The first implementation step for Phase E should now also be treated as
  decided:
  - begin with a thin Qt prototype
  - use `PySide6`
  - embed the existing runtime in `QWebEngineView`
  - preserve `Core` and `panel mode` semantics unchanged
  - keep the technical mini-plan in:
    - `devguide/standalone_qt_prototype_plan.md`
- Phase E is now no longer only planned:
  - the first thin Qt host prototype has started
  - it currently adds:
    - a dedicated `QMainWindow`
    - embedded `QWebEngineView`
    - a minimal menu bar
    - reuse of the current standalone HTML/runtime path
  - it should still be treated as a prototype, not as the final standalone host
  - the first real Qt spike has now also validated that:
    - the host can run successfully with a coherent `pip` PySide6 stack
    - the viewer should use the `lite` runtime path in Qt rather than the AMD
      widget-manager export path
    - final standalone packaging is now clearly an environment-recipe problem,
      not just a host-implementation problem
  - the Qt host now also owns first real app-level actions:
    - `View -> Navigate`
    - `View -> Workbench`
    - `View -> Close Panel Mode`
    - `File -> Open File`
    - `File -> Load Demo` submenu
    - `File -> Load PDB ID`
    - `File -> Load Source`
    - `File -> Recent` with persisted recent sources
    - `File -> Restore Last Source`
    - `Export -> Export HTML`
    - `Export -> Export Figure`
    - `Help -> About`
    - `Help -> Show Current Source`
    - `Help -> Reload Last Source`
  - the thin host now also persists a small shell-state layer that helps it
    feel application-like without leaking viewer logic into Qt:
    - recent sources
    - last source
    - last window size
  - the Qt host `Recent` menu now behaves more like application chrome and less
    like raw state dump:
    - grouped by source kind
    - explicit clear action
  - the thin Qt host now also handles load/export failures more like an
    application shell:
    - status-bar feedback
    - host-owned error dialog
  - the standalone Qt host now also gives a clearer startup feel:
    - explicit `Ready` status when a system is already loaded
    - explicit quickstart-style status when the host opens empty
  - the shared empty-host presentation now also teaches the app-shell flow more
    honestly:
    - `File` menu loader path is visible
    - CLI/browser-hosted startup remains visible too
  - the thin Qt host now also owns a first small keyboard-shortcut layer for
    app-level actions:
    - open file
    - restore last source
    - navigate/workbench switching
    - close panel mode
    - export actions
  - the Qt host help surface is now more cohesive:
    - stronger `About`
    - clearer current-source readback
    - explicit host-info summary with shortcuts and shell state
  - the notebook/runtime feedback path is now slightly stronger too:
    - `workspace_runtime(pretty=True)` gives a readable JSON snapshot for quick
      Jupyter diagnostics
    - the same `pretty` choice is now visible in the structured SMonitor
      timeline for that query
  - the thin Qt host now also supports returning to an empty shell without
    closing the app:
    - `File -> New Empty Host`
    - shortcut `Ctrl+N`
  - the next Phase E work should now be judged against an explicit
    pre-`1.0.0` host-sufficiency gate rather than against open-ended polish:
    - clear startup/empty-host flow
    - credible shell-owned load paths
    - return to empty host
    - app-level view/export affordances
    - small and useful shell persistence
    - non-silent error handling
    - still a thin host with no forked viewer semantics
  - work that should not be used to keep Phase E open by inertia:
    - more generic shell chrome
    - speculative session/project management
    - packaging closure before the host itself is judged sufficient
  - the current reading after the latest host slices is now:
    - that host-sufficiency gate is materially satisfied
    - the thin Qt host is no longer the main standalone unknown
    - the main remaining standalone uncertainty before `1.0.0` is now the
      supported packaging/distribution route
    - more host work should now be driven only by a real QA/runtime gap, not by
      generic shell polish
  - the packaging evaluation is now also more concrete:
    - A1:
      - conda-native route with standard package names
    - A2:
      - conda-native standalone runtime with specific package names
    - B:
      - hybrid conda+pip route as fallback/bridge only
  - the provisional reading is now:
    - if UIBCDF has to cover the Qt/WebEngine gap itself before upstream
      catches up, A2 currently looks safer than A1
    - and if A2 is pursued, the current naming preference is now:
      - stay close to the standard package roots
      - differentiate with a suffix rather than a completely unrelated name
    - the first technical packaging attempt should now be narrower still:
      - try a minimal WebEngine add-on slice first
      - only escalate to a broader A2 fork if the add-on hypothesis fails
    - the current environment comparison now also makes that add-on hypothesis
      more concrete:
      - `pyside6` and `qt6-main` from conda-forge look partially usable
      - the missing layer is concentrated in WebEngine
      - the first add-on experiment will likely need both:
        - top-level `PySide6/QtWebEngine*.abi3.so` bindings
        - and the matching native Qt WebEngine runtime under `PySide6/Qt`
    - the first scratch overlay has now tightened that reading further:
      - a `webengine-only` drop-in is too small
      - the validated `pip` stack shows the next missing boundary lives inside
        `PySide6_Addons`:
        - `QtPositioning`
        - WebEngine bindings/runtime
      - a naive overlay of those `pip` Addons files on top of the current
        conda-forge base discovers the modules and gets past early loader
        errors, but then segfaults
      - so the next serious packaging hypothesis is now:
        - an ABI-aligned `PySide6_Addons`-style package boundary
        - not a tiny WebEngine-only drop-in
      - a fuller `PySide6_Addons` overlay experiment confirms the same
        direction:
        - the packaging boundary still points toward `Addons`
        - but direct file transplant from the working `pip` environment onto
          the current conda-forge base is not stable enough
        - so the promising next route is:
          - a curated/aligned `PySide6_Addons`-style package
          - not a manual overlay solution
      - the later pip-family comparison now also sharpens the runtime model:
        - the natural `shiboken6 / PySide6_Essentials / PySide6_Addons` family
          appears to carry and prefer its own Qt runtime under
          `site-packages/PySide6/Qt`
        - that family also carries its own ICU runtime and does not look like a
          thin layer that can simply sit on top of the current `qt6-main`
          conda-forge base
        - the provisional clean route therefore looks more like:
          - a self-aligned Qt-for-Python family in UIBCDF
          - and less like:
            - `qt6-main` from conda-forge plus a small extension package
      - a first experimental scaffold for that family now belongs in
        `sandbox/qt_for_python_uibcdf_experiment/`:
        - derive manifests from a validated `pip` environment first
        - only then attempt conda recipes for:
          - `shiboken6`
          - `PySide6_Essentials`
          - `PySide6_Addons`
      - that scaffold is now also split locally as three future repo-shaped
        units under `sandbox/qt_for_python_uibcdf_experiment/repos/`:
        - `shiboken6-uibcdf`
        - `pyside6-essentials-uibcdf`
        - `pyside6-addons-uibcdf`
      - the packaging work is now also split operationally into sibling repos
        next to `molsysviewer`:
        - `../shiboken6-uibcdf`
        - `../pyside6-essentials-uibcdf`
        - `../pyside6-addons-uibcdf`
      - `molsysviewer` should now keep the evidence and integration notes,
        while recipe/build/release iteration for that family happens in those
        sibling repos
      - each sibling repo now also has its own `devguide/` with a local
        bootstrap recipe for the `6.9.2` line, so future version work such as
        `6.10.x` does not need to depend on `molsysviewer` as the only memory
        of how the repo was assembled
      - the first real recipe step is now underway in `../shiboken6-uibcdf`:
        - manifests copied locally into the repo
        - `build.sh` now follows that manifest and stages the boundary from the
          validated `molsyssuite-qt-spike` environment
        - a local non-conda smoke copy into a temporary `site-packages` worked
        - `import shiboken6` succeeded from that staged boundary
        - `conda build` itself could not yet be run from the current shell
          because `conda-build` is not available in this environment
      - `../shiboken6-uibcdf` now also contains the relevant upstream code
        imported from the local `pyside-setup` checkout:
        - `ApiExtractor`
        - `generator`
        - `libshiboken`
        - `shibokenmodule`
        - `cmake`
        - `config.tests`
        - `data`
        - `tests`
      - so that repo is no longer only a packaging shell; it now has both:
        - the upstream source tree
        - the first manifest-driven UIBCDF packaging attempt
      - `../pyside6-essentials-uibcdf` now also has its first real packaging
        step:
        - manifests copied locally into the repo
        - `build.sh` now stages the `PySide6_Essentials` boundary from the
          validated `molsyssuite-qt-spike` environment
        - the first pass intentionally excludes:
          - wrapper commands under `bin/`
          - a few inconsistent `PySide6/scripts/*` entries
          - a few inconsistent `PySide6/support/*` entries
        - a local non-conda smoke copy into a temporary `site-packages` worked
        - `import PySide6.QtCore` succeeded from that staged boundary
      - `../pyside6-addons-uibcdf` now also has its first real packaging step:
        - manifests copied locally into the repo
        - `build.sh` now stages the `PySide6_Addons` boundary from the
          validated `molsyssuite-qt-spike` environment
        - the first pass intentionally excludes:
          - wrapper commands under `bin/`
          - a few inconsistent `PySide6/scripts/*` entries
          - a few inconsistent `PySide6/support/*` entries
        - the meaningful smoke check for this repo is now family-level, not
          isolated:
          - staged together with `shiboken6-uibcdf`
          - staged together with `pyside6-essentials-uibcdf`
        - in that staged family layout:
          - `import shiboken6` worked
          - `import PySide6.QtCore` worked
          - `import PySide6.QtWebChannel` worked
          - `QtWebEngineProcess` and `QtWebEngineCore.abi3.so` were present
      - first pass remains explicitly scoped to:
        - Linux
        - Python 3.13
      - the namespace-split coexistence work is now also underway:
        - `../shiboken6-uibcdf` and `../pyside6-essentials-uibcdf` already
          carry first source-side `_uibcdf` namespace patches
        - their `build.sh` recipes also now rewrite the staged package layout
          to:
          - `shiboken6_uibcdf`
          - `PySide6_uibcdf`
      - the first true `conda build` rerun for `../shiboken6-uibcdf` now gives
        a decisive result:
        - the package layout rewrite itself works
        - but import still aborts inside the embedded
          `signature_bootstrap.py` path bundled in `Shiboken.abi3.so`
        - that embedded helper still imports canonical `shiboken6`
      - so the current packaging conclusion is now sharper:
        - boundary repackaging was a valid bootstrap step
        - but it is no longer sufficient for coexistence with native
          `shiboken6` / `PySide6`
        - the next real step is a true source rebuild of the family with the
          suffixed namespace carried through the embedded/runtime helpers too
- Phase A should now be read as effectively closed unless a downstream need
  exposes a real structural gap.
- The shared workspace launcher has now taken a first concrete step toward the
  future workspace mosaic:
  - when several workspaces coexist, the shared launcher can now present them
    as a small card-like grid rather than only as a flat list
  - `Core` can now also be separated visually from the add-on block inside that
    launcher
  - this should still be treated as a launcher refinement, not yet as the final
    mosaic or multi-panel layout system
- `Workbench` now also has a first body-level workspace overview:
  - small workspace cards inside the panel body
  - the current workspace card can now reflect the active panel hosted below
  - and can surface the active panel entry when that helps identify the runtime
  - the current workspace card can now also preview the active host more
    directly:
    - description
    - immediate capability counts
    - first dynamic section cards
  - the overview and the active host now also sit inside one shared runtime
    deck, so the body reads more like one domain surface and less like two
    unrelated stacked cards
  - non-current add-on workspace cards can now also expose small capability
    chips, so the workbench no longer reads as `Core` plus vague add-on
    metadata
  - that capability layer should now be treated as part of the add-on runtime
    proof itself:
    - add-on workspaces need to look informative and domain-bearing inside the
      shared workbench body,
      not only selectable from the launcher
  - the current workspace card now also carries a richer local panel lane:
    - panel title
    - panel description
    - current panel entry
    - direct switching across the local stack
    so the overview and the active host read more like one runtime surface
  - non-current add-on cards can now also expose the first real workbench
    section titles when available,
    so the shared workbench already hints at domain structure before the user
    opens that workspace
  - still a navigator, not yet a free multi-panel mosaic
  - intended as the first in-panel foothold for the future workspace mosaic
- the reference add-on smoke path is now also more honest as runtime pressure:
  - `build_reference_demo_view("topomt")` no longer stops at opening
    `Workbench`
  - it also activates the add-on workspace and its entry panel
  - so downstream teams land directly in a visible workspace-shaped runtime,
    not only in the generic shell
  - the same reference path is now also a better closure check for Phase B:
    - notebook queries can inspect the same workspace
    - the same local panel stack
    - and the same workbench sections
    that the shared host is rendering
  - after the latest runtime, notebook, smoke, and onboarding slices, Phase B
    should now be read as **near closure**:
    - do not keep extending it sideways by default
    - only keep it open if one more realistic add-on-pressure slice exposes a
      structural gap in the shared host
    - the only remaining work that should justify reopening it is:
      - a more realistic downstream add-on path that reveals a missing host
        capability
      - a real mismatch between:
        - workspace launcher
        - local panel stack
        - active panel host
        - notebook/runtime bridge
      - or a smoke/onboarding gap that makes the reference runtime hard to
        teach honestly
    - what should **not** justify reopening it is:
      - more chrome by default
      - more abstract add-on API surface without runtime pressure
      - or aesthetic work that does not change host credibility
- the shared workspace launcher/header now also carries a clearer domain hint:
  - the current trigger distinguishes `Core workspace` from `Add-on workspace`
  - so the shared header reads more clearly as a domain switcher rather than a
    generic dropdown
- Phase B is now advanced enough that it should not keep growing sideways
  without concrete ecosystem pressure.
- Phase C is now much stronger and should be considered substantial rather than
  exploratory.
- Phase D should now prefer product-facing tightening work that teaches the
  current runtime honestly:
  - workbench-oriented figure/export tutorials
  - workbench-oriented add-on/workspace tutorials
  - panel/workspace behavior docs that explain the shared workbench model
  - public docs that connect runtime surfaces to the now-real APIs
  - smoke guidance that includes the support-library observability layer we now
    rely on for fast QA (`smonitor`)
  - small but truthful user/developer guidance slices instead of broad new
    architecture
- the next useful tightening gate should now be read as a pre-`0.16.x`
  release-hardening check:
  - can the current mature product surfaces be taught and smoke-tested as one
    coherent story?
  - specifically:
    - panel/workspace runtime
    - add-on reference runtime
    - figure export from the workbench
  - if yes, the main remaining uncertainty moves to standalone/distribution,
    not back to the shared runtime
  - current reading after the latest tightening slices:
    - this gate is largely in place
    - the remaining work should now prefer small release-hardening checks and
      not another broad documentation rewrite
  - concrete `0.16.0` gate:
    - the recommended smoke subset is still green
    - `npm --prefix molsysviewer/js run test:js` is green again after hardening
      the interaction/active-selection/annotation test path
    - the three mature stories are still easy to find from docs navigation:
      - panel/workspace runtime
      - add-on reference runtime
      - figure export from the workbench
    - public docs and notebook-facing APIs still describe the same runtime
      shape
    - no new structural host gap has appeared while tightening release
      guidance
- The practical question is now shifting toward the next checkpoint gate:
  - before `0.14.0`, prefer checking whether the current Phase D slices are
    already enough to teach the product honestly
  - do not reopen broad architectural fronts unless the review exposes a real
    gap
  - likely candidates for a last tightening pass before `0.14.0` are:
    - one more docs/API parity review
    - or one more small regression bundle around recently taught surfaces
- That short pre-`0.14.0` review is now effectively closed:
  - docs/API/runtime parity for the recent tightening surfaces looks good
  - the small regression bundle for:
    - figure export
    - add-on workspaces
    - panel mode
    is green
  - so `0.14.0` is justified as the first checkpoint where product tightening
    itself becomes part of the release story
- After the latest workspace/panel runtime slices, Phase A should now be read as
  **near closure** rather than open-ended:
  - the shared workbench model is already coherent enough to stop iterating on
    chrome by default
  - the next major implementation focus should be Phase B
  - only keep touching Phase A when a downstream add-on/runtime need exposes a
    real structural gap
- Avoid opening many unrelated new surfaces at once.
- Prefer larger vertical slices that make one part of the product feel more
  real, rather than many small disconnected improvements.
- Keep the main product leitmotiv explicit:
  - scientific exploration is important,
  - but the outcome of that exploration should become reproducible viewer state.
- Keep `devguide/guiding_principles.md` as the stable place for project
  ideas-alma that should survive beyond the current checkpoint.
- Keep the interaction stack moving in order:
  - canvas gestures/context menu,
  - measurement tool modes,
  - `active_selection`,
  - `GroupStrip`,
  - `annotations`.
- Keep `devguide/interaction_verified_state.md` as the operational truth for:
  - what interaction behaviors are really implemented,
  - what has already been verified in smoke,
  - and what still needs re-checking.
- Keep `devguide/` aligned with the real repository state.
- The shared panel/workspace runtime now also has a clearer Python control
  surface for notebook use:
  - `view.set_panel_mode(...)`
  - `view.set_workspace(...)`
  - `view.set_workspace_panel(...)`
  - `view.get_panel_mode_state()`
  - `view.workspace_catalog()`
  - `view.workspace_panels(...)`
  - `view.workspace_sections(...)`
  - `view.workspace_runtime()`
  - this should be treated as the stable scripted doorway into the workspace
    runtime, not only as UI chrome
  - the catalog side now also reflects active workspace/panel state when the
    frontend has already reported it
  - notebook/runtime QA can now also inspect the visible workbench sections of
    the current workspace without reconstructing them indirectly from add-on
    specs
  - `workspace_runtime()` now also exposes:
    - `current_workspace_record`
    - `current_panel`
    so notebook code does not need to recombine the active records manually
- Keep the emerging MolSysSuite add-on direction explicit:
  - `MolSysViewer` 1.0 should stay as a strong core workbench
  - domain-specific ecosystem growth should prefer optional add-ons
  - even before real plugins exist, 1.0 should leave extension entry points and
    validate them with at least a plugin test or plugin template
- Treat `selections` as a first-class category distinct from `regions`; do not collapse them just because both derive from atom subsets.
- Keep the smoke runbook in `devguide/smoke_test.md` aligned with the real product surface before broadening interaction much further.
- `Save Selection` is now live-smoke verified both when the menu opens on empty canvas and when it opens on a structural context target; the earlier accidental fallthrough into measurement picking is fixed.
- Saved persistent selections can now be restored back into `active_selection` via API, and the context menu now has a saved-selection section ready to expose that bridge live.
- Next context-menu expansion should favor relevant persistent workbench objects in this order: `regions`, then richer `annotations`, then carefully-scoped `shapes`; avoid turning the menu into a general browser of every object.
- The first `regions` slice is now present in the context menu:
  - only relevant overlapping regions are shown
  - the first action is deliberately narrow:
    - `Focus Region`
  - defer richer region actions until this small slice proves useful and stays clean
- For `annotations` and `shapes`, keep the same discipline:
  - small target-specific menus
  - immediate actions only
  - likely ceiling:
    - annotation:
      - `Focus`
      - `Delete`
      - maybe later `Show/Hide`
    - shape:
      - `Focus`
      - `Delete`
      - maybe later `Show/Hide`
  - do not let these menus grow into rich editors or type-specific browsers
- The strip work has now crossed into a real `GroupPanel` + multiple-`GroupStrip` runtime.
- `GroupPanel` has now taken a first practical step toward the future `Navigate` panel:
  - it uses a reusable panel shell
  - it exposes an explicit `Navigate` title
  - but it still behaves as the current drawer-style strip container, not yet the final shared `panel mode`
  - it now also exposes first lightweight live summary sections:
    - `Active`
    - `Saved`
    - `Regions`
  - these are still list-style summaries, not yet a richer interactive inventory
  - first primary actions now exist there too:
    - click `Saved` row -> restore `active_selection`
    - click `Regions` row -> focus region
- `WorkbenchPanel` now also exists as a real shell-based runtime scaffold:
  - same panel shell family
  - explicit `Workbench` identity
  - sections for:
    - `Annotations`
    - `Measurements`
    - `Shapes`
    - `Scene`
  - now wired into the controller as a minimal right-side drawer
  - currently populated from a lightweight controller-side summary model:
    - annotation text + tag
    - measurement kind + pick count
    - shape title/tag
    - scene preset/representation summary
  - first row action now exists where the runtime has safe structural anchors:
    - click row -> focus target
    - currently reliable for:
      - annotations
      - measurements
      - shapes only when `atom_indices` are present in the layer metadata
  - row state has also started to align with the shared panel/canvas language:
    - `active` row state now exists in the runtime
    - `context` row state now also exists in the runtime for:
      - annotations with tag
      - shapes with tag
    - this is still a local drawer-era implementation, not yet the final shared `panel mode` state model
  - row affordances have now grown one more careful step:
    - tagged annotations, measurements, and shapes now expose a minimal visibility toggle
      through the existing `show_layer` / `hide_layer` path
    - workbench sections can now collapse/expand locally to reduce vertical noise
  - add-ons no longer surface only as summaries there:
    - `Workbench` can now materialize add-on-contributed workbench sections as
      real dynamic sections in the panel
    - each such section is still intentionally modest:
      - one informational row
      - no arbitrary frontend execution
      - enough to validate that add-ons can project structure into the shared workbench
  - still not yet integrated into a shared navigator or final `panel mode`
- The next strip step is no longer “multiple strips”, but a better `GroupPanel` shape: vertical per-chain strip-columns, independent scroll, and then show/hide; the permanent lower strip is no longer the intended final product shape.
- `chain` remains the primary strip organizer, but future strip grammar should also mark `component` and `molecule`.
- Do not adopt middle-click as the default `GroupPanel` toggle for now; Mol* already uses the middle/wheel path for camera behavior.
- Prioritize regression coverage for new product-facing behavior, especially where it composes runtime state, layers, and rebuild/replay.
- A direct code-vs-checkpoint review now confirms that the current reproducible interaction slice is materially present in code and covered by the targeted local regression block.
- The reproducible interaction workflow now also has an explicit integrated regression covering:
  - saved selection
  - region
  - label
  - persisted measurement
  together in export/replay and after `remove()` remap.
- The clearest next implementation gap is no longer the selection/annotation/measurement bridge itself, but the missing first-class `styles` layer above the current `representation` / `preset` / `user_preset` base.
- That `styles` gap now has a first concrete Python-side slice:
  - `Style`
  - `view.styles`
  - explicit style registry
  - explicit `_molsysviewer.py` loading support
  - canonical built-in scene-style battery
- The next `styles` gap is no longer basic API existence.
  It is the future scene-look layer:
  - clarify `default-look` and `illustrative` as visual looks, not structural recipes
  - preserve the distinction between structural targeting and visual styling
  - avoid opening canvas authoring or a second runtime protocol too early
- The canvas/popup UX direction should now be treated as explicitly decided at the principle level:
  - resting canvas as clean as possible
  - only two main interaction doors:
    - right-click context menu
    - panel mode
  - only three permanent meta-controls:
    - panel
    - fullscreen
    - popup
  - trajectory scrubber remains the one justified always-visible data control when a trajectory exists
  - panel mode should likely converge first on:
    - `Navigate`
    - `Workbench`
  - tabs are the preferred first panel navigator
  - a discreet carousel remains a possible later/configurable navigator variant
- The detailed record of canvas/popup UX decisions, still-open UX questions,
  and alternatives intentionally kept alive should now live in:
  - `devguide/canvas_minimal_ux.md`
  - do not let that discussion disappear into chat history only
- The first serious image-export slice now exists:
  - Python `view.export.image(...)`
  - PNG output
  - optional explicit pixel size
  - optional `scale` multiplier for higher-resolution export
  - optional transparent background
  - backed by Mol*'s real viewport screenshot helper rather than naive canvas capture
  - still no richer figure recipe/spec yet
- The figure-export story has also advanced one more careful step:
  - `view.export.figure(...)` now exists as the first explicit figure-oriented
    wrapper above raw image export
  - a first minimal reusable `FigureSpec` now exists on the Python side
  - `FigureSpec` can now also:
    - capture the current camera from a live `view`
    - derive small immutable variants through explicit overrides
    - expand a named batch of figure recipes from one base recipe
  - `view.export.figure_variants(...)` now exists as the first explicit batch
    figure-export path
  - `FigureSpec.build_publication_variants(...)` and
    `view.export.figure_publication_set(...)` now provide the first standard
    small publication bundle:
    - `light`
    - `dark`
    - `transparent`
    - optional `current`
  - `Workbench -> Scene` now also exposes the built-in figure baseline:
    - default figure preset
    - default figure scale
    - recommended figure variants
  - that recipe layer is still intentionally modest:
    - export-facing only
    - no detached project format yet
    - no independent frontend protocol yet
- The add-on/panel scaling direction is now clearer too:
  - do not assume future growth means one flat global pile of panels
  - `Core` should be understood as the native future workspace
  - larger add-ons may later contribute their own workspaces
  - each workspace would then carry its own local panel stack
  - smaller add-ons should still be allowed to remain lighter and never become
    a workspace
  - that workspace layer is now also present in the typed add-on contract and
    already propagates through the current addon runtime summary path
  - the shared panel shell now also has a first minimal runtime workspace
    launcher:
    - only shown when more than one workspace is effectively available
    - still far from the final launcher/mosaic
    - enough to make workspace state visible and steer add-on workbench slices
    - the shared header stays calmer because only the current workspace remains
      visible until the launcher is opened
    - it now also prefers effective workspace entries only:
      - workspaces with no visible panel/section runtime do not clutter the
        launcher
    - launcher entries can already expose lightweight summaries of what they
      contain
    - the current workspace trigger can also carry a compact subtitle, so the
      active domain is legible without opening the launcher
    - the launcher can explicitly mark the current workspace, making it read
      more like a domain selector than a flat dropdown
  - the shared panel header is now also becoming workspace-aware:
    - non-core workspaces remain workbench-centric for now
    - the runtime offers a direct return to `Core`
    - it does not pretend every add-on workspace already has a full native
      `Navigate` stack
    - the next honest runtime step is to make that true in behavior too:
      - non-core workspaces should hide `Navigate`
      - returning to `Core` should restore the last core panel choice
  - `Workbench` now also materializes a first generic panel-stack bridge for
    add-on workspaces:
    - selector of workspace panels
    - generic active-panel host surface
    - workspace-specific add-on sections can now be absorbed into that host so
      the workspace panel does not feel split from its own immediate runtime
    - the host can now also surface the active add-on's immediate capabilities:
      - context actions
      - export helpers
    - still no arbitrary add-on frontend runtime, but no longer just a summary
  - that panel selector is now also part of the shared header chrome:
    - core stack feels more like a real `panel mode`
    - non-core panel stacks stop feeling like a local workbench-only detail
    - the header now reads more clearly as:
      - workspace launcher first
      - active workspace panel stack second
- `0.12.0` now marks a coherent pre-1.0 checkpoint:
  - `standalone 0` exists and is already teachable as a browser-hosted first cut
  - the add-on starter pack is real:
    - public docs
    - cookbook
    - standards
    - importable reference template
  - the panel/runtime model has moved beyond two ad hoc drawers:
    - workspace launcher
    - local panel stacks
    - generic add-on workspace host

The next route should now be read more sharply:

- first:
  - keep consolidating the shared workbench/runtime
- second:
  - use that runtime to validate a richer add-on path
- third:
  - mature `image` / `figure` export further
- fourth:
  - tighten docs/tutorials/verification around the now-real product
- The bundled add-on starter pack now also has a single smoke/demo path teams
  can share:
  - `molsysviewer.addon_templates.build_reference_demo_view("topomt")`
  - use that as the shortest reproducible reference route when onboarding
    `MolSysMT`, `TopoMT`, `PharmacophoreMT`, or similar teams
- fifth and last major step before `1.0.0`:
  - standalone

## Near-Term Route To 1.0

The current preferred route to 1.0 is incremental and workbench-first:

1. keep the reproducible scene/state model hard and boring:
   - export/replay
   - rebuild/remap
   - popup sync
   - persistent artifacts
2. keep the canvas minimal:
   - right click
   - panel mode
   - three meta-controls only
3. converge the current drawer-era runtime toward the two-panel workbench model:
   - `Navigate`
   - `Workbench`
4. strengthen row/list semantics before inventing richer chrome:
   - primary action
   - `active`
   - `context`
   - `hidden` / visibility treatment where appropriate
   - local section collapse before a richer navigator
5. finish the first healthy `styles` story before opening richer look systems:
   - stable scene styles now
   - scene looks later
   - focus styles later still
6. add a first serious image-export story on top of the same reproducible scene model
7. harden that image-export story toward:
   - camera/composition reuse
   - publication looks
   - figure recipes/specs
8. only after that, consider the shared panel navigator and richer publication-oriented layers
9. treat standalone as the final major pre-`1.0.0` step:
   - same workbench
   - same scene/state model
   - CLI-first host
   - no forked UX
10. before calling `1.0.0`, ensure the core is add-on-compatible even if no real
    MolSysSuite plugin ships yet:
    - explicit extension points
    - and at least a plugin test or plugin template

That add-on-compatibility story now has a first real slice:

- `molsysviewer.addons` as host-level registry
- `view.addons` as local projection with per-view enable/disable overrides
- explicit typed add-on specs for:
  - panels
  - context actions
  - workbench sections
  - shape providers
  - style helpers
  - export helpers
  - tool modes
- validated with a fake add-on test rather than a real ecosystem package

The next add-on step is now more specific:

- keep `addons` as the only public vocabulary
- add a simple discovery path based on a maintained list of known add-on
  modules
- keep explicit manual coupling for local or unpublished add-on development
- document the packaging contract early so downstream add-ons do not have to
  guess their module shape
- do not stop at `devguide`:
  - user docs should explain installation/discovery/use of add-ons
  - developer docs should explain the host/local registry contract
  - cookbook should stay actionable for external teams

The add-on starter-pack story should now be treated as real deliverable work:

- bundled reference template:
  - [`molsysviewer/addon_templates/minimal_topomt.py`](/home/diego/repos@uibcdf/molsysviewer/molsysviewer/addon_templates/minimal_topomt.py)
- public docs:
  - developer add-on contract
  - cookbook recipe
  - showcase placeholder with starter links
- stable normative references under:
  - [`standards/addons/README.md`](/home/diego/repos@uibcdf/molsysviewer/standards/addons/README.md)
  - [`standards/addons/IMPLEMENTATION_CONTRACT.md`](/home/diego/repos@uibcdf/molsysviewer/standards/addons/IMPLEMENTATION_CONTRACT.md)
- those `standards/` files must now stay aligned with:
  - the runtime contract
  - the reference template
  - developer docs
  - cookbook guidance

For standalone, the next communication milestone is also clearer:

- before the final standalone implementation push, preserve a credible
  `standalone 0`
- that is the version to show early to the MolSysMT/TopoMT/
  PharmacophoreMT teams
- its job is to prove the host model and add-on/workspace fit, not to pretend
  the final product UX is already finished
- the first public slice should stay deliberately small:
  - `build_standalone0_html(...)`
  - `launch_standalone0(...)`
  - `molsysviewer ...`
  - `python -m molsysviewer.standalone ...`

  - cookbook should carry a "build a minimal add-on" recipe
  - showcase should eventually include at least one add-on-shaped scientific
    story

That story now also has a concrete reference template module:

- `molsysviewer.addon_templates.minimal_topomt`

It is not a real ecosystem integration, but it gives add-on authors and tests a
stable importable target beyond ad hoc fake specs.

The add-on platform now also has a first intentionally small lifecycle slice:

- `AddonLifecycleSpec`
- `on_enable(view)`
- `on_disable(view)`
- `on_context_action(view, action_id, payload)`

This is still Python-side and deliberately narrow.
It should help validate realistic add-on activation without opening a large
hook surface too early.

Add-ons now also have a first visible runtime surface:

- Python sends a small add-on runtime summary to the frontend
- `Workbench` exposes that through an `Add-ons` section
- the current visible content is still intentionally summary-only:
  - enabled add-on names
  - contributed panel titles
  - contributed workbench-section titles

This is the first runtime proof that add-ons are no longer only a registry/API
story; they now reach the visible viewer surface without opening full dynamic UI
execution yet.

There is now also a first visible add-on context-menu slice:

- enabled add-ons may contribute compatible context actions
- the menu renders them in an `Add-ons` section
- clicking one emits a structured Python-side `interaction_context_action`
  carrying:
  - add-on name
  - add-on action id
  - add-on action title

This is still a bridge and visibility slice, not yet a rich domain action
runtime.

Enabled add-ons can now also handle that bridge through the new Python-side
lifecycle hook above, so add-on context actions are no longer only observable;
they can already trigger explicit view-local runtime behavior.

Working rule:

- do not jump early to the final panel switcher, offline rendering, or a desktop-like host shell
- first make the existing workbench slices coherent, reproducible, and pleasant

## 0.9.0 Checkpoint

`0.9.0` marks the point where MolSysViewer has a coherent pre-1.0 workbench direction rather than a loose collection of slices.

What this checkpoint consolidates:

- a recognizable two-panel workbench trajectory:
  - `Navigate`
  - `Workbench`
- a minimal canvas UX direction that is already explicit and stable at the principle level
- first-class scene styles through `Style` and `view.styles`
- first-class export namespace:
  - `view.export.html(...)`
  - `view.export.image(...)`
- a reproducible scene/workbench baseline strong enough to support the next steps toward `1.0.0`

Follow-up convergence after `0.11.0`:

- `Navigate` and `Workbench` now share a minimal drawer expansion contract
- only one of the two drawer panels expands at a time
- `Escape` closes an expanded drawer before falling back to clearing active
  selection
- the first shared runtime API now exists:
  - `view.set_panel_mode(panel="navigate"|"workbench"|None, expanded=True|False)`

What `0.9.0` does not mean yet:

- no final shared panel navigator yet
- no full figure recipe/spec yet
- no standalone host yet
- no real MolSysSuite plugins yet
- not the final publication-quality rendering story

## 0.10.0 Checkpoint

`0.10.0` marks the point where MolSysViewer's add-on story stops being only a
future architectural intention and becomes a real public-facing platform slice.

What this checkpoint consolidates:

- host-level add-on registry:
  - `molsysviewer.addons`
- per-view add-on projection:
  - `view.addons`
- explicit typed contribution specs for:
  - panels
  - context actions
  - workbench sections
  - shape providers
  - style helpers
  - export helpers
  - tool modes
- first simple discovery path:
  - maintained list of known add-on modules
  - `molsysviewer.addons.discover()`
- explicit manual coupling path for local or unpublished development:
  - `molsysviewer.addons.register(...)`
  - `molsysviewer.addons.register_module(...)`
- first public docs surface for add-ons in:
  - user introduction
  - cookbook
  - developer docs
  - showcase placeholder
- cleaner public export wording around:
  - `view.export.html(...)`

What `0.10.0` does not mean yet:

- no real MolSysSuite add-on shipped yet
- no entry-point metadata discovery yet
- no persisted add-on preferences yet
- no richer add-on runtime lifecycle yet
- no standalone host yet

## 0.11.0 Checkpoint

`0.11.0` marks the point where the add-on platform becomes visibly present in
the running viewer, not only in API contracts and developer documentation.

What this checkpoint consolidates:

- importable reference add-on template:
  - `molsysviewer.addon_templates.minimal_topomt`
- first intentionally small add-on lifecycle:
  - `AddonLifecycleSpec`
  - `on_enable(view)`
  - `on_disable(view)`
- first visible workbench runtime surface for add-ons:
  - `Workbench` now includes an `Add-ons` section
  - enabled add-on names are shown there
  - contributed panel titles, workbench-section titles, context-action titles,
    and export-helper titles are summarized there
- first visible context-menu bridge for add-ons:
  - compatible add-on context actions can appear in an `Add-ons` section
  - clicking one emits a structured `interaction_context_action`
  - the payload now carries:
    - add-on name
    - add-on action id
    - add-on action title
- first explicit project-level add-on defaults:
  - `_molsysviewer.py` may now define `ADDONS_ENABLED` and `ADDONS_DISABLED`
  - `molsysviewer.addons.load_project_config(...)` applies those defaults at
    host level
  - new views inherit them while `view.addons` keeps local override semantics

What `0.11.0` does not mean yet:

- no real MolSysSuite scientific add-on shipped yet
- no persisted enable/disable preferences yet
- no entry-point metadata discovery yet
- no full add-on frontend execution contract yet
- no standalone host yet

Post-`0.11.0` export work:

- `view.export.image(...)` now also accepts `camera_snapshot=...`
- the explicit snapshot should be treated as a reproducible figure/export aid,
  not merely as another UI convenience parameter
- `view.export.image(...)` now also accepts a first small `preset=...` surface:
  - `current`
  - `publication-light`
  - `publication-dark`
- in the current implementation that preset only controls reversible background
  treatment during the capture itself
- `view.export.figure(...)` now exists as the first explicit figure-oriented
  wrapper over raw image export:
  - stronger default scale
  - `background=...`
  - figure-oriented preset defaults

## Current State

- JS/TS tests
  - Unit suite was stabilized and split by handler domain.
  - Coverage now includes `trajectory`, `state`, `loader`, `scene`, and `shape` guard semantics.
  - E2E covers:
    - region creation + hide,
    - tagged shape add/clear,
    - `clear_all` + `registry_cleared`,
    - reload after full reset.
  - E2E remains environment-dependent because browser/WebGL support is required.

- Python live-edit coverage
  - Regression coverage now exists for:
    - `remove()`: rebuild with atom-index remap,
    - `append_structures()`: rebuild without atom-index remap, multi-structure payload,
    - `add()`: rebuild with expanded atom payload,
    - `set()`: rebuild after topological and structural edits,
    - consecutive live-edit chains with replay/export assertions.
  - These regressions use real demo viewers instead of synthetic mocks.

- Python visibility semantics
  - Regression coverage now exists for:
    - sticky `whole.hide()` across `show(all)`,
    - sticky hidden region/layer state across `view.hide()` / `view.show()`,
    - `show(all)` restoring the atom mask without explicitly re-showing hidden regions.
  - These assertions are aligned directly with `devguide` visibility semantics.

- Export / popout core contracts
  - Regression coverage now exists for:
    - export replay ordering with `set_camera_snapshot` appended after cleaned message history,
    - standalone export state honoring `enable_popout=False`,
    - popup host runtime bootstrap via `moduleUrl`,
    - popup host sync messages being gated on `isReady` and open window state.

- Popup live-sync baseline
  - Regression coverage now exists for:
    - popup initial sync replaying message history and camera snapshot,
    - popup autohide initialization from host state,
    - popup -> host camera sync being gated by user interaction,
    - host -> popup camera sync being blocked while the popup user is interacting.

- **Technical & Scientific Assessment (March 2026):** Completed. The library's health, strategic workbench direction, and critical risks are now formally documented.
- **Support-library integration hardening:** 
    - `depdigest` now runs before importing heavier public submodules.
    - `pyunitwizard` usage is unified.
    - `smonitor` coverage expanded and structurally enforced.
    - `argdigest` hardening covers core public wrappers.
    - **Git Hygiene:** JS test build outputs should stay out of git. `dist-index.js`, `dist-region-hide.js`, `harness.bundle.js`, and `region-hide.e2e.js` belong in ignore rules unless there is a documented reason to version them.

- `molsysviewer.tools`
  - The package now exists and starts with `molsysviewer.tools.basic.concatenate_structures(...)`.
  - `molsysviewer.tools.basic.merge(...)` now exists as the second pure composition primitive.
  - `molsysviewer.tools.basic` now also exposes functional wrappers over core `MolSysView` operations:
    - `select`, `get`, `info`,
    - `extract`,
    - `set`, `remove`, `add`, `append_structures`,
    - `contains`, `is_composed_of`.
  - `copy(view)` now exists with a scene-aware contract: it duplicates the molecular system and recreates useful scene state.
  - `compare(view_a, view_b)` now exists with a deliberately narrower contract: it compares loaded molecular systems, not full visual scene state.
  - This first tool is intentionally a pure operation:
    - it accepts multiple MolSysMT-compatible systems or `MolSysView` objects,
    - delegates structural concatenation to `molsysmt.concatenate_structures(...)`,
    - and returns a fresh `MolSysView`.
  - `merge(...)` is intentionally view-centric:
    - it accepts `MolSysView` objects,
    - delegates molecular-system merging to `molsysmt.merge(...)`,
    - imports regions/layers/shapes/visibility from all inputs,
    - resolves tag collisions deterministically with suffixes such as `__2`,
    - and uses the first view as the source of global representation, controls, and camera snapshot state.
  - The purpose is to grow advanced functionality without inflating the core `MolSysView` facade.
  - The package is now also part of the project’s “inspection/workbench” identity, not just its “viewer/export” identity.

- Inspection-oriented object API
  - `MolSysView` is now growing along two complementary axes:
    - functional helpers in `molsysviewer.tools.basic`,
    - direct object methods when the behavior is naturally scene-centric or inspection-centric.
  - Camera/inspection helpers are now expected to live on the object side:
    - `focus_selection(...)`,
    - `focus_region(...)`,
    - `Whole.focus(...)`,
    - `Region.focus(...)`,
    - `Region.show_only(...)`.
  - Structural partition helpers also belong on `MolSysView`, not in `tools.basic`, because their real product value is creating region objects in the active scene.
  - The public API for this is now one operation:
    - `make_regions_by(element=...)`
    - instead of multiple `split_by_*` entrypoints.
    - allowed hierarchy levels are intentionally limited for now to `chain`, `molecule`, and `entity`.
  - Region tags produced by viewer-managed region-building helpers should follow a stable policy:
    - derive from a MolSysMT human-readable label when possible,
    - sanitize to a replay-safe tag token,
    - keep semantic prefixes where needed to avoid ambiguity (`molecule_...`, `entity_...`) while allowing concise chain tags,
    - resolve collisions deterministically with suffixes such as `__2`.

- User documentation
  - The user guide now has a dedicated `tools/` section.
  - The first module documented is `tools.basic`.
  - Each currently exposed `tools.basic` function now has its own user-facing page under `user/tools/basic/`.
  - Developer docs now also document the first explicit style/configuration path:
    - `Style`
    - `view.styles`
    - explicit project config loading via `_molsysviewer.py`

- Styles and configuration
  - The first public `Style` slice now exists in Python:
    - `Style`
    - `view.styles.apply(...)`
    - `view.styles.current()`
    - `view.styles.info()`
  - A second Python-side slice now also exists:
    - registry methods such as `add()`, `get()`, `tags()`, `records()`
    - application by tag
    - explicit project-config loading via `view.styles.load_project_config(...)`
  - The first canonical built-in battery is now exposed directly through the API:
    - `default`
    - `polymer-cartoon`
    - `polymer-and-ligand`
    - `atomic-detail`
    - `coarse-surface`
    - `empty`
  - Current implementation rule:
    - these styles are still backed by the existing global representation pathway,
      not by a new frontend protocol
  - Current configuration rule:
    - `_molsysviewer.py` support is explicit-load only for now
    - there is no ambient discovery yet
    - explicit user calls still win over project defaults
  - Current architectural rule:
    - MolSysMT remains the canonical source of structural targeting semantics
    - MolSysViewer styles define visual treatment
    - future targeted styles should compose with MolSysMT-compatible selection
      semantics or stable MolSysViewer selection-derived objects
  - Current future-facing rule:
    - `default-look` and `illustrative` should be treated as future scene-look
      targets
    - they should not be collapsed prematurely into the current structural
      recipe battery

- Interaction and taxonomy direction
  - Interaction taxonomy now uses:
    - `element`,
    - `shape`,
    - `annotation`,
    - `empty`
    instead of overloading `structure` in the interaction contract.
  - Element hierarchy now explicitly tracks:
    - `atom`, `group`, `component`, `chain`, `molecule`, `entity`.
  - The first lightweight public wrappers now exist for:
    - `view.hover_target`
    - `view.context_target`
  - Current wrapper rule:
    - query-oriented only
    - do not overdesign them yet into a richer object model than current runtime payloads justify
  - `devguide/annotations.md` now records the viewer taxonomy around:
    - `elements`,
    - `regions`,
    - `shapes`,
    - `annotations`,
    - `layers`.
  - Persistent labels are now a documented `annotations` concern, not a `shapes` concern.
  - Mol* precedents reviewed for this design include:
    - built-in structure labels,
    - loci-based labels,
    - MVS custom and annotation-driven labels,
    - tooltip separation from persistent labels.
- Mouse-navigation compatibility is now part of the interaction contract:
    - `left drag` rotates,
    - `right drag` pans/translates,
    - right-click context handling must coexist with that drag behavior and suppress the host menu only inside the viewer canvas.
  - Manual smoke in JupyterLab now confirms:
    - the host `contextmenu` conflict is resolved in both the main notebook canvas and the popup canvas,
    - `right drag` now pans without leaking the host menu in both surfaces,
    - `right click` now opens the viewer-owned menu in both surfaces,
  - the remaining canvas-side picking hardening is specifically about bond/edge fragments resolving consistently to the default `group` target.
  - live smoke has now also confirmed:
    - canvas `left click`, additive `Shift + click`, `Esc`, and order-independent selection visuals,
    - popup canvas context behavior,
    - notebook-canvas `double click -> focus`,
    - `GroupStrip` click / additive click / hover / right-click / double-click.
    - interactive `distance` measurement UX is clear in live smoke,
    - `get_last_measurement_created_event()` now yields the expected replay-safe
      payload shape with `action`, `picked_count`, and `picks_atom_indices`.
  - The first concrete context-menu bridge now exists:
    - right-click without drag is captured from Mol* click events,
    - the canvas suppresses the host `contextmenu`,
    - Python stores both the last context-target event and the last chosen context action event,
    - a viewer-owned context menu now exists with:
      - `Focus Target` for structure, annotation, and first-slice shape targets,
      - target-scoped measurement seed actions for `distance`, `angle`, and `dihedral`,
      - a secondary active-selection section with:
        - `Focus Selection`
        - `Create Region from Selection`
        - `Add Label from Selection` when the selection resolves to exactly one group
        - `Persist Last Measurement` when a recent interactive measurement exists
        - `Clear Selection`
  - Interactive measurement now has a first real implementation path:
    - menu-seeded `distance` / `angle` / `dihedral` actions start a frontend tool mode,
    - picks are forced down the Mol* element/atom path for measurement purposes,
    - Mol* `StructureMeasurementManager` is the calculation/rendering engine for interactive measurements,
    - Python currently observes tool-state and measurement-created events rather than driving the measurement math itself,
    - a visible in-canvas tool-status overlay now shows the active measurement mode, remaining picks, and the `Esc` cancel hint.
  - `active_selection` now has a first concrete runtime slice:
    - ordinary left click replaces the active selection,
    - `Shift + left click` adds uniquely,
    - empty left click clears,
    - active measurement tool modes do not overwrite it,
    - the current implementation is now `group`-centric for element picks,
    - it already emits derived `atom_indices` plus `group_indices`, `chain_indices`, and `entity_indices`,
    - it now also has a narrow `annotation` slice seeded from `GroupStrip` label badges,
    - `element + annotation` now mix in one `active_selection` payload,
    - it now also has a first narrow `shape` slice from Mol* `shape-loci`,
    - broader shape metadata and richer shape/mixed policies still remain ahead.
  - `GroupStrip` now has a first concrete implementation slice:
    - it renders groups from the currently loaded structure,
    - groups are organized by chain,
    - it mirrors `active_selection`,
    - click / `Shift + click` from the strip updates the same active selection state used by the canvas,
    - double click on a strip item focuses that group in the viewer,
    - strip hover now mirrors into the viewer highlight path and emits the same hover event family,
    - right click on a strip item now opens the same viewer context menu contract used by the canvas,
    - compact annotation overlays for persistent group labels now exist,
    - right click on a strip label overlay now seeds `annotation` as a real `context_target`,
    - it is still intentionally narrow and does not yet implement range selection, region overlays, tool-pick overlays, or canvas-side annotation pickability.
  - `annotations` now have a first concrete implementation slice:
    - `view.annotations.add_label(text=..., group_index=..., tag=...)` exists in Python,
    - `view.annotations` is now also growing into a real management API instead of a creation-only entrypoint:
      - `tags()`
      - `count()`
      - `contains(tag)`
      - `get(tag)`
      - `records()`
      - `info(tag=None)`
      - `show(tag)` / `hide(tag)`
      - `delete(tag)` / `set_tag(tag, new_tag)` / `set_text(tag, text)` / `set_group_index(tag, group_index)`
      - `clear(tag=None)`
    - labels are implemented as `annotations`, not `shapes`,
    - the first slice is intentionally narrow: one persistent label anchored to one `group`,
    - labels participate in `layers` with `kind="annotation"`,
    - labels survive export/replay/rebuild through dedicated annotation-history replay,
    - live `hide()/show()` on annotation layers is now verified in notebook smoke and is implemented through explicit artifact removal/rebuild, not only generic subtree visibility,
    - `clear_decorations(..., labels=True)` now clears real frontend labels instead of a placeholder path,
    - strip label badges can now seed both `annotation` context and `annotation` active selection,
    - annotation context now has a first concrete action: `Focus Target`.
  - The first explicit exploration -> reproducible-state bridge now exists in Python:
    - `view.new_region_from_active_selection(...)`
    - `view.annotations.add_label_from_active_selection(...)`
    - `view.measurements.persist_last_measurement(...)`
  - `active_selection` is no longer only a cached frontend event:
    - `view.active_selection` now exists as a public Python wrapper with:
      - `info()`
      - `is_empty()`
      - `clear()`
      - `focus(...)`
      - `new_region(...)`
      - `add_label(...)`
      - `save(...)`
    - persistent selections can now be restored into `active_selection` via `view.selections.activate(tag)` and `view.selections[tag].activate()`
  - `selections` now exist as a first-class persistent category:
    - `view.selections.add_from_active_selection(tag=...)`
    - `view.selections.records()`, `count()`, `info()`
    - per-selection wrappers with `focus(...)`, `new_region(...)`, and `add_label(...)`
    - selections are stored by `atom_indices` and treat derived hierarchy indices as summaries
    - they do not create scene representation automatically
    - they replay/export as explicit non-visual viewer messages
  - The context menu now also exposes `Save Selection` from `active_selection`.
    - It uses an inline tag composer instead of `prompt()`.
    - The UI -> Python bridge executes `active_selection.save(tag=...)`.
    - this turns the selection into a real object of work instead of a raw event payload
  - The current bridge is intentionally narrow:
    - region creation uses stored `active_selection.atom_indices`,
    - label creation currently requires an active selection resolving to exactly one `group`,
      and the current UI capture path is now a minimal inline composer inside the viewer menu.
    - measurement persistence currently replays the last interactive `distance` / `angle` / `dihedral` by storing its `picks_atom_indices`.
  - Measurements now also have an explicit replay/runtime path of their own:
    - Python can send `add_distance_measurement`, `add_angle_measurement`, and `add_dihedral_measurement`,
    - JS reconstructs them through Mol* `StructureMeasurementManager`,
    - they are tracked as `measurement` layers and replayed across rebuild/export.
    - `view.measurements` now also has a minimum inspection surface:
      - `count()`
      - `records()`
      - `info()`
  - `_build_export_messages()` now has an integral regression over the current reproducible workbench surface:
    - `create_region`
    - `set_region_representation`
    - `add_label`
    - `update_label`
    - `add_distance_measurement`
    - `add_angle_measurement`
    - `add_dihedral_measurement`
    - `set_camera_snapshot`
  - measurement APIs now also have nominal argdigest coverage for their explicit
    atom-pick arguments (`atom_indices_a` ... `atom_indices_d`), removing the
    warning path that the integral export regression exposed
  - Region creation from active selection is now confirmed as a reproducibility
    operation first:
    - it creates a real region object and export messages,
    - but does not imply an immediate visual change unless a representation/show
      path is also applied.
  - Validation note:
    - JS regression remains green,
    - Python regressions for `tests/test_annotations.py` are green again after fixing layer-tag/delete replay bookkeeping in `molsysviewer`,
    - the latest hardening also added replay-safe label reanchoring with `view.annotations.set_group_index(...)`,
    - the `new_region_from_active_selection(...)` path required one contract fix so region representations are recorded explicitly as `set_region_representation` during replay/export,
    - the UI-to-Python bridge now executes `Create Region from Selection`, `Add Label from Selection`, and `Persist Last Measurement` directly from `interaction_context_action`,
    - broader Python validation outside the annotation slice may still see sibling-checkout instability in `../molsysmt`, so package-wide reruns should be treated separately from this local block.
  - A dedicated smoke runbook now exists in `devguide/smoke_test.md` so we can evaluate:
    - interaction correctness,
    - UX feel,
    - and exploration -> reproducible-state flows together instead of as disconnected features.
  - Current smoke automation result:
    - `pytest tests/test_annotations.py tests/test_reproducible_interaction.py tests/test_measurements.py tests/test_interaction_events.py -q` is green,
    - `PW_CHROMIUM_BIN=/usr/bin/google-chrome npm --prefix molsysviewer/js run test:e2e` is now verified as passing on this workstation.
  - Immediate smoke follow-up:
    - after the latest `Bond.Loci -> element loci` normalization, recheck `right click` on visible bonds/links in the main notebook canvas,
    - expected behavior: those clicks should now resolve to the same `group`-centric context target as atom clicks,
    - if not, inspect the exact Mol* loci returned for bond fragments in notebook embedding before broadening interaction further.

## Active Decisions

- Treat reproducibility as a primary product goal, not just a packaging/export concern.
- Prefer features that convert exploratory interaction into replay-safe, rebuild-safe, exportable state.
- Avoid growing interaction-only affordances without a credible path to:
  - Python representation,
  - replay,
  - rebuild,
  - export,
  - or explicit scientific state capture.
- Use real demo viewers when regression value depends on real MolSysMT behavior.
- Prefer contract-level and externally observable assertions over private implementation coupling.
- Treat `DigestNotDigestedWarning` on stable public API as integration debt, not benign noise.
- Keep `MolSysView` small; place advanced composition/analysis operations in `molsysviewer.tools`.
- Keep the interaction contract aligned with MolSysSuite vocabulary:
  - use `elements` / `element levels` instead of overloading `structure` in picking/selection docs.
- Let users work with `MolSysView` in both styles:
  - object-oriented (`view.get(...)`, `view.set(...)`, ...)
  - functional (`tools.basic.get(view, ...)`, `tools.basic.set(view, ...)`, ...)
- Keep scene-centric inspection affordances on the object side even when an equivalent pure helper could exist:
  - focus operations belong to `MolSysView` / `Whole` / `Region`,
  - region-partition helpers belong to `MolSysView` when they create live region objects.
  - prefer one parameterized entrypoint (`make_regions_by(element=...)`) over multiple thin `split_by_*` variants.
- Keep `tools.basic.compare(...)` explicitly molecular for now; if scene comparison is needed later, that should be a separately documented contract.
- Treat internal rebuild/replay as internal state application:
  - it must not re-digest already normalized state,
  - it must preserve replayable `_message_history`,
  - it must preserve region/layer/tag continuity.
- Keep environment workarounds narrowly scoped to concrete failing paths, not as blanket repository policy.
- Treat sibling support libraries (`argdigest`, `depdigest`, `pyunitwizard`, `smonitor`) as active engineering dependencies, not passive externals.
- Keep `molsysviewer` on one local `pyunitwizard` instance/configuration path.
- Prefer `smonitor` `extra_factory` + `SIGNALS` contracts on the main orchestration wrappers when that makes developer/QA debugging materially better.
- Keep persistent labels out of `shapes`; the category should be `annotations`.
- Keep hover tooltips and persistent annotations as separate concerns.
- Keep `annotations` layer-aware from the first implementation.
- Keep the first annotation slice narrow:
  - explicit text,
  - one `group` anchor,
  - no atom labels or free-point labels yet.
- Keep the first exploration -> reproducible-state bridge narrow and explicit:
  - active selection may become a region,
  - active selection may become a label when it resolves to exactly one `group`,
  - the last interactive measurement may become a replayable measurement artifact,
  - broader UI flows should come only after the Python-side contract is stable.
- Keep persisted measurements as explicit viewer artifacts:
  - persist picks, not opaque frontend state,
  - rebuild by replaying the same measurement op through Mol*,
  - keep them layer/tag aware like other non-element scene artifacts.
- Use Mol* rather than MolSysMT as the first engine for interactive distance/angle/dihedral:
  - Mol* already owns the live picked loci and the native measurement representations,
  - MolSysMT remains appropriate for later Python-side analysis or validation, not for the first interactive gesture loop.
- Keep measurement tool feedback local-first in JS:
  - active mode and pick progress should be visible in the canvas without requiring Python callbacks,
  - Python still receives state/result events for inspection, automation, and notebook use.

## Next Step

- Continue building out the interaction stack, but subordinate it to reproducibility.
- The next high-value work should increasingly convert exploration into explicit state:
  - selection -> region,
  - selection -> label,
  - measurement -> persistent/replayable artifact,
  - and then richer mixed-selection semantics only where they help that goal.
- The UI now exposes that direction explicitly in the active-selection context menu,
  and the Python-side bridge for the current narrow slice has been revalidated.
- The measurement branch has now advanced one step further than selection/label:
  - persisted measurement ops exist in the runtime,
  - the menu now exposes and executes a first explicit UI affordance for committing the last interactive measurement,
  - the current label-text capture path has already moved from `prompt()` to a small inline composer,
  - the remaining work is refining that composer UX and broadening reproducible interaction flows.
- Enrich `active_selection` beyond the current element/annotation/shape slices toward richer mixed behavior and metadata quality only when that improves reproducible scientific workflows.
- Grow `GroupStrip` from the current selection/focus/hover/context slice toward:
  - range selection,
  - region overlays,
  - tool-pick overlays.
- Formalize the path from current representation mechanics into the future `styles` model:
  - today the repository has real `representation`, `preset`, and `user_preset` support,
  - but it does not yet have a public first-class `Style` object or `Scene Style` / `Focus Style` runtime contract,
  - so the next design/implementation step should define that first narrow reproducible slice explicitly rather than treating the vision page as if it were already implemented.
- Decide the next annotation-interaction step carefully:
  - keep current label overlays on the strip,
  - keep the new strip-seeded `annotation` context + selection slices stable,
  - then choose between canvas annotation pickability or richer mixed-selection semantics before broadening the model further.
- Use the current active-selection section in the context menu to make selection useful before adding more target families:
  - `Focus Selection`,
  - `Clear Selection`.
- Keep pushing MolSysViewer toward a molecular-system inspection/workbench role for structural biochemistry and drug-design workflows, not only a viewer/export role.

Why this is next:

- The live-edit matrix now covers:
  - single operations,
  - a consecutive mutation chain,
  - and replay/export safety of the rebuilt history.
- The next high-value core gaps are no longer centered on rebuild mechanics, baseline visibility semantics, or popup/export synchronization basics.
- The strongest remaining architectural risks are:
  - broader export reliability outside the already-tested rebuild chain.
  - replay ordering and camera/state continuity across embedded/exported flows.
  - feature breadth toward the still-incomplete 1.0 surface.
  - functionality that is still simply not implemented yet.
- The core product risk is not lack of interactivity by itself.
  It is letting interaction outrun reproducibility.
- The next steps should therefore prefer features that preserve the project identity:
  exploration that can be captured, replayed, rebuilt, and shared.
- The support-library layer is now in active hardening, so regressions there should be caught early instead of worked around ad hoc.
- The second `smonitor` pass is now covering real traceability behavior, not just configuration/catalog presence.
- The current `smonitor` integration is now close to exhaustive on the main public orchestration surface.
- The next work should benefit from cleaner `argdigest` behavior on the public API instead of accumulating more migration warnings.
- The standard test entrypoint is again reliable for package-root imports, so export/import regressions can be exercised with plain `pytest`.
- `concatenate_structures(...)` was the correct first step because it opened `tools` with a pure composition primitive that reused stable contracts we already hardened.
- `merge(...)` is the correct second step because it defines the policy for multi-view composition explicitly instead of leaving regions/layers/shapes/tag collisions as ad hoc user work.

## Immediate Plan

1. Enrich `active_selection` from the current group-centric element-only slice toward the documented taxonomy:
  - `element`,
  - `shape`,
  - `annotation`,
  - `mixed`,
  - `empty`.
2. Keep lifting the current element-only selection semantics toward richer hierarchy coverage and metadata quality without inventing fake `component`/`molecule` semantics.
3. Broaden `GroupStrip` from the current narrow slice toward the documented interaction contract:
  - range selection,
  - overlays for regions/annotations/tool picks.
4. After that base is in place, use `active_selection` for:
  - future context-menu enrichment,
  - annotation pickability decisions,
  - Python callbacks on interaction objects instead of only raw last-event snapshots.

## What We Learned About `set()`

- `MolSysView.set()` needed a MolSysViewer-side wrapper instead of blind delegation to `molsysmt.set(...)`.
- The important fixes were:
  - resolving attributes with `include_none=True`,
  - calling the concrete `set_*` function with `skip_digestion=True`,
  - normalizing `coordinates` as a quantity with length units before applying the setter.
- With that adapter in place, at least these core paths are now covered and working:
  - topological string edit (`group_name`),
  - structural edit (`coordinates` with units).

## Immediate Plan

1. Pick the next core cross-cutting behavior:
  - move to canvas interaction and picking/hover behavior.
2. Keep the first interaction slice narrow:
  - transport Mol* hover/click events to Python,
  - store the last hover/click payload on the view,
  - keep the payload atom-centric for element picks.
3. Delay richer interaction semantics until the transport contract is stable:
  - active selection wiring,
  - region-aware picks,
  - shape-aware picks,
  - shared highlight/selection,
  - real tool-mode state instead of menu-seeded placeholder actions.
4. Return to support-library integration only if a new product path exposes a real contract gap.
5. Use the annotation taxonomy in `devguide/annotations.md` when label work starts; do not re-open the `shape` vs `annotation` split ad hoc.
6. When interaction implementation starts, treat click-vs-drag discrimination on both mouse buttons as part of the core contract, not a later polish task.

Interaction design reference:

- the interaction contract now lives across:
  - `devguide/interaction_overview.md`
  - `devguide/interaction_targets_and_selection.md`
  - `devguide/interaction_gestures_and_menus.md`
  - `devguide/interaction_modifiers_and_future.md`
- together, these pages define:
  - target taxonomy,
  - gesture semantics,
  - `active_selection`,
  - `context_target`,
  - measurement/tool-mode planning,
  - and tracked modifier ideas.

Strip design reference:

- `devguide/strips.md` now records:
  - why a 1D strip matters,
  - why `GroupStrip` is the right first strip,
  - which alternatives were considered and rejected,
  - and why strip work should follow immediately after `active_selection` is clarified.

## Criteria

- Do not treat generated JS artifacts as implementation source.
- Preserve Python <-> TypeScript payload/message contracts.
- Preserve region/layer/tag identity across rebuilds.
- Keep `_message_history` replay-safe for HTML export and popup/docs-lite flows.
- Prefer evidence-based docs over inherited setup folklore.

## Technical & Scientific Assessment (March 2026)

This assessment captures the current health and strategic position of the library.

### Engineering & Architecture
- **Hybrid Model Success:** The choice of `anywidget` + Mol* + Python (MolSysMT) is validated. It successfully bridges high-performance WebGL rendering with a robust scientific state in Python.
- **Replay & Export Resilience:** The `ViewerMessage` history and replay mechanism are the core strengths for scientific reproducibility and static HTML exports.
- **Support Layer Hardening:** The integration of SMonitor/ArgDigest/DepDigest provides a professional-grade API surface, though it adds a significant maintenance overhead (the "over-engineering" risk).

### Scientific Workbench Direction
- **Inspection-Centricity:** The library is successfully moving from a "renderer" to a "workbench". The group-centric picking and measurement tools are the right steps.
- **Taxonomy Alignment:** Strict adherence to MolSysMT hierarchy (`group`, `chain`, etc.) is a major differentiator for structural biology workflows.

## Open Risks & Critical Points

- **Rebuild Fragility:** The atom-index remap logic during live-edits (`remove`, `add`, `set`) is technically complex and a potential source of silent corruption if state synchronization fails.
- **Atom vs. Group Tension:** The UX switch between atom-level (measurements) and group-level (inspection) picking needs to be seamless to avoid scientist frustration.
- **Build Artifact Dependency:** Reliance on generated `viewer.js` adds friction to frontend development and requires strict discipline to avoid manual edit corruption.
- **E2E Testing Gap:** Interactive breadth (clicks, gestures, tool modes) is still under-tested compared to the robust runtime/protocol coverage.
- **large Systems Performance:** The Python-to-TS payload transfer for systems with millions of atoms is a potential bottleneck that hasn't been fully stress-tested.

## Maintenance, Scalability, and Lifecycle Risks

These deeper technical challenges affect the long-term sustainability of the project:

### 1. Ecosystem Coupling & Maintenance Burden
- MolSysViewer is the "integration hub" for the UIBCDF ecosystem (MolSysMT, ArgDigest, SMonitor, PyUnitWizard).
- **Risk:** Any breaking change in sibling libraries forces an immediate update in MolSysViewer's decorators, digesters, and signals. The cost of "ecosystem synchronization" competes with feature development.

### 2. Protocol Complexity & "Bus Factor"
- The custom `ViewerMessage` protocol and its TypeScript handlers are powerful but have a steep learning curve.
- **Risk:** Deep knowledge of the Python/JS bridge is currently concentrated. Failure to democratize this architecture through better internal documentation or simpler patterns increases project fragility.

### 3. Latency vs. Consistency Policy
- Hybrid architectures face a trade-off between instant local (JS) feedback and scientifically consistent (Python) validation.
- **Risk:** Without a clear policy on which operations must be "local-first" vs. "round-trip-required," the user experience may feel laggy or inconsistent, especially in large-scale systems or high-latency environments.

### 4. Message History Bloat & Snapshotting
- Operations like `merge()` and consecutive live-edits grow the `_message_history`.
- **Risk:** Static HTML exports carrying a massive replay log will suffer from slow initialization and memory bloat. A "message compaction" or "snapshotting" strategy is needed for 1.0 but is currently missing from the implementation.
- `add()` still depends on a scoped `NUMBA_CACHE_DIR` workaround in this environment.
- Popup/popout behavior is still lighter in coverage than live-edit, but no longer the clearest blocker for resuming implementation.
- `argdigest` still does not cover every public shape/detail argument; the remaining gaps should be prioritized by real product usage and warnings, not by raw parameter count.

## Useful Follow-ups

- Extend `molsysviewer.tools.basic` beyond `merge(...)` only when the next composition/analysis policy is explicit enough to document and test.
- Add canvas interaction work:
  - `Done`: minimal hover/click event transport from Mol* to Python with atom-centric payloads.
  - `Done`: `active_selection` integration with `GroupStrip` and `GroupPanel`.
  - `Done`: annotation (label) synchronization between Mol* and `GroupPanel` (badge overlays).
  - `Next`: implement the richer contract now documented in the new interaction pages under `devguide/`.
- Keep `GroupStrip` in scope as the first strip-style companion view once `active_selection` is concrete enough.
- Continue visual and behavioral refinement of pockets and pharmacophore overlays.
- Add popup/popout sync regressions around camera/state replay if the harness can support them.
- Add export regressions that mix camera snapshots, visibility cleaning, and replay ordering.
- Expand JS tests from guards into more success-path and replay-sensitive behavior where seams are controllable:
  - `Done`: added `group-panel-interaction.e2e.ts` verifying load -> select -> label flow with Google Chrome.
- Add targeted `smonitor` refinements only when a new public orchestration path is introduced.

### Progress March 2026 (Mid-Month Update)

- **Interaction & E2E:**
  - Added `group-panel-interaction.e2e.ts` verifying load -> select -> label flow.
  - Added `measurements-interaction.e2e.ts` verifying Distance and Angle measurement tools from the context menu.
  - Added `hierarchy-interaction.e2e.ts` verifying hierarchical Molecule/Component selection in the GroupStrip.
  - Implemented Range Selection using `Shift + Alt + click` both in the 3D canvas and GroupStrip.
  - Added cross-view anchor synchronization for range selection.
  - Enforced usage of `google-chrome` for E2E tests to ensure WebGL availability.
- **Structural Rebuild Robustness:**
  - Fixed a critical gap where specialized history lists (shapes, annotations, measurements) were not updated with remapped indices during a structural rebuild.
  - Corrected `_record_shape_message` to prevent duplicate replaying of measurements and labels.
  - Verified that hierarchical metadata (Molecule/Component) survives structural modifications and is correctly re-emitted to the frontend.
  - Validated persistence of annotations, measurements, and saved selections across structural edits via stress test (`test_rebuild_persistence.py`).
- **GroupStrip Hierarchy:**
  - Implemented nested visualization (Molecule -> Component -> Group) in the `GroupPanel` using colored left-border lines.
  - Enabled hierarchical selection: clicking on the molecule or component border markers selects all child atoms.
  - Enriched the Python-to-JS payload with `molecule_index` and `component_index` data from MolSysMT.
  - Persisted hierarchical metadata in Mol* via custom `atom_site` columns.
- **Annotation Sync:**
  - Fixed gap where `add_label` messages were not notifying the `GroupPanel`.
  - Labels now show up as "L" badges in the `GroupStrip`.
- **ArgDigest Coverage (Shapes):**
  - Implemented missing digestors for complex shape arguments: `iso_levels`, `iso_colors`, `iso_alphas`, `eigenvalues`, `eigenvectors`, `tensors`.
  - Refactorized `PocketSurfaces` and `AnisotropyEllipsoids` to remove manual normalization, simplifying the Python API and improving robustness.
- **Testability & Infrastructure:**
  - Added data attributes to UI components for stable E2E selection.
  - Updated E2E harness to maintain a message history log (`__messages`).


## Current Panel Direction

The current adopted container direction is:

- `GroupPanel` docked laterally on the left
- collapsed by default
- the chevron tab is physically attached to the panel and remains visible as the only exposed part when collapsed
- the panel slides as one piece, so the tab behaves like a true sidebar handle
- the notebook embedding now clips viewer overflow explicitly so the sliding panel does not provoke output-cell scrollbars or canvas blink/reflow loops

This is preferred over a permanent lower band because it preserves canvas area while keeping the strip tool quickly reachable.

## Current Panel-Mode Convergence

- `Navigate` and `Workbench` already expose a shared minimal navigator in the drawer header chrome.
- The runtime can now jump directly:
  - `Navigate -> Workbench`
  - `Workbench -> Navigate`
- This is still an intermediate step before the final shared `panel mode` container and its definitive navigator (`tabs` first, `carousel` later if it still proves useful).

## Packaging Progress March 2026

- The Qt-for-Python packaging split is now operational and pushed in sibling
  repos on branch `6.9.2`:
  - `../shiboken6-uibcdf`
  - `../pyside6-essentials-uibcdf`
  - `../pyside6-addons-uibcdf`
- Each sibling repo now has a local `devguide/` documenting:
  - where the upstream code came from
  - how the first `6.9.2` boundary was derived
  - and how to reopen the line for a future `6.10.x` family without depending
    on this repo as the only memory of the process
- `shiboken6-uibcdf` has now crossed an important first boundary:
  - the initial manifest-driven recipe no longer depends by default on the
    external `molsyssuite-qt-spike` environment
  - the first validated `shiboken6` boundary was copied into:
    - `package_boundary/site-packages`
  - `devtools/conda-build/build.sh` now stages from that repo-local boundary by
    default
  - a non-GUI smoke still passes when staging to a temporary `site-packages`
    and importing `shiboken6` from the staged tree
- `pyside6-essentials-uibcdf` and `pyside6-addons-uibcdf` are still earlier in
  this migration:
  - both already have vendored upstream subsets
  - both already have manifest-driven recipes
  - `pyside6-essentials-uibcdf` has now also crossed the same first boundary:
    - the initial manifest-driven recipe no longer depends by default on the
      external `molsyssuite-qt-spike` environment
    - the first validated `PySide6_Essentials` boundary was copied into:
      - `package_boundary/site-packages`
    - `devtools/conda-build/build.sh` now stages from that repo-local boundary
      by default
    - a non-GUI family-level smoke passes when staging:
      - `shiboken6-uibcdf`
      - `pyside6-essentials-uibcdf`
      into a temporary `site-packages` and importing `PySide6.QtCore`
    - the first repo-local boundary push is large but still accepted by GitHub;
      at least one file (`PySide6/lupdate`) already triggers the GitHub
      warning threshold at about 52.5 MB, so payload size needs to stay visible
      before repeating the same pattern for `Addons`
  - `addons` has now become much more concrete:
    - the full observed Addons payload is about 400 MB
    - the standalone-focused reduced subset
      (`WebEngine + WebChannel + Positioning`) is about 244 MB
    - `pyside6-addons-uibcdf` now defaults to that reduced manifest rather than
      the full Addons payload
    - a family-level smoke passes when staging:
      - `shiboken6-uibcdf`
      - `pyside6-essentials-uibcdf`
      - reduced `pyside6-addons-uibcdf`
      into a temporary `site-packages` and importing:
      - `from PySide6.QtWebEngineWidgets import QWebEngineView`
    - this makes the first public packaging story materially more plausible
      than the earlier full-Addons reading
- Pause checkpoint before the first real local conda builds:
  - the three sibling repos are clean and pushed on branch `6.9.2`
  - `shiboken6-uibcdf` stages from a repo-local boundary by default
  - `pyside6-essentials-uibcdf` stages from a repo-local boundary by default
  - `pyside6-addons-uibcdf` now defaults to the reduced standalone-focused
    manifest rather than the full Addons payload
  - local non-GUI family-level smoke is good for:
    - `shiboken6-uibcdf`
    - `pyside6-essentials-uibcdf`
    - reduced `pyside6-addons-uibcdf`
    with `QWebEngineView` importable
  - `conda-build` was initially missing from the active environment
  - the user then installed `conda-build`, so the next step on resume should
    be the first real build sequence:
    1. `conda build ../shiboken6-uibcdf/devtools/conda-build`
    2. `conda build ../pyside6-essentials-uibcdf/devtools/conda-build`
    3. `conda build ../pyside6-addons-uibcdf/devtools/conda-build`
  - after those builds, the next checkpoint is not release yet:
    - install the three locally built packages into a fresh test env
    - verify the family by import and standalone smoke there
- Real local conda builds now passed for the Linux / Python 3.13 line:
  - `shiboken6-uibcdf-6.9.2-py313_0.conda`
  - `pyside6-essentials-uibcdf-6.9.2-py313_0.conda`
  - `pyside6-addons-uibcdf-6.9.2-py313_0.conda`
- The first real build loop also exposed and validated a recipe fix:
  - `source.path` in the three sibling repos needed to be `../..`
  - not `../../..`
  - otherwise `conda build` pulled in the parent `repos@uibcdf` tree instead of
    the individual package repo
- `shiboken6-uibcdf` now has a real local package build and test pass.
- `pyside6-essentials-uibcdf` now has a real local package build and test pass.
  - it also surfaces a cleanup target for later:
    - template/script files under `PySide6/scripts/.../*.tmpl.py` should
      probably not be compiled or shipped unchanged forever
  - it emits many overlinking / missing-system-DSO warnings, but they did not
    block the first local package build or test
- `pyside6-addons-uibcdf` now has a real local package build and test pass.
  - the reduced standalone-focused manifest remains good enough for:
    - `from PySide6.QtWebEngineWidgets import QWebEngineView`
    in the `_test_env`
- The next checkpoint is now concrete:
  - create a fresh test env
  - install those three locally built conda artifacts
  - verify family imports and the standalone smoke from that clean env
- The next sensible direction is to keep reducing external-environment
  dependence repo by repo, starting from the smallest slice upward.
- The clean-env verification did prove one strong thing:
  - the three locally built conda artifacts can be installed together
  - and the canonical family imports work there:
    - `import shiboken6`
    - `import PySide6.QtCore`
    - `from PySide6.QtWebEngineWidgets import QWebEngineView`
- But the packaging target has now been tightened again:
  - the user requirement is coexistence with a native `PySide6` installation
  - so the provisional UIBCDF family must not keep importing as:
    - `shiboken6`
    - `PySide6`
  - it must move to a separated Python namespace instead, for example:
    - `shiboken6_uibcdf`
    - `PySide6_uibcdf`
  - and `molsysviewer.standalone_qt` must import that suffixed family
- A scratch rename experiment already narrowed the difficulty:
  - simple directory rename plus minimal `__init__.py` patching is enough for:
    - `import shiboken6_uibcdf`
    - `import PySide6_uibcdf.QtCore`
  - but it is not enough for the Addons/WebEngine layer:
    - `from PySide6_uibcdf.QtWebEngineWidgets import QWebEngineView`
      currently segfaults
    - `faulthandler` shows the loaded extension modules still register as:
      - `PySide6.QtCore`
      - `PySide6.QtGui`
      - `PySide6.QtWidgets`
      - `PySide6.QtNetwork`
      - `PySide6.QtPrintSupport`
      - `PySide6.QtWebChannel`
      - `PySide6.QtWebEngineCore`
    - so the current wheel-boundary repackage is not namespace-isolated
- Operational consequence:
  - do not treat the current `*-uibcdf` artifacts as ready for coexistence with
    native `PySide6`
  - the next real packaging step is source/build-time namespace separation for
    the Qt-for-Python family, not more publication work on the current
    canonical-name artifacts
- That namespace-separation work has now started in the two base repos:
  - `shiboken6-uibcdf`
    - initial source/CMake hooks now point at `shiboken6_uibcdf`
    - lazy-loading and signature-support code now also targets
      `PySide6_uibcdf` / `shiboken6_uibcdf`
  - `pyside6-essentials-uibcdf`
    - the missing top-level upstream `PySide6/` package templates were vendored
      into the repo
    - `BINDING_NAME` is now switched to `PySide6_uibcdf`
    - `libpyside` now looks up the top-level package as `PySide6_uibcdf`
    - the top-level `__init__.py.in` now imports `shiboken6_uibcdf`
    - the install/RPATH side has started moving toward the suffixed package
      family as well
- Relevant namespace-split commits now exist upstream of this repo:
  - `../shiboken6-uibcdf`
    - `4954d4a` `feat: start uibcdf python namespace split`
  - `../pyside6-essentials-uibcdf`
    - `fc107ed` `feat: start uibcdf python namespace split`
- The first rebuild loop after that patch also exposed the next necessary
  packaging correction:
  - the recipes were still staging canonical paths from the boundary
    manifests into:
    - `shiboken6/`
    - `PySide6/`
  - so even with source/CMake hooks patched, the built artifacts were still
    being assembled under canonical install paths
  - that has now been corrected in the two base repos:
    - `../shiboken6-uibcdf`
      - `6666f0e` `fix: stage suffixed shiboken package layout`
    - `../pyside6-essentials-uibcdf`
      - `dab1691` `fix: stage suffixed pyside package layout`
  - the next rebuilds of those two repos are therefore the first ones that
    really test the `_uibcdf` install layout end to end
- The next checkpoint is therefore:
  1. define the Python import namespace for the UIBCDF family
     - likely `_uibcdf`, not `-uibcdf`, because Python imports cannot contain
       hyphens
  2. rebuild `shiboken6-uibcdf` and `pyside6-essentials-uibcdf` after this
     first namespace patch and see which additional generated/binary hooks
     still register under canonical names
  3. only then propagate the same namespace split to
     `pyside6-addons-uibcdf`
  4. only after that, adapt `molsysviewer.standalone_qt` to import the
     suffixed family and resume coexistence testing in `molsyssuite-qt-spike`

- That line has now advanced materially:
  - the working family line was realigned from the mislabeled `6.9.2` branch
    to the actual vendored source line `6.10.2`
  - the three sibling repos now also publish branch `6.10.2` on GitHub:
    - `shiboken6-uibcdf`
    - `pyside6-essentials-uibcdf`
    - `pyside6-addons-uibcdf`
  - `shiboken6-uibcdf` is no longer just a theory or partial build:
    - `conda build ../shiboken6-uibcdf/devtools/conda-build` now passes end to
      end on Linux/Python 3.13
    - the successful artifact is:
      - `shiboken6-uibcdf-6.10.2-py313h3fd9d12_0.conda`
    - the package now:
      - builds from source
      - installs into `shiboken6_uibcdf`
      - and passes its import test under conda-build
- Practical consequence:
  - the first member of the `_uibcdf` family is now real
  - the next serious target is `pyside6-essentials-uibcdf`, not more theory on
    whether the namespace-separated family can exist at all
- One tactical pin is now also explicit to avoid future confusion:
  - the current `6.10.2` source-build work is still using `qt6-main =6.9.2`
  - that is a transition choice to keep the first `Essentials`/`Addons`
    source-build loops focused on namespace/build issues
  - it is not yet the final intended compatibility story
  - a later validation remains required:
    - test whether the `*_uibcdf 6.10.2` family also behaves correctly with
      `qt6-main 6.10.2`
## 2026-03-28 Addons 6.9.2 First Source-Build Blocker

- `shiboken6-uibcdf 6.9.2` ya construye como paquete conda local.
- `pyside6-essentials-uibcdf 6.9.2` ya construye como paquete conda local.
- `pyside6-addons-uibcdf 6.9.2` ya fue realineado a:
  - upstream `pyside-setup@v6.9.2`
  - namespace `_uibcdf`
  - source-build real
  - módulo reducido:
    - `QtPositioning`
    - `QtWebChannel`
    - `QtWebEngineCore`
    - `QtWebEngineQuick`
    - `QtWebEngineWidgets`

- El primer `conda build` real de `pyside6-addons-uibcdf` ya pasó:
  - metadata
  - resolución de entorno
  - entrada a `BUILD START`

- El bloqueo actual ya no está en:
  - namespace `_uibcdf`
  - receta de conda
  - toolchain general

- El bloqueo actual es Qt base:
  - `find_package(Qt6 ...)` falla al buscar `Qt6QtPositioning`
  - `qt6-main 6.9.2` en el entorno host no expone `Qt6Positioning`
  - `mamba search -c conda-forge qt6-location` no devuelve resultados
  - `mamba search -c conda-forge qt6-webengine` no devuelve resultados

- Lectura actual:
  - para cerrar `pyside6-addons-uibcdf`, ya no basta con la familia Python:
    - `shiboken6-uibcdf`
    - `pyside6-essentials-uibcdf`
    - `pyside6-addons-uibcdf`
  - también hará falta resolver la capa Qt que `Addons` consume:
    - al menos `QtPositioning`
    - y previsiblemente `QtWebEngine`

- Esto confirma la hipótesis central del trabajo:
  - la distribución limpia del standalone no termina solo en PySide6
  - acaba empujando también una capa Qt adicional no presente en `qt6-main 6.9.2`

- Matiz importante refinado:
  - `qt6-main 6.9.2` sí expone `Qt6WebChannel`
  - en el prefix activo existen:
    - `libQt6WebChannel.so.6`
    - `libQt6WebChannelQuick.so.6`
    - `lib/cmake/Qt6WebChannel*`
  - por tanto, la capa Qt adicional que hoy falta no parece ser `WebChannel`
  - los candidatos reales pasan a ser:
    - `QtPositioning`
    - `QtWebEngine`

- Inventario útil desde `molsyssuite-qt-spike`:
  - `QtPositioning` es pequeño:
    - `libQt6Positioning.so.6` ~668 KB
    - `libQt6PositioningQuick.so.6` ~424 KB
  - `QtWebEngine` es el bloque grande:
    - `libQt6WebEngineCore.so.6` ~190 MB
    - `libQt6WebEngineQuick.so.6` ~780 KB
    - `libQt6WebEngineWidgets.so.6` ~164 KB
    - `libQt6WebEngineQuickDelegatesQml.so.6` ~148 KB
    - `Qt/resources` ~24 MB
    - `Qt/translations/qtwebengine_locales` ~38 MB
    - `Qt/qml/QtWebEngine` ~236 KB
    - `Qt/libexec/QtWebEngineProcess` ~32 KB

- Dependencias directas relevantes:
  - `libQt6Positioning.so.6` depende sobre todo de:
    - `Qt6Core`
    - ICU
  - `libQt6WebEngineCore.so.6` depende de:
    - `Qt6WebChannel`
    - `Qt6Positioning`
    - `Qt6Quick`
    - `Qt6OpenGL`
    - `Qt6Qml*`
    - `Qt6Network`
    - `Qt6Core`
    - más librerías de sistema gráficas/X11/DBus/NSS

- Siguiente corte natural de trabajo:
  - estudiar una capa Qt provisional partida al menos en:
    - `qt6-positioning-uibcdf`
    - `qt6-webengine-uibcdf`
  - reusar `Qt6WebChannel` desde `qt6-main 6.9.2`

## 2026-03-28 qt6-positioning-uibcdf First Success

- Se abrió el repo hermano:
  - `../qt6-positioning-uibcdf`

- Se definió un payload mínimo real desde `molsyssuite-qt-spike`:
  - `Qt/lib/libQt6Positioning.so.6`
  - `Qt/lib/libQt6PositioningQuick.so.6`
  - `Qt/qml/QtPositioning/libpositioningquickplugin.so`
  - `Qt/qml/QtPositioning/plugins.qmltypes`
  - `Qt/qml/QtPositioning/qmldir`

- Se montó una primera receta manifest-driven que instala ese payload en:
  - `$PREFIX/lib`
  - `$PREFIX/qml/QtPositioning`

- El primer build local ya quedó verde:
  - `qt6-positioning-uibcdf-6.9.2-py313_0.conda`

- Los tests del paquete que ya pasaron:
  - `test -f "$PREFIX/lib/libQt6Positioning.so.6"`
  - `test -f "$PREFIX/lib/libQt6PositioningQuick.so.6"`
  - `test -f "$PREFIX/qml/QtPositioning/libpositioningquickplugin.so"`

- Lectura importante:
  - la estrategia de separar la capa Qt faltante empieza a validarse
  - `QtPositioning` se deja empaquetar como pieza pequeña y aislada
  - el siguiente frente natural ya es `qt6-webengine-uibcdf`

## 2026-03-28 qt6-webengine-uibcdf First Success

- Se abrió el repo hermano:
  - `../qt6-webengine-uibcdf`

- Se definió un payload real desde `molsyssuite-qt-spike` con:
  - `libQt6WebEngineCore.so.6`
  - `libQt6WebEngineQuick.so.6`
  - `libQt6WebEngineQuickDelegatesQml.so.6`
  - `libQt6WebEngineWidgets.so.6`
  - `QtWebEngineProcess`
  - `qml/QtWebEngine/...`
  - `resources/qtwebengine*.pak`
  - `translations/qtwebengine_locales/...`

- La receta se apoyó explícitamente en:
  - `qt6-main 6.9.2`
  - `qt6-positioning-uibcdf 6.9.2`

- El primer build local ya quedó verde:
  - `qt6-webengine-uibcdf-6.9.2-py313_0.conda`

- Los tests del paquete que ya pasaron:
  - `test -f "$PREFIX/lib/libQt6WebEngineCore.so.6"`
  - `test -f "$PREFIX/lib/libQt6WebEngineQuick.so.6"`
  - `test -f "$PREFIX/lib/libQt6WebEngineWidgets.so.6"`
  - `test -f "$PREFIX/lib/libQt6WebEngineQuickDelegatesQml.so.6"`
  - `test -f "$PREFIX/libexec/QtWebEngineProcess"`
  - `test -f "$PREFIX/qml/QtWebEngine/libqtwebenginequickplugin.so"`
  - `test -f "$PREFIX/qml/QtWebEngine/ControlsDelegates/libqtwebenginequickdelegatesplugin.so"`
  - `test -f "$PREFIX/resources/qtwebengine_resources.pak"`
  - `test -f "$PREFIX/translations/qtwebengine_locales/en-US.pak"`

- Lectura importante:
  - la capa Qt faltante ya no es una hipótesis
  - `QtPositioning` y `QtWebEngine` ya construyen como paquetes conda locales
  - el siguiente frente natural vuelve a ser:
    - `pyside6-addons-uibcdf 6.9.2`
  - esta vez con:
    - `qt6-positioning-uibcdf`
    - `qt6-webengine-uibcdf`
    disponibles en el host build env

- Siguiente paso natural:
  - decidir si la estrategia correcta es
    - empaquetar módulos Qt adicionales tipo `qt6-positioning-uibcdf` / `qt6-webengine-uibcdf`
    - o cambiar el modelo de `Addons` para usar runtime Qt embebido más cercano al wheel family

## 2026-04-04 Stack completo publicado en el canal uibcdf — Checkpoint final de packaging

### Lo que se completó

El stack Qt-for-Python UIBCDF está ahora **completo, validado y publicado** en el canal
conda `uibcdf` para Linux / Python 3.13. No quedan pasos de packaging pendientes para esta línea.

#### Paquetes publicados (todos en build 3)

| Paquete | Artifact |
|---------|----------|
| `shiboken6-uibcdf` | `6.9.2-py313h3fd9d12_3.conda` |
| `pyside6-essentials-uibcdf` | `6.9.2-py313h3fd9d12_3.conda` |
| `pyside6-addons-uibcdf` | `6.9.2-py313h3fd9d12_3.conda` |
| `qt6-positioning-uibcdf` | `6.9.2-py313_0.conda` |
| `qt6-webengine-uibcdf` | `6.9.2-py313_0.conda` |

#### Repos en GitHub

Los 5 repos están en GitHub bajo la organización `uibcdf`, rama `6.9.2`, con devguides
actualizados incluyendo instrucciones de build local, upload y checklist para 6.10.x:

- `uibcdf/shiboken6-uibcdf`
- `uibcdf/pyside6-essentials-uibcdf`
- `uibcdf/pyside6-addons-uibcdf`
- `uibcdf/qt6-positioning-uibcdf`
- `uibcdf/qt6-webengine-uibcdf`

### Bug crítico resuelto: disambiguación de enums en shiboken

**Síntoma original:** `QFileDialog` y `QMessageBox` requerían `generate="no"` como
workaround porque shiboken confundía `QFlags<QFileDialog::Option>` con
`QFlags<QAbstractFileIconProvider::Option>` (misma enum corta `Option` en clases distintas).

**Causa raíz:** `TypeDatabase::findFlagsType` tiene un "last hope" que itera
`m_flagsEntries` (un `QMap`, orden alfabético) buscando la primera clave que termine
con el nombre buscado. Sin contexto de clase, `"QAbstractFileIconProvider::Options"`
gana sobre `"QFileDialog::Options"` por ser anterior alfabéticamente.

**Fix canónico (shiboken6-uibcdf, dos parches):**

1. `ApiExtractor/typedatabase.cpp` — "last hope" usa `endsWith("::" + name)` en lugar
   de `endsWith(name)`. Evita falsos positivos como `"CheckIndexOptions"` para `"Options"`.

2. `ApiExtractor/abstractmetabuilder.cpp` — en el paso 6 de `findTypeEntriesHelper`,
   antes del "last hope" general, se intentan primero `currentClass::name` y luego
   `baseClass::name` para cada clase base. Resultado:
   - `QFileDialog` + `"Options"` → encuentra `"QFileDialog::Options"` directamente ✓
   - `QFileIconProvider` + `"Options"` → encuentra `"QAbstractFileIconProvider::Options"`
     vía base class scope ✓

**Consecuencia:** No se necesita `DROPPED_ENTRIES` en el CMakeLists de QtWidgets.
`QFileDialog`, `QMessageBox` y `QFileIconProvider` compilan y funcionan sin workarounds.

### Estado de molsysviewer

`molsysviewer/standalone_qt.py` importa directamente desde el namespace `PySide6_uibcdf`:

```python
from PySide6_uibcdf.QtWidgets import (
    QApplication, QFileDialog, QInputDialog, QMainWindow, QMessageBox,
)
```

Validado en el entorno de desarrollo (`molsyssuite@uibcdf_3.13`):

```python
from PySide6_uibcdf.QtWidgets import QFileDialog, QMessageBox, QFileIconProvider
from PySide6_uibcdf.QtGui import QAbstractFileIconProvider
from PySide6_uibcdf.QtWebEngineWidgets import QWebEngineView
# → ALL OK
```

### Supported conda recipe (actualizada)

El entorno de desarrollo del standalone ahora usa conda nativo, sin pip:

```bash
conda install -n <env> \
    -c uibcdf -c conda-forge \
    shiboken6-uibcdf pyside6-essentials-uibcdf pyside6-addons-uibcdf
```

O desde fichero directo (más fiable con el solver):

```bash
conda install -n <env> \
    /path/to/conda-bld/linux-64/shiboken6-uibcdf-6.9.2-*_3.conda \
    /path/to/conda-bld/linux-64/pyside6-essentials-uibcdf-6.9.2-*_3.conda \
    /path/to/conda-bld/linux-64/pyside6-addons-uibcdf-6.9.2-*_3.conda
```

El recipe `pip install PySide6==6.9.2` documentado anteriormente queda **obsoleto**
y no debe usarse para desarrollo del standalone.

### Pendiente (no bloquea uso actual)

- Python 3.11 y 3.12: los parches son Python-version-independent; requiere builds
  adicionales con `python =3.11` / `=3.12` en meta.yaml.
- macOS arm64/x86_64: los parches C++ son platform-independent; principales diferencias
  son `.dylib`, RPATH, y disponibilidad de `qt6-webengine` en conda-forge para arm64.
- Windows: requiere `bld.bat`, adaptación de test commands, y verificar disponibilidad
  de `qt6-webengine` en conda-forge para Windows.
- Runner self-hosted GitHub Actions: Diego planea runner organizacional en uibcdf para
  acelerar CI en todos los repos del ecosistema.

## 2026-04-04 Corrección contratos de cantidad en argumentos espaciales y argdigest [skip ci]

### Contexto

Tras publicar el stack `PySide6_uibcdf` y validar el standalone, se detectaron fallos
en la suite de tests relacionados con cambios de API en `pyunitwizard`:

- `puw.get_form()` ya no acepta tipos Python planos (`float`, `list`, `tuple`,
  `ndarray`). Solo acepta cantidades bien formadas.
- `puw.get_value(quantity, to_unit=...)` requiere una cantidad como entrada.

### Decisión de diseño

**Los argumentos espaciales de las funciones `shapes.*` deben ser cantidades pint,
no floats planos.** Esta es la política del ecosistema UIBCDF desde esta fecha.

Los tests que pasaban valores planos estaban mal escritos y han sido corregidos.

### Defaults visibles como strings

Los valores por defecto de parámetros espaciales usan strings de cantidad (parseable
por `puw.is_quantity()`), lo que hace el contrato visible en la firma sin importar puw:

```python
def add_sphere(self, center="[0.0, 0.0, 0.0] nm", radius="1.0 nm", ...):
def add_links(self, ..., radii="0.2 nm", ...):
def add_spheres(self, centers, radii="1.0 nm", ...):
def add_set_alpha_spheres(self, ..., atom_radius="1.0 nm", ...):
def add_displacement_vectors(self, ..., min_length="0.0 nm", ...):
```

`puw.is_quantity("1.0 nm")` devuelve `True`, así que los digestors y `puw.get_value`
los tratan correctamente sin código especial.

Los parámetros dimensionless (`length_scale`, `radius_scale`) se usan directamente
con `float()` — no necesitan puw.

### argdigest: callers de molsysviewer en digestors n_*

`view.contains()`, `view.whole.contains()`, `view.regions.contains()` y sus variantes
`is_composed_of` usan los digestors `n_*.py` heredados de molsysmt. Estos digestors
aceptan `True` como valor válido solo para los callers conocidos. Se añadieron los
callers de molsysviewer a los 20 digestors `n_*.py`.

### Digestors actualizados: center, centers, radii, radius, atom_centers, alpha

Se añadió soporte `puw.is_quantity()` en los digestors de argumentos espaciales para
que manejen cantidades pint correctamente (incluyendo strings de cantidad).

`digest_alpha` actualizado para aceptar `None` (usado como default en `add_pocket_surface`).

### Orden de mensajes en `_build_export_messages`

`set_addon_runtime_summary` siempre precede a `load_molsys_payload` en `_message_history`
porque `bind_runtime()` se llama en `__init__` antes de que se cargue ninguna molécula.
Los tests que asumían `ops[0] == "load_molsys_payload"` han sido corregidos a
`assert "load_molsys_payload" in ops`.

### Resultado

186 tests pasan (0 fallos) en la suite principal (excluyendo integration/loaders).

## 2026-04-04 Phase C — Maduración de figure export y workbench Scene

### Contexto

El roadmap Phase C tiene como criterio de éxito: "the figure story feels like part of the
workbench, not a bolt-on helper". El problema concreto: la sección Scene del Workbench
mostraba "No scene style selected." para cualquier vista creada con `demo[...]` porque
`workbenchScene` solo se inicializaba en `set_global_representation`.

### Cambios implementados

**Frontend (TS):**

- `viewer-controller.ts` — On any load op (`load_molsys_payload`, `load_structure_from_string`,
  `load_pdb_string`, `load_pdb_id`, `load_structure_from_url`), si `workbenchScene` es null,
  se inicializa con el baseline de figura por defecto:
  `{ figurePreset: "publication-light", figureScale: 2.0, figureVariants: ["dark", "transparent"] }`.
  Esto garantiza que la sección Scene del Workbench siempre muestre información de figura
  tras cargar una estructura.
- `viewer-messages.ts` — Nuevo tipo `SetFigureSpecMessage` (`op: "set_figure_spec"`) añadido
  al union `ViewerMessage`.
- `viewer-controller.ts` — Maneja el op `set_figure_spec`: actualiza `workbenchScene` con los
  campos de figura explícitos (figurePreset, figureScale, figureVariants).
- `viewer-controller.ts` — `set_global_representation` ahora usa spread (`...this.workbenchScene`)
  para preservar información de figura si ya había un baseline.

**Python:**

- `viewer.py` — Nuevo campo `_current_figure_spec: dict | None = None`.
- `viewer.py` — Nuevo método `set_figure_spec(figure_spec: FigureSpec)`:
  - Valida que el argumento sea un `FigureSpec`.
  - Construye el payload `set_figure_spec` con `figure_preset`, `figure_scale`, `figure_variants`.
  - Almacena en `_current_figure_spec` para replay en exports HTML.
  - Envía el op al frontend.
- `viewer.py` — `reset_viewer()` limpia `_current_figure_spec = None`.
- `viewer.py` — `_build_export_messages()` incluye `_current_figure_spec` si no es None.
- `viewer.py` — Importa `FigureSpec` directamente desde `.figures`.

**Tests:**

- `tests/test_image_export_request.py` — 3 nuevos tests:
  - `test_set_figure_spec_sends_correct_op` — verifica el payload enviado al frontend.
  - `test_set_figure_spec_stored_and_included_in_export_messages` — verifica que se incluye en el replay.
  - `test_set_figure_spec_cleared_after_reset_viewer` — verifica limpieza tras reset.

### Flujo de uso (smoke test step 12)

```python
from molsysviewer.figures import FigureSpec

view.set_panel_mode(panel="workbench", expanded=True)
# Scene section ya muestra baseline de figura (desde la carga)

base = FigureSpec.from_view(view, preset="publication-light", scale=2.0)
view.set_figure_spec(figure_spec=base)
# Scene section ahora refleja el spec explícito

view.export.figure("figure.png", figure_spec=base)
view.export.figure_variants("figures/", variants=base.build_variants({
    "dark": {"background": "dark", "preset": "publication-dark"},
}), stem="scene")
view.export.figure_publication_set("publication/", figure_spec=base, stem="scene")
```

### Criterio Phase C: ahora satisfecho

- Scene section muestra figura baseline inmediatamente tras cargar una estructura ✓
- `view.set_figure_spec(base)` conecta la FigureSpec con el workbench ✓
- El spec se incluye en el replay de HTML exports ✓
- JS unit tests: 64 passing ✓

## 2026-05-22 Phase D — Refactor de copia, consistencia de unidades y actualización rápida de WebGL

### Contexto

El roadmap de la Phase D se enfocó en tres grandes ejes: consistencia de unidades físicas según el contrato de `molsysmt`, integración directa de geometrías analíticas complejas desde `topomt`, y rendimiento extremo en trayectorias 3D (para evitar cuellos de botella en Jupyter y lograr 60 FPS). Adicionalmente, se resolvieron dos problemas críticos de base: el desajuste de índices de átomos/estructuras en sub-sistemas moleculares sub-seleccionados y la pérdida de estado visual al copiar descriptores de relieve en `topomt`.

### Cambios implementados

**Core de TopoMT y Addon de Visualización:**
- **BaseFeature.py**: Rediseño de `__copy__` y `__deepcopy__` para duplicar dinámicamente `self.__dict__` en lugar de una lista fija de atributos.
- **integration.py**: Eliminación del workaround `_clone_feature_preserving_state` en `molsysviewer_topomt`; ahora se invoca nativamente `feature.copy(deep=True)`.

**Resolución de Desajuste de Índices (Problem 2):**
- **index_mapper.py**: Nueva clase `IndexMapper` que calcula bidireccionalmente la traslación entre los índices globales del sistema molecular cargado y los índices locales asignados en el visor de Mol*.
- **Integración**: Conexión de `IndexMapper` en la carga (`load_from_molsysmt`), eventos de pick/hover (`_enrich_interaction_payload`), cambios de selección activa, navegación del player de trayectorias, zoom de cámara y la persistencia en `SelectionsManager` y `regions`.

**Consistencia de Unidades en Geometrías de Soporte (Task 3):**
- **ShapesManager.info()** y **MeasurementsManager.info()**: Modificación para que todos los parámetros espaciales (radios, vectores, centros, vértices) retornen cantidades físicas Pint/PyUnitWizard expresadas en nanómetros (`nm`).
- **Intercepción de Eventos**: Conversión automática al vuelo de coordenadas obtenidas mediante interacciones en el canvas ( picks, hovers, medidas ) desde Ángstroms (unidades de Mol*) a nanómetros en Pint.

**Soporte de Accidentes Topográficos de TopoMT (Task 4):**
- **ShapesManager.add_topomt_feature(feature)**: Nuevo despachador unificado que reconoce los tipos de accidentes topográficos de `topomt` (`pocket`, `void`, `mouth`, `channel`, `branched_channel`, `boundary`), extrae automáticamente los puntos/centros/radios/índices, aplica conversiones Pint y los registra en las capas de representación correspondientes (`add_pocket_surface`, `add_channel_tube`).

**Actualizaciones Rápidas WebGL y ACKs de Transacción (Task 5 & partial_coordinates_update):**
- **Python (scene.py / core.py)**: Método `partial_coordinates_update(coords_ang, atom_indices, transaction_id)` para despachar arreglos numéricos de coordenadas y mapear transacciones. Integración de control de flujo (backpressure) en `player.py` para pausar la reproducción hasta recibir el ACK de renderizado de la transacción previa.
- **TypeScript (trajectory-handlers.ts)**: Implementación de `partialCoordinatesUpdate` que sobrescribe directamente en sitio los arreglos de Float32Array (`model.atomicConformation.x/y/z`) de la estructura activa. Incrementa el número de versión `(structure).conformation.id` para indicarle a Mol* que realice una sub-transferencia WebGL directa (`gl.bufferSubData`) en lugar de recrear la geometría del render, logrando latencias de renderizado inferiores a 10ms.
- **TS (viewer-controller.ts)**: Enrutamiento y despacho de los mensajes de coordenadas parciales.

### Pruebas y Verificación

1. **Pruebas de Interacción y Eventos de Transacción (Python)**:
   - `test_trajectory_frame_rendered_transaction_ack()` en `tests/test_interaction_events.py`.
   - `test_add_topomt_feature_*` en `tests/shapes/test_topomt_features.py`.
   - 423 de 423 pruebas de Python pasando exitosamente.

2. **Pruebas de Frontend (JS/TS)**:
   - Nuevo archivo `trajectory-handler.test.ts` en `js/tests/unit/` para probar mutaciones en sitio y emisión de ACKs.
   - 110 de 110 pruebas de JavaScript pasando exitosamente.

### Criterio Phase D: satisfecho

- Unidades Pint consistentes en nanómetros para todas las formas y consultas espaciales ✓
- Carga e integración directa de accidentes topográficos de `topomt` ✓
- Actualizaciones de trayectorias en sitio por WebGL ultra-rápidas (<10ms) con control de flujo por ACKs ✓
- Desajuste de índices resuelto de manera completamente transparente en el backend y frontend ✓

## 2026-06-27 Phase E — Refactor de Layouts Unificados (Integrated, Cinema, Split) y Controles de Opacidad/Anclaje Dinámicos

### Contexto

El roadmap de la Phase E se enfocó en la simplificación de los modos de visualización de MolSysViewer, consolidando 7 presets confusos en 3 modos principales (`classic`, `integrated`, `cinema`). Se introdujeron controles dinámicos directamente en el panel flotante de la interfaz para permitir al usuario cambiar la opacidad, la transparencia del fondo (candado) y el anclaje a pantalla dividida (split) en tiempo real con un solo clic, alineando la molécula automáticamente.

### Cambios implementados

**Frontend (JS/TS):**
- **floating-panel-shell.ts**:
  - Implementación de estado reactivo dinámico (`isSplit`, `isAmbient`) controlado por botones dedicados en la cabecera.
  - **lockButton**: Añadido un botón de candado (🔓/🔒) en la cabecera que alterna entre el fondo transparente interactivo (`ambient`, `pointer-events: none`) y el fondo oscuro modal bloqueado (`integrated`, `pointer-events: auto`).
  - **dockButton**: Añadido un botón de anclaje que alterna entre el panel flotante centrado y el panel lateral izquierdo (`split`). Al activarse, la tarjeta se estira y el canvas 3D se encoge y auto-centra reactivamente a la derecha.
  - **updateLayout()**: Centraliza la aplicación de estilos CSS para posicionamiento absoluto (`left`, `top`, `width`, `height`), bordes, sombras y desenfoque (`blur(20px)`), permitiendo transiciones suaves sin saltos de color ni pérdida de redimensionamiento manual.
  - **Redimensionamiento Tradicional**: Se migró de la escala simétrica basada en `transform: translate` a un posicionamiento absoluto real en píxeles. Arrastrar la esquina inferior derecha ahora fija la esquina superior izquierda, comportándose como una ventana estándar de escritorio.
  - **Unificación de Opacidades**: Se unificó el ciclo de opacidades a una sola escala `[0.90, 0.70, 0.45]` con color base `rgba(18, 18, 22, 0.90)` para ambos modos.
  - **Desactivación de Cierre en Fondo**: Se eliminó el listener de `pointerdown` en el backdrop para evitar que clics erróneos fuera del panel cierren la tarjeta.
- **controls.ts**:
  - Se actualizó el validador `isFocus` para aceptar tanto `"cinema"` como `"focus"` (modo de presentación limpio).
  - En modo `cinema`, se añade el Scrubber Invisible en la base con atajos de teclado no conflictivos y botones multimedia refinados.

**Backend (Python):**
- **viewer/core.py**:
  - Se actualizaron los presets mapeando `"focus"` y `"cinema"` a `("cinema", "integrated")` y mapeando `"integrated"`, `"ambient"` y `"split"` al nuevo panel unificado `"integrated"`.
  - El validador `c_mode_valid` ahora admite `"cinema"`.
- **viewer_mode.py** y **controls_mode.py**:
  - Se añadió soporte para `"cinema"` en la digestión de argumentos.

### Pruebas y Verificación

1. **Pruebas de Inicialización y Presets (Python)**:
   - Se actualizó `tests/test_init.py` para validar la nueva resolución de presets (`integrated`, `ambient`, `split`, `focus` y `cinema`).
   - Toda la suite de pruebas de Python (`pytest tests/`) pasó exitosamente.
2. **Pruebas de Frontend (JS/TS)**:
   - Se validaron todos los módulos modificados. 111 de 111 pruebas de JavaScript pasaron exitosamente (`npm run test:js`).

### Criterio Phase E: satisfecho

- Reducción a 3 modos principales (`classic`, `integrated`, `cinema`) en el backend y frontend ✓
- Botones de control dinámico (`lockButton`, `dockButton`, `opacityButton`) integrados en el shell ✓
- Resizing y posicionamiento absoluto tradicional de ventana implementados sin saltos ✓
- Alineación y centrado de la molécula automáticos reactivos al cambio de docking ✓
- Coherencia y unificación de opacidades y color base de cristal en ambos estados del candado ✓

## 2026-06-29 — PyUnitWizard conversion factor for nm -> angstrom wire boundaries

- Replaced Python-side literal `10.0` conversions at MolSysViewer nm -> Mol* angstrom boundaries with `pyunitwizard.conversion_factor("nm", "angstroms")`, following the TopoMT pattern.
- Covered MolSysMT payload serialization, simulation boxes, partial coordinate updates, measurement distance series, shape wire helpers, and shape/object focus radius conversion.
- This does not close `pending_proposals/units_friction_nm_vs_angstroms.md`: bare numeric visual API values are still interpreted as nm; the pending UX decision is whether to warn or make the default configurable.

## 2026-06-29 — Add-on discovery import side-effect hardening

- `addons.discover()` now loads only `molsysviewer.addons` entry points by default; legacy `KNOWN_ADDON_MODULES` fallback discovery is opt-in via `include_known_modules=True`.
- This prevents importing MolSysViewer from importing heavy add-on stacks such as TopoMT and inheriting their import-time global warning/logging side effects.
- Coordinated with TopoMT/SMonitor fixes for `BUG_global_warning_formatter_hijacked_by_imported_addons.md`.

## 2026-06-29 — Add-on discovery diagnostics exposed in Workbench

- `set_addon_runtime_summary` now carries `discovery_failures` from the view-local add-on manager, preserving `source`, `reason`, and `traceback` for failed entry point loads.
- The Workbench Add-ons section renders non-blocking diagnostic rows for discovery failures while leaving the viewer and successfully loaded add-ons operational.
- Covered by `tests/test_addons.py` and `npm run test:js`.

## 2026-06-29 — Add-on lifecycle exception isolation

- Wrapped `on_enable`, `on_disable`, and `on_context_action` callbacks so add-on exceptions no longer propagate into user cells or leave the viewer half-synchronized.
- `on_enable` failures disable that add-on for the affected view and all lifecycle failures are stored as view-local diagnostics with `source`, `reason`, and `traceback`.
- Lifecycle diagnostics are emitted through SMonitor and surfaced in the Workbench Add-ons section alongside discovery diagnostics.
- Covered by `tests/test_addons.py`, `tests/test_export_messages_e2e.py`, and `npm run test:js`.

## 2026-06-29 — Add-on panel state namespace isolation

- `AddonPanelWidget.state` and `set_state(...)` now use the widget instance bound `_addon_name` instead of `view._active_panel_widget`.
- `ViewAddonsManager.resolve_panel_widget(...)` binds `_addon_name` when instantiating panel widgets, so background updates cannot write into whichever add-on panel is currently active.
- Covered by `tests/test_addons.py` with two live add-on panel widgets writing under simulated panel navigation changes.

## 2026-06-29 — Add-on compatibility and namespace collision validation

- Added `AddonSpec.requires_molsysviewer` with standard Python version specifier validation and early rejection when the installed MolSysViewer version is incompatible.
- `GlobalAddonsRegistry.register(...)` now rejects duplicate add-on namespaces and duplicate global workspace IDs before mutating registry state.
- Added `packaging>=23` as an explicit runtime dependency for PEP 440/specifier handling.
- Covered by `tests/test_addons.py` plus an import smoke check for the new requirement metadata.

## 2026-06-29 — Add-on frontend panel cleanup contract

- Confirmed and documented the add-on ESM `render({ model, el }) => cleanup` contract: returned cleanup functions run before the panel DOM host is unmounted.
- Added a focused JS unit test for cleanup ordering without starting Mol*.
- Fixed add-on panel active-key comparisons to use the actual mounted key (`addon:panel`) instead of `workspace:panel`, avoiding unnecessary remounts when workspace IDs differ from add-on names.

## 2026-06-30 — Suppressed exception diagnostics in state paths

- Added a shared `emit_suppressed_exception(...)` SMonitor diagnostic for recovered internal exceptions that previously disappeared silently.
- Instrumented the prioritized state paths in `IndexMapper`, visibility/module binding, region splitting/scoping, measurement metadata/series fallbacks, state import restoration, and active-selection context refresh.
- Extended the IndexMapper degraded fallback test to assert that an injected failure increments the observable SMonitor warning count.

## 2026-06-30 — Index mapper rebuild orphan cleanup

- Closed `pending_proposals/index_mapper_out_of_sync.md`: public edit APIs already rebuild and remap the viewer state through `add`, `remove`, `set`, and `append_structures`.
- Tightened atom-removal rebuild cleanup so regions, shapes, annotations, and measurements whose atom anchors disappear are removed from Python registries and replay histories instead of lingering as empty/stale objects.
- Added a regression covering fully orphaned region, shape, annotation, and measurement records after `remove(...)`.

## 2026-06-30 — Annotation anchor remap proposal closed

- Closed `pending_proposals/annotation_index_orphan_topology.md` as fully resolved by the rebuild remapping path.
- Existing rebuild persistence coverage verifies surviving annotation anchors are remapped after atom removal.
- The orphan cleanup regression added in the previous round verifies annotations whose anchors are fully removed are dropped from replay history and Python registries.

## 2026-06-30 — Scene look state survives rebuild/export

- Closed `pending_proposals/scene_look_state_reconstruction.md` and the subsumed background-color proposals.
- Added `_scene_look` as the persistent backend state for scene look channels: background, fog, lighting, clip planes, legend, and focus-fade.
- Rebuild now remaps or drops focus-fade atom targets and replays all surviving scene-look messages before the visibility refresh.
- Export now re-injects any scene-look channel missing from the cleaned message history.
- Added regression coverage for look preservation through `remove(...)` and HTML export message generation.

## 2026-06-30 — Player state survives rebuild/export

- Closed `pending_proposals/player_state_persistence_gap.md`.
- Added a backend `_player_state` snapshot driven by `PlayerManager` mutators for fps, step, mode, direction, and active playback state.
- Rebuild and export now replay the current trajectory frame plus canonical `set_trajectory_playback` state, including autoplay when the player was active.
- Added regression coverage for 10 FPS ping-pong export/rebuild and paused custom settings without autoplay.

## 2026-06-30 — Trajectory player frame sync

- Closed `pending_proposals/trajectory_player_sync_desync.md`.
- The frontend now emits throttled `trajectory_frame_changed` events every 200 ms while browser playback is active, carrying `is_playing: true` to avoid confusing live pulses with stop events.
- Python now updates `view.player.index` and preserves `view.player.is_playing` from those events; final stop events without `is_playing` keep the existing exact pause semantics.
- Covered with JS trajectory-handler and Python frontend-event regression tests.

## 2026-06-30 — Empty shape focus fallback

- Closed `pending_proposals/bounding_sphere_empty_sequence_crash.md`.
- `_bounding_sphere_nm([])` now returns a deterministic scene-center fallback instead of raising divide-by-zero or empty-sequence errors.
- `Shape.focus()` now warns and zooms to the scene-center fallback when a shape has no geometric points, instead of aborting the user cell.
- Added focused regressions for the geometry helper and the public shape focus path.

## 2026-06-30 — Payload group-to-residue vocabulary documented

- Closed `pending_proposals/payload_residue_vocabulary_consistency.md` as an intentional boundary translation.
- Documented that Python/MolSysSuite `group_id` and `group_name` are serialized as payload `residue_id` and `residue_name` only because the TypeScript loader materializes them into Mol*/mmCIF `atom_site` residue columns.
- Added comments at both the Python serializer and TypeScript payload interface, and recorded the contract in developer protocol docs.

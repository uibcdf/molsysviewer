# Development Roadmap (Status-Aligned)

Last update: 2026-04-20

This roadmap is status-aligned with the current repository state.
It is organized by execution priority and uses three labels:

- `Done`: implemented and present in codebase.
- `In progress`: partially implemented or implemented with limited coverage/docs.
- `Planned`: not implemented yet or not stabilized.

## Route From `0.13.0` To `1.0.0`

After `0.13.0`, the project is no longer missing a direction.
The near-term problem is now consolidation.

What already exists in meaningful form:

- reproducible scene/state and replay/export foundations
- `Navigate` and `Workbench` as real runtime panels
- add-ons as a real host/view platform with docs, standards, template, and
  lifecycle
- `standalone 0` as a teachable browser-hosted first cut
- a now much stronger `image` / `figure` export story:
  - reusable `FigureSpec`
  - camera-derived figure recipes
  - named figure variants
  - standard publication bundles
  - a visible figure baseline in `Workbench -> Scene`
- a workspace-aware panel runtime with:
  - launcher
  - local panel stacks
  - generic add-on workspace host
- the first coherent reference add-on smoke/demo path for downstream teams

So the path to `1.0.0` should now be:

1. close the shared workbench model
2. validate one richer add-on path on top of that workbench
3. mature figure export enough to feel intentional, not incidental
4. tighten verification and user/developer guidance around the now-real product
5. only then make the final standalone push

The intended release rhythm from here should stay pre-1.0 and incremental:

- `0.14.x`:
  - richer add-on proof through the now-solid workbench/runtime
- `0.15.x`:
  - cross-surface polish and verification tightening
- `0.16.x`:
  - documentation/tutorial tightening and release hardening
- `0.17.x+`:
  - final standalone push
- `1.0.0`:
  - once that standalone host sits on a stable workbench/export/add-on core

This sequence matters:

- standalone is no longer "someday"
- but it also should not become the place where unfinished workbench decisions
  are hidden
- the core viewer must already feel coherent before the final host step

## Current 1.0 Plan

The current preferred execution plan toward `1.0.0` is:

### Phase A. Shared Workbench Consolidation

Status:

- effectively closed, with targeted follow-up only

Goal:

- make `panel mode` feel like one coherent workbench system rather than two
  coordinated drawers plus add-on fragments

Main work:

- keep the shared header and the body-level workbench overview aligned
- strengthen the relation:
  - workspace launcher
  - panel stack
  - workspace overview / runtime deck
  - panel host
- keep `Navigate` and `Workbench` visually and behaviorally aligned
- avoid adding new permanent canvas chrome

Success criteria:

- switching workspace/panel feels native and unsurprising
- `Core` remains the calm default
- add-on workspaces can exist without flattening the product into one giant
  panel list
- the body-level workbench overview already feels like the seed of the future
  workspace mosaic rather than a temporary summary list

### Phase B. Add-On Runtime Proof

Status:

- done enough, reopen only if new structural addon pressure appears

Goal:

- prove that external MolSysSuite teams can start real add-on work without
  forcing another redesign of the host

Main work:

- make at least one reference add-on path more realistic through the shared
  workbench runtime
- keep `standards/`, cookbook, template, runtime contract, and tests aligned
- prefer explicit, teachable contributions over a broad but vague API

Success criteria:

- a downstream team can build against the published add-on contract
- a larger add-on workspace feels plausible in the real runtime
- the host no longer looks "core-only with addon metadata attached"

Current reading:

- the reference add-on path is now teachable and smokeable as one shared
  runtime from both host UI and notebook API
- notebook/runtime queries now expose the same workspace/panel/section shape
  that the workbench renders
- the main reason to reopen Phase B would now be a new real add-on path
  exposing a missing host capability, not lack of credibility in the current
  host
- work that should **not** reopen it:
  - generic chrome
  - abstract contract growth without runtime pressure
  - cosmetic polish that does not improve host credibility

### Phase C. Figure Export Maturation

Status:

- done

Goal:

- move from "serious image export exists" to "figure export feels deliberate"

Main work (completed):

- `FigureSpec` as a frozen reusable recipe for figure export ✓
- `FigureSpec.from_view(...)` captures the current camera ✓
- `FigureSpec.with_overrides(...)` / `build_variants(...)` / `build_publication_variants(...)` ✓
- `view.export.figure(...)`, `figure_variants(...)`, `figure_publication_set(...)` ✓
- `view.set_figure_spec(figure_spec)` anchors a recipe to the workbench and replay ✓
- `Workbench -> Scene` shows the figure baseline immediately on any structure load ✓
- cookbook `figure_export_workbench` documents the full end-to-end flow ✓

Success criteria:

- exported figures reuse explicit camera/state choices ✓
- the figure story feels like part of the workbench, not a bolt-on helper ✓
- the current Mol* pipeline is being exploited well before considering deeper
  rendering ambitions ✓

### Phase D. Product Tightening

Goal:

- tighten the real product surface before the final host push

Main work:

- smoke and regression breadth where runtime contracts are already real
- workbench-oriented tutorials and docs parity
- public docs aligned with:
  - add-ons
  - exports
  - panel/workspace behavior

Success criteria:

- the current public product can be taught without relying on chat history
- the docs tell the truth about the current runtime
- the remaining gap to `1.0.0` is mostly host-level, not conceptual confusion

Current interpretation after `0.15.0`:

- support-library hardening (`argdigest`, `depdigest`, `pyunitwizard`,
  `smonitor`) is now strong enough that it should stop dominating the roadmap
- the best next tightening is no longer generic support work, but workbench/API
  slices that immediately improve the teachable product

Immediate `0.16.x` hardening gate:

- before treating `0.16.x` as the next strong checkpoint, prefer checking that
  the current mature surfaces can be taught and smoke-tested as one product:
  - panel/workspace runtime
  - add-on reference runtime
  - figure export from the workbench
- the preferred final tightening slices before that gate are:
  - docs/navigation parity so users can actually find the mature stories
  - smoke guidance that reflects the same product story and support tooling
  - small regression additions only where a real teaching path would otherwise
    drift
- do not reopen architecture to chase this gate
- if that gate is satisfied, the next major uncertainty should shift toward the
  final standalone/distribution story rather than toward the shared runtime
- current reading after the latest tightening slices:
  - this gate is now materially satisfied and should stop dominating the
    roadmap:
    - the Python smoke subset is green
    - `npm --prefix molsysviewer/js run test:js` is green again
    - docs/API/runtime parity across the three mature stories remains aligned
- the next useful work should be the next real product slice, not another
  large conceptual pass over the shared runtime
- concrete `0.16.0` release gate:
  - the recommended smoke subset remains green
  - docs navigation still makes the three mature stories easy to find:
    - panel/workspace runtime
    - add-on reference runtime
    - figure export from the workbench

## Active Add-On Slice: ElasNetMT

Status:

- panel widget contract implemented and first proof complete (2026-04-17)

Immediate working documents:

- [`elasnetmt_addon_plan.md`](/home/diego/repos@uibcdf/molsysviewer/devguide/elasnetmt_addon_plan.md)
- [`addon_panel_widget_contract.md`](/home/diego/repos@uibcdf/molsysviewer/devguide/addon_panel_widget_contract.md)

Reason to open this slice:

- the add-on host is credible enough that the next useful pressure should come
  from one real downstream-shaped domain
- `ElasNetMT` is a strong fit because it can already reuse existing overlay
  primitives:
  - links
  - displacement vectors
  - anisotropy ellipsoids

What is done:

- add-on registration, lifecycle, context actions, workbench sections: done
- per-view runtime state (`ElasNetMTAddonRuntime`): done
- overlay adapters (contacts, modes, anisotropy): done
- export helper (`build_figure_export_payload`): done
- `AddonPanelWidget` base class + `widget_class` in `AddonPanelSpec`: done
- TS panel host: `workspaceAddonWidgetHost`, ESM blob import, model proxy: done
- Python panel lifecycle: `_mount_addon_panel`, `_unmount_addon_panel`: done
- `ElasNetMTModelPanel` — first `AddonPanelWidget` in production: done
- 12 integration tests in `molsysviewer_elasnetmt`: all passing

What remains:

- broader panel widget coverage in downstream add-ons
- no structural ElasNetMT host work pending

### Phase E. Final Standalone Push

Status:

- done for the pre-`1.0.0` host gate
- packaging decision (A2) closed and validated

Goal:

- turn the already-validated Qt host direction into a credible standalone path
  to `1.0.0`

Main work (completed):

- Qt host satisfies the pre-`1.0.0` sufficiency gate ✓
  - startup/empty-host flow explicit
  - shell-owned load flows: demo, file, PDB ID, generic source ✓
  - clean return to empty host ✓
  - app-level navigation/export affordances ✓
  - shell-level persistence: recent sources, last source, window size ✓
  - host-side error handling no longer silent ✓
  - host stays thin: no duplicate viewer logic, no forked panel semantics ✓
- `standalone_qt.py` imports from `PySide6_uibcdf` directly ✓
- A2 packaging decision chosen and closed ✓
  - 5-package conda-native family published to `uibcdf` channel
  - Python bindings (`shiboken6-uibcdf`, `pyside6-essentials-uibcdf`,
    `pyside6-addons-uibcdf`) built and validated
  - Qt native runtime (`qt6-positioning-uibcdf`, `qt6-webengine-uibcdf`)
    built and validated
  - supported environment recipe documented in
    `devguide/standalone_supported_environment.md`
- packaging strategy rationale documented in
  `devguide/standalone_packaging_strategy.md` ✓

What remains open (not a `molsysviewer` blocker):

- final end-user installation/distribution story (conda recipe for users,
  not just for development)
- multi-platform support (macOS, Windows) — documented in sibling repo devguides
- future build iterations in sibling repos do not require changes here unless
  version pins need updating

Current reading:

- Phase E in `molsysviewer` is materially complete
- the remaining standalone uncertainty is end-user distribution, not host
  credibility or packaging direction
- do not reopen host slices unless a real runtime or QA gap appears

See also:

- `devguide/standalone_direction.md`
- `devguide/standalone_host_plan.md`
- `devguide/standalone_qt_prototype_plan.md`
- `devguide/standalone_supported_environment.md`
- `devguide/standalone_packaging_strategy.md`

## Guiding Principle

MolSysViewer is guided by a simple product idea:

- scientific work has an interactive and exploratory phase,
- but scientific results must remain reproducible.

So the roadmap should not optimize for interaction breadth alone.
It should optimize for interaction that can become explicit, replayable,
rebuild-safe, exportable viewer state.

This affects prioritization:

- `selection`, `regions`, `labels`, `measurements`, `layers`, and scene state
- `selections` should now be treated as their own persistent category, not as a thin alias for `regions`
  matter more than ephemeral interaction for its own sake,
- exploration should tend toward artifacts that can be reproduced later from
  Python or exported viewer state,
- new interaction surfaces should be judged by how well they feed that
  reproducible model.

That principle is also recorded in `devguide/guiding_principles.md`, which
should grow over time as additional project-level principles become clear.

## 1) Core Runtime and Contracts

### Status

- `Done`
  - Python facade centered on `MolSysView`.
  - TypeScript runtime centered on `MolSysViewerController` + handler split.
  - Stable Python -> TS op protocol (`ViewerMessage` union).
  - MolSys payload path (`load_molsys_payload`) with native topology/trajectory construction.
  - Region/layer/whole abstractions with tag-based state.
  - Trajectory control Python API: `view.set_structure(index)`, `view.play(...)`,
    `view.pause()`, `view.set_play_speed(fps)`, `view.current_structure_id`.
  - Workspace switch toast notification in TS (`ViewerController.showToast`):
    shown when `selectWorkspace` changes the active workspace.

- `In progress`
  - Contract hardening by test breadth across all ops and edge paths.
  - Cross-check consistency between docs snapshots and runtime behavior.
  - Support-library integration hardening (`argdigest`, `depdigest`, `pyunitwizard`, `smonitor`) is active because it affects runtime behavior directly.
  - `argdigest` now covers the main noisy public wrappers, but broader shape/detail coverage is still partial.
  - `smonitor` now has regression-backed wrapper coverage beyond config/catalog smoke tests, and the package-wide public signal map is largely enforced structurally.

### Next actions

- ~~Expand protocol-focused tests for non-trivial operations (`set_global_representation`, layer retag, clear/reset interactions).~~ Done (2026-04-21): `tests/test_protocol_contracts.py` — 12 tests covering `reset_viewer`/`clear_all`, `clear_decorations`/`clear_scene`, annotation/measurement layer retag history rewrite, and `set_global_representation` replay after rebuild.
- Keep support-library integration aligned with sibling-library contracts, especially around bootstrap, quantity handling, and public API digestion.
- Keep contract changes additive unless versioned.

### Criteria

- Preserve payload schema: top-level `structures`, each with `coordinates` and optional `box`/`time`.
- Do not reintroduce legacy payload names.

## 2) Structural Editing and Live Rebuild

### Status

- `Done`
  - Live operations exposed in Python: `append_structures`, `set`, `add`, `remove`.
  - Rebuild pipeline remaps indices and replays state/history.

- `In progress`
  - Behavioral stabilization and broader regression coverage for remap/replay scenarios.
  - Rebuild regressions now exist for `remove()`, `append_structures()`, `add()`, `set()`, and a consecutive-operation chain, and combined visibility semantics.

### Next actions

- ~~Extend coverage from rebuild mechanics into combined visibility semantics and replay-sensitive export behavior.~~ Done (2026-04-21): `tests/test_rebuild_visibility.py` — 5 tests for hidden-region stickiness after rebuild + global show, annotation layer-tag retag survival, selection index remapping, and style replay across two successive rebuilds.
- Validate export message ordering (replay-safe after chain) — partially covered; popup live-sync remains only lightly exercised.

### Criteria

- Preserve tag identity and region/layer continuity after rebuild.
- No silent index desynchronization between Python and TS state.

## 3) Shapes and Scientific Overlays

### Status

- `Done`
  - Python and TS support for major overlay families:
    - spheres/alpha-sphere sets,
    - pocket surfaces/blobs,
    - channel tubes,
    - anisotropy ellipsoids,
    - pharmacophore features,
    - links, vectors, triangle faces, tetrahedra.
  - Tag-based registration for selective clear/hide.
  - Exhaustive Python-side digestion for major overlay/detail arguments (PocketSurfaces, AnisotropyEllipsoids).
  - Dict-like interface on `ShapesManager`: `keys()`, `values()`, `items()`.
  - `Shape.focus(duration_ms, extra_radius)`: bounding-sphere focus for any
    shape op family; Python extracts geometry, converts nm → Å, sends generic
    `zoom_to_position` op.
  - `zoom_to_position` TS op + `SceneHandlers.zoomToPosition()`: generic camera
    focus via `plugin.managers.camera.focusSphere(Sphere3D)`.
  - Structure-aware shapes: per-structure coordinate arrays and atom-index pairs:
    - `add_sphere(structure_centers=...)`, `add_triangle_faces(structure_vertices=...)`,
      `add_links(structure_coordinate_pairs=...)`, `add_channel_tube(structure_centers=...)`
    - `add_hbonds(structures=[None, [[donor,acceptor],...], ...])` — topology-only; JS resolves coords from current structure
    - JS rebuilds affected shapes on structure change via `onTrajectoryState` subscription in `ShapeHandlers`
    - `None` in a structure slot hides the shape for that structure

- `In progress`
  - Deep coverage of TS shape handler branches and error paths.
  - Docs parity for all implemented overlays.

### Next actions

- ~~Extend JS tests beyond region-hide to shape routing and tag-index lifecycle.~~ Done (2026-04-21): `shape-handler.test.ts` expanded to 11 tests — `structures_coords` storage for all 5 trajectory-shape families, `addHbonds` warn path, frame subscription (`clearByTag` + render on change, null-frame skip, same-frame no-op), single-subscription guarantee, and `frameUpdateInProgress` concurrent guard.
- Keep filling `argdigest` gaps in shape methods only where the public call surface is actually used or warning-prone.
- Close docs gaps where implemented APIs are still documented as placeholders.

### Criteria

- Keep Python option normalization deterministic and validated.
- Keep shape ops replay-safe for exports and rebuild flow.

## 4) Tools and Advanced Viewer-Safe Operations

### Status

- `Done` (scope intentionally frozen, 2026-04-27)
  - `molsysviewer.tools.basic` provides the viewer-centric composition surface:
    `concatenate_structures`, `merge`, `copy`, `compare`, `make_regions_by`.
  - Focus helpers live on the object side (`Whole.focus`, `Region.focus`, etc.).
  - User docs include a dedicated `tools/` section with module/function pages.

### Decision

`tools` is intentionally kept at its current scope. Molecular analysis (topology,
hbonds, ANM, etc.) belongs in the **MolSysMT addon** — an optional add-on that
connects MolSysMT with the viewer — not here. Expanding `tools` into that territory
would duplicate MolSysMT's surface without benefit and blur the dependency boundary.

The only functions that belong in `tools` are operations that take `MolSysView`
objects as their primary input and produce viewer-centric outputs (new views,
scene comparisons). Everything else → MolSysMT addon.

### Next actions

- No planned additions to `tools.basic`.
- MolSysMT integration → see addon direction in `molsyssuite_addon_direction.md`.

### Criteria

- Do not add analysis primitives that replicate MolSysMT functionality.
- New `tools` entries only if they are unambiguously viewer-centric with no MolSysMT equivalent.

## 5) Visibility, Regions/Layers, and Global Semantics

### Status

- `Done`
  - Atom-level visibility masking from Python.
  - Global vs region visibility split in TS (`show_global` / `hide_global`, region hidden memory).
  - Region/layer acks from frontend to keep Python registries synchronized.

- `In progress`
  - Complex interaction tests are broader than before, but popup/export-connected visibility flows still need more coverage.
  - Support diagnostics are now strong enough that new visibility work should use `smonitor` context/contracts instead of ad hoc debugging.

### Next actions

- Extend coverage from core visibility invariants into popup/export-connected flows.
- Document edge semantics with executable examples in devguide checkpoints as needed.

### Criteria

- `region.hide()` must remain sticky across global show/hide cycles.
- Whole/global operations must not accidentally mutate region-specific hidden state.

## 5.5) Canvas Minimal UX and Panel Architecture

### Status

- `Done` (2026-04-21)
  - Design target fully documented in `devguide/canvas_minimal_ux.md` ✓
  - Workspace launcher/mosaic direction implemented and aligned with spec ✓
  - Coexistence strategy documented in `devguide/canvas_panel_transition.md` ✓
  - `controls_mode="minimal"` implemented: three SVG icon cluster (panel, fullscreen, popup) + `?` help button ✓
    - `HelpOverlay` (two-column cheat-sheet Mouse | Keyboard), toggled by `H` key or button ✓
    - `N`/`W` keyboard shortcuts toggle Navigate/Workbench panels ✓
    - Scene actions (Reset View, Toggle Background, Toggle Spin, Toggle Swing) added to empty-canvas context menu ✓
  - `panel_mode_style="floating"` implemented: `FloatingPanelShell` centered overlay ✓
    - `~72% × 68%` of canvas, rounded card, translucent background, backdrop-click-to-close ✓
    - Zero viewport shift (`panelContentWidth = 0`) ✓
    - `GroupPanel` and `WorkbenchPanel` use `FloatingPanelShell` when `floating=true` ✓
  - Both `"classic"` / `"drawer"` remain defaults; experimental modes activated via constructor argument ✓

### Next actions

- Validate `controls_mode="minimal"` and `panel_mode_style="floating"` through real scientific workflows
- Close the transition decision at `0.16.x` → `0.17.x` boundary (see `canvas_panel_transition.md`)

### Criteria

- Do not switch defaults until scene-facing actions have alternative surfaces
- Do not duplicate panel content logic — only the container/shell differs
- The decision must be closed; indefinite coexistence is not acceptable

## 6) Canvas Interaction and Picking

### Status

- `In progress` — one item pending; everything else is implemented and verified.

**Implemented and verified (do not re-propose):**

- JS → Python transport for `hover`, `click`, `context_menu`, `context_action` ✓
- Four event types: `interaction_hover`, `interaction_click`,
  `interaction_context_menu`, `interaction_context_action` ✓
- Four target families: `kind: "structure"`, `kind: "shape"`,
  `kind: "annotation"`, `kind: "empty"` ✓
- Python stores last events; `view.hover_target`, `view.context_target` wrappers ✓
- Python callbacks fully wired: `view.on_hover(cb)`, `view.on_click(cb)`,
  `view.on_context_menu(cb)` — `_hover_callbacks`, `_click_callbacks`,
  `_context_callbacks` in `core.py` ✓
- `active_selection` mature bidirectional state; context menu bridges
  (Save Selection, Create Region, Add Label) ✓
- **Interactive measurement tool** fully implemented (`measurement-tools.ts`):
  - full state machine: started → progress → completed / cancelled
  - `Escape` key cancels via `window keydown` listener
  - `ToolStatusOverlay` shows pick count and hint in the canvas corner
  - `MeasurementToolController` wired into `viewer-controller.ts`
  - `interaction_tool_state` and `interaction_measurement_created` events
    received and stored in Python:
    `view.get_last_tool_state_event()`, `view.get_last_measurement_created_event()` ✓
- `GroupPanel` with per-chain `GroupStrip` columns, molecule/component
  hierarchy, collapse/expand, auto-scroll ✓
- Strip interactions converged with canvas (same event families) ✓

**Pending — the only remaining item:**

- `region_tags` enrichment: when a picked atom belongs to one or more
  named regions, the `kind: "structure"` payload does not currently include
  which regions that atom belongs to. Decision taken: add an optional
  `region_tags: string[]` field to the existing payload (no new `kind`
  variant needed). Lookup is Python-side: `atom_indices` vs region index sets.

### Next actions

- Add `region_tags: string[]` to the `kind: "structure"` payload for
  `interaction_hover`, `interaction_click`, and `interaction_context_menu`.
  Python enriches the payload after receiving it (it owns the region index).

### Criteria

- Do not add a new `kind: "region"` variant — `kind` describes the Mol*
  object type, not a Python-side category.
- Region tag enrichment must not break existing consumers of the payload.

## 6.5) Annotations and Persistent Labels

### Status

- `Done`
  - `annotations` is a mature Python API surface:
    - `add_annotation(text, selection=..., atom_indices=..., tag=..., layer_tag=...)` — primary entry point ✓
    - `set_anchor(tag, selection=..., atom_indices=...)` — replay-safe reanchor ✓
    - `set_text`, `set_tag`, `set_layer_tag`, `show`, `hide`, `delete`, `clear` ✓
    - `records()` / `info()` dual inspection layers ✓
    - `add_label(group_index=...)` and `set_group_index` kept as deprecated aliases ✓
    - layer-aware, replay/rebuild/export-safe, atom-index remapping on `view.remove` ✓
    - compact "L" badge overlays on `GroupStrip` ✓
    - `annotation` as `context_target` from strip overlays ✓
    - first narrow `annotation` slice in `active_selection` via strip ✓
  - **Objective A** — label visual knobs ✓
    - `add_annotation(..., label_style={"color": "#RRGGBB", "size_em": 1.5, "background": True, "background_opacity": 0.7})`
    - `LabelStyle` type in `viewer-messages.ts`; `styleToVisualParams` in `annotation-handlers.ts`
    - forwarded to Mol* `addLabel` as `visualParams`; stored in `specsByTag` so it survives hide/show cycles
  - **Objective B** — layer-level visibility ✓
    - fixed shared `layer_tag` case: `layerTagIndex` map in `AnnotationHandlers`; `setVisibility(layerTag, ...)` fans out to all member annotation tags
  - **Objective C** — canvas label pickability ✓
    - `tooltip: tag` passed in `visualParams` enables `pickable: true` in Mol*'s `StructureSelectionsLabel3D`
    - hover/click events on labels detected via `ev.current.repr.props.tooltip` → emitted as `{ kind: "annotation", tag, text, atom_indices }`
    - `registerInteractionObservers` uses optional `notifyHover`/`notifyClick` override callbacks
    - `resolveTooltipPayload(kind, ev, annotations, measurements)` extracted as testable pure function; same mechanism covers measurements
  - Atom labels, free-point labels, and shape-attached labels remain deferred.

### Next actions

- Keep annotation API stable; defer new annotation families (callouts, badges, point labels) until a real downstream need appears.

## 6.6) Exploration to Reproducible Artifacts

### Status

- `In progress`
- `active_selection` has a solid Python bridge into reproducible state:
  - `new_region_from_active_selection(tag=...)`
  - `view.annotations.add_label_from_active_selection(...)`
  - `view.measurements.persist_last_measurement(...)`
  - `active_selection.save(tag=...)`
- `view.selections` is the persistent named-selection surface; saved selections can be
  restored into `active_selection` via API.
- Context menu: complete set of selection → reproducible-state bridges ✓
  - `Save Selection` — inline composer with tag input
  - `Create Region from Selection` — inline composer with optional tag; creates region via Python
  - `Add Label from Selection` — inline composer with text input (single-group guard)
  - Region rows: focus, toggle hide/show (eye icon), delete (trash icon)
  - `toggle_region_visibility` / `delete_region` Python handlers wired
- Persisted measurement ops are fully implemented and replay-safe:
  - `add_distance_measurement`, `add_angle_measurement`, `add_dihedral_measurement`
  - replayed through Mol* from stored `picks_atom_indices`

### Next actions

- Richer selection → annotation flows: multi-group label support, label style from
  context menu (color, size), richer inline composer.
- Consider region rename from context menu (inline tag edit after creation).
- Shapes bridge is intentionally deferred: prioritize annotations/regions first; only
  add shape context actions after deciding the replay/rebuild contract.

### Criteria

- The bridge from interaction to persisted state must remain explicit and reproducible.
- Do not hide scientifically meaningful state creation behind frontend-only transient behavior.
- Keep persistent labels separate from hover tooltips.
- Keep annotation taxonomy separate from shape taxonomy.

## 7) Export, Embedding, and Popup

### Status

- `Done`
  - `view.export.html(...)` in `standalone` and `lite` modes.
  - Message-history replay and camera snapshot embedding.
  - Popup host logic with runtime source/module URL modes.
  - `view.export.html(mode='lite')` and `mode='standalone'` are fully
    headless-capable: Python-side only, no live frontend required.
  - `view.export.image(...)` now works without a live Jupyter frontend via a
    three-layer fallback:
    1. live anywidget frontend round-trip (existing path)
    2. Qt WebEngine offscreen rendering (primary headless backend; uses
       `PySide6_uibcdf` or `PySide6` with SwiftShader software WebGL)
    3. playwright fallback (browser binary assumed present; clear error if not)
  - `data-molsysviewer-rendered` DOM signal on `#molsysviewer-root` after
    `boot()` + 2000ms settle: shared synchronization point for both headless
    backends.

- `In progress`
  - Robustness tests for popup sync flows and camera sync edge cases.
  - Documentation parity for embed/export troubleshooting.
  - Baseline export ordering and popup host bootstrap contracts are now covered, but live mirror behavior remains only partially exercised.
  - Popup live-sync baseline is now regression-covered for initial replay and camera fight avoidance, though broader interactive breadth is still limited.

### Next actions

- Add tests around export message cleaning and replay ordering.
- Add explicit checklist for popup host/popout behavior verification.

### Criteria

- Export output must be reproducible from message history.
- Runtime source should remain decoupled from generated-artifact manual edits.

## 7.5) Movie and Video Export (`view.movie`)

### Status

- `Done` (2026-04-27)
  - **Phase 1 — Python data model**: `MovieManager` as `view.movie`. Full
    keyframe timeline API: `add_keyframe`, `add_visibility_transition`,
    `add_camera_orbit`, `add_structure_sweep`, `clear`, `info`,
    `duration_ms`, `to_dict`/`from_dict`, `save`/`load`. 40 Python unit
    tests; all pass.
  - **Phase 2 — JS animation engine**: `movie-handlers.ts` with
    `requestAnimationFrame`-driven `play()`. Camera lerp + normalize-up,
    structure index round-lerp, layer-visibility accumulation,
    loop-restart tracking, `movie_playback_done` event back to Python.
    `play_movie` / `stop_movie` ops. Python `play()`/`stop()` use
    `_send_runtime_only` (not in message history).
  - **Phase 3 — Export pipeline**: JS `exportFrames()` (tick-by-tick,
    `getImageDataUri`, `movie_frame` / `movie_export_done` events).
    Python `export()` polls for completion, decodes PNG frames,
    stitches with `imageio.mimwrite()`. Optional dep: `imageio[ffmpeg]`.
    42 Python tests pass, 1 skipped (imageio guard).
  - **Phase 4 — Convenience builders**: `add_camera_orbit` and
    `add_structure_sweep` (done inside Phase 1).
  - **Phase 5 — Docs**: `docs/content/user/movie/` (index, timeline,
    playback, export) + cookbook `movie_recipes.md` (orbit, sweep,
    storyboard, combined, GIF). Sphinx build: no new warnings.

### Next actions

- Validate `play()` and `export()` through a real scientific session
  (smoke test with a demo system in Jupyter).
- Consider adding `start_time_ms` offset to `play()` for mid-timeline
  preview (deferred open question from the plan).
- Headless export path (standalone/playwright): movie export currently
  requires a live Jupyter canvas; document this limitation clearly.

### Criteria

- `play_movie` / `stop_movie` must not appear in message history or HTML
  export replay.
- `export()` must raise a clear `ImportError` if `imageio[ffmpeg]` is
  absent; never silently fail.
- The timeline serialization format is versioned (`molsysmovie_version: 1`);
  any breaking change must increment the version and add migration logic.

## 8) Testing and Quality Gates

### Status

- `Done`
  - Python test suite covers loaders, shapes, core viewer helpers, and key integration paths.
  - JS unit/e2e scaffolding exists with runnable scripts.
  - `pytest` and `python -m pytest` now resolve the same in-repo package during test collection.

- `In progress`
  - JS coverage is still narrower than the runtime surface, but handler-level breadth is improving.
  - E2E matrix is minimal.
  - Public API digestion coverage now has explicit regression tests for core wrapper methods and selected shape helpers.

### Next actions

- Extend JS unit coverage from handler guards into deeper success-path and replay/remap semantics.
- E2E paths now include: region-hide and annotations+measurements interaction (`test:e2e:annotations`). ✓
- ~~Add further E2E paths for structure-aware shapes~~. Done (2026-04-24): `shape-trajectory.e2e.ts` (`test:e2e:shapes`) — 5 scenarios: trajectory sphere storage, all 5 trajectory-shape families registered via handleMessage, frame navigation updates ShapeHandlers currentFrame, clear_shapes_by_tag persistence, clear_all + reload lifecycle.
- ~~Add further E2E paths for export flows~~. Done (2026-04-24): `export-replay.e2e.ts` (`test:e2e:export`) — 4 scenarios: replay export sequence (structure+region+label+camera), replay order preserved (no null-dereference errors), standalone-like fresh replay after clear_all, update_visibility graceful handling. Also added 2 popup-logic unit tests: `molsysviewer-sync-op` live mirror, `molsysviewer-sync-autohide` listener lifecycle. JS suite: 103 tests.

### Criteria

- Every protocol-significant behavior should be covered in either Python or JS tests.
- Keep E2E deterministic and environment-aware (browser/WebGL constraints).

## 10) Strategic Directions (2026)

To reach a successful **1.0 release**, these three pillars must be prioritized over further support-layer abstractions.

### 1. Close the Interaction & E2E Gap
- The value of MolSysViewer lies in how it feels to interact with it.
- **Priority:** Implement more complex E2E tests simulating real scientific workflows (e.g., "identify a binding site, select it, label it, and measure distances").

### 2. GroupStrip / GroupPanel: The 1D Navigation Pivot
- The 1D strip view (`GroupStrip`) inside `GroupPanel` is a primary differentiator.
- **Current state:** `GroupPanel` is live as a lateral sliding panel with one `GroupStrip` per chain. Molecule/component hierarchy with visual cues (color borders, chevrons, captions), collapse/expand, auto-scroll to selection, and annotation badge overlays are all implemented and regression-tested (76 JS unit tests green). ✓
- **Priority:** This pillar is materially complete. Future growth: drag-range selection within strips, region overlays, richer annotation overlay semantics.

### 3. Documentation for the "Scientific Workbench"
- The documentation must shift from API reference to case-study-driven tutorials.
- **Priority:** Create "Workbench Tutorials" (e.g., "How to analyze pocket contacts") that showcase the library as an integrated tool for structural biochemistry and drug design.

# Public API and stability

This page defines what is public API in MolSysViewer.
It also defines which contracts must remain stable.

## Public Python API

You treat these as public:

- `molsysviewer.viewer.MolSysView`
- `molsysviewer.new_view.new_view`
- `molsysviewer.tools.*`
- `molsysviewer.load.load` (convenience wrapper, if exposed)
- `molsysviewer.demo` (demo viewers used by docs and tests)
- `molsysviewer.config.*` (configuration and user presets)
- `molsysviewer.config.load_project_config`
- `molsysviewer.styles.Style`
- `molsysviewer.styles.BUILTIN_SCENE_STYLES`
- `molsysviewer.styles.BUILTIN_FOCUS_STYLES`
- `molsysviewer.set_structure_scale_budget`

If you rename, remove, or change behavior here, you update docs and add tests.

### `set_structure_scale_budget(budget_bytes)`

MolSysViewer materializes **every** selected structure: `view.molsys` is the
complete selected system, and scientific operations, add-ons and measurements
rely on that. A large trajectory is therefore held in full, in Python and in the
browser.

To keep that honest, a load whose coordinates exceed a budget warns with the
measured size and a concrete `structure_indices` subset that fits. The default
ceiling is 256 MB of coordinates (`atoms x structures x 3 x float32`).

```python
import molsysviewer as msv

msv.set_structure_scale_budget(1024 * 1024 * 1024)  # allow up to 1 GB
msv.set_structure_scale_budget(0)                   # silence the warning
```

It **warns, never refuses** — only you know what your machine can hold. Note
that opening a canvas popup roughly doubles the renderer-side cost, because two
Mol* instances each keep their own coordinate axes.

Current scope clarification for `Style`:

- the current public slice is scene-recipe oriented
- it is still backed by the existing whole-representation pathway
- it does not yet include an independent scene-look layer such as
  `default-look` or `illustrative`

`new_view(...)` includes a convenience argument `load_mode`:

- `"selection"` (default): `selection` subsets the loaded system.
- `"all"`: the full system loads, the whole baseline is hidden, and a
  region tagged `"selection"` is created for the selection.

`molsysviewer.tools.basic` is now a public module. Current public helpers there include:

- `extract(...)`
- `copy(...)`
- `concatenate_structures(...)`
- `merge(...)`

Removed before 1.0:

- `molsysviewer.tools.basic.{get, select, info, convert, contains, compare,
  is_composed_of}`
- `molsysviewer.tools.basic.{remove, add, set, append_structures}`
- top-level `molsysviewer.tools.*` reexports for those removed functions
- `view.{remove, add, set, append_structures}`
- `view.whole.{remove, add, set, append_structures}`

Pure molecular-system reads should use `molsysmt.*(view, ...)`. Live molecular
edits on an existing viewer are provided by the MolSysMT addon namespace:
`view.addons.molsysmt.basic.*`.

`MolSysView` is also explicitly growing an inspection-oriented object API beyond the minimal viewer shell. Public user-facing methods now include:

- `close()`
  - explicitly releases the frontend widget and its owned resources
  - views can also be used as context managers to close them on block exit
- `attributed_to(owner)`
  - context manager for add-ons creating scene objects through the public API
  - objects created inside expose the immutable informational property `owner`
  - attribution does not grant ownership rights or prevent user operations
- `load(..., mode="add" | "replace" | "append_structures" | "auto", ...)`
  - current default is `mode="add"`
  - first load initializes `whole` without creating an automatic region
  - second additive load back-fills block 1 and creates block 2 as automatic regions
  - later additive loads create only the new automatic load-region
  - `mode="append_structures"` is explicit structural extension:
    - it does not add atoms
    - it does not create automatic load-regions
    - it may attach the first structures to a topology-only `_molsys`
  - `mode="auto"` is currently a conservative first version:
    - empty viewer -> `replace`
    - same atom count + no topology in the input -> `append_structures`
    - same atom count + matching topology -> `append_structures`
    - different atom count -> `add`
- `apply_system_edit(new_molsys, atom_index_map=None, ...)`
  - advanced integration primitive for add-ons and tooling
  - replaces the view's molecular system and reconciles viewer-owned state
    (regions, selections, visibility, colors, shapes, annotations,
    measurements, layers, and index mappings)
  - does not define molecular edit semantics; those belong to MolSysMT or an
    add-on
- `contains(...)`
- `convert(...)`
- `extract(...)`
- `is_composed_of(...)`
- `info(source="all" | "molsys" | "view", output_type="styler" | "dataframe" | "dictionary", ...)`
- `focus_selection(...)`
- `focus_region(...)`
- `make_regions_by(...)`
  - limited for now to `element="chain" | "molecule" | "entity"`
- `get_last_hover_event()`
- `get_last_click_event()`
  - current interaction payloads are intentionally minimal and atom-centric
- `hover_target`
  - `info()`
  - `is_empty()`
- `context_target`
  - `info()`
  - `is_empty()`
- `get_last_active_selection_event()`
- `styles`
  - `add(tag, style, ...)`
  - `apply(...)`
  - `builtin_tags()`
  - `builtin_records()`
  - `representation_types()`
  - `representation_type_records()`
  - `representation_param_schema(representation)`
  - `representation_param_schema_records()`
  - `representation_presets()`
  - `representation_preset_records()`
  - `contains(tag)`
  - `get(tag)`
  - `get_builtin(tag)`
  - `tags()`
  - `records()`
  - `count()`
  - `clear(tag=None)`
  - `current()`
  - `info()`
  - `structural_color_schemes()`
  - `structural_color_scheme_records()`
  - `structural_size_schemes()`
  - `structural_size_scheme_records()`
  - `molstar_color_themes()`
  - `molstar_color_theme_records()`
  - `molstar_size_themes()`
  - `molstar_size_theme_records()`
  - `load_project_config(path, apply_default=False)`
  - `focus(style_or_tag=None, *, selection, atom_indices, representation, **params)` — additive overlay over the current scene
  - `clear_focus(tag=None)` — remove one or all active focus overlays
  - `focus_tags()` — list of currently active focus overlay tags
  - `builtin_focus_tags()` — list of built-in focus style names
  - `builtin_focus_records()` — list of built-in focus style info dicts
  - `get_builtin_focus(tag)` — retrieve a built-in focus `Style` by name
- `load_project_config(path, *, apply_default=False)` — convenience bridge: applies styles and add-on defaults from a `_molsysviewer.py` config file in one call
- `active_selection`
  - `info()`
  - `is_empty()`
  - `clear()`
  - `focus(...)`
  - `new_region(...)`
  - `add_label(...)` — deprecated alias for `annotations.add_label_from_active_selection(...)`
  - `save(...)`
  - canvas context-menu removal is contributed by the MolSysMT addon as
    `remove-selected-atoms`; core does not own molecular-editing semantics
- `view.selections`
  - `add(tag, *, atom_indices, items=None)` — direct-index shortcut, no MolSysMT lookup
  - `add_selection(tag, selection, *, element, mask, syntax)` — MolSysMT-based selection
  - `add_from_active_selection(tag)`
  - `activate(tag)`
  - `view.selections.tags()` (method)
  - `count()`
  - `contains(tag)`
  - `get(tag)`
  - `records()`
  - `info(tag=None)`
  - `set_tag(tag, new_tag)`
  - `delete(tag)`
  - `clear(tag=None)`
- `get_last_measurement_created_event()`
- `new_region_from_active_selection(...)`
- `show_orientation_axes(selection="all", *, atom_indices=None, tag=None, alpha=None)` — overlay Mol* orientation-ellipsoid axes; returns Region
- `show_best_fit_plane(selection="all", *, atom_indices=None, tag=None, alpha=None)` — overlay Mol* best-fit plane; returns Region
- `view.annotations.add_label_from_active_selection(...)`
- `view.measurements.count()`
- `view.measurements.records()`
- `view.measurements.info()`
  - current first slice: interactive `distance` / `angle` / `dihedral` measurements are registered automatically as replayable viewer state
  - `info()` and `records()` now expose endpoint metadata:
    - `endpoint_kinds`
    - `endpoint_policy`
    - `endpoint_labels`

Shape methods that accept per-structure arrays are also public:

- `view.shapes.add_sphere(..., structure_centers=[array_per_structure, ...])`
- `view.shapes.add_triangle_faces(..., structure_vertices=[array_per_structure, ...])`
- `view.shapes.add_links(..., structure_coordinate_pairs=[array_per_structure, ...])`
- `view.shapes.add_channel_tube(..., structure_centers=[array_per_structure, ...])`
- `view.shapes.links.add_hbonds(structures=[None | [[donor, acceptor], ...], ...])`
  - per-structure atom-index pairs; JS resolves coordinates from the current loaded structure
  - `None` in a slot hides the shape for that structure
  - arrays are in Angstroms (raw); `add_hbonds` uses atom indices (topology-only)

Related object wrappers are also part of the intended public surface:

- `view.whole.focus(...)`
- `view.whole.set_color(color)`
- `view.regions[tag].focus(...)`
- `view.regions[tag].set_color(color)`
- `view.regions[tag].show_only(...)`
- `view.regions[tag].rename(new_tag)`
  - renames the region in Python state and sends `rename_region` to JS
  - `_build_export_messages()` rewrites prior region ops to use the new tag, so the export replay uses the final name directly
- `view.selections[tag].info()`
- `view.selections[tag].activate()`
- `view.selections[tag].focus(...)`
- `view.selections[tag].new_region(...)`
- `view.selections[tag].add_label(...)`
- `view.selections[tag].set_tag(...)`
- `view.selections[tag].delete()`
- `view.annotations.add_annotation(text, selection=..., atom_indices=..., tag=..., layer_tag=..., label_style=...)`
  - primary entry point for persistent labels anchored to atom selections
  - anchor resolves via MolSysMT selection string or explicit `atom_indices`
  - `label_style` accepts a dict with optional keys: `color` (CSS hex string), `size_em` (float), `background` (bool), `background_opacity` (float 0–1)
  - `add_label(group_index=...)` is a deprecated alias; use `add_annotation` instead
- `view.annotations.add_label_from_active_selection(text, tag=..., label_style=...)`
  - anchors to all atom indices in the last active canvas selection (multi-group supported)
  - `label_style` accepts the same dict as `add_annotation` (`color`, `size_em`)
- `view.annotations.set_anchor(tag, selection=..., atom_indices=...)`
  - reanchor an existing label to a different atom set
  - `set_group_index(tag, group_index)` is a deprecated alias; use `set_anchor` instead
- `view.annotations.set_text(tag, text)`
- `view.annotations.set_tag(tag, new_tag)`
- `view.annotations.set_layer_tag(tag, new_layer_tag)`
- `view.annotations.tags()` (method)
- `view.annotations.count()`
- `view.annotations.contains(tag)`
- `view.annotations.get(tag)`
- `view.annotations.records()`
- `view.annotations.info(tag=None)`
- `view.annotations.show(tag)`
- `view.annotations.hide(tag)`
- `view.annotations.delete(tag)`
- `view.annotations.clear(tag=None)`
- `view.measurements.add_distance(atom_indices, tag=..., layer_tag=..., measurement_style=...)`
- `view.measurements.add_angle(atom_indices, tag=..., layer_tag=..., measurement_style=...)`
- `view.measurements.add_dihedral(atom_indices, tag=..., layer_tag=..., measurement_style=...)`
  - `measurement_style` accepts a dict with optional keys: `color` (CSS hex), `size_em` (float), `background` (bool), `background_opacity` (float 0–1)
- `view.measurements.tags()` (method)
- `view.measurements.contains(tag)`
- `view.measurements.get(tag)`
- `view.measurements.show(tag)`
- `view.measurements.hide(tag)`
- `view.measurements.delete(tag)`
- `view.measurements.clear(tag=None)`
- `view.measurements.set_tag(tag, new_tag)`
- `view.measurements.set_layer_tag(tag, new_layer_tag)`
- `view.selections.add_from_active_selection(...)`

Scene-object managers use the same callable discovery vocabulary. In
particular, `view.shapes.tags()` (method) and `view.layers.tags()` (method)
provide their live tags, and new logical layers are created with
`view.layers.add(tag, ...)`.

Tags are unique within a scene domain, not across the entire scene. A shape,
annotation, measurement, region, selection, and layer may deliberately share
the same tag; APIs resolve identity as `(domain, tag)`.
- `view.movie`
  - `add_keyframe(time_ms, *, camera, structure_index, layer_visibility, easing)`
  - `add_visibility_transition(layer_tag, visible, *, at_time_ms)`
  - `add_camera_orbit(duration_ms, *, n_turns, n_keyframes, easing)`
  - `add_structure_sweep(*, from_index, to_index, duration_ms, start_time_ms, end_time_ms)`
  - `play(loop=False)`
  - `stop()`
  - `clear()`
  - `duration_ms` (property)
  - `keyframes` (property)
  - `info()`
  - `to_dict()` / `from_dict(data)`
  - `save(path)` / `load(path)`
  - `export(path, *, fps, format)` — requires `imageio`; sends `play_movie` with `mode="export"` and collects frames from the JS runtime
- `view.on_hover(callback)` / `view.off_hover(callback)`
- `view.on_click(callback)` / `view.off_click(callback)`
- `view.on_context(callback)` / `view.off_context(callback)`
  - reactive (non-polling) Python callbacks for interaction events
  - callbacks receive the same payload dict as `get_last_hover_event()` etc.
  - multiple callbacks per event type are supported; `off_*` removes a specific one
- `view.export_state()` → JSON-serializable dict
  - captures annotations, measurements, selections, regions, shapes, layers, clipping sections, and whole state
- `view.import_state(state, *, clear_first=True)`
  - replays a state dict onto a viewer with compatible structure
  - `clear_first=True` wipes existing scene objects, clipping sections, selections, and regions before replay
- `view.set_structure(index)`
- `view.play(fps=..., step=...)`
- `view.pause()`
- `view.set_play_speed(fps)`
- `view.current_structure_id` (property)
  - structure/trajectory navigation controls; `@signal(tags=["structures"])`
- `add(...)`
  - lower-level structural merge into `_molsys`
  - updates additive-load block bookkeeping
  - does **not** create automatic load-regions
- `convert(...)`
  - current first slice delegates to the molecular system currently stored in
    the viewer
  - this is intentionally compatible with richer future conversions once
    MolSysMT supports direct `MolSysView` target-form conversions

### Notebook rendering

`MolSysView` implements the Jupyter display hook (`_repr_mimebundle_`). This means:

- If a `MolSysView` instance is the last expression in a notebook cell, it renders automatically.
- `MolSysView.load(...)` does **not** return the viewer, so it does not trigger rendering on its own.
- `MolSysView.show()` remains the explicit way to display the widget in scripts or when needed.

## Internal Python APIs

You can change these without a stability guarantee:

- Most of `molsysviewer._private.*`
- Helper functions inside loaders and shapes modules
- Non-exported functions and private methods (`_name`)

## Python ↔ TypeScript contracts

These are stability-critical:

- MolSys payload schema (Python → JS):
  - top-level `structures` list
  - each structure has `coordinates` (Å), optional `box` as three vectors (Å), optional `time`
  - do not reintroduce legacy names like `positions` or `frames`
- Message protocol (`op` + payload):
  - the TypeScript union type `ViewerMessage` is the contract view
  - changes must be versioned and tested
- Tag semantics:
  - tags must remain stable across regions, layers, and shapes
  - `Layer.set_tag(...)` must keep working across tag renames/merges

See also

- {doc}`protocol_and_payloads`
- {doc}`regions_layers`

## Exports

Preferred export surface:

- `view.export.html(...)`
- `view.export.image(...)`
- `view.export.figure(...)`
- `view.export.figure_variants(...)`
- `view.export.figure_publication_set(...)`

`view.export.image(...)` may receive an explicit `camera_snapshot=...` when the
export should use a saved camera rather than the live current viewport.

`view.export.image(...)` also accepts a first small export-oriented
`preset=...` surface:

- `current`
- `publication-light`
- `publication-dark`

At this stage these presets are intentionally modest. They currently steer only
the background treatment used during the capture itself, and the live viewer
state is restored immediately after export.

`view.export.figure(...)` is now the first explicit figure-oriented wrapper above
raw image export. It currently provides:

- stronger default `scale`
- a `background=...` surface (`white`, `dark`, `transparent`, `current`)
- figure-oriented preset defaults
- an optional reusable `figure_spec=FigureSpec(...)` recipe layer
- `FigureSpec.from_view(...)` to capture the current camera into a reusable
  recipe
- `FigureSpec.with_overrides(...)` to derive small recipe variants without
  mutating the original
- `FigureSpec.build_variants(...)` to expand a named batch of figure recipes
- `view.export.figure_variants(...)` to materialize those named recipes into a
  directory in one pass
- `FigureSpec.build_publication_variants(...)` to get the standard small
  `light` / `dark` / `transparent` publication bundle
- `view.export.figure_publication_set(...)` to export that standard bundle in
  one call

`view.set_figure_spec(figure_spec=FigureSpec(...))` is now public.
It anchors an explicit `FigureSpec` to the workbench (updates `Workbench -> Scene`)
and stores the recipe for replay in HTML exports.
This is the intended way to connect a Python-derived figure recipe to the live
workbench view.

The runtime `Workbench -> Scene` surface now also reflects the current built-in
figure baseline so that figure export is visible as part of the workbench
story, not only as a scripting API.

It is still intentionally modest and should be treated as the first step toward
the future richer `figure` export contract, not as the final publication export
system.

`view.export.html(..., mode="lite")` is a public, user-facing export mode.
It must remain reproducible.

## Standalone 0 bridge

The current pre-`1.0` standalone bridge is intentionally small:

- `molsysviewer.build_standalone0_html(...)`
- `molsysviewer.launch_standalone0(...)`
- `molsysviewer ...`
- `python -m molsysviewer.standalone ...`

These surfaces should be treated as a host-facing bridge built on top of the
existing standalone HTML export path, not as the final standalone product.

The first Qt-host prototype now also exists as an explicit experimental surface:

- `molsysviewer.create_standalone_qt0_window(...)`
- `molsysviewer.launch_standalone_qt0(...)`
- `molsysviewer-qt ...`
- `python -m molsysviewer.standalone_qt ...`

For development, this prototype requires `PySide6` and access to
`PySide6.QtWebEngineWidgets`. If the conda-forge `pyside6` build in your
environment does not expose that module, install the matching
`PySide6-Addons` wheel as a temporary development fallback.

This should still be read as:

- a thin host prototype
- not the final standalone host
- not a second viewer/runtime

Its current purpose is to prove that the existing standalone/runtime path can
live inside a real app window without forking viewer semantics.

If you change:

- the runtime URL logic,
- the initial message replay behavior,
- or popup synchronization,

you must validate the docs-lite output.

## Canvas UX modes

`MolSysView` accepts two experimental constructor arguments:

```python
view = MolSysView(controls_mode="minimal", panel_mode_style="floating")
```

- `controls_mode="classic"` (default): six text buttons (Reset, Full, Bg, Spin, Swing, Pop).
- `controls_mode="minimal"`: three SVG icon cluster (panel / fullscreen / popup) plus a `?` help
  button. Scene actions (reset view, toggle background, toggle spin/swing) move to the empty-canvas
  context menu. Keyboard shortcuts: `H` toggles the help overlay, `N`/`W` open Navigate/Workbench.

- `panel_mode_style="drawer"` (default): Navigate panel 560 px left, Workbench 240 px right.
- `panel_mode_style="floating"`: centered overlay card (~72 % × 68 % of canvas), backdrop-click-to-close, zero viewport shift.

Both `"classic"` / `"drawer"` remain the defaults until at least one scientific workflow
has been validated with the new design (`0.16.x → 0.17.x` horizon).

## Panel Mode

The current pre-`1.0` shared panel-mode entrypoint is:

- `view.set_panel_mode(...)`
- `view.set_workspace(...)`
- `view.set_workspace_panel(...)`
- `view.get_panel_mode_state()`
- `view.workspace_catalog()`
- `view.workspace_panels(...)`
- `view.workspace_sections(...)`
- `view.workspace_runtime()`

This API is intentionally small:

- `panel="navigate"` or `panel="workbench"` opens that panel
- `expanded=False` collapses the current panel-mode surface
- `panel=None` lets the frontend reuse its remembered last panel when opening
- `workspace="core"` selects the native workspace
- other workspace ids select the corresponding add-on workspace when available
- `view.set_workspace_panel("topo", workspace="topomt")` lands directly on a
  local workspace panel from Python/notebook code
- `view.get_panel_mode_state()` returns the last panel/workspace state reported
  by the frontend runtime
- `view.workspace_catalog()` returns the effective workspace list visible to the
  view, including `Core`
- `view.workspace_panels("topomt")` returns the local panel stack for that
  workspace
- `view.workspace_sections("topomt")` returns the visible workbench sections
  for that workspace
- `workspace_catalog()`, `workspace_panels(...)`, and `workspace_sections(...)`
  also reflect the current runtime view of the shared workspace model when the
  frontend has already reported state
- `workspace_runtime()` returns a single notebook-facing snapshot combining:
  runtime state, effective workspace catalog, the current workspace record, the
  current local panel stack, the current active panel record, and the current
  workspace sections

This small surface matters especially for notebook usage:

- it gives Jupyter users an explicit Python control door into the shared
  panel/workspace runtime
- it avoids requiring mouse-only navigation for workspace changes
- it also lets notebook code drive the local panel stack of larger add-on
  workspaces

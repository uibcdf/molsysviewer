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

If you rename, remove, or change behavior here, you update docs and add tests.

Current scope clarification for `Style`:

- the current public slice is scene-recipe oriented
- it is still backed by the existing whole-representation pathway
- it does not yet include an independent scene-look layer such as
  `default-look` or `illustrative`

`new_view(...)` includes a convenience argument `load_mode`:

- `"selection"` (default): `selection` subsets the loaded system.
- `"all"`: the full system loads, the global representation is hidden, and a
  region tagged `"selection"` is created for the selection.

`molsysviewer.tools.basic` is now a public module. Current public helpers there include:

- `select(...)`
- `get(...)`
- `info(...)`
- `extract(...)`
- `set(...)`
- `remove(...)`
- `add(...)`
- `append_structures(...)`
- `contains(...)`
- `is_composed_of(...)`
- `copy(...)`
- `compare(...)`
- `concatenate_structures(...)`
- `merge(...)`

`MolSysView` is also explicitly growing an inspection-oriented object API beyond the minimal viewer shell. Public user-facing methods now include, in addition to the older load/query/edit surface:

- `contains(...)`
- `extract(...)`
- `is_composed_of(...)`
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
  - `contains(tag)`
  - `get(tag)`
  - `get_builtin(tag)`
  - `tags()`
  - `records()`
  - `count()`
  - `clear(tag=None)`
  - `current()`
  - `info()`
  - `load_project_config(path, apply_default=False)`
- `active_selection`
  - `info()`
  - `is_empty()`
  - `clear()`
  - `focus(...)`
  - `new_region(...)`
  - `add_label(...)`
  - `save(...)`
- `view.selections`
  - `add(...)`
  - `add_from_active_selection(...)`
  - `activate(...)`
  - `tags()`
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
- `view.annotations.add_label_from_active_selection(...)`
- `view.measurements.persist_last_measurement(...)`
 - `view.measurements.count()`
 - `view.measurements.records()`
 - `view.measurements.info()`
  - current first slice: persist the last interactive `distance` / `angle` / `dihedral` as replayable viewer state

Related object wrappers are also part of the intended public surface:

- `view.whole.focus(...)`
- `view.regions[tag].focus(...)`
- `view.regions[tag].show_only(...)`
- `view.selections[tag].info()`
- `view.selections[tag].activate()`
- `view.selections[tag].focus(...)`
- `view.selections[tag].new_region(...)`
- `view.selections[tag].add_label(...)`
- `view.selections[tag].set_tag(...)`
- `view.selections[tag].delete()`
- `view.annotations.add_label(...)`
  - current first slice: persistent label on exactly one `group`
- `view.annotations.tags()`
- `view.annotations.count()`
- `view.annotations.contains(tag)`
- `view.annotations.get(tag)`
- `view.annotations.records()`
- `view.annotations.info(tag=None)`
- `view.annotations.show(tag)`
- `view.annotations.hide(tag)`
- `view.annotations.delete(tag)`
- `view.annotations.set_tag(tag, new_tag)`
- `view.annotations.set_text(tag, text)`
- `view.annotations.set_group_index(tag, group_index)`
- `view.annotations.clear(tag=None)`
- `view.measurements.add_distance(...)`
- `view.measurements.add_angle(...)`
- `view.measurements.add_dihedral(...)`
- `view.measurements.persist_last_measurement(...)`
- `view.selections.add_from_active_selection(...)`

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
  runtime state, effective workspace catalog, the current local panel stack,
  and the current workspace sections

This small surface matters especially for notebook usage:

- it gives Jupyter users an explicit Python control door into the shared
  panel/workspace runtime
- it avoids requiring mouse-only navigation for workspace changes
- it also lets notebook code drive the local panel stack of larger add-on
  workspaces

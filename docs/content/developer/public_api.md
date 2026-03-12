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

If you rename, remove, or change behavior here, you update docs and add tests.

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
- `get_last_active_selection_event()`
- `new_region_from_active_selection(...)`
- `view.annotations.add_label_from_active_selection(...)`

Related object wrappers are also part of the intended public surface:

- `view.whole.focus(...)`
- `view.regions[tag].focus(...)`
- `view.regions[tag].show_only(...)`
- `view.annotations.add_label(...)`
  - current first slice: persistent label on exactly one `group`

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

## Exports (HTML lite)

`MolSysView.write_html(..., mode="lite")` is a public, user-facing export mode.
It must remain reproducible.

If you change:

- the runtime URL logic,
- the initial message replay behavior,
- or popup synchronization,

you must validate the docs-lite output.

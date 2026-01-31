# Architecture snapshot (2026-01)
_Last updated: 2026-01-30_

This page preserves a detailed, implementation-oriented snapshot of the current
MolSysViewer architecture. It is not the source of truth, but it is useful when
you need a compact description of the data flow and message protocol.

If you want the current high-level view, see {doc}`architecture` and
{doc}`architecture_full`.

## 1. High-level layers

MolSysViewer is split into:

- **Python layer (`molsysviewer/`)**
  - `MolSysView` facade and widget wrapper.
  - Loaders for MolSysMT/PDB/mmCIF/URL.
  - Regions/layers/whole and shapes APIs.
  - HTML export helpers (standalone + docs-lite).
- **TypeScript/Mol* layer (`molsysviewer/js/src/`)**
  - AnyWidget entry (`index.ts`).
  - `MolSysViewerController` and handlers (`loader`, `scene`, `state`, `trajectory`).
  - Shape builders under `shapes/`.
  - Popup host + popup implementation.

The original design overview is preserved in {doc}`design_overview`.

## 2. Python ↔ JS message protocol

### 2.1 Python → JS

All visual actions are sent as JSON-like dictionaries with:

- `op`: an operation identifier.
- `options` (or additional fields) depending on the operation.

Examples

- Load a MolSys payload:
  ```python
  view._send({
      "op": "load_molsys_payload",
      "payload": payload,
      "label": label,
  })
  ```
- Update visibility:
  ```python
  view._send({
      "op": "update_visibility",
      "options": {"visible_atom_indices": visible_indices},
  })
  ```
- Shapes:
  ```python
  view._send({
      "op": "add_sphere",
      "options": {...},
  })
  ```

The TypeScript union type `ViewerMessage` (`molsysviewer/js/src/messages/viewer-messages.ts`)
is the best “contract” view.

### 2.2 JS → Python

The widget emits events back to Python via `widget.on_msg`:

- `ready`: frontend initialized; Python flushes `_pending_messages`.
- `region_ack`: region creation confirmation (`atom_indices`, `selection`).
- `region_deleted`
- `layer_ack`
- `layer_deleted`
- `registry_cleared`: `clear_all` was executed; Python must reset registries.
- `camera_snapshot`: camera state sent from the frontend.
- `js_log`: debug logs when `debug_js=True`.

These events keep the Python mirrors (`view.regions`, `view.layers`) consistent
with the Mol* state tree.

## 3. Data path: MolSysMT → Mol*

1. You call `MolSysView.load(molecular_system, ...)`.
2. Python converts inputs to `molsysmt.MolSys`.
3. `ViewerJSON` is serialized into a stable MolSys payload:
   - `atoms`: parallel arrays (ids, names, residue, chain, element, charge).
   - `structures`: snapshots with `coordinates` (Å), optional `box` (Å), optional `time`.
   - optional `bonds`: `indexA/indexB` (+ optional `order`).
4. Python sends `{"op": "load_molsys_payload", "payload": ...}`.
5. TypeScript builds Mol* objects:
   - `Topology`, `Coordinates`, and a `Trajectory`.
   - A trajectory node in the Mol* state tree (`InsertMolSysTrajectory`).
   - A default representation preset (`default` / `auto`).
6. The controller captures the loaded structure and notifies state/trajectory handlers.

This path avoids intermediate PDB conversions when MolSysMT inputs are available.

### new_view convenience modes

`new_view(...)` is a convenience wrapper around `MolSysView.load(...)` and adds
`load_mode`:

- `load_mode="selection"` (default): the selection subsets the system before loading.
- `load_mode="all"`: the full system loads, the global representation is hidden,
  and a region tagged `selection` is created for the requested selection.

## 4. Visibility and masking

### 4.1 Python

- `MolSysView` maintains a boolean `atom_mask` (`n_atoms`).
- `hide(selection)` updates the mask and then calls `_update_visibility_in_frontend()`.
- `show(selection, structure_indices, force=False)` restores parts of the mask and re-applies global visibility intent.
- `visible_atom_indices` is computed as `np.nonzero(atom_mask)[0].tolist()` and sent through `update_visibility`.

### 4.2 TypeScript

- `StateHandlers.updateVisibility`:
  - If no structure is loaded yet, stores `pendingVisibility`.
  - Otherwise:
    - Clears previous transparency.
    - Computes the hidden selection as the complement of `visible_atom_indices`.
    - Applies transparency/visibility via Mol* helpers to global reps and regions.

The source of truth for visibility is Python.
Mol* is responsible for render-time application.

## 5. Regions and layers

### 5.1 Python API

- `MolSysView.new_region(...)`:
  - Accepts a MolSysMT selection or explicit `atom_indices`.
  - Supports complements (`complement_of_regions=["tagA", ...]` or `"all"`).
  - Registers a `Region` and sends `create_region`.
- `Region.set_representation(...)`:
  - Normalizes representation type/preset and user preset rules.
  - Sends `set_region_representation`.
- `Region.show/hide/delete`:
  - Send `show_region`, `hide_region`, `delete_region`.
- `MolSysView.new_layer(...)`:
  - Registers a `Layer` and sends `create_layer`.
- `Layer.show/hide/delete/set_tag`:
  - Send `show_layer`, `hide_layer`, `delete_layer`, `set_layer_tag`.
- `Whole.set_representation(...)`:
  - Resolves user preset rules in Python and sends `set_global_representation`.

### 5.2 TypeScript state model

`StateHandlers` maintains:

- `regionIndex`: `tag -> { component, representations[], atomIndices[], selection, hidden }`
- `layerMeta`: `tag -> { kind, meta }`
- `tagIndex`: `tag -> Set<StateObjectRef>` (refs for shapes/overlays)
- `globalReprs`: baseline/global representations for the root structure
- pending flags for operations invoked before a structure exists

Operations

- `create_region`: build `StructureSelection` from indices, create `StructureComponent`, add reps, store refs.
- `set_region_representation`: replace region reps (type, preset, or user preset).
- `show/hide_region`: toggle visibility via `setSubtreeVisibility`.
- `create_layer`: store metadata and acknowledge to Python.
- `show/hide_layer`: toggle visibility of all refs under a tag.
- `set_global_representation`: rebuild baseline/global reps and store them in `globalReprs`.
- `show/hide_global`: show/hide baseline/global reps; `target="all"` can include everything.

`clear_all` clears regions, layers, and global reps, removes the loaded structure,
and emits `registry_cleared`.

## 6. Popup (host ↔ popup)

Host (notebook)

- `PopupHostManager` opens a window and injects the runtime:
  - Blob + `import` in notebooks, or
  - `moduleUrl` in docs-lite exports.
- Keeps a `commandLog` (Python → JS messages) to reconstruct state.
- Uses `postMessage` to:
  - send `molsysviewer-initial-sync` (commands + camera snapshot + UI state),
  - stream `molsysviewer-sync-op` messages,
  - send `molsysviewer-sync-camera` while the user interacts.

Popup

- `bootPopup` creates a new `MolSysViewerController` in the popup DOM.
- Replays the `commandLog` and applies the initial camera snapshot.
- Syncs camera host ↔ popup without “camera fights”.

This design keeps the popup as a live mirror of the host.

## 7. HTML export behavior (current)

- HTML export replays `_message_history` and does not require `show()` to run.
- If the frontend is live, `write_html(...)` requests a fresh camera snapshot
  before exporting (best-effort).
- UI-only changes (toggle buttons, manual style changes) do not populate
  `_message_history` and are not exported.

## 8. What was still aspirational (at the time)

The design overview mentions additional modules (hbonds, topology, alternative engines) and richer `structure.get_* / show_*` APIs.
At this snapshot:

- Implemented core:
  - MolSys payload loading,
  - scientific shapes (spheres, pockets, tubes, pharmacophores),
  - regions/layers/whole,
  - popup,
  - trajectory controls,
  - automatic display in notebooks via `_repr_mimebundle_`.
- Still future:
  - dedicated hbonds module (`get_hbonds/show_hbonds`),
  - topology module with higher-level APIs (`get_bonds/show_bonds`),
  - extended numeric APIs under `structure.*`.

Revisit this page when a “design” item becomes a shipped feature.

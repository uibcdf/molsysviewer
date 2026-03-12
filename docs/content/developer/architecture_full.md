# Architecture (full)

This page is the canonical architecture reference for MolSysViewer.
It complements the short overview in {doc}`architecture`.
If you want a longer, implementation-oriented snapshot from the original
devguide, see {doc}`architecture_snapshot_2026_01` (latest) or
{doc}`architecture_snapshot_2025_11` (historical).

## Layers and responsibilities

MolSysViewer is split into two runtime layers with a thin protocol between them.

- Python layer (`molsysviewer/`)
  - Public API (`MolSysView`), loaders, shapes APIs, regions/layers/whole.
  - Owns the MolSysMT system and visibility masks.
  - Sends JSON-like messages to the frontend and stores a message history.
  - Exports HTML by replaying stored messages (standalone and docs-lite).
- TypeScript/Mol* layer (`molsysviewer/js/src/`)
  - AnyWidget entrypoint, controller, handlers, and shape builders.
  - Owns the Mol* plugin, state tree, and WebGL rendering.
  - Applies representations, regions, layers, and shapes using Mol* internals.

## Core data model

### MolSys payload schema (Python to JS)

The payload is the stable contract when loading MolSysMT systems:

- `atoms`: parallel arrays (`atom_id`, `atom_name`, `residue_id`, `residue_name`, `chain_id`, `entity_id`, `element_symbol`, `formal_charge`).
- `structures`: list, each with:
  - `coordinates`: N x 3 array in Å.
  - optional `box`: three vectors in Å.
  - optional `time`: numeric value.
- optional `bonds`: `indexA`, `indexB`, optional `order`.

Do not reintroduce legacy names like `positions` or `frames`.

### Message protocol

Python sends operations as dictionaries:

```text
{"op": "some_operation", "options": {...}}
```

The TypeScript union type `ViewerMessage` (`molsysviewer/js/src/messages/viewer-messages.ts`)
reflects the current contract.

### JS to Python events

The widget emits events back to Python via `widget.on_msg`:

- `ready`: frontend initialized, pending messages flushed.
- `region_ack`, `region_deleted`
- `layer_ack`, `layer_deleted`
- `registry_cleared`
- `camera_snapshot`
- `interaction_hover`, `interaction_click`
- `js_log` (debug only)

Current interaction contract

- first slice is minimal and atom-centric
- structure picks emit:
  - `event`
  - `kind: "structure"`
  - `atom_indices`
- empty canvas hover/click emits:
  - `event`
  - `kind: "empty"`
- richer semantics for regions, shapes, callbacks, or shared highlight are deliberately deferred

## Data flow

### MolSysMT native load

1. You call `MolSysView.load(molecular_system, ...)`.
2. MolSysMT converts to `molsysmt.MolSys`.
3. ViewerJSON is serialized into the MolSys payload.
4. Python sends `load_molsys_payload`.
5. TS builds Mol* `Topology`, `Coordinates`, `Trajectory` and applies a preset.
6. The controller captures the structure and notifies state/trajectory handlers.

Note: `new_view(..., load_mode="selection")` uses the same flow but subsets the
system before loading, while `new_view(..., load_mode="all")` loads the full
system and creates a `selection` region for the requested selection.

### String/URL loads

String, ID, and URL inputs are handled through MolSysMT in Python.
The Python layer sends `load_molsys_payload` for these inputs too.

## Visibility model

Python owns `atom_mask` (boolean per atom).
Python sends visible indices to TS.
TS computes hidden atoms and applies transparency via Mol* helpers.

## Regions, layers, and whole

Regions
- A region is a structural subset identified by `tag`.
- Python `Region` wraps a Mol* component plus its representations.
- JS tracks a region index and applies reps per region.

Layers
- A layer is a tag-based group for non-structural visuals (shapes/overlays).
- JS stores refs per tag and applies show/hide/delete to all refs under that tag.

Whole (global)
- `Whole` controls the baseline/global representation for the full structure.
- `show_global` / `hide_global` target either `global` only or `all` reps.

Semantics to preserve
- `region.hide()` remains hidden after `viewer.hide(); viewer.show()`.
- `whole.hide()` only affects the baseline/global reps, not regions.
- `viewer.hide(selection=\"all\")` hides all reps and masks; `show()` restores masks and re-applies the baseline visibility intent.

## Shapes pipeline

- Python shape APIs normalize inputs and send `add_*` operations.
- TS shape handlers delegate to Mol* shape builders under `molsysviewer/js/src/shapes/`.
- Each shape registers refs under a tag to allow selective clear/hide.

## Popup (popout) architecture

- The host stores a command log of Python → JS messages.
- The popout initializes with the runtime (Blob or module URL).
- The host sends initial sync (commands + camera + UI state), then streams ops.
- Camera sync is bidirectional but only when the user is actively interacting.

## Trajectory controls

- TS `TrajectoryHandlers` manages frame stepping and playback.
- The UI calls `step_trajectory`, `set_trajectory_frame`, `set_trajectory_playback`.
- State is reflected in the on-canvas UI and in the popout mirror.

## Implementation notes (detailed)

This section preserves a more detailed implementation-oriented snapshot.
It is useful when you need to match behavior to concrete message ops or
debug a host↔frontend↔popup sync issue.

### Python → JS operations (examples)

You send actions as JSON-like dictionaries with an `op` field:

```python
view._send({"op": "load_molsys_payload", "payload": payload, "label": label})
```

Common operations include:

- Loading:
  - `load_molsys_payload`
  - `load_structure_from_string` (legacy path; prefer payloads when available)
  - `load_pdb_id`, `load_url` (when delegating to Mol*)
- Visibility:
  - `update_visibility`
  - `show_global`, `hide_global`
- Regions:
  - `create_region`, `set_region_representation`
  - `show_region`, `hide_region`, `delete_region`
- Layers:
  - `create_layer`, `show_layer`, `hide_layer`, `delete_layer`
  - `set_layer_tag`
- Shapes:
  - `add_*` (sphere, spheres, pocket_surface, pocket_blob, channel_tube, …)
- Reset/cleanup:
  - `clear_all`, `clear_decorations`, `reset_viewer`

The TypeScript union type `ViewerMessage` (`molsysviewer/js/src/messages/viewer-messages.ts`)
is the contract for the current set.

### JS → Python events

The widget emits events back to Python via `widget.on_msg`, including:

- `ready` – frontend initialized; Python can flush pending messages.
- `region_ack` / `region_deleted`
- `layer_ack` / `layer_deleted`
- `registry_cleared`
- `interaction_hover` / `interaction_click`
- `js_log` (debug only)

### Regions & layers: semantics to preserve

These semantics are user-visible and should remain stable:

- `region.hide()` stays hidden after `viewer.hide(); viewer.show()`.
- `whole.hide()` only affects the baseline/global reps, not regions.
- `viewer.hide(selection="all")` hides all reps and masks; `show()` restores
  masks and re-applies the baseline visibility intent while respecting
  already-hidden regions.

### Popup (popout) sync model

- The host keeps a command log of Python → JS messages.
- The popout is initialized with the runtime (Blob or module URL for docs-lite).
- The host sends an initial sync (commands + camera + UI state), then streams ops.
- Camera sync is bidirectional but should only happen when the user is actively
  interacting (to avoid “camera fights”).

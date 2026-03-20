# Modules overview (snapshot)
_Last updated: 2025-11-21_

This page is a historical snapshot of how MolSysViewer was described during the initial architecture phase.
It is still useful as a conceptual map, but the current source of truth is always the code.

## 1. `MolSysView` (Python facade)

**File:** `molsysviewer/viewer.py`

Responsibilities

- Own the widget (`MolSysViewerWidget`) and the underlying MolSysMT system (`_molsys`).
- Maintain visibility masks (`atom_mask`, `structure_mask`) and compute `visible_atom_indices`.
- Expose the public Python API for:
  - Loading (`load`, `load_pdb_string`, `load_mmcif_string`, `load_pdb_id`, `load_from_url`).
  - Visibility (`show`, `hide`, `isolate`).
  - Regions and layers (`new_region`, `new_layer`, `regions`, `layers`, `whole`).
  - Shapes (`self.shapes`).
  - Export (`view.export.html(...)` with `standalone` and `lite` modes).
- Encapsulate Python ↔ JS messaging (`_send`, `_message_history`, `_clean_message_history`).

In practice, `MolSysView` plays multiple “logical module” roles:

- **basic**: info, show/hide/isolate, visibility reset.
- **structure**: MolSysMT integration (`_molsys`, selections, payloads).
- **shapes**: access to `ShapesManager`.
- **view/cam**: camera helpers (`reset_camera`, snapshots) and UI control toggles.

## 2. Loaders (MolSysMT and other sources)

**Directory:** `molsysviewer/loaders/`

Modules

- `load_molsysmt.py`
  - Converts inputs to `molsysmt.MolSys`, creates `atom_mask`, serializes `ViewerJSON` into a MolSys payload.
  - Sends `{"op": "load_molsys_payload", "payload": ...}` to the frontend.
- `load_pdb_string.py`, `load_mmcif_string.py`
  - Load structures from strings.
  - Build `_molsys` + masks and send a load operation.
- `load_pdb_id.py`
  - Load by PDB ID.
  - Build `_molsys` + masks and send `load_pdb_id` (Mol* handles the download).
- `load_url.py`
  - Delegate parsing entirely to Mol* (no `_molsys` or masks on the Python side).

## 3. Shapes (scientific overlays)

**Directory:** `molsysviewer/shapes/`

Responsibilities

- Normalize inputs (types, lengths, defaults).
- Build typed `options` payloads for the TypeScript message protocol.
- Send messages (`{"op": "add_*", "options": {...}}`) to the frontend.
- Register/update `Layer` objects in the Python registry.

On the TypeScript side, these messages are handled by builders under `molsysviewer/js/src/shapes/`.
Those builders translate the options into Mol* state objects (meshes, tubes, volumes, glyphs).

## 4. Regions, layers, and whole

**Files:** `molsysviewer/regions.py`, `molsysviewer/layers.py`, `molsysviewer/whole.py`  
**TypeScript:** `molsysviewer/js/src/managers/handlers/state-handlers.ts`

Region

- A region is a structural subset addressed by `tag`.
- It stores `selection` and `atom_indices`.
- It owns one Mol* `StructureComponent` and one or more representations.
- Main operations: `set_representation`, `show`, `hide`, `delete`.

Layer

- A layer is a tag-based group for non-structural visuals (shapes/overlays).
- Main operations: `show`, `hide`, `delete`, `set_tag`.

Whole (global)

- `Whole` controls the baseline/global representation for the full structure.
- It must not collide with region tags.
- It has its own visibility semantics (see {doc}`regions_layers`).

State handlers (TypeScript)

- Track region state: refs, atom indices, selection, hidden state.
- Track layer refs per tag and apply show/hide/delete to all refs under a tag.
- Track global reps (`globalReprs`) separately from regions.
- Apply visibility updates via transparency using Mol* helpers.

## 5. Trajectory

**TypeScript:** `molsysviewer/js/src/managers/handlers/trajectory-handlers.ts`

Responsibilities

- Read the current Mol* `Trajectory` from the state tree.
- Implement stepping and playback:
  - `stepTrajectory(by)`
  - `setTrajectoryFrame(index)`
  - `playTrajectory({ fps, step, mode, direction })`
  - `stopTrajectoryPlayback()`
- Report state to the UI (host and popup): `frameCount`, `currentFrame`, `isPlaying`.

## 6. Popup / popout

**TypeScript:** `molsysviewer/js/src/managers/popup-host.ts`, `molsysviewer/js/src/popup/popup-logic.ts`

Responsibilities

- Open/close a mirror window.
- Inject the runtime:
  - Blob + `import` for notebook contexts.
  - module URL for docs-lite contexts.
- Re-play the host command log and apply the initial camera snapshot.
- Sync host ↔ popup state:
  - ops (`molsysviewer-sync-op`)
  - camera (`molsysviewer-sync-camera`) without “camera fights”
  - UI state (dark mode, spin/swing, autohide)

## 7. Documentation and tests

Maintenance modules

- `docs/`: Sphinx docs, authored pages under `docs/content/`, HTML lite exports under `docs/_static/views/`.
- `tests/`: Python unit/integration tests.
- `molsysviewer/js/tests/`: TS unit tests and Playwright E2E tests.

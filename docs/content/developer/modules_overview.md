# Modules overview (snapshot)
_Last updated: 2026-05-22_

This page is a historical snapshot of how MolSysViewer was described during the initial architecture phase.
It is still useful as a conceptual map, but the current source of truth is always the code.

## 1. `MolSysView` (Python facade)

**Package:** `molsysviewer/viewer/`

Responsibilities

- Own the widget (`MolSysViewerWidget`) and the underlying MolSysMT system (`_molsys`).
- Maintain the structure mask. Atom visibility is a region concern; the atom mask was removed in `uibcdf/molsysviewer#75`.
- Expose the public Python API for:
  - Loading (`load`, `load_pdb_string`, `load_mmcif_string`, `load_pdb_id`, `load_from_url`).
  - Visibility (`show`, `hide`, `isolate`).
  - Regions and layers (`regions.add`, `layers`, `whole`).
  - Shapes (`self.shapes`).
  - Export (`view.export.html(...)` with `standalone` and `lite` modes).
- Encapsulate Python ↔ JS messaging (`_send`, `_message_history`, `_clean_message_history`).

Current package split

- `core.py`
  - High-level `MolSysView` facade orchestration and central class definition.
- **Mixins** (modular core split):
  - `regions.py`: Manages spatial regions and atom selection logic.
  - `panel_mode.py`: Manages sidebar panel rendering and dynamic workspace contexts.
  - `load.py`: Handles importing structures and parsing project stylesheets.
  - `visibility.py`: Controls whole, representation, and component-level visibility.
  - `scene.py`: Manages camera, snapshots, figures, and exports.
  - `molsysmt_interface.py`: Dedicated interface layer for MolSysMT integration.
  - `state.py`: Handles layout state synchronization.
  - `interaction.py`: Manages click, hover, and reproducible signal callbacks.
- `history.py`
  - Replayable history recording and message rewriting.
- `export.py`
  - Export-time message assembly and HTML serialization helpers.
- `scene_registry.py`
  - Non-structural scene-object and layer registries.
- `representations.py`, `presets.py`
  - Normalization tables and preset resolution.

In practice, `MolSysView` plays multiple “logical module” roles:


- **basic**: info, show/hide/isolate, visibility reset.
- **structure**: MolSysMT integration (`_molsys`, selections, payloads).
- **shapes**: access to `ShapesManager`.
- **view/cam**: camera helpers (`reset_camera`, snapshots) and UI control toggles.

## 2. Loaders (MolSysMT and other sources)

**Directory:** `molsysviewer/loaders/`

Modules

- `load_molsysmt.py`
  - Converts inputs to `molsysmt.MolSys` and records a
    generation-bound lazy molecular projection.
  - The array-native and portable-JSON encoders both read MolSys directly;
    portable JSON is materialized only for compatibility or export consumers.
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

Whole

- `Whole` controls the baseline representation for the full structure.
- It must not collide with region tags.
- It has its own visibility semantics (see {doc}`regions_layers`).

State handlers (TypeScript)

- Track region state: refs, atom indices, selection, hidden state.
- Track layer refs per tag and apply show/hide/delete to all refs under a tag.
- Track whole baseline refs (`globalReprs` internally) separately from regions.
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

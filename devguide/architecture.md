# Architecture

MolSysViewer is built as a hybrid Python/TypeScript application that bridges the **MolSysMT** ecosystem with the **Mol*** visualization engine.

## The Python/JS Bridge (`anywidget`)

We use `anywidget` to embed Mol* inside Jupyter environments.

- **State Management**: Python is the source of truth for the loaded molecular system, regions, layers, live-edit state, and exportable message history.
- **Messaging**: communication is asynchronous and operation-based (`op`). Python sends commands like `load_molsys_payload`, `set_region_representation`, `update_visibility`, or shape ops.
- **Latency Handling**: if the frontend is not ready, messages are queued in `MolSysView._pending_messages` and flushed upon the `ready` event.
- **Replayability**: Python keeps `_message_history` and `_shape_history` so standalone HTML exports, popup bootstrap, and rebuild flows can replay externally visible state.

## Frontend Components (TypeScript)

The JS layer is organized into specialized handlers to manage Mol* complexity and keep the protocol stable:

1. **`MolSysViewerController`**: The central dispatcher.
2. **Handlers**:
   - `LoaderHandlers`: process native `MolSysPayload` and build Mol* state.
   - `ShapeHandlers`: render geometric objects and keep tag-based refs for clear/hide/replay.
   - `StateHandlers`: manage visibility masks, whole/region semantics, and registry acknowledgements.
   - `TrajectoryHandlers`: control frame playback and synchronization.
   - popup host / popup logic modules: mirror replay state, camera sync, and bootstrap behavior across host and popout windows.

## Python Runtime Layers

The Python side is intentionally layered:

- **`MolSysView`**:
  - orchestration facade for loading, visibility, editing, export, and camera control.
  - owns replay state and viewer-facing registries.
- **`Whole`, `Region`, `Layer`**:
  - small domain wrappers around global representation, structural subsets, and non-structural visual groups.
- **`ShapesManager` + shape modules**:
  - public overlay API plus specialized argument normalization and message construction.
- **Loaders / private helpers**:
  - payload building, remapping, coordinate normalization, and export helpers.

## Live Edit and Rebuild

Live structural edits (`set`, `add`, `append_structures`, `remove`) are a core architectural path.

- the underlying MolSysMT object is mutated on the Python side;
- the viewer is rebuilt from current molecular state;
- regions/layers/tags are replayed;
- visibility is restored;
- atom-index based state is remapped when topology changes;
- the resulting `_message_history` must remain replay-safe for export and popup flows.

This rebuild path is now a regression-tested contract, not an implementation detail.

## Visibility Model

Visibility has three distinct layers:

- **whole/global visibility**
- **region visibility**
- **atom mask visibility**

Important invariant:

- global show/hide must not accidentally erase sticky hidden state of regions or layers.

This is part of the runtime contract because it affects rebuilds, exports, and popup sync.

## Static Exports

MolSysViewer supports high-fidelity static HTML exports:

- **Standalone**:
  - embeds widget state and manager state;
  - carries replay messages and optional popup support.
- **Lite**:
  - documentation-oriented mode;
  - loads runtime assets externally and replays cleaned message history.

Export correctness depends on:

- deterministic replay ordering,
- visibility-cleaning rules,
- and appending camera snapshot state at the correct point in the replay stream.

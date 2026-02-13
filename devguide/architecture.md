# Architecture

MolSysViewer is built as a hybrid Python/TypeScript application that bridges the **MolSysMT** ecosystem with the **Mol*** visualization engine.

## The Python/JS Bridge (`anywidget`)

We use `anywidget` to embed Mol* inside Jupyter environments. 

- **State Management**: Python maintains the "Source of Truth" for the molecular system and structural subsets (Regions).
- **Messaging**: Communication is asynchronous and operation-based (`op`). Python sends commands like `load_molsys_payload` or `add_sphere`.
- **Latency Handling**: If the frontend is not ready, messages are queued in `MolSysView._pending_messages` and flushed upon the `ready` event.

## Frontend Components (TypeScript)

The JS layer is organized into specialized handlers to manage Mol* complexity:

1. **`MolSysViewerController`**: The central dispatcher.
2. **Handlers**:
   - `LoaderHandlers`: Processes PDBs and native `MolSysPayload`.
   - `ShapeHandlers`: Renders geometric objects (spheres, tubes, etc.) using Mol* state transforms.
   - `StateHandlers`: Manages visibility masks and Region components.
   - `TrajectoryHandlers`: Controls frame playback and synchronization.

## Static Exports

MolSysViewer supports high-fidelity static HTML exports:
- **Standalone**: Embeds the full widget state and Jupyter manager.
- **Lite**: A documentation-friendly mode that loads the runtime from a CDN and replays the session's message history to recreate the view exactly as it appeared in the notebook.

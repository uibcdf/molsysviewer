# Protocol and payloads (Python ↔ TypeScript)

Use this page as the source of truth for the Python ↔ TypeScript boundary.
These contracts are stability-critical.

## ViewerMessage protocol

All Python → frontend operations are JSON-like dictionaries.
They include an `op` field and additional fields depending on the operation.

Contract view

- TypeScript: `molsysviewer/js/src/messages/viewer-messages.ts` (`ViewerMessage` union type)

Guidelines

- Do not rename an `op` without a versioned migration.
- Keep option keys consistent with the TS types.
- Prefer additive changes to preserve backward compatibility.

## MolSys payload schema (Python → JS)

When loading MolSysMT-native systems, Python sends a stable payload:

- top-level `structures` list
- each structure:
  - `coordinates` in Å
  - optional `box` as three vectors in Å
  - optional `time`

Do not reintroduce legacy names such as `positions` or `frames`.

## JS → Python events

The widget emits events back to Python via `widget.on_msg`.
These events keep Python registries consistent with the Mol* state tree.

Common events

- `ready`: frontend initialized; Python flushes queued messages.
- `region_ack` / `region_deleted`
- `layer_ack` / `layer_deleted`
- `registry_cleared`
- `js_log` (debug only)

## Tags and registries

Tags are the common namespace across:

- regions (structural subsets),
- layers (non-structural visuals),
- shapes/overlays (registered under layer tags).

Tag semantics must remain stable.
See {doc}`regions_layers` for user-visible rules.


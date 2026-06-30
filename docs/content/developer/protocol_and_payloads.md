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

- top-level `atoms` object
- top-level `structures` list
- each structure:
  - `coordinates` in Å
  - optional `box` as three vectors in Å
  - optional `time`

Atom vocabulary at this boundary deliberately follows the Mol*/mmCIF builder where needed.
In particular, MolSysSuite `group_id` / `group_name` are serialized as `residue_id` /
`residue_name` because TypeScript maps them to `atom_site.label_seq_id`,
`atom_site.auth_seq_id`, `atom_site.label_comp_id`, and `atom_site.auth_comp_id`.
This is a wire-format translation only: Python APIs and JS interaction events keep using
MolSysSuite `group_*` vocabulary. Do not rename these payload fields to `group_*` without
changing the Mol* atom_site construction contract.

Do not reintroduce legacy names such as `positions` or `frames`.

## JS → Python events

The widget emits events back to Python via `widget.on_msg`.
These events keep Python registries consistent with the Mol* state tree.

Common events

- `ready`: frontend initialized; Python flushes queued messages.
- `region_ack` / `region_deleted`
- `layer_ack` / `layer_deleted`
- `registry_cleared`
- `interaction_hover` / `interaction_click`
- `js_log` (debug only)

Interaction payloads

- first slice is intentionally atom-centric and minimal
- structure picks emit:
  - `event`
  - `kind: "structure"`
  - `atom_indices`
- empty canvas hover/click emits:
  - `event`
  - `kind: "empty"`

## Tags and registries

Tags are the common namespace across:

- regions (structural subsets),
- layers (non-structural visuals),
- shapes/overlays (registered under layer tags).

Tag semantics must remain stable.
See {doc}`regions_layers` for user-visible rules.

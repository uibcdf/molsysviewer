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

`clear_all` normally declares an empty session and restores Welcome. A prepared
system rebuild or replacement adds `awaiting_structure: true`: the canvas is
cleared while Welcome stays hidden until the following load succeeds or fails.
Loader cleanup releases this state, including failed array-native decoding.
Panel-only endpoints never show Welcome. Empty-state detection reads the
actual Mol* structure hierarchy, rather than cached references to deleted nodes.

Region enablement uses `set_region_enabled` with `tag` and boolean `enabled`.
`create_region` accepts optional `enabled` (default true); Python creation and
snapshot messages include false for suspended regions. Region summaries carry
both `enabled` and `hidden`, and Studio forwards `toggle_region_enabled` through
the existing `interaction_context_action` event to Python. Hide masks Whole
and hides own representations while enabled; disabling releases that region's
Whole/color effects while retaining its hidden request. State-v2 region records
save both booleans. See {doc}`regions_layers` for scope and overlapping regions.

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

The additive `atoms.unassigned_scope_atoms` declaration preserves native group
and chain membership before rendering defaults. Each level is `"all"` when no
atom has membership, an empty list when all do, or a list of unassigned atom
indices for a partial topology. JSON and array-native encoders share this
declaration. Mol* model source data retains it, and hierarchy projections carry
the derived `available_scopes` to panel-only hosts. Group/Chain menu actions and
composer options are disabled when none of the target atoms has membership.
Legacy payloads without this declaration retain backend validation; missing
metadata is unknown, not proof of membership. The declaration is a UI hint,
never authority to bypass Python scope resolution.

## Partial coordinate edits

`partial_coordinates_update` contains explicit `atom_indices` and
`structure_indices`, `coordinates` shaped `(structures, atoms, 3)`, and
`coordinate_unit: "angstrom"`. The frontend validates the complete message before replacing
native trajectory models. A new conformation identity causes Mol* to rebuild
geometry; edited offscreen structures are updated before later playback.
The acknowledgement follows application of the update.

Python invalidates derived interaction occurrences on the edited structures
and refreshes its molecular projection. A pending native transfer is superseded
so an old buffer cannot later overwrite the edit.

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

## Studio exports

`set_figure_spec` carries `figure_background` for the actual recipe background;
`figure_variants` lists the available publication variants. PNG controls and
dimensions use the actual background and renderer drawing buffer.

For browser HTML download, Studio sends `export_html` with a frontend-generated
`request_id`. Python replies with transient `html_export_ready`, the same ID,
`filename` and self-contained `html`. The requesting controller consumes the
reply once. It is excluded from popup scene replay and bypasses structure
streaming. Remote sessions retain their existing download URL delivery; Python
`view.export.html(path)` retains file output. This reply is a browser effect,
not persisted scene state.

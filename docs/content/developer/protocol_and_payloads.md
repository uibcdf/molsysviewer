# Protocol and payloads (Python ↔ TypeScript)

Use this page as the source of truth for the Python ↔ TypeScript boundary.
These contracts are stability-critical.

## Renderer-owned frame queries

`request_interaction_frame` uses a renderer-local integer `request_id`. The
authenticated widget or live Qt host stamps `_query_endpoint_id` from the
actual originating canvas, overriding any domain-payload value. Python accepts
the primary or a registered open canvas, then targets both
`set_interaction_frame` and `interaction_frame_complete` to that requester.
Failures use the same destination. A legacy request without this private field
belongs to the primary. The IDs do not identify a query across renderers.

The live Qt host reports authenticated `popup_endpoint_opened` and
`popup_endpoint_closed` lifetime events; widgets retain registration through
their canonical popup snapshot request. Closed, unknown and panel-only
endpoints cannot request graphical interaction frames. Detached Studio consumes
authority summaries without requesting invisible geometry. Actual interaction
edits remain scene-wide projections; requester isolation only scopes query
answers. A targeted reply is relayed to its owner instead of entering the
primary canvas or its replay log. These internal transport fields are not a
new public Python API or a visual-state-capture stability declaration.

`request_dynamic_region_evaluation` uses the same owner stamp and returns a
complete membership for each evaluated region, including unchanged and empty
selections. New requests carry a local monotonically increasing `request_id`;
replies match both ID and frame. Obsolete replies may release their own query
without changing another frame's atoms. Model/coordinate and region-lifetime
changes retire pending IDs. Uncorrelated managed scene projections apply only
at their actual current frame. A budget-triggered freeze is a separate shared
static-scene change: its warning carries the complete frozen `atom_indices`
for every renderer, independently of each local trajectory frame.

Frame-query consumers allow at most two outstanding requests per family and
renderer. This overlaps an older answer with the current frame; further desired
frames coalesce to the latest frame instead of accumulating trajectory-wide
requests. Completion retires only its own request, and an obsolete completion
does not restart an already satisfied current frame. This internal scheduling
bound does not establish moving-capture availability or a universal memory bound.

`trajectory_frame_changed.box_display` confirms an already applied native cell.
After validating its definition revision and index, Python updates its canonical
cell/shape records without sending that geometry back to the renderers.
Duplicate feedback is idempotent. Explicit Python seeks and box/style changes
retain normal projection, as does the legacy feedback path without a resolved
cell declaration.

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

The live widget's synced `has_molecular_system` boolean declares that Python has
prepared a molecular load. It does not carry coordinates or certify frontend
rendering. `initial_messages` can be empty because the molecular data is delivered
only after `ready`; the boolean lets a newly attached controller keep Welcome
hidden throughout its setup and that handshake. Molecular projection/replay sets
the hint, and resetting the Python view clears it. Initial replay messages also
declare molecular intent when present. The controller enters the existing pending
load state before panel setup and releases it on loader success/failure or an
explicit clear. A genuinely empty widget retains Welcome without an artificial
delay. These rules also apply when rebuilding an endpoint from the same Python view.

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

The static payload reads covalent bonds from the native `ChemicalStates`
reference state, independently of `Topology`. It does not infer bonds from
coordinates or choose state zero when the reference is ambiguous. An absent
chemical domain or a collection with no states contributes no explicit bond
array; an empty array is not evidence of complete chemical knowledge. Existing
native completeness and structure-to-state associations remain unchanged.
This static projection does not implement per-structure chemical-state switching.

Programmatic active selection retains its ordered, deduplicated atom indices.
Unknown memberships and unavailable hierarchy levels contribute no group,
component, chain, molecule or entity metadata indices. Rendering defaults do not
become native memberships. See the source receiving contract in
[MolSysViewer #269](https://github.com/uibcdf/molsysviewer/issues/269).

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

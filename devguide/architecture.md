# Architecture

MolSysViewer is built as a hybrid Python/TypeScript application that bridges the **MolSysMT** ecosystem with the **Mol*** visualization engine.

## The Python/JS Bridge (`anywidget`)

We use `anywidget` to embed Mol* inside Jupyter environments.

- **State Management**: Python is the source of truth for the loaded molecular system, regions, layers, live-edit state, and canonical export projections.
- **Messaging**: communication is asynchronous and operation-based (`op`). Python sends commands like `load_molsys_payload`, `set_region_representation`, `set_regions_visibility`, or shape ops.
- **Runtime envelope (2026-07)**: those ops now travel inside a `RuntimeEnvelope` carrying viewer, session and endpoint identity, a declared direction, and the action name. Python is the single authority: it validates identity and direction, deduplicates commands so one accepted command means one public-API mutation and one history checkpoint, and only it emits projections. A shared manifest, `molsysviewer/runtime_actions.json`, classifies every action and is loaded by both Python and TypeScript, so neither side can drift. See [`runtime_message_router.md`](runtime_message_router.md).
- **Structural data plane**: coordinates for a materialized `MolSys` travel as typed binary buffers, planar per structure, so Mol\* frames are zero-copy views. JSON remains as an observable fallback. See [`data_plane_architecture.md`](data_plane_architecture.md).
- **MolSys payload vocabulary**: `residue_id` / `residue_name` are intentional in the Python → TypeScript payload. The TS loader materializes them as Mol*/mmCIF `atom_site` columns (`label_seq_id`, `auth_seq_id`, `label_comp_id`, `auth_comp_id`). This is only a wire-boundary translation from MolSysSuite `group_id` / `group_name`; public Python APIs and interaction payloads keep the `group_*` vocabulary.
- **Readiness**: live mutations are sent only after the frontend is ready. A new
  or reattached frontend receives the embedded-runtime canonical projection;
  array-native structure delivery remains ahead of its deferred scene through S8.
- **Projection**: popup, embedded-runtime reconnect and static HTML bootstrap
  rebuild current state from live registries. Their size depends on the scene,
  not on how long the session has run. There is no generic replay journal.

## Frontend Components (TypeScript)

The JS layer is organized into specialized handlers to manage Mol* complexity and keep the protocol stable:

1. **`MolSysViewerController`**: The central dispatcher.
2. **Handlers**:
   - `LoaderHandlers`: process native `MolSysPayload` and build Mol* state.
   - `ShapeHandlers`: render geometric objects and keep tag-based refs for clear/hide/replay.
   - `StateHandlers`: manage visibility masks, whole/region semantics, and registry acknowledgements.
   - `TrajectoryHandlers`: control frame playback and synchronization.
   - popup host / popup logic modules: authenticated channel, camera sync, and bootstrap across host and popout windows. They no longer mirror replay state in the interactive path; `PopupReplayLog` survives only in `bootDocsView`, where a static HTML export has no Python to ask.

## Python Runtime Layers

The Python side is intentionally layered:

- **`MolSysView`**:
  - orchestration facade for loading, visibility, editing, export, and camera control.
  - owns current molecular projection and viewer-facing registries.
- **`Whole`, `Region`, `Layer`**:
  - small domain wrappers around global representation, structural subsets, and non-structural visual groups.
- **`ShapesManager` + shape modules**:
  - public overlay API plus specialized argument normalization and message construction.
- **`InteractionsManager`**:
  - native scientific discovery, sparse queries, declared H5MSM import and named
    calculations, backed by MolSysMT without addon registration;
  - scientific results live in `view.molsys.interactions`, independent of visual
    undo. Calculation publishes a complete snapshot only if the system revision
    still matches. Tagged visual sets, current-frame observed-position Mol*
    meshes and the native Studio subpanel now use those scientific snapshots.
    Provider-release qualification remains open under `uibcdf/molsysviewer#114`.
- **Loaders / private helpers**:
  - payload building, remapping, coordinate normalization, and export helpers.

## Molecular-system index space

There is **one canonical, functional index space: the loaded system, `view._molsys`**
(the input converted to `molsysmt.MolSys`). Every selection and interaction — atom
indices **and** structure/frame indices, on the Python API, the frontend, and what the
user sees — is expressed in `_molsys` space. Atom `0` is the atom the user sees as `0`;
`view.select`, `active_selection`, regions, expansion, and trajectory frames all resolve
against `_molsys`.

`view.molecular_system` is the **original input** (often a raw file form, e.g. an
`.h5msm`) and is **provenance only** — never queried on the functional path (querying it
is both fragile, e.g. h5py fancy-index ordering, and slow).

When a **subset** is loaded, the link back to the original is kept as **reference only**,
in **two independent per-axis mappers**:

- `view._atom_index_mapper` — present iff *atoms* are a real subset (`selection != "all"`).
- `view._structure_index_mapper` — present iff *structures* are a real subset
  (`structure_indices != "all"`).

Each is `None` when its axis is fully loaded (no identity mappers), and **neither is
consulted in the functional path** — they exist solely to recover original indices on
demand. This is a deliberate correction of an earlier "everything mapped to the original
system" default; see the git history of
`pending_bugs/active_selection_index_space_unification.md` for the full diagnosis.

The only atom-index remapping that *is* functional is `apply_system_edit`'s
`atom_index_map` — a **temporal** reconciliation of old↔new `_molsys` across an edit,
orthogonal to the loaded↔original axis above.

## Independent-source loading

`view.load(..., multiple=True)` interprets the outer list/tuple as independent
systems. Default `multiple=False` keeps one-system semantics, including lists of
complementary forms. Batch loading supports `add` and `replace`; both prepare all
sources and one detached composite candidate before changing the active scene.
Progressive `load(source)` uses the same preparation/composition owner.

Flat atom/frame index lists apply to every source; nested lists and lists of atom
selection expressions apply per source. One structure per source is supported.
Multi-frame composition additionally requires equal selected counts and explicit
`structure_pairing="by_index"`. Available times must agree in ps within
`rtol=atol=1e-9`; whole retains the first/destination time and box, including
absence. No alignment, static broadcasting or frame-axis concatenation is implied.

Detached `load_blocks` record distinct source occurrences, origin descriptions
and compact original/current atom and structure runs. Generated base regions link
by UID; renaming or deleting a region does not erase its source occurrence.
Single loading of named analyses is supported; incoming analyses during
composition require a future explicit embedding policy and currently fail before
scene mutation. Destination analyses follow existing edit invalidation.

These loading contracts are guarded by `tests/test_composite_load.py` and the
real-Mol* `composite-load` browser suite. Source records now persist through the
additive v2-state `sources` extension, version 1; sessions, copy/extraction and
explicit atom edit maps retain/remap them. Sources without surviving atoms drop
out. Atom bounds enclose the runs and need not be contiguous membership. Scene
merge preserves distinct IDs; a repeated source occurrence gets a new ID with
`parent_source_id` and corresponding region links remapped.

The source extension binds its records to topology, atom/frame counts and ordered
coordinates/time/box in canonical units. Its SHA-256 is computed in bounded
chunks, cached across scene operations and invalidated by announced molecular
edits. This content check does not authenticate claimed file origins. Topological
scene identity remains separate: ordinary state import may restore overlays on a
different system while retaining that destination's source inventory. Only a
matching binding replaces source records, and `clear_first=False` keeps destination
records. Sessions require a matching binding before replacing an open view.

Without atom correspondence, a changed atom count collapses the old inventory.
Atoms missing from a supplied edit map have an explicit `unmapped_edit` origin.
With unchanged counts, callers declare index order unchanged; extraction supplies
explicit subset/reorder correspondence for both axes. A changed structure count
without that correspondence clears old frame maps with `status="unverified"`.
Explicit `load(mode="append_structures")` preserves known prefix maps; new frames
have no fabricated original-frame provenance. Noncoverage is explicit in the map.
Guard: `tests/test_source_records.py`. Integrated qualification remains under
uibcdf/molsysviewer#151; no hard memory ceiling is established.

### Studio loading

The System subpanel offers a persistent loading draft with explicit independent
systems versus complementary files, add/replace/append intentions, optional
labels, atom selectors and ordered structure selectors. Multiple selected frames
require the same explicit pairing as Python. The empty-view welcome action opens
this form. It accepts paths available to the Python session and PDB IDs, rather
than transporting uploaded browser files. Exported browser-only views omit it.

Studio's private action handler delegates to public `view.load` with digestion
enabled. Request-specific runtime acknowledgments report completion/error and
counts, without entering the molecular replay journal. A failure retains the
draft for correction; an unrelated acknowledgment cannot complete the request.
Hierarchy/frame refreshes do not reconstruct the draft. Preparation-failure
atomicity remains the load owner's contract, not an extra rendering rollback.

Guards: `tests/test_studio_loading.py`, `system-load-controls.test.ts` and real-Mol*
`composite-load`. Complementary Amber topology/coordinates use the public provider
route. Provider-owned partial extraction and complementary H5MSM 0.5 composition
are repaired in the editable provider under uibcdf/molsysmt#307 and
uibcdf/molsysmt#309. Composition precedes atom/frame selection. Viewer keeps the
provider's scientific validation: capable providers compose the domains; older
experimental providers raise their public composition diagnostic before scene
mutation. Six selectors guard both outcomes, and a direct current-provider probe
verifies all six positive combinations through Python loading. No consumer
extraction or composition engine is introduced; published-artifact availability
remains a separate gate.

### Controlled whole-system cell assignment

`view.set_box(box, structure_indices="all")` accepts a quantity with explicit
length units and a finite, nondegenerate right-handed basis, with the three
vectors as rows. A single submitted matrix applies uniformly to the selected
structures; an array supplies one matrix per selected structure, in that order.
Initialization and `set_box(None)` removal require the complete structure axis.
A partial replacement requires an existing complete cell series; no missing-frame
cell or zero placeholder is invented.

`view.set_box(molecular_system=source, source_structure_indices=..., ...)` reads
cells through public MolSysMT `get`. Supported source forms include Structures
and H5MSM. The selected counts must agree; more than one pair requires explicit
`structure_pairing="by_index"`. Source cells never broadcast. Selected times are
compared in ps with `rtol=atol=1e-9` when both are present. `box` and a source are
mutually exclusive. Source selectors/pairing are invalid without a source.

Assignment uses public MolSysMT `set`, verifies shape and unit-converted values
through public `get`, then calls the existing system-edit reconciliation owner.
A provider that ignores the edit gets a compatibility diagnostic before scene
publication or analysis invalidation; the prior cell is restored on a mismatched
result. This protects older compatible base providers that cannot initialize an
absent cell (uibcdf/molsysviewer#155). Coordinates, time, atom/frame order and source occurrence maps remain
unchanged; later atom additions retain the assigned cell, including its absence.
Only selected structures lose evaluated interaction coverage, with immutable
original results retained. Scene history is cleared; content binding, molecular
projection, scientific visual sets and visible box edges are refreshed. Removing
the cell hides its edge display. Rebuilds regenerate edges from current data
rather than replaying their old coordinates.

Invalid selectors, units, matrices, source counts/times and unsupported source
data fail before science/scene mutation, including with digestion bypassed.
Unexpected runtime/render errors are outside the preparation rollback guarantee.
This path rebuilds the molecular projection through existing transport; it does
not certify incremental box streaming, an I/O budget or a hard memory ceiling.
Guards: `tests/test_box_assignment.py` and real-Mol* `coordinate-edits`.

## Live Edit and Rebuild

Scientific molecular edits belong to MolSysMT. The viewer exposes a
public reconciliation primitive,
`view.apply_system_edit(new_molsys, atom_index_map=…, load_blocks="keep"|"collapse"|"append")`.
Native workflows such as loading, coordinate/cell assignment and interactions
use the provider without requiring addon registration. Optional domain addons
and advanced callers can also drive this primitive. The older MolSysMT addon is
being retired as its useful workflows acquire native replacements, as recorded
in `molsyssuite_addon_direction.md`.

When `apply_system_edit` runs:

- the reconciled MolSysMT object becomes the viewer's current molecular state;
- named interaction analyses lose their evaluated coverage by default, because
  topology or geometry edits can invalidate scientific evidence;
- `interactions_policy="preserve"` explicitly declares that incoming analyses
  have already been reconciled and remain valid. Direct unannounced array or
  system mutation is outside the interaction validity contract;
- the viewer is rebuilt from that state;
- regions/layers/tags are replayed;
- visibility is restored;
- atom-index based state is remapped when topology changes;
- the rebuilt live registries must remain sufficient for canonical popup and static-export projection;
- reconnect and export are regenerated from those registries, not from commands
  emitted before the rebuild.

This rebuild path is a regression-tested contract, not an implementation detail.

**Coordination invariant.** Any code that edits the molecular system — including
addons — must go through `view.apply_system_edit(...)`. The viewer must not regrow
public molecular-system *editing* mutators (`set`/`add`/`remove`/`append_structures`).
This does not constrain representation/visual state: `view.whole.set_representation`,
colors, and styles remain first-class public viewer API.

## Visibility Model

Visibility has three distinct layers:

- **whole/global visibility**
- **region visibility**
- **atom mask visibility**

Important invariant:

- global show/hide must not accidentally erase sticky hidden state of regions or layers.

This is part of the runtime contract because it affects rebuilds, exports, and popup sync.

## Scene Object and Layer Model

> **The scene's behaviour is governed by [`scene_contracts.md`](scene_contracts.md), which is
> normative.** This section describes the *registries*; that document describes the *rules* —
> representation states, colour ownership, ordering, recipes and serialisation. If the two
> disagree, the contracts win. Read them before changing anything below.

There are three registries on every `MolSysView` instance:

- **`_scene_objects: dict[tuple[str, str], SceneObject]`** — individual Shape,
  Annotation, and Measurement objects. Each entry is keyed by `(kind, tag)`.
- **`_regions: dict[str, Region]`** — structural regions over the molecular system.
- **`_layers: LayersManager`** — `Layer` instances that group one or
  more scene objects (or structural regions) under a shared visibility/color
  toggle. It remains a `dict` subclass keyed by the layer's `tag`.

### The scene model in one paragraph

A **region is a recipe**, not a set of atoms: it carries a `provenance` (how it was defined) and a
`mode` (`static` / `dynamic`), and its `atom_indices` are the cached result of evaluating that
recipe. A region's representation is in one of three states — **None** (no own visual; the atoms
are painted by nothing else, so the region disappears if the whole is hidden), **Inherit** (the
sentinel string `"inherit"`; the region draws what the whole draws, and follows it when it
changes), or **Own**. Colour is **layered**: a base layer owned by `whole`, with one layer per
region stacked on top by a single `order` per region, and an atom in no layer falls through to the
structural colour theme rather than being painted grey. Scene mutations are recorded in **one**
scene-level history (`view.history`, snapshot-based undo/redo). All of it serialises to state
**v2**. Each of those sentences is a contract; the details, and the reasons, are in
`scene_contracts.md`.

### Key invariants

1. **Identity is `(domain, tag)`.** A tag is unique inside its domain, while
   different domains may deliberately reuse it (for example, a shape and an
   annotation may both be named `site1`). `TagsManager` owns each domain's
   naming policy and monotonic high-water mark; the live registries remain the
   source of truth for which tags exist.

2. **`layer_tag` is the grouping channel — for scene objects.**  A `SceneObject` carries a
   `layer_tag` attribute that names the `Layer` it belongs to.  When no
   explicit `layer_tag` is given, the object's own `tag` is used as a
   degenerate single-object layer.  To move an object between layers, call
   `obj.set_layer_tag(new_tag)`; the registry cleanup (de-register from the old
   layer, register into the new one) is handled inside `set_layer_tag`.

   **Regions are the exception, and it bites.**  A `Region`'s membership lives in
   `region.layer` (set via `region.set_layer(...)` / `remove_from_layer()`), **not** in
   `layer_tag`.  Any code that walks a layer's members and writes `member.layer_tag` will
   silently orphan every region in it — which is exactly what a layer rename used to do.  Iterate
   `Layer.members` and branch on which channel the member actually uses.

3. **`Layer.add(obj)` / `Layer.detach(obj)`** are the high-level membership
   management methods.  Both delegate to `obj.set_layer_tag(...)` and therefore
   respect the same registry cleanup semantics.

4. **`layer_ack` events from the JS side must not pollute `_layers`.**  When
   a batch shape op (e.g. adding 10 spheres) is sent, the JS side emits one
   `layer_ack` per Mol* node.  The Python handler checks
   `tag not in self._scene_objects` before registering into `_layers`, so
   individual shape tags are never promoted to group layers.

5. **Flat layer model.** Layers are one level deep.  There is no nesting.
   A `Layer` cannot contain another `Layer`; it can only contain
   `SceneObject` entries.

6. **`get_center()` / `focus()` naming convention.** Methods that return a
   geometric position use `get_center()`; methods that move the camera to
   focus on an object use `focus()`.  Both exist on `Region`, `Shape`,
   `Measurement`, and `Annotation` (where applicable).

## Static Exports

MolSysViewer supports high-fidelity static HTML exports:

- **Standalone**:
  - embeds widget state and manager state;
  - carries a canonical current-scene projection and optional popup support.
- **Lite**:
  - documentation-oriented mode;
  - loads runtime assets externally and applies the same canonical projection.

Export correctness depends on deterministic projection ordering, complete live
registries, and appending the captured camera after the renderable scene. The
static artifact deliberately carries camera state because no live host remains
to supply endpoint-local state when it is opened.

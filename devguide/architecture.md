# Architecture

MolSysViewer is built as a hybrid Python/TypeScript application that bridges the **MolSysMT** ecosystem with the **Mol*** visualization engine.

## The Python/JS Bridge (`anywidget`)

We use `anywidget` to embed Mol* inside Jupyter environments.

- **State Management**: Python is the source of truth for the loaded molecular system, regions, layers, live-edit state, and canonical export projections.
- **Messaging**: communication is asynchronous and operation-based (`op`). Python sends commands like `load_molsys_payload`, `set_region_representation`, `update_visibility`, or shape ops.
- **Runtime envelope (2026-07)**: those ops now travel inside a `RuntimeEnvelope` carrying viewer, session and endpoint identity, a declared direction, and the action name. Python is the single authority: it validates identity and direction, deduplicates commands so one accepted command means one public-API mutation and one history checkpoint, and only it emits projections. A shared manifest, `molsysviewer/runtime_actions.json`, classifies every action and is loaded by both Python and TypeScript, so neither side can drift. See [`pending_proposals/runtime_message_router.md`](pending_proposals/runtime_message_router.md).
- **Structural data plane**: coordinates for a materialized `MolSys` travel as typed binary buffers, planar per structure, so Mol\* frames are zero-copy views. JSON remains as an observable fallback. See [`pending_proposals/data_plane_architecture.md`](pending_proposals/data_plane_architecture.md).
- **MolSys payload vocabulary**: `residue_id` / `residue_name` are intentional in the Python → TypeScript payload. The TS loader materializes them as Mol*/mmCIF `atom_site` columns (`label_seq_id`, `auth_seq_id`, `label_comp_id`, `auth_comp_id`). This is only a wire-boundary translation from MolSysSuite `group_id` / `group_name`; public Python APIs and interaction payloads keep the `group_*` vocabulary.
- **Latency Handling**: if the frontend is not ready, messages are queued in `MolSysView._pending_messages` and flushed upon the `ready` event.
- **Projection**: popup and static HTML bootstrap rebuild current state from live registries. Their size depends on the scene, not on how long the session has run. `_message_history` remains a live-runtime implementation detail while Phase 4b decides its bounded reconnect contract; it is not static-export authority.

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
  - owns replay state and viewer-facing registries.
- **`Whole`, `Region`, `Layer`**:
  - small domain wrappers around global representation, structural subsets, and non-structural visual groups.
- **`ShapesManager` + shape modules**:
  - public overlay API plus specialized argument normalization and message construction.
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

## Live Edit and Rebuild

Editing the molecular system lives **outside** the viewer core. The viewer exposes a
single public reconciliation primitive,
`view.apply_system_edit(new_molsys, atom_index_map=…, load_blocks="keep"|"collapse"|"append")`.
The MolSysMT addon (`view.addons.molsysmt.basic.*`) owns the edit *semantics*
(`set`/`add`/`remove`/`append_structures`) and drives them through that primitive;
the viewer's own loader sugar `view.load(mode="add"|"append_structures")` routes
through it as well.

When `apply_system_edit` runs:

- the reconciled MolSysMT object becomes the viewer's current molecular state;
- the viewer is rebuilt from that state;
- regions/layers/tags are replayed;
- visibility is restored;
- atom-index based state is remapped when topology changes;
- the rebuilt live registries must remain sufficient for canonical popup and static-export projection;
- any intentionally retained `_message_history` use belongs to the separate live reconnect contract, not export correctness.

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

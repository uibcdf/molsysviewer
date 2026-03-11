(Dev_Future_MolSysView_MolSysMTOps)=
# MolSysView ↔ MolSysMT operations

This page captures the agreed design direction for exposing a subset of MolSysMT operations through MolSysViewer objects
(`MolSysView`, `Whole`, and `Region`), and tracks what is already implemented vs what is still planned.

The core goal is to **avoid encouraging users to mutate `view.molsys` directly**. Instead, MolSysViewer should provide
safe, user-facing methods that keep the viewer state (regions, layers, tags, shapes, UI controls) consistent.

## Current status (summary)

Implemented (Level A)
- `MolSysView.select/get/info` and scoped `Whole`/`Region` counterparts.
- Live operations on `MolSysView`: `append_structures`, `set`, `add`, `remove`.
  These use a “Level A” strategy: mutate the MolSysMT system, then reload the `load_molsys_payload` payload and replay
  scene state.

Planned
- The `molsysviewer.tools.*` toolbox module for advanced operations (multi-view composition, geometry edits, analysis).
- “Level B” Mol* state-tree integration for incremental updates.

Implemented (initial `tools`)
- `molsysviewer.tools.basic.concatenate_structures(...)`.
  This is the first pure composition helper and returns a fresh `MolSysView`.

## Scope and principles

- **User-facing surface stays small**: we expose only what makes sense in a viewer-centric workflow.
- **Keep `MolSysView` small; grow `molsysviewer.tools`**: advanced operations should live in a dedicated toolbox module
  (planned as `molsysviewer.tools.*`) that operates on `MolSysView` objects. This keeps the viewer API predictable, while
  still enabling rich workflows (analysis, geometry edits, multi-view composition).
- **Live vs “returns new view” is explicit**:
  - *Live operations* mutate the system behind an existing viewer and must refresh the frontend and all dependent state.
  - *Pure operations* return a new `MolSysView` when the semantics imply creating a new combined system/view.
- **Regions act as a scope**: `Region.select/get/info` operate *inside the region* by intersecting with the region atom
  set.
- **Aggregation rule for region scope**: when `element != "atom"`, the region mask is applied by deriving indices at that
  level from the region atoms (not by passing atom indices as if they were indices of another element level).

## Must / Should / Could

| Priority | Item | Where | Status | Behavior |
|---|---|---|---|---|
| Must | `select(...)` | `MolSysView`, `Whole`, `Region` | Implemented | Wrapper to MolSysMT selection; `Region` is scoped by intersection. |
| Must | `get(...)` | `MolSysView`, `Whole`, `Region` | Implemented | Wrapper to MolSysMT get; `Region` is scoped by intersection. |
| Must | `info(...)` | `MolSysView`, `Whole`, `Region` | Implemented | Wrapper to MolSysMT info; `Region` is scoped by intersection. |
| Should | `append_structures(...)` | `MolSysView` | Implemented | Live: append frames; reload payload; replay state. |
| Should | `set(...)` | `MolSysView` | Implemented | Live: mutate via MolSysMT; reload payload; replay state. |
| Could | `remove(...)` | `MolSysView` | Implemented (experimental) | Live: remove atoms/structures; remap indices; reload payload; replay state. |
| Could | `add(...)` | `MolSysView` | Implemented (experimental) | Live: add another system into current view; reload payload; replay state. |
| Could | `concatenate_structures(...)` | `molsysviewer.tools.basic` | Implemented (initial) | Pure: return a new view built from multiple inputs/frames. |
| Could | `merge(...)` | `molsysviewer.tools.basic` | Implemented (initial) | Pure: return a new view from multiple views (systems + imported scene state). |
| Could | Geometry and analysis ops | `molsysviewer.tools` | Planned | Distances/angles/dihedrals, coordinate edits, etc. |

## Contracts (what users should be able to assume)

### `MolSysView`, `Whole`

- `Whole.select/get/info` behave as “the whole system”, i.e., they are equivalent to calling the corresponding method on
  the parent `MolSysView`.
- Defaults should match MolSysMT defaults (for example, `element="system"` where applicable).

### `Region.select/get/info` (scoped queries)

`Region` is a *scope* over the current viewer’s molecular system.

If the user passes an additional `selection=...`, it is interpreted as “selection **inside** the region”.

Implementation rule (aggregation when `element != "atom"`):

1. Resolve region atoms (the region’s atom set).
2. Resolve the user selection (if provided) *at the requested element level*.
3. Intersect the two in the right space:
   - If `element == "atom"`: intersect atom indices directly.
   - If `element != "atom"`: derive the element indices present in the region from the region atom set (e.g., map region
     atoms → group indices → unique group indices), then intersect at that element level.

This avoids the silent bug where atom indices are accidentally interpreted as indices of another element level.

## Implementation notes (high level)

### `molsysviewer.tools` (active direction)

The `molsysviewer.tools` namespace is intended for operations that go beyond “viewer basics”, for example:

- Multi-view composition (`merge`, `concatenate_structures`).
- Analysis helpers (distances, angles, dihedrals, contact queries).
- Geometry editing and structural manipulation that must coordinate “system mutation” with “viewer refresh”.

These functions may be *pure* (return a new `MolSysView`) or *live* (mutate an existing view), but the behavior must be
explicit in their docstrings and user-facing documentation.

Current direction:

- start with `tools.basic` for broadly useful composition helpers;
- grow additional modules (`structure`, `topology`, `hbonds`, `build`) only when their responsibilities become concrete in MolSysViewer terms.

### Mol* state-tree integration (Level B, planned for v2)

The initial implementation can follow a “Level A” strategy: mutate the MolSysMT system, then reload the whole
`load_molsys_payload` payload and replay the scene state (regions/layers/shapes).

This Level A approach is already implemented for the current live operations, and it is the baseline behavior until
Level B is introduced.

For a second iteration, the goal should be a more Mol*-native pipeline that enables incremental updates:

- Represent **topology** and **coordinates** as separate nodes in the Mol* state tree.
- Build a trajectory using Mol*’s `TrajectoryFromModelAndCoordinates` transformer (or an equivalent internal helper),
  with explicit `dependsOn` links between nodes.
- For operations like `append_structures` and coordinate edits, update only the **coordinates node** and let the state
  tree propagate updates instead of recreating the whole structure.

This change should reduce reload/replay complexity, improve responsiveness, and make “live editing” operations more
robust.

**MolSysMT ↔ Mol* converter (planned)**:

It would be valuable to implement a dedicated MolSysMT converter that maps `molsysmt.MolSys` to a Mol* `Trajectory`
object (and/or the pair Topology + Coordinates), so that MolSysViewer’s JS layer can build state-tree nodes directly
without going through the intermediate `MolSysPayload` path.

### Live operations: general obligations

Any live operation that mutates the molecular system behind an existing view must:

- Update `view.molsys` (or its internal storage) consistently.
- Rebuild and resend the viewer payload to the frontend (Mol*).
- Reconcile scene state that depends on atom indices:
  - Regions and their stored atom indices.
  - Layers (if they store atom indices or derived selections).
  - Shapes/overlays that store atom indices.
  - Tags that reference regions/layers/shapes.
- Refresh UI elements that depend on structures (trajectory frame controls, time/structure id indicators, etc.).

### `append_structures(...)` (live)

Minimum expected behavior:

- Increase the number of structures available in the viewer.
- Keep topology intact.
- Keep existing regions/layers/shapes valid without user intervention.
- Update any frame/trajectory controls to reflect the new range.

### `set(...)` (live)

Minimum expected behavior:

- Changes apply to the underlying molecular system.
- If the modified attribute affects what the viewer displays (ids/names, coordinates, bonds, etc.), the viewer refreshes
  accordingly.

### `remove(...)` (live)

Key complexity: atom index remapping.

Minimum expected behavior:

- Atom/structure removal updates the viewer payload and refreshes the frontend.
- All objects that store atom indices (regions, shapes, etc.) are updated (remapped and/or reduced).
- Regions that become empty are handled explicitly (either kept as empty, hidden, or deleted—decision to be documented
  when implemented).

### `add(...)` (live) vs `merge(...)` (pure)

`add(...)` is a live “extend this view” operation.

`merge(...)` is a pure “build a new view” operation and currently handles:

- Tag collisions via deterministic suffixes (`__2`, `__3`, ...).
- Atom index remapping for imported regions and atom-index-based shapes.
- First-view-wins policy for global representation, controls, and last camera snapshot.

Not yet part of the current contract:

- background/spin/swing state import,
- richer popup-linked UI state,
- non-atom-index scene semantics that only exist in frontend memory.

## Acceptance criteria (minimal tests)

When these features are implemented, each should have at least one regression-style test that uses real demo systems (no
mocks), and checks that:

- The viewer still renders and responds to messages after the operation.
- Regions/layers/shapes remain consistent (or fail in a controlled, documented way).
- For structure operations, frame controls reflect the new structure count.

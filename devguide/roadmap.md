# Development Roadmap (Status-Aligned)

Last update: 2026-03-04

This roadmap is status-aligned with the current repository state.
It is organized by execution priority and uses three labels:

- `Done`: implemented and present in codebase.
- `In progress`: partially implemented or implemented with limited coverage/docs.
- `Planned`: not implemented yet or not stabilized.

## 1) Core Runtime and Contracts

### Status

- `Done`
  - Python facade centered on `MolSysView`.
  - TypeScript runtime centered on `MolSysViewerController` + handler split.
  - Stable Python -> TS op protocol (`ViewerMessage` union).
  - MolSys payload path (`load_molsys_payload`) with native topology/trajectory construction.
  - Region/layer/whole abstractions with tag-based state.

- `In progress`
  - Contract hardening by test breadth across all ops and edge paths.
  - Cross-check consistency between docs snapshots and runtime behavior.
  - Support-library integration hardening (`argdigest`, `depdigest`, `pyunitwizard`, `smonitor`) is active because it affects runtime behavior directly.
  - `argdigest` now covers the main noisy public wrappers, but broader shape/detail coverage is still partial.
  - `smonitor` now has regression-backed wrapper coverage beyond config/catalog smoke tests, and the package-wide public signal map is largely enforced structurally.

### Next actions

- Expand protocol-focused tests for non-trivial operations (`set_global_representation`, layer retag, clear/reset interactions).
- Keep support-library integration aligned with sibling-library contracts, especially around bootstrap, quantity handling, and public API digestion.
- Keep contract changes additive unless versioned.

### Criteria

- Preserve payload schema: top-level `structures`, each with `coordinates` and optional `box`/`time`.
- Do not reintroduce legacy payload names.

## 2) Structural Editing and Live Rebuild

### Status

- `Done`
  - Live operations exposed in Python: `append_structures`, `set`, `add`, `remove`.
  - Rebuild pipeline remaps indices and replays state/history.

- `In progress`
  - Behavioral stabilization and broader regression coverage for remap/replay scenarios.
  - Rebuild regressions now exist for `remove()`, `append_structures()`, `add()`, `set()`, and a consecutive-operation chain, but broader cross-feature coverage is still partial.

### Next actions

- Extend coverage from rebuild mechanics into combined visibility semantics and replay-sensitive export behavior.
- Validate replay consistency across additional user-facing flows that are not purely live-edit operations.

### Criteria

- Preserve tag identity and region/layer continuity after rebuild.
- No silent index desynchronization between Python and TS state.

## 3) Shapes and Scientific Overlays

### Status

- `Done`
  - Python and TS support for major overlay families:
    - spheres/alpha-sphere sets,
    - pocket surfaces/blobs,
    - channel tubes,
    - anisotropy ellipsoids,
    - pharmacophore features,
    - links, vectors, triangle faces, tetrahedra.
  - Tag-based registration for selective clear/hide.

- `In progress`
  - Deep coverage of TS shape handler branches and error paths.
  - Python-side digestion for overlay/detail arguments is broader than before but still not exhaustive across every shape method.
  - Docs parity for all implemented overlays.

### Next actions

- Extend JS tests beyond region-hide to shape routing and tag-index lifecycle.
- Keep filling `argdigest` gaps in shape methods only where the public call surface is actually used or warning-prone.
- Close docs gaps where implemented APIs are still documented as placeholders.

### Criteria

- Keep Python option normalization deterministic and validated.
- Keep shape ops replay-safe for exports and rebuild flow.

## 4) Tools and Advanced Viewer-Safe Operations

### Status

- `In progress`
  - `molsysviewer.tools` now exists as the intended home for advanced operations that should not inflate `MolSysView`.
  - `molsysviewer.tools.basic.concatenate_structures(...)` exists as the first pure composition primitive.
  - `molsysviewer.tools.basic.merge(...)` now exists as the first view-centric composition primitive.
  - `molsysviewer.tools.basic` now also provides functional wrappers so users can operate on `MolSysView` in a MolSysMT-like style.
  - `molsysviewer.tools.basic.copy(...)` and `compare(...)` now extend that workbench surface.
  - The object-side inspection API is now the preferred home for scene-centric helpers such as focus and region partitioning.
  - User docs now include a dedicated `tools/` section with module/function pages for `tools.basic`.

### Next actions

- Add the next `tools.basic` operation only when its behavior and ownership are clear beyond `merge(...)`.
- Decide module boundaries intentionally (`basic`, `structure`, `topology`, `hbonds`, `build`) instead of copying MolSysMT mechanically.
- Keep `tools` operations explicit about whether they are pure (return a new view) or live (mutate an existing one).
- Keep user docs organized under `user/tools/<module>/<function>.md` or notebook equivalents so the tools surface can grow without scattering tutorials.
- Prioritize `tools` functions that make MolSysViewer more useful as an inspection/workbench tool for molecular systems.
- Keep focus helpers (`focus_selection`, `focus_region`, `Whole.focus`, `Region.focus`) on the object side.
- Keep region-building helpers on `MolSysView` when they create live scene objects rather than pure return values.
- Prefer one parameterized region-building entrypoint (`make_regions_by(element=...)`) over multiple near-duplicate `split_by_*` methods.
- Keep `make_regions_by(...)` intentionally limited to useful inspection levels (`chain`, `molecule`, `entity`) unless a stronger product need appears.

### Criteria

- `tools` should grow product capability without turning `MolSysView` into a grab bag.
- Operations that compose multiple systems/views should use real demo regressions and preserve viewer-safe semantics.

## 5) Visibility, Regions/Layers, and Global Semantics

### Status

- `Done`
  - Atom-level visibility masking from Python.
  - Global vs region visibility split in TS (`show_global` / `hide_global`, region hidden memory).
  - Region/layer acks from frontend to keep Python registries synchronized.

- `In progress`
  - Complex interaction tests are broader than before, but popup/export-connected visibility flows still need more coverage.
  - Support diagnostics are now strong enough that new visibility work should use `smonitor` context/contracts instead of ad hoc debugging.

### Next actions

- Extend coverage from core visibility invariants into popup/export-connected flows.
- Document edge semantics with executable examples in devguide checkpoints as needed.

### Criteria

- `region.hide()` must remain sticky across global show/hide cycles.
- Whole/global operations must not accidentally mutate region-specific hidden state.

## 6) Canvas Interaction and Picking

### Status

- `In progress`
  - The first JS -> Python interaction transport now exists for Mol* `hover` and `click`.
  - Right-click context transport now also exists as a first viewer-owned slice:
    - host context menu suppression inside the canvas,
    - separate context-target event,
    - minimal viewer context menu with seed actions.
  - The current contract is intentionally minimal and atom-centric:
    - `interaction_hover`
    - `interaction_click`
    - `interaction_context_menu`
    - `interaction_context_action`
    - `kind: "structure"` with `atom_indices`
    - `kind: "empty"` for canvas-empty interactions
  - Python now stores the last hover/click payload on `MolSysView`.
  - Python now also stores the last context-menu target payload and the last context-menu action payload.

### Next actions

- Use the interaction pages in `devguide/` as the implementation contract for the next slices.
- Add Python-side callback registration only after the transport contract settles.
- Decide whether region-aware and shape-aware picks belong in the same event family or in richer payload variants.
- Add pointer semantics and shared highlight/selection only after event ownership is clear.
- Turn menu-seeded `distance` / `angle` / `dihedral` actions into real tool-mode state machines.
- Keep interactive measurement in Mol* first:
  - it already owns picked loci and measurement representations,
  - Python/MolSysMT can consume emitted results later without entering the immediate click loop.
- Add visible tool-mode feedback and cancellation semantics before layering richer selection state on top.
- Build `active_selection` after the measurement path is locally coherent, then reuse it for strips, menus, and annotation interaction.
- Broaden `active_selection` from the first atom-centric element slice toward the documented element/shape/annotation/mixed contract.
  - `annotation` now has a first narrow slice via `GroupStrip` label badges.
  - `element + annotation` mixed selection is now supported as the first mixed path.
  - `shape` now has a first narrow slice via Mol* `shape-loci`.
- Keep the current element slice group-centric and only add hierarchy levels when the runtime can support them cleanly.
- Grow `GroupStrip` from the first chain-grouped selection/focus slice toward the full strip contract documented in `devguide/strips.md`.
- Keep strip interactions converged with canvas interactions:
  - hover and context menu should use the same event families instead of becoming a separate UX island.
- Make the active selection materially useful through the context menu before opening more target families:
  - selection-focused actions such as `Focus Selection` and `Clear Selection` are now the first concrete slice.

### Criteria

- Keep the first interaction contract additive and easy to replay/debug.
- Do not overfit the payload before real picking workflows exist.

## 6.5) Annotations and Persistent Labels

### Status

- `In progress`
  - `annotations` now exist as a real category instead of a pure design note.
  - The first implemented slice is narrow:
    - `view.annotations.add_label(text=..., group_index=..., tag=...)`
    - group-anchored persistent labels
    - layer-aware
    - replay/rebuild/export-safe
    - real frontend clearing through `clear_decorations(..., labels=True)`

### Next actions

- Keep the first slice narrow and stable.
- Broaden annotation interaction in controlled slices:
  - first `annotation` as `context_target` through strip overlays,
  - `annotation` now also has a first narrow `active_selection` slice through strip overlays,
  - `annotation` context now also has a first real action through the menu: `Focus Target`,
  - later hover/pick behavior,
  - canvas annotation pickability only after that path is stable.
- Grow the current strip overlay slice:
  - compact label marks now exist on `GroupStrip`,
  - strip label overlays can already seed annotation context,
  - richer annotation overlay semantics still need design and tests.
- Revisit atom labels, free-point labels, and shape-attached labels only after the first slice is solid.

### Criteria

- Keep persistent labels separate from hover tooltips.
- Keep annotation taxonomy separate from shape taxonomy.
- Keep annotation/layer semantics explicit and stable.

## 7) Export, Embedding, and Popup

### Status

- `Done`
  - `write_html` in `standalone` and `lite` modes.
  - Message-history replay and camera snapshot embedding.
  - Popup host logic with runtime source/module URL modes.

- `In progress`
  - Robustness tests for popup sync flows and camera sync edge cases.
  - Documentation parity for embed/export troubleshooting.
  - Baseline export ordering and popup host bootstrap contracts are now covered, but live mirror behavior remains only partially exercised.
  - Popup live-sync baseline is now regression-covered for initial replay and camera fight avoidance, though broader interactive breadth is still limited.

### Next actions

- Add tests around export message cleaning and replay ordering.
- Add explicit checklist for popup host/popout behavior verification.

### Criteria

- Export output must be reproducible from message history.
- Runtime source should remain decoupled from generated-artifact manual edits.

## 8) Testing and Quality Gates

### Status

- `Done`
  - Python test suite covers loaders, shapes, core viewer helpers, and key integration paths.
  - JS unit/e2e scaffolding exists with runnable scripts.
  - `pytest` and `python -m pytest` now resolve the same in-repo package during test collection.

- `In progress`
  - JS coverage is still narrower than the runtime surface, but handler-level breadth is improving.
  - E2E matrix is minimal.
  - Public API digestion coverage now has explicit regression tests for core wrapper methods and selected shape helpers.

### Next actions

- Extend JS unit coverage from handler guards into deeper success-path and replay/remap semantics.
- Add at least one additional E2E path beyond region hide.

### Criteria

- Every protocol-significant behavior should be covered in either Python or JS tests.
- Keep E2E deterministic and environment-aware (browser/WebGL constraints).

## 10) Strategic Directions (2026)

To reach a successful **1.0 release**, these three pillars must be prioritized over further support-layer abstractions.

### 1. Close the Interaction & E2E Gap
- The value of MolSysViewer lies in how it feels to interact with it.
- **Priority:** Implement more complex E2E tests simulating real scientific workflows (e.g., "identify a binding site, select it, label it, and measure distances").

### 2. GroupStrip: The 1D Navigation Pivot
- The 1D strip view (`GroupStrip`) is a primary differentiator. It's the key tool for navigating long proteins or complex systems where the 3D scene is cluttered.
- **Priority:** Ensure the strip is synchronized with the 3D canvas from day one, using the shared `active_selection` model.

### 3. Documentation for the "Scientific Workbench"
- The documentation must shift from API reference to case-study-driven tutorials.
- **Priority:** Create "Workbench Tutorials" (e.g., "How to analyze pocket contacts") that showcase the library as an integrated tool for structural biochemistry and drug design.

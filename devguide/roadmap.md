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
  - Support-library integration hardening (`depdigest`, `pyunitwizard`, `smonitor`) is active because it affects runtime behavior directly.

### Next actions

- Expand protocol-focused tests for non-trivial operations (`set_global_representation`, layer retag, clear/reset interactions).
- Keep support-library integration aligned with sibling-library contracts, especially around bootstrap and quantity handling.
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
  - Docs parity for all implemented overlays.

### Next actions

- Extend JS tests beyond region-hide to shape routing and tag-index lifecycle.
- Close docs gaps where implemented APIs are still documented as placeholders.

### Criteria

- Keep Python option normalization deterministic and validated.
- Keep shape ops replay-safe for exports and rebuild flow.

## 4) Visibility, Regions/Layers, and Global Semantics

### Status

- `Done`
  - Atom-level visibility masking from Python.
  - Global vs region visibility split in TS (`show_global` / `hide_global`, region hidden memory).
  - Region/layer acks from frontend to keep Python registries synchronized.

- `In progress`
  - Complex interaction tests are broader than before, but popup/export-connected visibility flows still need more coverage.

### Next actions

- Extend coverage from core visibility invariants into popup/export-connected flows.
- Document edge semantics with executable examples in devguide checkpoints as needed.

### Criteria

- `region.hide()` must remain sticky across global show/hide cycles.
- Whole/global operations must not accidentally mutate region-specific hidden state.

## 5) Export, Embedding, and Popup

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

## 6) Testing and Quality Gates

### Status

- `Done`
  - Python test suite covers loaders, shapes, core viewer helpers, and key integration paths.
  - JS unit/e2e scaffolding exists with runnable scripts.

- `In progress`
  - JS coverage is still narrower than the runtime surface, but handler-level breadth is improving.
  - E2E matrix is minimal.

### Next actions

- Extend JS unit coverage from handler guards into deeper success-path and replay/remap semantics.
- Add at least one additional E2E path beyond region hide.

### Criteria

- Every protocol-significant behavior should be covered in either Python or JS tests.
- Keep E2E deterministic and environment-aware (browser/WebGL constraints).

## 7) Documentation and Development Memory

### Status

- `Done`
  - Strong developer docs for architecture/protocol/public API.
  - Canonical infra guides integrated (SMonitor/ArgDigest/DepDigest/PyUnitWizard).

- `In progress`
  - Multiple user/developer pages remain placeholders.
  - Historical docs and current docs can diverge in status wording.

### Next actions

- Use `devguide/` checkpoints as authoritative development memory.
- Keep roadmap and checkpoints synchronized with executed work.

### Criteria

- Development decisions must be logged in `devguide/checkpoints.md`.
- Roadmap status must reflect repository reality, not aspirational-only lists.

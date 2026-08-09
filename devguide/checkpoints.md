# Development checkpoint

This is the current handoff, not a changelog. Replace it when the project state
changes. Normative behavior remains in the contracts linked below.

## Repository state

- Branch: `main`, at `55839d23`, plus the implemented and validated Phase 10
  scene-state file helpers awaiting independent audit. Phases 8 and 9 are
  committed separately; the scratch notebook is not part of any change.
- Phase 8 — representative performance and memory — is implemented in
  `15d86a8a` and awaits independent audit. Its evidence is in
  [`performance/representative_scale_gate_2026_08.md`](performance/representative_scale_gate_2026_08.md).
- `sandbox/Smoke_Test.ipynb` is developer-owned scratch state. Never stage it and
  never use it as architectural evidence.
- `molsysviewer/viewer.js` was regenerated with `npm run build:runtime`; it is a
  generated artifact, never a source file.

## Validation observed

- Phase 10 persistence focused checks: state serialization 15 passed, state v2
  22 passed, executable README 3 passed, Qt transport contract 12 passed.
- Phase 10 full Python attempt, 12 workers: 1,311 passed, 3 environmental skips
  and one stale Phase 9 test-message assertion. The assertion was corrected and
  its 12-test file passed; the full suite was not repeated blindly after the
  diagnosis.
- Focused Python: 22 passed (`test_scene_history.py` plus the representative
  fixture guard).
- Full Python, 12 workers: 1,304 passed, 3 documented environmental skips and
  one version-mismatch failure caused by running before regenerating
  `viewer.js`. After `build:runtime`, that sole real-Chrome target passed. The
  full suite was not repeated blindly after diagnosing the build-order cause.
- `npm run test:js`: exit 0.
- `npx tsc --noEmit`: exit 0.
- `npm run build:runtime`: exit 0.
- `npm run test:perf`: exit 0; 95k unknown 0.40 ms, hide 0.30 ms,
  dynamic-region gate 0.000723 ms/frame.
- `npm run test:e2e`: 30/30 suites passed in one real Chrome/SwiftShader
  process, with no browser/WebGL skips.
- Representative browser anchor after the final classifier change: 2,882 atoms
  x 10 structures, real Mol*, exit 0.

## Phase 8 result

The measurement matrix uses 2,882, 26,214, 104,856 and 314,568 atom molecular
supercells, crossed with 1, 10 and 100 structures where feasible. Fixture work
is owned and timed separately as MolSysMT work; no time coordinate is invented.

Main findings:

1. Typed coordinate transport scales well with structure count. At 314,568
   atoms, topology metadata is still 25.3 MiB JSON and Python serialization is
   about 1.63 s. Topology encoding, not `view.molsys`, is the next data-plane
   target.
2. Real Mol*/SwiftShader rendering is the scale ceiling: the 314k x 10 case
   peaks around 5.67 GiB process RSS and first becomes visible in about 31 s.
   Page close removes the scale-proportional renderer process.
3. Slow structure switches are variable first-visit/state-tree work, not a fixed
   1.36 s transport tax. Do not prewarm every structure without an A/B against
   startup and peak memory.
4. Host traffic remains isolated from a 314k popup transfer: 0.0088 ms against
   the fixed 100 ms threshold.
5. Qt assembly still peaks at 2x for representative coordinate-dominated
   payloads. Preallocating `bytearray` does not improve that shape; a future fix
   needs lower-copy delivery.
6. Scene-history snapshots now use compact deterministic JSON bytes and a
   64 MiB combined undo/redo budget. A 100k literal-overlay history dropped from
   about 212 MiB to 52.66 MiB retained RSS. The byte guard is mutation-verified.

## What is next

Phase 9 — documentation and upstream closure — is implemented in `55839d23`
and awaits audit. Phase 10 is active. Its persistence decision is implemented:
`save_state` / `load_state` are atomic JSON conveniences over the existing v2
overlay contract, not molecular-session bundles. Dependency-channel closure is
deliberately blocked until the sibling packages are release-ready; final
installed-artifact validation follows that closure.

Phase 7 still has two human/environment observations outside this automated
closure: Qt real-window/GPU and the human reload smoke. Do not report them as
automated passes.

## Resume cautions

- Read
  [`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md),
  [`scene_contracts.md`](scene_contracts.md),
  [`data_plane_architecture.md`](data_plane_architecture.md) and
  [`runtime_message_router.md`](runtime_message_router.md) before changing the
  runtime.
- Python remains the authority for reproducible scene state.
- Keep `molsysmt.MolSys` as the scientific authority; optimize wire projections
  instead of introducing a second in-memory truth.
- A sequence of structures need not have time. Missing box and time remain
  missing; never synthesize either for transport convenience.
- Binary buffers are runtime data, never scene history.
- Never validate rendering with `E2E_ALLOW_SKIP=1`.
- If a mutation remains green, first suspect that it hit the wrong layer or a
  stale build artifact.

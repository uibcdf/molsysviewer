# Development checkpoint

This is the current handoff, not a changelog. Replace it when the project state
changes. Normative behavior remains in the contracts linked below.

## Repository state

- Branch: `main`; the latest committed slice is opt-in hover telemetry and its
  audit closure. The scratch notebook is not part of any change.
- Phases 5, 6, 8 and 9 and the Phase 10 persistence slice were independently
  audited and closed on 2026-08-09. Phase 8 evidence remains in
  [`performance/representative_scale_gate_2026_08.md`](performance/representative_scale_gate_2026_08.md).
- `sandbox/Smoke_Test.ipynb` is developer-owned scratch state. Never stage it and
  never use it as architectural evidence.
- `molsysviewer/viewer.js` was regenerated with `npm run build:runtime`; it is a
  generated artifact, never a source file.

## Validation observed

- Current hover slice: 18 focused Python tests; 273 JS tests; TypeScript exit 0;
  runtime build exit 0; real-Chromium widget seam exit 0. Five prevention
  mechanisms fail under their mutations and pass restored.
- Full Python after the implementation, normal pytest with 12 workers: 1,316
  passed, 3 environmental skips, exit 0. One strict-boolean regression was
  added afterward and passed focused; production code did not change after the
  full run.
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

Resume in this order:

1. Scope the decided public-API digestion rule from
   [`pending_proposals/digest_every_public_callable.md`](pending_proposals/digest_every_public_callable.md):
   first produce the closed inventory of genuinely public callables and missing
   argument digesters, then execute it module by module. Do not equate every
   non-underscore implementation method with supported public API without that
   inventory.
2. In parallel when the required workstation is available, close Phase 7's two
   observations: Qt real-window/GPU and ten human live-demo replacements. Never
   report the existing offscreen/browser evidence as those observations.
3. Complete scientific dogfooding and the remaining human decisions in
   [`pending_proposals/what_needs_a_human_2026_08.md`](pending_proposals/what_needs_a_human_2026_08.md).
4. Once sibling releases are ready, close dependency channels; build wheel and
   conda artifacts; verify imports, resources and the one-line path from clean
   installations.
5. Run the final smoke/version matrix and release only with no open pre-1.0 gate.

Already closed in Phase 10: atomic overlay-state file helpers, notebook CI and
opt-in hover telemetry. The state helpers are not a molecular-session bundle;
hover is runtime/session state rather than scene state.

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

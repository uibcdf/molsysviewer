# Development checkpoint

This is the current handoff, not a changelog. Replace it when the project state
changes. Normative behavior remains in the contracts linked below.

## Repository state

- Branch: `main`, pushed. The latest committed slice adopted MolSysMT's reporting
  protocol for the two work queues and built the governance around it.
- Phases 5, 6, 8 and 9 and the Phase 10 persistence slice were independently
  audited and closed on 2026-08-09. Phase 8 evidence remains in
  [`performance/representative_scale_gate_2026_08.md`](performance/representative_scale_gate_2026_08.md).
- **Gate 9 of Phase 10 is done** (2026-08-12): every public callable is digested or
  deliberately exempt, and every argument name they introduce has a digester. Phase 10 is
  4 of 11.
- Phase 7 stays `⚠ 90%`: its automated seams are complete and its two visible-window Qt
  observations are not, and cannot be done here.
- `sandbox/Smoke_Test.ipynb` is developer-owned scratch state. Never stage it and
  never use it as architectural evidence.
- `molsysviewer/viewer.js` was regenerated with `npm run build:runtime`; it is a
  generated artifact, never a source file.
- **Reports are coordinated with the issue board** (2026-08-14). All 29 documents in
  `pending_bugs/` and `pending_proposals/` carry front matter and a GitHub issue; the
  queue READMEs are generated; `devtools/release_gate.py` is gate 11's command. See
  [`reporting_protocol.md`](reporting_protocol.md).
- Two commands need the network and live outside the suite:
  `python devtools/devguide_issue.py sync --check` compares the board with the front
  matter, and `python devtools/devguide_index.py --check` (which does run in the suite)
  keeps the queue READMEs honest. Run the first before a release and after any session
  that closed or restatused an entry.
- Whether the reporting vocabularies become an ecosystem-wide shared source of truth is
  asked at [uibcdf/molsysmt#156](https://github.com/uibcdf/molsysmt/issues/156). Their
  answer changes what is worth investing in the local tooling.

## Validation observed

- Current slice, 2026-08-14: **1,602 Python passed, 4 skips, exit 0**
  (`--receptor=llm -n 12`). Three of the skips are environmental — no display, no
  WebGL, imageio present — and the fourth is an optional MolSysSuite add-on that is not
  installed here.
- Gate 9 was verified by behaviour as well as by count: exercising a broad slice of the
  public surface with `UserWarning` promoted to an error produces no
  `DigestNotDigestedWarning`.
- The latest frontend validation remains the Phase 8/9 result: **273 JS**, `tsc` clean,
  **30/30 E2E**, `build:runtime` and `test:perf` green. **No TypeScript changed since**,
  so it was not re-run.
- Every guard added in this round is mutation-verified; each test says which mutation
  kills it.

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

**Read [`capability_audit.md`](capability_audit.md) before writing any claim about what
MolSysViewer does.** It is generated; regenerate with
`python devtools/capability_audit.py --write`.

**A defect or a proposal is filed under
[`reporting_protocol.md`](reporting_protocol.md)** — front matter, a GitHub issue, and a
`guard` named at close. Adopted 2026-08-14 from MolSysMT; the 28 documents in the two
queues all carry it.

Resume in this order:

1. **Widen `EXECUTABLE_PAGES`** in `tests/test_documentation_pages_run.py`. It executes
   three documentation pages today; the rest of the markdown is run by nothing, which is
   how a half-applied rename left a `NameError` in four pages. This is the only remaining
   item that needs neither another machine nor a decision.

   The audit's second-sharpest gap is next to it: **four capabilities have no browser
   observation at all** — trajectory plot, movie, `save_state`/`load_state`, units — and
   two of them are `stable`. See the *Nothing has watched these draw* section of
   [`capability_audit.md`](capability_audit.md).
2. In parallel when the required workstation is available, close Phase 7's two
   observations: Qt real-window/GPU and ten human live-demo replacements. Never
   report the existing offscreen/browser evidence as those observations.
3. Complete scientific dogfooding and the remaining human decisions in
   [`pending_proposals/what_needs_a_human_2026_08.md`](what_needs_a_human_2026_08.md)
   — three items, all needing a screen or a judgement.
4. Once sibling releases are ready, close dependency channels; build wheel and
   conda artifacts; verify imports, resources and the one-line path from clean
   installations.
5. Run `python devtools/release_gate.py` and release only when it exits zero. It
   refuses to be silent: anything it cannot run is `BLOCKED` with the reason, and
   that is still a non-zero exit.

Closed in Phase 10 so far: atomic overlay-state file helpers, notebook CI, opt-in hover
telemetry, and public-callable digestion. The state helpers are not a molecular-session
bundle; hover is runtime/session state rather than scene state.

### Two proposals waiting on a decision, not on work

- [`pending_proposals/what_save_state_promises.md`](pending_proposals/what_save_state_promises.md)
  — five numbered decisions about what a saved state means. The cheapest and most valuable
  is binding a state document to the structure it was written from.
- [`pending_proposals/addon_maturity_and_ownership.md`](pending_proposals/addon_maturity_and_ownership.md)
  — the maturity vocabulary is defined; each toolkit adopts it by re-declaring
  `meta["status"]`. Until then the README reports what each add-on says today.

## Resume cautions

- Read
  [`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md),
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

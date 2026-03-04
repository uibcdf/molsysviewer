# Development Checkpoints

This file is the running development log for the repository.
It is intentionally concise and operational.

## Entry Format

- `Date`: YYYY-MM-DD
- `ID`: stable checkpoint identifier
- `Scope`: what was addressed
- `Decisions`: explicit choices made
- `Status`: current project status for that scope
- `Plan`: next concrete actions
- `Criteria`: invariants/rules to preserve
- `Perspectives`: medium-term direction
- `Ideas`: optional backlog notes

---

## 2026-03-04 — CP-2026-03-04-A

- `Scope`: Establish dev workflow governance and align development truth source.
- `Decisions`:
  - `devguide/` is the source of truth for development status and planning.
  - Progress will be tracked via explicit checkpoints in this file.
  - `devguide/roadmap.md` must reflect real implementation status (not only aspirational phases).
- `Status`:
  - Checkpoint process established.
  - `devguide/README.md` updated to include source-of-truth policy and checkpoints index.
  - Roadmap alignment completed in the current cycle (`devguide/roadmap.md` status-aligned).
- `Plan`:
  - Keep checkpoints updated after each substantial step.
  - Use checkpoints to drive prioritization step-by-step.
- `Criteria`:
  - Do not treat generated JS artifacts as implementation source.
  - Preserve Python <-> TypeScript message contract stability.
  - Keep region/layer/tag semantics stable unless explicitly versioned.
- `Perspectives`:
  - Use checkpoint history as release-quality technical memory.
  - Increase traceability between decisions, status, and executed changes.
- `Ideas`:
  - Add a lightweight checkpoint index by topic (protocol, tests, docs, release).
  - Add checkpoint references in PR descriptions for auditability.

## 2026-03-04 — CP-2026-03-04-B

- `Scope`: Start roadmap block "Testing and Quality Gates" for JS unit tests.
- `Decisions`:
  - Replace fragile unit test coupled to obsolete controller internals.
  - Focus initial JS coverage on stable handler-level behavior (`trajectory`, `state`).
- `Status`:
  - Existing JS unit test suite was red due to stale assumptions.
  - `molsysviewer/js/tests/unit/region-hide.test.ts` updated with handler-focused tests.
  - `npm run test:js` is now green in current workspace.
- `Plan`:
  - Continue adding handler-level tests (`loader`, `scene`, additional `state` and `trajectory` paths).
  - Add one more E2E path beyond region hide.
- `Criteria`:
  - Tests must avoid brittle coupling to private controller internals.
  - Prefer deterministic mocks and explicit assertions on contract-relevant behavior.
- `Perspectives`:
  - Incremental JS test expansion should reduce regression risk in protocol/state changes.
- `Ideas`:
  - Split `tests/unit/region-hide.test.ts` into themed files as coverage grows.

## 2026-03-04 — CP-2026-03-04-C

- `Scope`: Extend JS unit coverage for `LoaderHandlers` and `SceneHandlers`.
- `Decisions`:
  - Keep tests deterministic and mock-based; avoid depending on live Mol* runtime.
  - Prioritize contract-relevant behavior: validation guards, callback orchestration, state toggles.
- `Status`:
  - Added loader guard tests for invalid inputs (`loadFromString`, `loadMolSysPayload`, `loadFromUrl`, `loadPdbId`).
  - Added scene tests for `clearScene` flag behavior, `clearAll` reset notification, and spin/swing mutual exclusion.
  - JS unit suite remains green with updated coverage.
- `Plan`:
  - Add tests for successful loader paths (with controllable stubs) and additional state/trajectory branches.
  - Add a second E2E scenario beyond region hide.
- `Criteria`:
  - Test assertions must map to externally meaningful handler behavior, not brittle internals.
  - Preserve compatibility of Python -> TS op handling while increasing guard coverage.
- `Perspectives`:
  - Incremental handler coverage should make protocol refactors safer and faster.
- `Ideas`:
  - Introduce a simple test helper module for common plugin/callback mocks.

## 2026-03-04 — CP-2026-03-04-D

- `Scope`: Add JS unit tests for successful loader forwarding and pending layer visibility state.
- `Decisions`:
  - Verify successful public handler paths by stubbing private internal methods at runtime.
  - Expand state coverage around pending layer visibility bookkeeping before refs exist.
- `Status`:
  - Added tests for valid forwarding/default behavior in `LoaderHandlers`.
  - Added test for `StateHandlers` pending visibility transitions (`hideLayer` then `showLayer` without refs).
  - JS unit suite remains green after changes.
- `Plan`:
  - Continue with E2E expansion (second scenario beyond current region-hide path).
  - Consider splitting growing unit test file by handler domain.
- `Criteria`:
  - Keep tests independent from Mol* runtime side effects where possible.
  - Keep assertions on externally meaningful orchestration behavior.
- `Perspectives`:
  - Handler-level confidence is improving enough to support safer protocol-level refactors.
- `Ideas`:
  - Add explicit success-path tests for `SceneHandlers.toggleBackground` and fullscreen fallback behavior.

## 2026-03-04 — CP-2026-03-04-E

- `Scope`: Add second JS E2E scenario beyond region hide.
- `Decisions`:
  - Extend existing E2E script with a second scenario instead of creating a separate harness flow.
  - Validate full-reset resilience through `clear_all` and explicit `registry_cleared` event check.
- `Status`:
  - E2E now covers:
    - region creation + hide,
    - shape add/clear by tag,
    - `clear_all` + registry reset signal,
    - reload after full reset.
  - In this workspace, Chromium launch is sandbox-blocked; test exits with documented skip path.
- `Plan`:
  - Keep this scenario as baseline for future interactive regressions.
  - Add one more E2E around trajectory controls when browser/WebGL environment is available.
- `Criteria`:
  - E2E scripts must remain resilient to sandbox/WebGL restrictions and skip cleanly when required.
  - Assertions should target stable externally observable behavior (events, no console errors).
- `Perspectives`:
  - This gives first coverage of lifecycle reset behavior that unit tests cannot fully emulate.
- `Ideas`:
  - Add artifact capture (last message + operation trace) to ease debugging when E2E fails outside sandbox.

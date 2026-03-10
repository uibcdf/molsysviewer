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

## 2026-03-04 — CP-2026-03-04-F

- `Scope`: Increase unit coverage for state/global visibility queueing and scene background toggling.
- `Decisions`:
  - Validate queue behavior for global visibility ops when structure is unavailable.
  - Add explicit assertions for shape-tag indexing and first-time layer ack emission.
  - Cover dark/light background toggling with cached renderer snapshots.
- `Status`:
  - Added `StateHandlers` tests for:
    - queued `hideGlobal/showGlobal` behavior and `requestedGlobalHidden` semantics,
    - `registerShapeRef` indexing + `layer_ack` emission.
  - Added `SceneHandlers` test for deterministic `toggleBackground` dark/light transitions.
  - JS unit suite remains green with expanded assertions.
- `Plan`:
  - Continue by splitting the growing unit test file into handler-specific files.
  - Start a trajectory-focused E2E when browser/WebGL-capable environment is available.
- `Criteria`:
  - Keep state/scene assertions tied to stable observable behavior (maps, flags, emitted events).
  - Avoid tests that rely on fragile private controller internals.
- `Perspectives`:
  - Current coverage now spans guard paths, success forwarding, queueing semantics, and key UI state toggles.
- `Ideas`:
  - Add helper factories for mock plugin/callback creation to reduce test boilerplate.

## 2026-03-04 — CP-2026-03-04-G

- `Scope`: Split JS unit test suite into handler-domain files.
- `Decisions`:
  - Keep `region-hide.test.ts` as stable entrypoint used by existing npm scripts.
  - Move test cases into domain-focused files: `trajectory`, `state`, `loader`, `scene`.
  - Extract shared utilities (`withWarnCapture`, trajectory plugin mock) into `helpers.ts`.
- `Status`:
  - Unit tests are now physically split by concern with a small aggregator entrypoint.
  - Existing `npm run test:js` flow remains unchanged and green after refactor.
- `Plan`:
  - Optionally rename the legacy entrypoint in a later step (`unit/index.test.ts`) once scripts are updated.
  - Continue expanding coverage per-domain without growing a monolithic test file.
- `Criteria`:
  - Preserve compatibility with current build/test scripts while improving maintainability.
  - Keep each test file narrowly scoped to one handler area.
- `Perspectives`:
  - This unlocks cleaner growth of JS coverage and easier review of behavior changes.
- `Ideas`:
  - Add a tiny README in `js/tests/unit` describing file ownership by handler domain.

## 2026-03-05 — CP-2026-03-05-H

- `Scope`: Complete step 1 by normalizing JS unit test entrypoint naming.
- `Decisions`:
  - Replace legacy `region-hide` unit entrypoint name with neutral `index`.
  - Keep test content split by handler domain with `index.test.ts` as aggregator only.
- `Status`:
  - Unit entrypoint/files renamed to `tests/unit/index.test.ts` and `tests/unit/dist-index.js`.
  - npm scripts updated in `molsysviewer/js/package.json` (`build:test:js`, `test:js`, `coverage:js`).
- `Plan`:
  - Re-run JS unit tests with updated scripts and keep E2E flow unchanged.
  - Continue roadmap "Testing and Quality Gates" with next planned coverage target.
- `Criteria`:
  - Preserve deterministic build/test commands and avoid legacy naming drift.
  - Keep `devguide` as authoritative checkpoint log before each next step.
- `Perspectives`:
  - Neutral naming avoids coupling test infrastructure to a single scenario and clarifies intent.
- `Ideas`:
  - Add a short `js/tests/unit/README.md` documenting the entrypoint and handler-file layout.

## 2026-03-10 — CP-2026-03-10-I

- `Scope`: Extend JS unit coverage to `ShapeHandlers` guard semantics.
- `Decisions`:
  - Prioritize contract-level validation paths for shape ops before deeper Mol* builder success-path tests.
  - Keep shape tests mock-light and focused on invalid payload rejection plus no-ref-registration invariants.
- `Status`:
  - Added `molsysviewer/js/tests/unit/shape-handler.test.ts`.
  - Unit coverage now includes guard behavior for `alpha sphere set`, `pocket surface`, `pocket blob`, `channel tube`, `anisotropy ellipsoids`, `pharmacophore`, `displacement vectors`, `tetrahedra`, and `triangle faces`.
- `Plan`:
  - Re-run JS unit suite and keep the shape file as the base for later success-path registration tests.
  - Next high-value target remains structural-edit/remap regression coverage or trajectory E2E when browser/WebGL is available.
- `Criteria`:
  - Invalid shape payloads must fail softly with warnings and must not register frontend refs.
  - `devguide` remains the checkpoint ledger before selecting the next coverage increment.
- `Perspectives`:
  - This closes the largest missing handler-family gap in JS unit coverage without coupling tests to Mol* internals.
- `Ideas`:
  - Add success-path shape tests later through controlled builder seams if the runtime surface is refactored for easier injection.

## 2026-03-10 — CP-2026-03-10-J

- `Scope`: Harden live-edit rebuild coverage for Python-side `remove()` remap/replay flow.
- `Decisions`:
  - Use a real demo viewer (`molsysviewer.demo["dialanine"]`) instead of synthetic system mocks for rebuild regression coverage.
  - Treat rebuild replay as an internal path and bypass public digestion when reapplying already-normalized region/layer/global state.
  - Derive `multiple_structures` during rebuild from the serialized payload, not from unstable MolSysMT structure accessors.
- `Status`:
  - Added a regression test for `remove()` covering:
    - `clear_all` + payload reload ordering,
    - region atom-index remap,
    - shape replay remap for `atom_indices`, `mouth_atom_indices`, and `atom_pairs`,
    - dropped shapes whose atom-index payload becomes empty,
    - preserved hidden-layer/global visibility semantics after rebuild.
  - Fixed rebuild regressions found while exercising the real path:
    - stale `get_n_structures()` assumption,
    - unintended argument digestion during internal replay.
- `Plan`:
  - Extend live-edit coverage to `append_structures()` and `add()`/`set()` replay semantics.
  - Reuse this file as the base for future remap/replay edge cases.
- `Criteria`:
  - Live edits must preserve region/layer/tag continuity and not corrupt replayable message history.
  - Internal rebuilds must not re-digest already normalized state.
- `Perspectives`:
  - This starts closing the highest-risk Python-side mutation gap: rebuild correctness after atom removal.
- `Ideas`:
  - Add a focused export test ensuring rebuilt `_message_history` remains HTML-replay-safe after consecutive live edits.

## 2026-03-10 — CP-2026-03-10-K

- `Scope`: Remove stale default guidance around `NUMBA_CACHE_DIR`.
- `Decisions`:
  - `NUMBA_CACHE_DIR=/tmp/numba_cache` is no longer documented as a default requirement.
  - MolSysMT/Numba workarounds should only be documented after reproducing and capturing a concrete failure.
- `Status`:
  - Repo guidance and developer docs were updated to remove unconditional `NUMBA_CACHE_DIR` setup instructions.
  - The current workspace was validated without that variable for demo loading and `tests/test_live_edit_rebuild.py`.
- `Plan`:
  - Keep observing for environment-specific MolSysMT/Numba failures before reintroducing any workaround guidance.
- `Criteria`:
  - Developer guidance should reflect validated current behavior, not obsolete setup habits.
- `Perspectives`:
  - This removes unnecessary environment ceremony and keeps troubleshooting evidence-based.

## 2026-03-10 — CP-2026-03-10-L

- `Scope`: Extend live-edit rebuild coverage from `remove()` to `append_structures()`.
- `Decisions`:
  - Reuse the same demo-based regression file for structural editing scenarios to keep invariants comparable across operations.
  - Treat `append_structures()` as the next lowest-friction live-edit path because it exercises replay/rebuild without atom-index remap complexity.
- `Status`:
  - Added a regression test asserting that `append_structures()`:
    - rebuilds history from `clear_all`,
    - emits a `load_molsys_payload` with `multiple_structures=True`,
    - preserves region atom indices,
    - preserves hidden region/layer state,
    - replays shape messages unchanged when no remap is needed.
- `Plan`:
  - Continue the file with `set()` and `add()` scenarios.
  - Add a consecutive-mutations case once the single-operation matrix is in place.
- `Criteria`:
  - Appending structures must not break tag continuity or replay ordering.
  - Multi-structure payload state must remain explicit in replayed history.
- `Perspectives`:
  - The live-edit matrix now covers both rebuild-with-remap (`remove`) and rebuild-without-remap (`append_structures`).

## 2026-03-10 — CP-2026-03-10-M

- `Scope`: Extend live-edit rebuild coverage to `add()`.
- `Decisions`:
  - Keep the `add()` regression in the same demo-based test file used for other live-edit operations.
  - Apply `NUMBA_CACHE_DIR=/tmp/numba_cache` only inside the `add()` regression, because this workflow reproduced a concrete MolSysMT/Numba cache failure in the current environment.
- `Status`:
  - Added a regression test asserting that `add()`:
    - rebuilds history from `clear_all`,
    - expands the atom payload from 22 to 44 atoms,
    - preserves region atom indices,
    - preserves hidden region/layer state,
    - keeps single-structure replay semantics explicit in the payload.
- `Plan`:
  - Investigate a stable `set()` scenario next, or document its current backend limitations if the issue remains upstream in MolSysMT value digestion.
  - Add a consecutive-mutations regression once `set()` or another final single-operation case is covered.
- `Criteria`:
  - Environment-specific workarounds stay narrowly scoped to the exact failing path.
  - Live-edit coverage should keep using real demo systems and replay-history assertions.
- `Perspectives`:
  - The matrix now covers `append_structures`, `add`, and `remove`, leaving `set()` as the main uncovered live-edit API.

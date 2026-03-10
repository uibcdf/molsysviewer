# Development Checkpoint

This file is not a changelog.
Git history already covers that.

This file is the current handoff checkpoint for ongoing development work.
It should help a developer answer, quickly:

- where we are,
- what is already decided,
- what should happen next,
- why that is the right next step,
- what constraints must not be broken.

Update this file to reflect the current state.
Do not append dated historical entries unless a date is itself operationally relevant.

## Current Focus

- Stabilize and expand test coverage with the highest immediate return.
- Keep `devguide/` aligned with the real repository state.
- Prioritize regression coverage for behavior that crosses Python <-> TypeScript boundaries or rebuild/replay flows.

## Current State

- JS/TS tests
  - Unit suite was stabilized and split by handler domain.
  - Coverage now includes `trajectory`, `state`, `loader`, `scene`, and `shape` guard semantics.
  - E2E covers:
    - region creation + hide,
    - tagged shape add/clear,
    - `clear_all` + `registry_cleared`,
    - reload after full reset.
  - E2E remains environment-dependent because browser/WebGL support is required.

- Python live-edit coverage
  - Regression coverage now exists for:
    - `remove()`: rebuild with atom-index remap,
    - `append_structures()`: rebuild without atom-index remap, multi-structure payload,
    - `add()`: rebuild with expanded atom payload.
  - These regressions use real demo viewers instead of synthetic mocks.

- Dev/docs workflow
  - `devguide/` is the source of truth for active development status and handoff context.
  - `NUMBA_CACHE_DIR=/tmp/numba_cache` is no longer treated as a default global requirement.
  - A localized workaround is still needed in the current `add()` regression because that exact flow reproduces a real MolSysMT/Numba cache failure in this environment.

## Active Decisions

- Use real demo viewers when regression value depends on real MolSysMT behavior.
- Prefer contract-level and externally observable assertions over private implementation coupling.
- Treat internal rebuild/replay as internal state application:
  - it must not re-digest already normalized state,
  - it must preserve replayable `_message_history`,
  - it must preserve region/layer/tag continuity.
- Keep environment workarounds narrowly scoped to concrete failing paths, not as blanket repository policy.

## Next Step

- Attack `MolSysView.set()` directly.

Why this is next:

- It is the last uncovered live-edit API in the current matrix.
- `remove()`, `append_structures()`, and `add()` are now protected by regressions.
- `set()` already exposed backend friction during exploration, so it is now more valuable to treat it as an implementation/debugging target than to defer it.

## What We Learned About `set()`

- The current backend path is not yet yielding a clean regression scenario.
- Observed blockers during direct exercise:
  - string-valued edits can fall into MolSysMT/PyUnitWizard unit parsing,
  - some attribute/form resolution paths in `molsysmt.set(...)` do not behave robustly in the current environment,
  - coordinate edits also hit value-digestion expectations that need explicit handling.

Working assumption:

- `set()` likely needs implementation hardening or a narrower supported-path policy before it can be covered with a stable regression test.

## Immediate Plan

1. Reproduce `set()` with the smallest meaningful mutation that should be supported.
2. Decide whether the right fix is:
   - a MolSysViewer-side adaptation before calling `molsysmt.set(...)`, or
   - documenting a more constrained supported `set()` surface if the issue is upstream.
3. Add the regression only after the supported behavior is clear and stable.
4. After `set()`, add one consecutive-mutations regression to validate replay consistency across multiple live edits.

## Criteria

- Do not treat generated JS artifacts as implementation source.
- Preserve Python <-> TypeScript payload/message contracts.
- Preserve region/layer/tag identity across rebuilds.
- Keep `_message_history` replay-safe for HTML export and popup/docs-lite flows.
- Prefer evidence-based docs over inherited setup folklore.

## Open Risks

- `set()` is still uncovered and currently appears brittle because of backend digestion/value-resolution behavior.
- `add()` still depends on a scoped `NUMBA_CACHE_DIR` workaround in this environment.
- E2E breadth is still thin relative to the runtime surface.
- Export/replay regression coverage is still lighter than live-edit coverage.

## Useful Follow-ups

- Add a regression around consecutive live edits (`remove` + `append_structures`, or `add` + `remove`) once `set()` is resolved.
- Add a focused export test that asserts rebuilt `_message_history` remains HTML-replay-safe.
- Expand JS tests from guards into more success-path and replay-sensitive behavior where seams are controllable.

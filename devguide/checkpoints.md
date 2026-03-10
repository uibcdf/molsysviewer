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
    - `add()`: rebuild with expanded atom payload,
    - `set()`: rebuild after topological and structural edits.
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

- Add a regression for consecutive live edits and confirm replay/export safety after rebuild chains.

Why this is next:

- The single-operation live-edit matrix is now covered for `remove()`, `append_structures()`, `add()`, and `set()`.
- The next failure mode with the highest architectural risk is no longer “one operation breaks rebuild”, but “multiple live edits leave replay/history inconsistent”.
- This also connects directly to export reliability, because HTML replay depends on `_message_history` staying coherent after rebuilds.

## What We Learned About `set()`

- `MolSysView.set()` needed a MolSysViewer-side wrapper instead of blind delegation to `molsysmt.set(...)`.
- The important fixes were:
  - resolving attributes with `include_none=True`,
  - calling the concrete `set_*` function with `skip_digestion=True`,
  - normalizing `coordinates` as a quantity with length units before applying the setter.
- With that adapter in place, at least these core paths are now covered and working:
  - topological string edit (`group_name`),
  - structural edit (`coordinates` with units).

## Immediate Plan

1. Add one consecutive-mutations regression over the current live-edit matrix.
2. Add a focused export/replay regression using rebuilt `_message_history`.
3. Revisit any remaining unsupported `set()` attribute families only if they surface as real user-facing needs.

## Criteria

- Do not treat generated JS artifacts as implementation source.
- Preserve Python <-> TypeScript payload/message contracts.
- Preserve region/layer/tag identity across rebuilds.
- Keep `_message_history` replay-safe for HTML export and popup/docs-lite flows.
- Prefer evidence-based docs over inherited setup folklore.

## Open Risks

- `add()` still depends on a scoped `NUMBA_CACHE_DIR` workaround in this environment.
- E2E breadth is still thin relative to the runtime surface.
- Export/replay regression coverage is still lighter than live-edit coverage.

## Useful Follow-ups

- Add a regression around consecutive live edits (`remove` + `append_structures`, or `add` + `remove`).
- Add a focused export test that asserts rebuilt `_message_history` remains HTML-replay-safe.
- Expand JS tests from guards into more success-path and replay-sensitive behavior where seams are controllable.

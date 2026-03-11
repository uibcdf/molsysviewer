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
    - `set()`: rebuild after topological and structural edits,
    - consecutive live-edit chains with replay/export assertions.
  - These regressions use real demo viewers instead of synthetic mocks.

- Python visibility semantics
  - Regression coverage now exists for:
    - sticky `whole.hide()` across `show(all)`,
    - sticky hidden region/layer state across `view.hide()` / `view.show()`,
    - `show(all)` restoring the atom mask without explicitly re-showing hidden regions.
  - These assertions are aligned directly with `devguide` visibility semantics.

- Export / popout core contracts
  - Regression coverage now exists for:
    - export replay ordering with `set_camera_snapshot` appended after cleaned message history,
    - standalone export state honoring `enable_popout=False`,
    - popup host runtime bootstrap via `moduleUrl`,
    - popup host sync messages being gated on `isReady` and open window state.

- Popup live-sync baseline
  - Regression coverage now exists for:
    - popup initial sync replaying message history and camera snapshot,
    - popup autohide initialization from host state,
    - popup -> host camera sync being gated by user interaction,
    - host -> popup camera sync being blocked while the popup user is interacting.

- Dev/docs workflow
  - `devguide/` is the source of truth for active development status and handoff context.
  - `NUMBA_CACHE_DIR=/tmp/numba_cache` is no longer treated as a default global requirement.
  - A localized workaround is still needed in the current `add()` regression because that exact flow reproduces a real MolSysMT/Numba cache failure in this environment.

- Support-library integration hardening
  - `depdigest` now runs before importing the heavier public submodules from package init.
  - `pyunitwizard` usage is being unified around `molsysviewer._pyunitwizard.puw` instead of mixing local and `molsysmt` aliases.
  - Support helpers around coordinates/units were tightened to match the actual PyUnitWizard contract.
  - `smonitor` coverage has been expanded to more public wrapper APIs (`Whole`, `Region`, `Layer`, `ShapesManager`).

## Active Decisions

- Use real demo viewers when regression value depends on real MolSysMT behavior.
- Prefer contract-level and externally observable assertions over private implementation coupling.
- Treat internal rebuild/replay as internal state application:
  - it must not re-digest already normalized state,
  - it must preserve replayable `_message_history`,
  - it must preserve region/layer/tag continuity.
- Keep environment workarounds narrowly scoped to concrete failing paths, not as blanket repository policy.
- Treat sibling support libraries (`argdigest`, `depdigest`, `pyunitwizard`, `smonitor`) as active engineering dependencies, not passive externals.
- Keep `molsysviewer` on one local `pyunitwizard` instance/configuration path.

## Next Step

- Resume implementation on the highest-value 1.0 path, with core regressions now covering the main architectural contracts that were previously risky.

Why this is next:

- The live-edit matrix now covers:
  - single operations,
  - a consecutive mutation chain,
  - and replay/export safety of the rebuilt history.
- The next high-value core gaps are no longer centered on rebuild mechanics, baseline visibility semantics, or popup/export synchronization basics.
- The strongest remaining architectural risks are:
  - broader export reliability outside the already-tested rebuild chain.
  - replay ordering and camera/state continuity across embedded/exported flows.
  - feature breadth toward the still-incomplete 1.0 surface.
  - functionality that is still simply not implemented yet.
- The support-library layer is now in active hardening, so regressions there should be caught early instead of worked around ad hoc.

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

1. Pick the next core cross-cutting behavior:
   - finish any remaining support-library integration cleanup that blocks clean implementation work, or
   - resume feature implementation on the highest-value 1.0 path.
2. Add one regression that exercises that behavior through externally visible outcomes.
3. Revisit additional `set()` attribute families only if they become a real product need.

## Criteria

- Do not treat generated JS artifacts as implementation source.
- Preserve Python <-> TypeScript payload/message contracts.
- Preserve region/layer/tag identity across rebuilds.
- Keep `_message_history` replay-safe for HTML export and popup/docs-lite flows.
- Prefer evidence-based docs over inherited setup folklore.

## Open Risks

- `add()` still depends on a scoped `NUMBA_CACHE_DIR` workaround in this environment.
- E2E breadth is still thin relative to the runtime surface.
- Popup/popout behavior is still lighter in coverage than live-edit, but no longer the clearest blocker for resuming implementation.
- The support-library hardening pass is still in progress until the remaining integration cleanup is committed and documented.

## Useful Follow-ups

- Add popup/popout sync regressions around camera/state replay if the harness can support them.
- Add export regressions that mix camera snapshots, visibility cleaning, and replay ordering.
- Expand JS tests from guards into more success-path and replay-sensitive behavior where seams are controllable.
- Audit any remaining public wrappers that still miss `@signal` coverage.

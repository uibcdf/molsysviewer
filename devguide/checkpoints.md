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

- Resume feature implementation toward 1.0 on top of the now-hardened runtime/contracts layer.
- Start the `molsysviewer.tools` package as the home for advanced viewer-safe operations.
- Keep `devguide/` aligned with the real repository state.
- Prioritize regression coverage for new product-facing behavior, especially where it composes multiple systems/views.

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
  - Test bootstrap now forces the repository root onto `sys.path` via [`tests/conftest.py`](/home/diego/repos@uibcdf/molsysviewer/tests/conftest.py) so `pytest` and `python -m pytest` resolve the same in-repo `molsysviewer` package.

- Support-library integration hardening
  - `depdigest` now runs before importing the heavier public submodules from package init.
  - `pyunitwizard` usage is being unified around `molsysviewer._pyunitwizard.puw` instead of mixing local and `molsysmt` aliases.
  - Support helpers around coordinates/units were tightened to match the actual PyUnitWizard contract.
  - `config` now also uses the local `_pyunitwizard` instance directly instead of going back through package-root imports.
  - `smonitor` coverage has been expanded to more public wrapper APIs (`Whole`, `Region`, `Layer`, `ShapesManager`).
  - `smonitor` timeline coverage now also includes more `MolSysView` public wrappers (camera/query/edit/export), with regression evidence that these signals land in `Manager.report()["timeline"]`.
  - A structural regression now checks that public `@digest()` entrypoints across `MolSysView`, `new_view`, `Whole`, `Region`, `Layer`, and `shapes/` also carry `@signal()`.
  - `argdigest` hardening now covers previously noisy public wrappers such as:
    - controls visibility,
    - camera snapshot get/set,
    - representation presets,
    - HTML export options,
    - layer retagging,
    - user preset loading,
    - standard-units configuration.
  - A real integration bug was fixed in `set_camera_snapshot()`: `duration_ms` is now interpreted correctly when digested through the PyUnitWizard-aware `duration_ms` digester.
  - Variadic `ShapesManager` forwarding methods no longer pretend to digest `*args/**kwargs`; digestion is delegated to the concrete shape helper methods that actually own the argument contract.
  - New regression tests now fail if those core public paths emit `DigestNotDigestedWarning`.

- `molsysviewer.tools`
  - The package now exists and starts with `molsysviewer.tools.basic.concatenate_structures(...)`.
  - `molsysviewer.tools.basic.merge(...)` now exists as the second pure composition primitive.
  - `molsysviewer.tools.basic` now also exposes functional wrappers over core `MolSysView` operations:
    - `select`, `get`, `info`,
    - `extract`,
    - `set`, `remove`, `add`, `append_structures`,
    - `contains`, `is_composed_of`.
  - `copy(view)` now exists with a scene-aware contract: it duplicates the molecular system and recreates useful scene state.
  - `compare(view_a, view_b)` now exists with a deliberately narrower contract: it compares loaded molecular systems, not full visual scene state.
  - This first tool is intentionally a pure operation:
    - it accepts multiple MolSysMT-compatible systems or `MolSysView` objects,
    - delegates structural concatenation to `molsysmt.concatenate_structures(...)`,
    - and returns a fresh `MolSysView`.
  - `merge(...)` is intentionally view-centric:
    - it accepts `MolSysView` objects,
    - delegates molecular-system merging to `molsysmt.merge(...)`,
    - imports regions/layers/shapes/visibility from all inputs,
    - resolves tag collisions deterministically with suffixes such as `__2`,
    - and uses the first view as the source of global representation, controls, and camera snapshot state.
  - The purpose is to grow advanced functionality without inflating the core `MolSysView` facade.
  - The package is now also part of the project’s “inspection/workbench” identity, not just its “viewer/export” identity.

- Inspection-oriented object API
  - `MolSysView` is now growing along two complementary axes:
    - functional helpers in `molsysviewer.tools.basic`,
    - direct object methods when the behavior is naturally scene-centric or inspection-centric.
  - Camera/inspection helpers are now expected to live on the object side:
    - `focus_selection(...)`,
    - `focus_region(...)`,
    - `Whole.focus(...)`,
    - `Region.focus(...)`,
    - `Region.show_only(...)`.
  - Structural partition helpers also belong on `MolSysView`, not in `tools.basic`, because their real product value is creating region objects in the active scene.
  - The public API for this is now one operation:
    - `make_regions_by(element=...)`
    - instead of multiple `split_by_*` entrypoints.
    - allowed hierarchy levels are intentionally limited for now to `chain`, `molecule`, and `entity`.
  - Region tags produced by viewer-managed region-building helpers should follow a stable policy:
    - derive from a MolSysMT human-readable label when possible,
    - sanitize to a replay-safe tag token,
    - keep semantic prefixes where needed to avoid ambiguity (`molecule_...`, `entity_...`) while allowing concise chain tags,
    - resolve collisions deterministically with suffixes such as `__2`.

- User documentation
  - The user guide now has a dedicated `tools/` section.
  - The first module documented is `tools.basic`.
  - Each currently exposed `tools.basic` function now has its own user-facing page under `user/tools/basic/`.

- Interaction and taxonomy direction
  - Interaction taxonomy now uses:
    - `element`,
    - `shape`,
    - `annotation`,
    - `empty`
    instead of overloading `structure` in the interaction contract.
  - Element hierarchy now explicitly tracks:
    - `atom`, `group`, `component`, `chain`, `molecule`, `entity`.
  - `devguide/annotations.md` now records the viewer taxonomy around:
    - `elements`,
    - `regions`,
    - `shapes`,
    - `annotations`,
    - `layers`.
  - Persistent labels are now a documented `annotations` concern, not a `shapes` concern.
  - Mol* precedents reviewed for this design include:
    - built-in structure labels,
    - loci-based labels,
    - MVS custom and annotation-driven labels,
    - tooltip separation from persistent labels.
  - Mouse-navigation compatibility is now part of the interaction contract:
    - `left drag` rotates,
    - `right drag` pans/translates,
    - right-click context handling must coexist with that drag behavior and suppress the host menu only inside the viewer canvas.
  - The first concrete context-menu bridge now exists:
    - right-click without drag is captured from Mol* click events,
    - the canvas suppresses the host `contextmenu`,
    - Python stores both the last context-target event and the last chosen context action event,
    - a minimal viewer-owned context menu now exists with seed actions for `distance`, `angle`, and `dihedral`.
  - Interactive measurement now has a first real implementation path:
    - menu-seeded `distance` / `angle` / `dihedral` actions start a frontend tool mode,
    - picks are forced down the Mol* element/atom path for measurement purposes,
    - Mol* `StructureMeasurementManager` is the calculation/rendering engine for interactive measurements,
    - Python currently observes tool-state and measurement-created events rather than driving the measurement math itself,
    - a visible in-canvas tool-status overlay now shows the active measurement mode, remaining picks, and the `Esc` cancel hint.

## Active Decisions

- Use real demo viewers when regression value depends on real MolSysMT behavior.
- Prefer contract-level and externally observable assertions over private implementation coupling.
- Treat `DigestNotDigestedWarning` on stable public API as integration debt, not benign noise.
- Keep `MolSysView` small; place advanced composition/analysis operations in `molsysviewer.tools`.
- Keep the interaction contract aligned with MolSysSuite vocabulary:
  - use `elements` / `element levels` instead of overloading `structure` in picking/selection docs.
- Let users work with `MolSysView` in both styles:
  - object-oriented (`view.get(...)`, `view.set(...)`, ...)
  - functional (`tools.basic.get(view, ...)`, `tools.basic.set(view, ...)`, ...)
- Keep scene-centric inspection affordances on the object side even when an equivalent pure helper could exist:
  - focus operations belong to `MolSysView` / `Whole` / `Region`,
  - region-partition helpers belong to `MolSysView` when they create live region objects.
  - prefer one parameterized entrypoint (`make_regions_by(element=...)`) over multiple thin `split_by_*` variants.
- Keep `tools.basic.compare(...)` explicitly molecular for now; if scene comparison is needed later, that should be a separately documented contract.
- Treat internal rebuild/replay as internal state application:
  - it must not re-digest already normalized state,
  - it must preserve replayable `_message_history`,
  - it must preserve region/layer/tag continuity.
- Keep environment workarounds narrowly scoped to concrete failing paths, not as blanket repository policy.
- Treat sibling support libraries (`argdigest`, `depdigest`, `pyunitwizard`, `smonitor`) as active engineering dependencies, not passive externals.
- Keep `molsysviewer` on one local `pyunitwizard` instance/configuration path.
- Prefer `smonitor` `extra_factory` + `SIGNALS` contracts on the main orchestration wrappers when that makes developer/QA debugging materially better.
- Keep persistent labels out of `shapes`; the category should be `annotations`.
- Keep hover tooltips and persistent annotations as separate concerns.
- Keep `annotations` layer-aware from the first implementation.
- Use Mol* rather than MolSysMT as the first engine for interactive distance/angle/dihedral:
  - Mol* already owns the live picked loci and the native measurement representations,
  - MolSysMT remains appropriate for later Python-side analysis or validation, not for the first interactive gesture loop.
- Keep measurement tool feedback local-first in JS:
  - active mode and pick progress should be visible in the canvas without requiring Python callbacks,
  - Python still receives state/result events for inspection, automation, and notebook use.

## Next Step

- Continue building out the interaction stack on top of the now-working context menu + measurement tool-mode path.
- Start `active_selection` as the next shared state object before moving into `GroupStrip` and `annotations`.
- Keep pushing MolSysViewer toward a molecular-system inspection/workbench role for structural biochemistry and drug-design workflows, not only a viewer/export role.

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
- The second `smonitor` pass is now covering real traceability behavior, not just configuration/catalog presence.
- The current `smonitor` integration is now close to exhaustive on the main public orchestration surface.
- The next work should benefit from cleaner `argdigest` behavior on the public API instead of accumulating more migration warnings.
- The standard test entrypoint is again reliable for package-root imports, so export/import regressions can be exercised with plain `pytest`.
- `concatenate_structures(...)` was the correct first step because it opened `tools` with a pure composition primitive that reused stable contracts we already hardened.
- `merge(...)` is the correct second step because it defines the policy for multi-view composition explicitly instead of leaving regions/layers/shapes/tag collisions as ad hoc user work.

## Immediate Plan

1. Build `active_selection` as the next shared interaction state.
2. Keep `active_selection` aligned with the documented interaction taxonomy:
  - `element`,
  - `shape`,
  - `annotation`,
  - `mixed`,
  - `empty`.
3. Make ordinary left-click/shift-click semantics update `active_selection` without breaking the measurement tool mode path.
4. After `active_selection` exists, use it as the base for:
  - `GroupStrip`,
  - future context-menu enrichment,
  - annotation pickability decisions,
  - Python callbacks on interaction objects instead of only raw last-event snapshots.

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
  - move to canvas interaction and picking/hover behavior.
2. Keep the first interaction slice narrow:
  - transport Mol* hover/click events to Python,
  - store the last hover/click payload on the view,
  - keep the payload atom-centric for element picks.
3. Delay richer interaction semantics until the transport contract is stable:
  - active selection wiring,
  - region-aware picks,
  - shape-aware picks,
  - shared highlight/selection,
  - real tool-mode state instead of menu-seeded placeholder actions.
4. Return to support-library integration only if a new product path exposes a real contract gap.
5. Use the annotation taxonomy in `devguide/annotations.md` when label work starts; do not re-open the `shape` vs `annotation` split ad hoc.
6. When interaction implementation starts, treat click-vs-drag discrimination on both mouse buttons as part of the core contract, not a later polish task.

Interaction design reference:

- the interaction contract now lives across:
  - `devguide/interaction_overview.md`
  - `devguide/interaction_targets_and_selection.md`
  - `devguide/interaction_gestures_and_menus.md`
  - `devguide/interaction_modifiers_and_future.md`
- together, these pages define:
  - target taxonomy,
  - gesture semantics,
  - `active_selection`,
  - `context_target`,
  - measurement/tool-mode planning,
  - and tracked modifier ideas.

Strip design reference:

- `devguide/strips.md` now records:
  - why a 1D strip matters,
  - why `GroupStrip` is the right first strip,
  - which alternatives were considered and rejected,
  - and why strip work should follow immediately after `active_selection` is clarified.

## Criteria

- Do not treat generated JS artifacts as implementation source.
- Preserve Python <-> TypeScript payload/message contracts.
- Preserve region/layer/tag identity across rebuilds.
- Keep `_message_history` replay-safe for HTML export and popup/docs-lite flows.
- Prefer evidence-based docs over inherited setup folklore.

## Technical & Scientific Assessment (March 2026)

This assessment captures the current health and strategic position of the library.

### Engineering & Architecture
- **Hybrid Model Success:** The choice of `anywidget` + Mol* + Python (MolSysMT) is validated. It successfully bridges high-performance WebGL rendering with a robust scientific state in Python.
- **Replay & Export Resilience:** The `ViewerMessage` history and replay mechanism are the core strengths for scientific reproducibility and static HTML exports.
- **Support Layer Hardening:** The integration of SMonitor/ArgDigest/DepDigest provides a professional-grade API surface, though it adds a significant maintenance overhead (the "over-engineering" risk).

### Scientific Workbench Direction
- **Inspection-Centricity:** The library is successfully moving from a "renderer" to a "workbench". The group-centric picking and measurement tools are the right steps.
- **Taxonomy Alignment:** Strict adherence to MolSysMT hierarchy (`group`, `chain`, etc.) is a major differentiator for structural biology workflows.

## Open Risks & Critical Points

- **Rebuild Fragility:** The atom-index remap logic during live-edits (`remove`, `add`, `set`) is technically complex and a potential source of silent corruption if state synchronization fails.
- **Atom vs. Group Tension:** The UX switch between atom-level (measurements) and group-level (inspection) picking needs to be seamless to avoid scientist frustration.
- **Build Artifact Dependency:** Reliance on generated `viewer.js` adds friction to frontend development and requires strict discipline to avoid manual edit corruption.
- **E2E Testing Gap:** Interactive breadth (clicks, gestures, tool modes) is still under-tested compared to the robust runtime/protocol coverage.
- **large Systems Performance:** The Python-to-TS payload transfer for systems with millions of atoms is a potential bottleneck that hasn't been fully stress-tested.

## Maintenance, Scalability, and Lifecycle Risks

These deeper technical challenges affect the long-term sustainability of the project:

### 1. Ecosystem Coupling & Maintenance Burden
- MolSysViewer is the "integration hub" for the UIBCDF ecosystem (MolSysMT, ArgDigest, SMonitor, PyUnitWizard).
- **Risk:** Any breaking change in sibling libraries forces an immediate update in MolSysViewer's decorators, digesters, and signals. The cost of "ecosystem synchronization" competes with feature development.

### 2. Protocol Complexity & "Bus Factor"
- The custom `ViewerMessage` protocol and its TypeScript handlers are powerful but have a steep learning curve.
- **Risk:** Deep knowledge of the Python/JS bridge is currently concentrated. Failure to democratize this architecture through better internal documentation or simpler patterns increases project fragility.

### 3. Latency vs. Consistency Policy
- Hybrid architectures face a trade-off between instant local (JS) feedback and scientifically consistent (Python) validation.
- **Risk:** Without a clear policy on which operations must be "local-first" vs. "round-trip-required," the user experience may feel laggy or inconsistent, especially in large-scale systems or high-latency environments.

### 4. Message History Bloat & Snapshotting
- Operations like `merge()` and consecutive live-edits grow the `_message_history`.
- **Risk:** Static HTML exports carrying a massive replay log will suffer from slow initialization and memory bloat. A "message compaction" or "snapshotting" strategy is needed for 1.0 but is currently missing from the implementation.
- `add()` still depends on a scoped `NUMBA_CACHE_DIR` workaround in this environment.
- Popup/popout behavior is still lighter in coverage than live-edit, but no longer the clearest blocker for resuming implementation.
- `argdigest` still does not cover every public shape/detail argument; the remaining gaps should be prioritized by real product usage and warnings, not by raw parameter count.

## Useful Follow-ups

- Extend `molsysviewer.tools.basic` beyond `merge(...)` only when the next composition/analysis policy is explicit enough to document and test.
- Add canvas interaction work:
  - `Done`: minimal hover/click event transport from Mol* to Python with atom-centric payloads.
  - `Next`: implement the richer contract now documented in the new interaction pages under `devguide/`.
- Keep `GroupStrip` in scope as the first strip-style companion view once `active_selection` is concrete enough.
- Continue visual and behavioral refinement of pockets and pharmacophore overlays.
- Add popup/popout sync regressions around camera/state replay if the harness can support them.
- Add export regressions that mix camera snapshots, visibility cleaning, and replay ordering.
- Expand JS tests from guards into more success-path and replay-sensitive behavior where seams are controllable.
- Add targeted `smonitor` refinements only when a new public orchestration path is introduced.

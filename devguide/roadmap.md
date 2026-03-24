# Development Roadmap (Status-Aligned)

Last update: 2026-03-24

This roadmap is status-aligned with the current repository state.
It is organized by execution priority and uses three labels:

- `Done`: implemented and present in codebase.
- `In progress`: partially implemented or implemented with limited coverage/docs.
- `Planned`: not implemented yet or not stabilized.

## Route From `0.13.0` To `1.0.0`

After `0.13.0`, the project is no longer missing a direction.
The near-term problem is now consolidation.

What already exists in meaningful form:

- reproducible scene/state and replay/export foundations
- `Navigate` and `Workbench` as real runtime panels
- add-ons as a real host/view platform with docs, standards, template, and
  lifecycle
- `standalone 0` as a teachable browser-hosted first cut
- a now much stronger `image` / `figure` export story:
  - reusable `FigureSpec`
  - camera-derived figure recipes
  - named figure variants
  - standard publication bundles
  - a visible figure baseline in `Workbench -> Scene`
- a workspace-aware panel runtime with:
  - launcher
  - local panel stacks
  - generic add-on workspace host
- the first coherent reference add-on smoke/demo path for downstream teams

So the path to `1.0.0` should now be:

1. close the shared workbench model
2. validate one richer add-on path on top of that workbench
3. mature figure export enough to feel intentional, not incidental
4. tighten verification and user/developer guidance around the now-real product
5. only then make the final standalone push

The intended release rhythm from here should stay pre-1.0 and incremental:

- `0.14.x`:
  - richer add-on proof through the now-solid workbench/runtime
- `0.15.x`:
  - cross-surface polish and verification tightening
- `0.16.x`:
  - documentation/tutorial tightening and release hardening
- `0.17.x+`:
  - final standalone push
- `1.0.0`:
  - once that standalone host sits on a stable workbench/export/add-on core

This sequence matters:

- standalone is no longer "someday"
- but it also should not become the place where unfinished workbench decisions
  are hidden
- the core viewer must already feel coherent before the final host step

## Current 1.0 Plan

The current preferred execution plan toward `1.0.0` is:

### Phase A. Shared Workbench Consolidation

Status:

- effectively closed, with targeted follow-up only

Goal:

- make `panel mode` feel like one coherent workbench system rather than two
  coordinated drawers plus add-on fragments

Main work:

- keep the shared header and the body-level workbench overview aligned
- strengthen the relation:
  - workspace launcher
  - panel stack
  - workspace overview / runtime deck
  - panel host
- keep `Navigate` and `Workbench` visually and behaviorally aligned
- avoid adding new permanent canvas chrome

Success criteria:

- switching workspace/panel feels native and unsurprising
- `Core` remains the calm default
- add-on workspaces can exist without flattening the product into one giant
  panel list
- the body-level workbench overview already feels like the seed of the future
  workspace mosaic rather than a temporary summary list

### Phase B. Add-On Runtime Proof

Status:

- in strong progress

Goal:

- prove that external MolSysSuite teams can start real add-on work without
  forcing another redesign of the host

Main work:

- make at least one reference add-on path more realistic through the shared
  workbench runtime
- keep `standards/`, cookbook, template, runtime contract, and tests aligned
- prefer explicit, teachable contributions over a broad but vague API

Success criteria:

- a downstream team can build against the published add-on contract
- a larger add-on workspace feels plausible in the real runtime
- the host no longer looks "core-only with addon metadata attached"

Immediate next focus from here:

- keep using the now-stronger shared workbench as the main place to mature
  add-on/runtime behavior
- prefer vertical slices that make the current workspace mosaic direction more
  believable
- keep the notebook/runtime bridge strong enough that these slices are easy to
  drive and diagnose from Python
- specifically, the current best path is:
  - make add-on workspaces look and feel substantive inside `Workbench`
  - not by adding generic chrome,
  - but by making workspace cards, host previews, panel stacks, and capability
    summaries cooperate better
  - a good sign of progress is that non-current add-on workspaces already look
    informative before the user opens them, instead of reading like placeholder
    labels beside `Core`
  - another good sign is that the current workspace overview already exposes a
    meaningful local panel lane, so the add-on runtime feels navigable before
    the user even drops fully into the panel host

### Phase C. Figure Export Maturation

Status:

- in strong progress

Goal:

- move from "serious image export exists" to "figure export feels deliberate"

Main work:

- push `view.export.figure(...)` beyond a thin wrapper
- strengthen camera/composition reuse
- strengthen publication-oriented presets/looks
- keep figure export tied to reproducible viewer state

Success criteria:

- exported figures reuse explicit camera/state choices
- the figure story feels like part of the workbench, not a bolt-on helper
- the current Mol* pipeline is being exploited well before considering deeper
  rendering ambitions

### Phase D. Product Tightening

Goal:

- tighten the real product surface before the final host push

Main work:

- smoke and regression breadth where runtime contracts are already real
- workbench-oriented tutorials and docs parity
- public docs aligned with:
  - add-ons
  - exports
  - panel/workspace behavior

Success criteria:

- the current public product can be taught without relying on chat history
- the docs tell the truth about the current runtime
- the remaining gap to `1.0.0` is mostly host-level, not conceptual confusion

Current interpretation after `0.15.0`:

- support-library hardening (`argdigest`, `depdigest`, `pyunitwizard`,
  `smonitor`) is now strong enough that it should stop dominating the roadmap
- the best next tightening is no longer generic support work, but workbench/API
  slices that immediately improve the teachable product

Immediate pre-`0.14.0` interpretation:

- recent tightening already improved three real teaching surfaces:
  - figure export
  - add-on/workspace runtime
  - panel/workspace behavior
- before `0.14.0`, prefer confirming that these slices are enough rather than
  reopening broad design work
- the next useful question is no longer "what should panel mode be?" but:
  - does the current runtime already teach well enough to count as the next
    stable pre-`1.0` checkpoint?

### Phase E. Final Standalone Push

Goal:

- deliver the final major pre-`1.0.0` host step on top of the already-mature
  core

Main work:

- evolve `standalone 0` into the real standalone host
- keep the same workbench/runtime model
- avoid forking UX or scene/state behavior
- decide the first acceptable host shape:
  - browser-hosted
  - popup-style
  - or lightweight app shell

Success criteria:

- standalone feels like MolSysViewer, not a separate experiment
- add-ons/workspaces remain compatible there
- the host is good enough that `1.0.0` can reasonably ship on top of it

Current preferred host direction:

- keep browser-hosted `standalone 0` as the teaching bridge
- prefer a Python app shell with embedded webview for the final host
- currently the strongest pragmatic candidate is:
  - `PySide6 + Qt WebEngine`
- begin that push with a deliberately thin Qt prototype:
  - `QMainWindow`
  - `QWebEngineView`
  - same embedded runtime
  - no standalone-only viewer semantics
- keep the current Qt spike recipe explicit:
  - Qt host development may continue on top of a working `pip` PySide6 stack
  - final release packaging remains a separate decision

Practical rule from the current state:

- continue standalone when it validates the shared runtime or unblocks future
  host decisions
- do not let standalone packaging dominate the roadmap before the shared
  workbench/add-on story feels fully intentional

See also:

- `devguide/standalone_direction.md`
- `devguide/standalone_host_plan.md`
- `devguide/standalone_qt_prototype_plan.md`

## Guiding Principle

MolSysViewer is guided by a simple product idea:

- scientific work has an interactive and exploratory phase,
- but scientific results must remain reproducible.

So the roadmap should not optimize for interaction breadth alone.
It should optimize for interaction that can become explicit, replayable,
rebuild-safe, exportable viewer state.

This affects prioritization:

- `selection`, `regions`, `labels`, `measurements`, `layers`, and scene state
- `selections` should now be treated as their own persistent category, not as a thin alias for `regions`
  matter more than ephemeral interaction for its own sake,
- exploration should tend toward artifacts that can be reproduced later from
  Python or exported viewer state,
- new interaction surfaces should be judged by how well they feed that
  reproducible model.

That principle is also recorded in `devguide/guiding_principles.md`, which
should grow over time as additional project-level principles become clear.

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
  - Support-library integration hardening (`argdigest`, `depdigest`, `pyunitwizard`, `smonitor`) is active because it affects runtime behavior directly.
  - `argdigest` now covers the main noisy public wrappers, but broader shape/detail coverage is still partial.
  - `smonitor` now has regression-backed wrapper coverage beyond config/catalog smoke tests, and the package-wide public signal map is largely enforced structurally.

### Next actions

- Expand protocol-focused tests for non-trivial operations (`set_global_representation`, layer retag, clear/reset interactions).
- Keep support-library integration aligned with sibling-library contracts, especially around bootstrap, quantity handling, and public API digestion.
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
  - Exhaustive Python-side digestion for major overlay/detail arguments (PocketSurfaces, AnisotropyEllipsoids).

- `In progress`
  - Deep coverage of TS shape handler branches and error paths.
  - Docs parity for all implemented overlays.

### Next actions

- Extend JS tests beyond region-hide to shape routing and tag-index lifecycle.
- Keep filling `argdigest` gaps in shape methods only where the public call surface is actually used or warning-prone.
- Close docs gaps where implemented APIs are still documented as placeholders.

### Criteria

- Keep Python option normalization deterministic and validated.
- Keep shape ops replay-safe for exports and rebuild flow.

## 4) Tools and Advanced Viewer-Safe Operations

### Status

- `In progress`
  - `molsysviewer.tools` now exists as the intended home for advanced operations that should not inflate `MolSysView`.
  - `molsysviewer.tools.basic.concatenate_structures(...)` exists as the first pure composition primitive.
  - `molsysviewer.tools.basic.merge(...)` now exists as the first view-centric composition primitive.
  - `molsysviewer.tools.basic` now also provides functional wrappers so users can operate on `MolSysView` in a MolSysMT-like style.
  - `molsysviewer.tools.basic.copy(...)` and `compare(...)` now extend that workbench surface.
  - The object-side inspection API is now the preferred home for scene-centric helpers such as focus and region partitioning.
  - User docs now include a dedicated `tools/` section with module/function pages for `tools.basic`.

### Next actions

- Add the next `tools.basic` operation only when its behavior and ownership are clear beyond `merge(...)`.
- Decide module boundaries intentionally (`basic`, `structure`, `topology`, `hbonds`, `build`) instead of copying MolSysMT mechanically.
- Keep `tools` operations explicit about whether they are pure (return a new view) or live (mutate an existing one).
- Keep user docs organized under `user/tools/<module>/<function>.md` or notebook equivalents so the tools surface can grow without scattering tutorials.
- Prioritize `tools` functions that make MolSysViewer more useful as an inspection/workbench tool for molecular systems.
- Keep focus helpers (`focus_selection`, `focus_region`, `Whole.focus`, `Region.focus`) on the object side.
- Keep region-building helpers on `MolSysView` when they create live scene objects rather than pure return values.
- Prefer one parameterized region-building entrypoint (`make_regions_by(element=...)`) over multiple near-duplicate `split_by_*` methods.
- Keep `make_regions_by(...)` intentionally limited to useful inspection levels (`chain`, `molecule`, `entity`) unless a stronger product need appears.

### Criteria

- `tools` should grow product capability without turning `MolSysView` into a grab bag.
- Operations that compose multiple systems/views should use real demo regressions and preserve viewer-safe semantics.

## 5) Visibility, Regions/Layers, and Global Semantics

### Status

- `Done`
  - Atom-level visibility masking from Python.
  - Global vs region visibility split in TS (`show_global` / `hide_global`, region hidden memory).
  - Region/layer acks from frontend to keep Python registries synchronized.

- `In progress`
  - Complex interaction tests are broader than before, but popup/export-connected visibility flows still need more coverage.
  - Support diagnostics are now strong enough that new visibility work should use `smonitor` context/contracts instead of ad hoc debugging.

### Next actions

- Extend coverage from core visibility invariants into popup/export-connected flows.
- Document edge semantics with executable examples in devguide checkpoints as needed.

### Criteria

- `region.hide()` must remain sticky across global show/hide cycles.
- Whole/global operations must not accidentally mutate region-specific hidden state.

## 6) Canvas Interaction and Picking

### Status

- `In progress`
  - The first JS -> Python interaction transport now exists for Mol* `hover` and `click`.
  - Right-click context transport now also exists as a first viewer-owned slice:
    - host context menu suppression inside the canvas,
    - separate context-target event,
    - minimal viewer context menu with seed actions.
  - The current contract is intentionally minimal and atom-centric:
    - `interaction_hover`
    - `interaction_click`
    - `interaction_context_menu`
    - `interaction_context_action`
    - `kind: "structure"` with `atom_indices`
    - `kind: "empty"` for canvas-empty interactions
  - Python now stores the last hover/click payload on `MolSysView`.
  - Python now also stores the last context-menu target payload and the last context-menu action payload.

### Next actions

- Use the interaction pages in `devguide/` as the implementation contract for the next slices.
- Add Python-side callback registration only after the transport contract settles.
- Decide whether region-aware and shape-aware picks belong in the same event family or in richer payload variants.
- Add pointer semantics and shared highlight/selection only after event ownership is clear.
- Turn menu-seeded `distance` / `angle` / `dihedral` actions into real tool-mode state machines.
- Keep interactive measurement in Mol* first:
  - it already owns picked loci and measurement representations,
  - Python/MolSysMT can consume emitted results later without entering the immediate click loop.
- Add visible tool-mode feedback and cancellation semantics before layering richer selection state on top.
- Build `active_selection` after the measurement path is locally coherent, then reuse it for strips, menus, and annotation interaction.
- Broaden `active_selection` from the first atom-centric element slice toward the documented element/shape/annotation/mixed contract.
  - `annotation` now has a first narrow slice via `GroupStrip` label badges.
  - `element + annotation` mixed selection is now supported as the first mixed path.
  - `shape` now has a first narrow slice via Mol* `shape-loci`.
- Keep the current element slice group-centric and only add hierarchy levels when the runtime can support them cleanly.
- Grow `GroupStrip` from the first chain-grouped selection/focus slice toward the full strip contract documented in `devguide/strips.md`.
- The next strip step should be a `GroupPanel` evolution, not more investment in a permanently visible lower band.
- Keep `chain` as the first organizer, but plan explicit visual cues for `component` and `molecule`.
- Do not assume middle-click is available for the panel toggle; Mol* already uses the middle/wheel path for camera behavior.
- Keep strip interactions converged with canvas interactions:
  - hover and context menu should use the same event families instead of becoming a separate UX island.
- Make the active selection materially useful through the context menu before opening more target families:
  - selection-focused actions such as `Focus Selection` and `Clear Selection` are now the first concrete slice.
  - the next priority is not broader interaction for its own sake, but turning interaction into reproducible artifacts.

### Criteria

- Keep the first interaction contract additive and easy to replay/debug.
- Do not overfit the payload before real picking workflows exist.

## 6.5) Annotations and Persistent Labels

### Status

- `In progress`
  - `annotations` now exist as a real category instead of a pure design note.
  - The first implemented slice is narrow:
    - `view.annotations.add_label(text=..., group_index=..., tag=...)`
    - group-anchored persistent labels
    - layer-aware
    - replay/rebuild/export-safe
    - real frontend clearing through `clear_decorations(..., labels=True)`

### Next actions

- Keep the first slice narrow and stable.
- Broaden annotation interaction in controlled slices:
  - first `annotation` as `context_target` through strip overlays,
  - `annotation` now also has a first narrow `active_selection` slice through strip overlays,
  - `annotation` context now also has a first real action through the menu: `Focus Target`,
  - later hover/pick behavior,
  - canvas annotation pickability only after that path is stable.
- Grow the current strip overlay slice:
  - compact label marks now exist on `GroupStrip`,
  - strip label overlays can already seed annotation context,
  - richer annotation overlay semantics still need design and tests.
- Revisit atom labels, free-point labels, and shape-attached labels only after the first slice is solid.

## 6.6) Exploration to Reproducible Artifacts

### Status

- `In progress`
- `active_selection` now has a first explicit Python bridge into reproducible state:
  - `new_region_from_active_selection(...)`
  - `view.annotations.add_label_from_active_selection(...)`
  - `view.measurements.persist_last_measurement(...)`
  - `active_selection.save(tag=...)`
- `view.selections` now exists as the first persistent named-selection surface.
- Persistent selections can now be restored into `active_selection` via API, and the next UX step is to use the context menu as the first browser-side activator for those saved selections.
- After saved-selection activation is in place, the next context-menu broadening should prioritize relevant `regions`, then richer `annotations`, and only later carefully-scoped `shapes` actions.
- The context menu now also exposes `Save Selection`, backed by the same Python-side reproducible API.
  - The current contract is intentionally narrow and deterministic.
  - Persisted measurement ops now also exist in the runtime:
    - `add_distance_measurement`
    - `add_angle_measurement`
    - `add_dihedral_measurement`
    - replayed through Mol* from stored `picks_atom_indices`

### Next actions

- Keep the new Python bridge validated as `pyunitwizard` continues stabilizing; the current targeted regressions are green again.
- Add the next explicit bridge only after deciding its stable replay/rebuild/export contract:
  - named selections,
  - richer selection -> annotation flows.
- Broaden persisted measurements only after the first replayable `distance` / `angle` / `dihedral` slice is validated end to end.
- The explicit menu action path for persisted measurements now exists and executes.
- The explicit menu action path for `Add Label from Selection` now also exists
  and executes through a minimal inline composer.
- The next improvement is refining that inline composer or replacing it with a
  better small integrated text-entry UX without weakening the reproducibility
  contract.
- Keep hardening `annotations` as a Python API surface, not only as a UI flow:
  - explicit query/inspection methods,
  - explicit show/hide/delete/rename/text-edit/reanchor/clear methods by tag,
  - stable records suitable for replay-oriented debugging,
  - compact summaries that are more useful than raw records in notebook work.

### Criteria

- The bridge from interaction to persisted state must remain explicit and reproducible.
- Do not hide scientifically meaningful state creation behind frontend-only transient behavior.

### Criteria

- Keep persistent labels separate from hover tooltips.
- Keep annotation taxonomy separate from shape taxonomy.
- Keep annotation/layer semantics explicit and stable.

## 7) Export, Embedding, and Popup

### Status

- `Done`
  - `view.export.html(...)` in `standalone` and `lite` modes.
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

## 8) Testing and Quality Gates

### Status

- `Done`
  - Python test suite covers loaders, shapes, core viewer helpers, and key integration paths.
  - JS unit/e2e scaffolding exists with runnable scripts.
  - `pytest` and `python -m pytest` now resolve the same in-repo package during test collection.

- `In progress`
  - JS coverage is still narrower than the runtime surface, but handler-level breadth is improving.
  - E2E matrix is minimal.
  - Public API digestion coverage now has explicit regression tests for core wrapper methods and selected shape helpers.

### Next actions

- Extend JS unit coverage from handler guards into deeper success-path and replay/remap semantics.
- Add at least one additional E2E path beyond region hide.

### Criteria

- Every protocol-significant behavior should be covered in either Python or JS tests.
- Keep E2E deterministic and environment-aware (browser/WebGL constraints).

## 10) Strategic Directions (2026)

To reach a successful **1.0 release**, these three pillars must be prioritized over further support-layer abstractions.

### 1. Close the Interaction & E2E Gap
- The value of MolSysViewer lies in how it feels to interact with it.
- **Priority:** Implement more complex E2E tests simulating real scientific workflows (e.g., "identify a binding site, select it, label it, and measure distances").

### 2. GroupStrip: The 1D Navigation Pivot
- The 1D strip view (`GroupStrip`) is a primary differentiator. It's the key tool for navigating long proteins or complex systems where the 3D scene is cluttered.
- **Priority:** Ensure the strip is synchronized with the 3D canvas from day one, using the shared `active_selection` model.

### 3. Documentation for the "Scientific Workbench"
- The documentation must shift from API reference to case-study-driven tutorials.
- **Priority:** Create "Workbench Tutorials" (e.g., "How to analyze pocket contacts") that showcase the library as an integrated tool for structural biochemistry and drug design.

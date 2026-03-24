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

- `0.14.0` should now be read as the checkpoint where:
  - Phase D stopped being only intention and gained first real tightening
    slices
  - the product became materially easier to teach without chat history
  - figure export, add-on workspaces, and panel mode now have both user-facing
    guidance and matching smoke/regression coverage

- `0.13.0` should now be read as the checkpoint where:
  - the shared workbench/runtime became coherent enough to stop dominating the roadmap
  - the reference add-on path became teachable end to end
  - and figure export stopped being a thin helper and became a small but real subsystem

- Continue feature implementation toward 1.0 on top of the now-hardened runtime/contracts layer.
- Treat `0.12.0` as the end of the "prove the platform exists" stage.
- Treat `0.13.0` as the end of the first serious consolidation wave across:
  - workbench/workspace runtime
  - add-on onboarding
  - figure export
- The current stage is now:
  - finish squeezing the value out of the now-stronger add-on/runtime path,
  - treat figure export as a deliberate subsystem rather than a side helper,
  - and leave standalone as the final major pre-`1.0.0` host push.
- The standalone question should now be treated as more concrete than before:
  - browser-hosted `standalone 0` is already good enough as a teaching bridge
  - the final pre-`1.0.0` standalone host should now be planned as a dedicated
    application shell, not just "open HTML in browser"
  - the current preferred direction is:
    - Python app shell
    - embedded webview
    - likely `PySide6 + Qt WebEngine`
  - keep that host decision explicit in:
    - `devguide/standalone_host_plan.md`
- The first implementation step for Phase E should now also be treated as
  decided:
  - begin with a thin Qt prototype
  - use `PySide6`
  - embed the existing runtime in `QWebEngineView`
  - preserve `Core` and `panel mode` semantics unchanged
  - keep the technical mini-plan in:
    - `devguide/standalone_qt_prototype_plan.md`
- Phase E is now no longer only planned:
  - the first thin Qt host prototype has started
  - it currently adds:
    - a dedicated `QMainWindow`
    - embedded `QWebEngineView`
    - a minimal menu bar
    - reuse of the current standalone HTML/runtime path
  - it should still be treated as a prototype, not as the final standalone host
  - the first real Qt spike has now also validated that:
    - the host can run successfully with a coherent `pip` PySide6 stack
    - the viewer should use the `lite` runtime path in Qt rather than the AMD
      widget-manager export path
    - final standalone packaging is now clearly an environment-recipe problem,
      not just a host-implementation problem
  - the Qt host now also owns first real app-level actions:
    - `View -> Navigate`
    - `View -> Workbench`
    - `View -> Close Panel Mode`
    - `File -> Open File`
    - `File -> Load Demo` submenu
    - `File -> Load PDB ID`
    - `File -> Load Source`
    - `File -> Recent` with persisted recent sources
    - `File -> Restore Last Source`
    - `Export -> Export HTML`
    - `Export -> Export Figure`
    - `Help -> About`
    - `Help -> Show Current Source`
    - `Help -> Reload Last Source`
- Phase A should now be read as effectively closed unless a downstream need
  exposes a real structural gap.
- Phase B is now advanced enough that it should not keep growing sideways
  without concrete ecosystem pressure.
- Phase C is now much stronger and should be considered substantial rather than
  exploratory.
- Phase D should now prefer product-facing tightening work that teaches the
  current runtime honestly:
  - workbench-oriented figure/export tutorials
  - workbench-oriented add-on/workspace tutorials
  - panel/workspace behavior docs that explain the shared workbench model
  - public docs that connect runtime surfaces to the now-real APIs
  - small but truthful user/developer guidance slices instead of broad new
    architecture
- The practical question is now shifting toward the next checkpoint gate:
  - before `0.14.0`, prefer checking whether the current Phase D slices are
    already enough to teach the product honestly
  - do not reopen broad architectural fronts unless the review exposes a real
    gap
  - likely candidates for a last tightening pass before `0.14.0` are:
    - one more docs/API parity review
    - or one more small regression bundle around recently taught surfaces
- That short pre-`0.14.0` review is now effectively closed:
  - docs/API/runtime parity for the recent tightening surfaces looks good
  - the small regression bundle for:
    - figure export
    - add-on workspaces
    - panel mode
    is green
  - so `0.14.0` is justified as the first checkpoint where product tightening
    itself becomes part of the release story
- After the latest workspace/panel runtime slices, Phase A should now be read as
  **near closure** rather than open-ended:
  - the shared workbench model is already coherent enough to stop iterating on
    chrome by default
  - the next major implementation focus should be Phase B
  - only keep touching Phase A when a downstream add-on/runtime need exposes a
    real structural gap
- Avoid opening many unrelated new surfaces at once.
- Prefer larger vertical slices that make one part of the product feel more
  real, rather than many small disconnected improvements.
- Keep the main product leitmotiv explicit:
  - scientific exploration is important,
  - but the outcome of that exploration should become reproducible viewer state.
- Keep `devguide/guiding_principles.md` as the stable place for project
  ideas-alma that should survive beyond the current checkpoint.
- Keep the interaction stack moving in order:
  - canvas gestures/context menu,
  - measurement tool modes,
  - `active_selection`,
  - `GroupStrip`,
  - `annotations`.
- Keep `devguide/interaction_verified_state.md` as the operational truth for:
  - what interaction behaviors are really implemented,
  - what has already been verified in smoke,
  - and what still needs re-checking.
- Keep `devguide/` aligned with the real repository state.
- Keep the emerging MolSysSuite add-on direction explicit:
  - `MolSysViewer` 1.0 should stay as a strong core workbench
  - domain-specific ecosystem growth should prefer optional add-ons
  - even before real plugins exist, 1.0 should leave extension entry points and
    validate them with at least a plugin test or plugin template
- Treat `selections` as a first-class category distinct from `regions`; do not collapse them just because both derive from atom subsets.
- Keep the smoke runbook in `devguide/smoke_test.md` aligned with the real product surface before broadening interaction much further.
- `Save Selection` is now live-smoke verified both when the menu opens on empty canvas and when it opens on a structural context target; the earlier accidental fallthrough into measurement picking is fixed.
- Saved persistent selections can now be restored back into `active_selection` via API, and the context menu now has a saved-selection section ready to expose that bridge live.
- Next context-menu expansion should favor relevant persistent workbench objects in this order: `regions`, then richer `annotations`, then carefully-scoped `shapes`; avoid turning the menu into a general browser of every object.
- The first `regions` slice is now present in the context menu:
  - only relevant overlapping regions are shown
  - the first action is deliberately narrow:
    - `Focus Region`
  - defer richer region actions until this small slice proves useful and stays clean
- For `annotations` and `shapes`, keep the same discipline:
  - small target-specific menus
  - immediate actions only
  - likely ceiling:
    - annotation:
      - `Focus`
      - `Delete`
      - maybe later `Show/Hide`
    - shape:
      - `Focus`
      - `Delete`
      - maybe later `Show/Hide`
  - do not let these menus grow into rich editors or type-specific browsers
- The strip work has now crossed into a real `GroupPanel` + multiple-`GroupStrip` runtime.
- `GroupPanel` has now taken a first practical step toward the future `Navigate` panel:
  - it uses a reusable panel shell
  - it exposes an explicit `Navigate` title
  - but it still behaves as the current drawer-style strip container, not yet the final shared `panel mode`
  - it now also exposes first lightweight live summary sections:
    - `Active`
    - `Saved`
    - `Regions`
  - these are still list-style summaries, not yet a richer interactive inventory
  - first primary actions now exist there too:
    - click `Saved` row -> restore `active_selection`
    - click `Regions` row -> focus region
- `WorkbenchPanel` now also exists as a real shell-based runtime scaffold:
  - same panel shell family
  - explicit `Workbench` identity
  - sections for:
    - `Annotations`
    - `Measurements`
    - `Shapes`
    - `Scene`
  - now wired into the controller as a minimal right-side drawer
  - currently populated from a lightweight controller-side summary model:
    - annotation text + tag
    - measurement kind + pick count
    - shape title/tag
    - scene preset/representation summary
  - first row action now exists where the runtime has safe structural anchors:
    - click row -> focus target
    - currently reliable for:
      - annotations
      - measurements
      - shapes only when `atom_indices` are present in the layer metadata
  - row state has also started to align with the shared panel/canvas language:
    - `active` row state now exists in the runtime
    - `context` row state now also exists in the runtime for:
      - annotations with tag
      - shapes with tag
    - this is still a local drawer-era implementation, not yet the final shared `panel mode` state model
  - row affordances have now grown one more careful step:
    - tagged annotations, measurements, and shapes now expose a minimal visibility toggle
      through the existing `show_layer` / `hide_layer` path
    - workbench sections can now collapse/expand locally to reduce vertical noise
  - add-ons no longer surface only as summaries there:
    - `Workbench` can now materialize add-on-contributed workbench sections as
      real dynamic sections in the panel
    - each such section is still intentionally modest:
      - one informational row
      - no arbitrary frontend execution
      - enough to validate that add-ons can project structure into the shared workbench
  - still not yet integrated into a shared navigator or final `panel mode`
- The next strip step is no longer “multiple strips”, but a better `GroupPanel` shape: vertical per-chain strip-columns, independent scroll, and then show/hide; the permanent lower strip is no longer the intended final product shape.
- `chain` remains the primary strip organizer, but future strip grammar should also mark `component` and `molecule`.
- Do not adopt middle-click as the default `GroupPanel` toggle for now; Mol* already uses the middle/wheel path for camera behavior.
- Prioritize regression coverage for new product-facing behavior, especially where it composes runtime state, layers, and rebuild/replay.
- A direct code-vs-checkpoint review now confirms that the current reproducible interaction slice is materially present in code and covered by the targeted local regression block.
- The reproducible interaction workflow now also has an explicit integrated regression covering:
  - saved selection
  - region
  - label
  - persisted measurement
  together in export/replay and after `remove()` remap.
- The clearest next implementation gap is no longer the selection/annotation/measurement bridge itself, but the missing first-class `styles` layer above the current `representation` / `preset` / `user_preset` base.
- That `styles` gap now has a first concrete Python-side slice:
  - `Style`
  - `view.styles`
  - explicit style registry
  - explicit `_molsysviewer.py` loading support
  - canonical built-in scene-style battery
- The next `styles` gap is no longer basic API existence.
  It is the future scene-look layer:
  - clarify `default-look` and `illustrative` as visual looks, not structural recipes
  - preserve the distinction between structural targeting and visual styling
  - avoid opening canvas authoring or a second runtime protocol too early
- The canvas/popup UX direction should now be treated as explicitly decided at the principle level:
  - resting canvas as clean as possible
  - only two main interaction doors:
    - right-click context menu
    - panel mode
  - only three permanent meta-controls:
    - panel
    - fullscreen
    - popup
  - trajectory scrubber remains the one justified always-visible data control when a trajectory exists
  - panel mode should likely converge first on:
    - `Navigate`
    - `Workbench`
  - tabs are the preferred first panel navigator
  - a discreet carousel remains a possible later/configurable navigator variant
- The detailed record of canvas/popup UX decisions, still-open UX questions,
  and alternatives intentionally kept alive should now live in:
  - `devguide/canvas_minimal_ux.md`
  - do not let that discussion disappear into chat history only
- The first serious image-export slice now exists:
  - Python `view.export.image(...)`
  - PNG output
  - optional explicit pixel size
  - optional `scale` multiplier for higher-resolution export
  - optional transparent background
  - backed by Mol*'s real viewport screenshot helper rather than naive canvas capture
  - still no richer figure recipe/spec yet
- The figure-export story has also advanced one more careful step:
  - `view.export.figure(...)` now exists as the first explicit figure-oriented
    wrapper above raw image export
  - a first minimal reusable `FigureSpec` now exists on the Python side
  - `FigureSpec` can now also:
    - capture the current camera from a live `view`
    - derive small immutable variants through explicit overrides
    - expand a named batch of figure recipes from one base recipe
  - `view.export.figure_variants(...)` now exists as the first explicit batch
    figure-export path
  - `FigureSpec.build_publication_variants(...)` and
    `view.export.figure_publication_set(...)` now provide the first standard
    small publication bundle:
    - `light`
    - `dark`
    - `transparent`
    - optional `current`
  - `Workbench -> Scene` now also exposes the built-in figure baseline:
    - default figure preset
    - default figure scale
    - recommended figure variants
  - that recipe layer is still intentionally modest:
    - export-facing only
    - no detached project format yet
    - no independent frontend protocol yet
- The add-on/panel scaling direction is now clearer too:
  - do not assume future growth means one flat global pile of panels
  - `Core` should be understood as the native future workspace
  - larger add-ons may later contribute their own workspaces
  - each workspace would then carry its own local panel stack
  - smaller add-ons should still be allowed to remain lighter and never become
    a workspace
  - that workspace layer is now also present in the typed add-on contract and
    already propagates through the current addon runtime summary path
  - the shared panel shell now also has a first minimal runtime workspace
    launcher:
    - only shown when more than one workspace is effectively available
    - still far from the final launcher/mosaic
    - enough to make workspace state visible and steer add-on workbench slices
    - the shared header stays calmer because only the current workspace remains
      visible until the launcher is opened
    - it now also prefers effective workspace entries only:
      - workspaces with no visible panel/section runtime do not clutter the
        launcher
    - launcher entries can already expose lightweight summaries of what they
      contain
    - the current workspace trigger can also carry a compact subtitle, so the
      active domain is legible without opening the launcher
    - the launcher can explicitly mark the current workspace, making it read
      more like a domain selector than a flat dropdown
  - the shared panel header is now also becoming workspace-aware:
    - non-core workspaces remain workbench-centric for now
    - the runtime offers a direct return to `Core`
    - it does not pretend every add-on workspace already has a full native
      `Navigate` stack
    - the next honest runtime step is to make that true in behavior too:
      - non-core workspaces should hide `Navigate`
      - returning to `Core` should restore the last core panel choice
  - `Workbench` now also materializes a first generic panel-stack bridge for
    add-on workspaces:
    - selector of workspace panels
    - generic active-panel host surface
    - workspace-specific add-on sections can now be absorbed into that host so
      the workspace panel does not feel split from its own immediate runtime
    - the host can now also surface the active add-on's immediate capabilities:
      - context actions
      - export helpers
    - still no arbitrary add-on frontend runtime, but no longer just a summary
  - that panel selector is now also part of the shared header chrome:
    - core stack feels more like a real `panel mode`
    - non-core panel stacks stop feeling like a local workbench-only detail
    - the header now reads more clearly as:
      - workspace launcher first
      - active workspace panel stack second
- `0.12.0` now marks a coherent pre-1.0 checkpoint:
  - `standalone 0` exists and is already teachable as a browser-hosted first cut
  - the add-on starter pack is real:
    - public docs
    - cookbook
    - standards
    - importable reference template
  - the panel/runtime model has moved beyond two ad hoc drawers:
    - workspace launcher
    - local panel stacks
    - generic add-on workspace host

The next route should now be read more sharply:

- first:
  - keep consolidating the shared workbench/runtime
- second:
  - use that runtime to validate a richer add-on path
- third:
  - mature `image` / `figure` export further
- fourth:
  - tighten docs/tutorials/verification around the now-real product
- The bundled add-on starter pack now also has a single smoke/demo path teams
  can share:
  - `molsysviewer.addon_templates.build_reference_demo_view("topomt")`
  - use that as the shortest reproducible reference route when onboarding
    `MolSysMT`, `TopoMT`, `PharmacophoreMT`, or similar teams
- fifth and last major step before `1.0.0`:
  - standalone

## Near-Term Route To 1.0

The current preferred route to 1.0 is incremental and workbench-first:

1. keep the reproducible scene/state model hard and boring:
   - export/replay
   - rebuild/remap
   - popup sync
   - persistent artifacts
2. keep the canvas minimal:
   - right click
   - panel mode
   - three meta-controls only
3. converge the current drawer-era runtime toward the two-panel workbench model:
   - `Navigate`
   - `Workbench`
4. strengthen row/list semantics before inventing richer chrome:
   - primary action
   - `active`
   - `context`
   - `hidden` / visibility treatment where appropriate
   - local section collapse before a richer navigator
5. finish the first healthy `styles` story before opening richer look systems:
   - stable scene styles now
   - scene looks later
   - focus styles later still
6. add a first serious image-export story on top of the same reproducible scene model
7. harden that image-export story toward:
   - camera/composition reuse
   - publication looks
   - figure recipes/specs
8. only after that, consider the shared panel navigator and richer publication-oriented layers
9. treat standalone as the final major pre-`1.0.0` step:
   - same workbench
   - same scene/state model
   - CLI-first host
   - no forked UX
10. before calling `1.0.0`, ensure the core is add-on-compatible even if no real
    MolSysSuite plugin ships yet:
    - explicit extension points
    - and at least a plugin test or plugin template

That add-on-compatibility story now has a first real slice:

- `molsysviewer.addons` as host-level registry
- `view.addons` as local projection with per-view enable/disable overrides
- explicit typed add-on specs for:
  - panels
  - context actions
  - workbench sections
  - shape providers
  - style helpers
  - export helpers
  - tool modes
- validated with a fake add-on test rather than a real ecosystem package

The next add-on step is now more specific:

- keep `addons` as the only public vocabulary
- add a simple discovery path based on a maintained list of known add-on
  modules
- keep explicit manual coupling for local or unpublished add-on development
- document the packaging contract early so downstream add-ons do not have to
  guess their module shape
- do not stop at `devguide`:
  - user docs should explain installation/discovery/use of add-ons
  - developer docs should explain the host/local registry contract
  - cookbook should stay actionable for external teams

The add-on starter-pack story should now be treated as real deliverable work:

- bundled reference template:
  - [`molsysviewer/addon_templates/minimal_topomt.py`](/home/diego/repos@uibcdf/molsysviewer/molsysviewer/addon_templates/minimal_topomt.py)
- public docs:
  - developer add-on contract
  - cookbook recipe
  - showcase placeholder with starter links
- stable normative references under:
  - [`standards/addons/README.md`](/home/diego/repos@uibcdf/molsysviewer/standards/addons/README.md)
  - [`standards/addons/IMPLEMENTATION_CONTRACT.md`](/home/diego/repos@uibcdf/molsysviewer/standards/addons/IMPLEMENTATION_CONTRACT.md)
- those `standards/` files must now stay aligned with:
  - the runtime contract
  - the reference template
  - developer docs
  - cookbook guidance

For standalone, the next communication milestone is also clearer:

- before the final standalone implementation push, preserve a credible
  `standalone 0`
- that is the version to show early to the MolSysMT/TopoMT/
  PharmacophoreMT teams
- its job is to prove the host model and add-on/workspace fit, not to pretend
  the final product UX is already finished
- the first public slice should stay deliberately small:
  - `build_standalone0_html(...)`
  - `launch_standalone0(...)`
  - `molsysviewer ...`
  - `python -m molsysviewer.standalone ...`

  - cookbook should carry a "build a minimal add-on" recipe
  - showcase should eventually include at least one add-on-shaped scientific
    story

That story now also has a concrete reference template module:

- `molsysviewer.addon_templates.minimal_topomt`

It is not a real ecosystem integration, but it gives add-on authors and tests a
stable importable target beyond ad hoc fake specs.

The add-on platform now also has a first intentionally small lifecycle slice:

- `AddonLifecycleSpec`
- `on_enable(view)`
- `on_disable(view)`
- `on_context_action(view, action_id, payload)`

This is still Python-side and deliberately narrow.
It should help validate realistic add-on activation without opening a large
hook surface too early.

Add-ons now also have a first visible runtime surface:

- Python sends a small add-on runtime summary to the frontend
- `Workbench` exposes that through an `Add-ons` section
- the current visible content is still intentionally summary-only:
  - enabled add-on names
  - contributed panel titles
  - contributed workbench-section titles

This is the first runtime proof that add-ons are no longer only a registry/API
story; they now reach the visible viewer surface without opening full dynamic UI
execution yet.

There is now also a first visible add-on context-menu slice:

- enabled add-ons may contribute compatible context actions
- the menu renders them in an `Add-ons` section
- clicking one emits a structured Python-side `interaction_context_action`
  carrying:
  - add-on name
  - add-on action id
  - add-on action title

This is still a bridge and visibility slice, not yet a rich domain action
runtime.

Enabled add-ons can now also handle that bridge through the new Python-side
lifecycle hook above, so add-on context actions are no longer only observable;
they can already trigger explicit view-local runtime behavior.

Working rule:

- do not jump early to the final panel switcher, offline rendering, or a desktop-like host shell
- first make the existing workbench slices coherent, reproducible, and pleasant

## 0.9.0 Checkpoint

`0.9.0` marks the point where MolSysViewer has a coherent pre-1.0 workbench direction rather than a loose collection of slices.

What this checkpoint consolidates:

- a recognizable two-panel workbench trajectory:
  - `Navigate`
  - `Workbench`
- a minimal canvas UX direction that is already explicit and stable at the principle level
- first-class scene styles through `Style` and `view.styles`
- first-class export namespace:
  - `view.export.html(...)`
  - `view.export.image(...)`
- a reproducible scene/workbench baseline strong enough to support the next steps toward `1.0.0`

Follow-up convergence after `0.11.0`:

- `Navigate` and `Workbench` now share a minimal drawer expansion contract
- only one of the two drawer panels expands at a time
- `Escape` closes an expanded drawer before falling back to clearing active
  selection
- the first shared runtime API now exists:
  - `view.set_panel_mode(panel="navigate"|"workbench"|None, expanded=True|False)`

What `0.9.0` does not mean yet:

- no final shared panel navigator yet
- no full figure recipe/spec yet
- no standalone host yet
- no real MolSysSuite plugins yet
- not the final publication-quality rendering story

## 0.10.0 Checkpoint

`0.10.0` marks the point where MolSysViewer's add-on story stops being only a
future architectural intention and becomes a real public-facing platform slice.

What this checkpoint consolidates:

- host-level add-on registry:
  - `molsysviewer.addons`
- per-view add-on projection:
  - `view.addons`
- explicit typed contribution specs for:
  - panels
  - context actions
  - workbench sections
  - shape providers
  - style helpers
  - export helpers
  - tool modes
- first simple discovery path:
  - maintained list of known add-on modules
  - `molsysviewer.addons.discover()`
- explicit manual coupling path for local or unpublished development:
  - `molsysviewer.addons.register(...)`
  - `molsysviewer.addons.register_module(...)`
- first public docs surface for add-ons in:
  - user introduction
  - cookbook
  - developer docs
  - showcase placeholder
- cleaner public export wording around:
  - `view.export.html(...)`

What `0.10.0` does not mean yet:

- no real MolSysSuite add-on shipped yet
- no entry-point metadata discovery yet
- no persisted add-on preferences yet
- no richer add-on runtime lifecycle yet
- no standalone host yet

## 0.11.0 Checkpoint

`0.11.0` marks the point where the add-on platform becomes visibly present in
the running viewer, not only in API contracts and developer documentation.

What this checkpoint consolidates:

- importable reference add-on template:
  - `molsysviewer.addon_templates.minimal_topomt`
- first intentionally small add-on lifecycle:
  - `AddonLifecycleSpec`
  - `on_enable(view)`
  - `on_disable(view)`
- first visible workbench runtime surface for add-ons:
  - `Workbench` now includes an `Add-ons` section
  - enabled add-on names are shown there
  - contributed panel titles, workbench-section titles, context-action titles,
    and export-helper titles are summarized there
- first visible context-menu bridge for add-ons:
  - compatible add-on context actions can appear in an `Add-ons` section
  - clicking one emits a structured `interaction_context_action`
  - the payload now carries:
    - add-on name
    - add-on action id
    - add-on action title
- first explicit project-level add-on defaults:
  - `_molsysviewer.py` may now define `ADDONS_ENABLED` and `ADDONS_DISABLED`
  - `molsysviewer.addons.load_project_config(...)` applies those defaults at
    host level
  - new views inherit them while `view.addons` keeps local override semantics

What `0.11.0` does not mean yet:

- no real MolSysSuite scientific add-on shipped yet
- no persisted enable/disable preferences yet
- no entry-point metadata discovery yet
- no full add-on frontend execution contract yet
- no standalone host yet

Post-`0.11.0` export work:

- `view.export.image(...)` now also accepts `camera_snapshot=...`
- the explicit snapshot should be treated as a reproducible figure/export aid,
  not merely as another UI convenience parameter
- `view.export.image(...)` now also accepts a first small `preset=...` surface:
  - `current`
  - `publication-light`
  - `publication-dark`
- in the current implementation that preset only controls reversible background
  treatment during the capture itself
- `view.export.figure(...)` now exists as the first explicit figure-oriented
  wrapper over raw image export:
  - stronger default scale
  - `background=...`
  - figure-oriented preset defaults

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

- **Technical & Scientific Assessment (March 2026):** Completed. The library's health, strategic workbench direction, and critical risks are now formally documented.
- **Support-library integration hardening:** 
    - `depdigest` now runs before importing heavier public submodules.
    - `pyunitwizard` usage is unified.
    - `smonitor` coverage expanded and structurally enforced.
    - `argdigest` hardening covers core public wrappers.
    - **Git Hygiene:** JS test build outputs should stay out of git. `dist-index.js`, `dist-region-hide.js`, `harness.bundle.js`, and `region-hide.e2e.js` belong in ignore rules unless there is a documented reason to version them.

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
  - Developer docs now also document the first explicit style/configuration path:
    - `Style`
    - `view.styles`
    - explicit project config loading via `_molsysviewer.py`

- Styles and configuration
  - The first public `Style` slice now exists in Python:
    - `Style`
    - `view.styles.apply(...)`
    - `view.styles.current()`
    - `view.styles.info()`
  - A second Python-side slice now also exists:
    - registry methods such as `add()`, `get()`, `tags()`, `records()`
    - application by tag
    - explicit project-config loading via `view.styles.load_project_config(...)`
  - The first canonical built-in battery is now exposed directly through the API:
    - `default`
    - `polymer-cartoon`
    - `polymer-and-ligand`
    - `atomic-detail`
    - `coarse-surface`
    - `empty`
  - Current implementation rule:
    - these styles are still backed by the existing global representation pathway,
      not by a new frontend protocol
  - Current configuration rule:
    - `_molsysviewer.py` support is explicit-load only for now
    - there is no ambient discovery yet
    - explicit user calls still win over project defaults
  - Current architectural rule:
    - MolSysMT remains the canonical source of structural targeting semantics
    - MolSysViewer styles define visual treatment
    - future targeted styles should compose with MolSysMT-compatible selection
      semantics or stable MolSysViewer selection-derived objects
  - Current future-facing rule:
    - `default-look` and `illustrative` should be treated as future scene-look
      targets
    - they should not be collapsed prematurely into the current structural
      recipe battery

- Interaction and taxonomy direction
  - Interaction taxonomy now uses:
    - `element`,
    - `shape`,
    - `annotation`,
    - `empty`
    instead of overloading `structure` in the interaction contract.
  - Element hierarchy now explicitly tracks:
    - `atom`, `group`, `component`, `chain`, `molecule`, `entity`.
  - The first lightweight public wrappers now exist for:
    - `view.hover_target`
    - `view.context_target`
  - Current wrapper rule:
    - query-oriented only
    - do not overdesign them yet into a richer object model than current runtime payloads justify
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
  - Manual smoke in JupyterLab now confirms:
    - the host `contextmenu` conflict is resolved in both the main notebook canvas and the popup canvas,
    - `right drag` now pans without leaking the host menu in both surfaces,
    - `right click` now opens the viewer-owned menu in both surfaces,
  - the remaining canvas-side picking hardening is specifically about bond/edge fragments resolving consistently to the default `group` target.
  - live smoke has now also confirmed:
    - canvas `left click`, additive `Shift + click`, `Esc`, and order-independent selection visuals,
    - popup canvas context behavior,
    - notebook-canvas `double click -> focus`,
    - `GroupStrip` click / additive click / hover / right-click / double-click.
    - interactive `distance` measurement UX is clear in live smoke,
    - `get_last_measurement_created_event()` now yields the expected replay-safe
      payload shape with `action`, `picked_count`, and `picks_atom_indices`.
  - The first concrete context-menu bridge now exists:
    - right-click without drag is captured from Mol* click events,
    - the canvas suppresses the host `contextmenu`,
    - Python stores both the last context-target event and the last chosen context action event,
    - a viewer-owned context menu now exists with:
      - `Focus Target` for structure, annotation, and first-slice shape targets,
      - target-scoped measurement seed actions for `distance`, `angle`, and `dihedral`,
      - a secondary active-selection section with:
        - `Focus Selection`
        - `Create Region from Selection`
        - `Add Label from Selection` when the selection resolves to exactly one group
        - `Persist Last Measurement` when a recent interactive measurement exists
        - `Clear Selection`
  - Interactive measurement now has a first real implementation path:
    - menu-seeded `distance` / `angle` / `dihedral` actions start a frontend tool mode,
    - picks are forced down the Mol* element/atom path for measurement purposes,
    - Mol* `StructureMeasurementManager` is the calculation/rendering engine for interactive measurements,
    - Python currently observes tool-state and measurement-created events rather than driving the measurement math itself,
    - a visible in-canvas tool-status overlay now shows the active measurement mode, remaining picks, and the `Esc` cancel hint.
  - `active_selection` now has a first concrete runtime slice:
    - ordinary left click replaces the active selection,
    - `Shift + left click` adds uniquely,
    - empty left click clears,
    - active measurement tool modes do not overwrite it,
    - the current implementation is now `group`-centric for element picks,
    - it already emits derived `atom_indices` plus `group_indices`, `chain_indices`, and `entity_indices`,
    - it now also has a narrow `annotation` slice seeded from `GroupStrip` label badges,
    - `element + annotation` now mix in one `active_selection` payload,
    - it now also has a first narrow `shape` slice from Mol* `shape-loci`,
    - broader shape metadata and richer shape/mixed policies still remain ahead.
  - `GroupStrip` now has a first concrete implementation slice:
    - it renders groups from the currently loaded structure,
    - groups are organized by chain,
    - it mirrors `active_selection`,
    - click / `Shift + click` from the strip updates the same active selection state used by the canvas,
    - double click on a strip item focuses that group in the viewer,
    - strip hover now mirrors into the viewer highlight path and emits the same hover event family,
    - right click on a strip item now opens the same viewer context menu contract used by the canvas,
    - compact annotation overlays for persistent group labels now exist,
    - right click on a strip label overlay now seeds `annotation` as a real `context_target`,
    - it is still intentionally narrow and does not yet implement range selection, region overlays, tool-pick overlays, or canvas-side annotation pickability.
  - `annotations` now have a first concrete implementation slice:
    - `view.annotations.add_label(text=..., group_index=..., tag=...)` exists in Python,
    - `view.annotations` is now also growing into a real management API instead of a creation-only entrypoint:
      - `tags()`
      - `count()`
      - `contains(tag)`
      - `get(tag)`
      - `records()`
      - `info(tag=None)`
      - `show(tag)` / `hide(tag)`
      - `delete(tag)` / `set_tag(tag, new_tag)` / `set_text(tag, text)` / `set_group_index(tag, group_index)`
      - `clear(tag=None)`
    - labels are implemented as `annotations`, not `shapes`,
    - the first slice is intentionally narrow: one persistent label anchored to one `group`,
    - labels participate in `layers` with `kind="annotation"`,
    - labels survive export/replay/rebuild through dedicated annotation-history replay,
    - live `hide()/show()` on annotation layers is now verified in notebook smoke and is implemented through explicit artifact removal/rebuild, not only generic subtree visibility,
    - `clear_decorations(..., labels=True)` now clears real frontend labels instead of a placeholder path,
    - strip label badges can now seed both `annotation` context and `annotation` active selection,
    - annotation context now has a first concrete action: `Focus Target`.
  - The first explicit exploration -> reproducible-state bridge now exists in Python:
    - `view.new_region_from_active_selection(...)`
    - `view.annotations.add_label_from_active_selection(...)`
    - `view.measurements.persist_last_measurement(...)`
  - `active_selection` is no longer only a cached frontend event:
    - `view.active_selection` now exists as a public Python wrapper with:
      - `info()`
      - `is_empty()`
      - `clear()`
      - `focus(...)`
      - `new_region(...)`
      - `add_label(...)`
      - `save(...)`
    - persistent selections can now be restored into `active_selection` via `view.selections.activate(tag)` and `view.selections[tag].activate()`
  - `selections` now exist as a first-class persistent category:
    - `view.selections.add_from_active_selection(tag=...)`
    - `view.selections.records()`, `count()`, `info()`
    - per-selection wrappers with `focus(...)`, `new_region(...)`, and `add_label(...)`
    - selections are stored by `atom_indices` and treat derived hierarchy indices as summaries
    - they do not create scene representation automatically
    - they replay/export as explicit non-visual viewer messages
  - The context menu now also exposes `Save Selection` from `active_selection`.
    - It uses an inline tag composer instead of `prompt()`.
    - The UI -> Python bridge executes `active_selection.save(tag=...)`.
    - this turns the selection into a real object of work instead of a raw event payload
  - The current bridge is intentionally narrow:
    - region creation uses stored `active_selection.atom_indices`,
    - label creation currently requires an active selection resolving to exactly one `group`,
      and the current UI capture path is now a minimal inline composer inside the viewer menu.
    - measurement persistence currently replays the last interactive `distance` / `angle` / `dihedral` by storing its `picks_atom_indices`.
  - Measurements now also have an explicit replay/runtime path of their own:
    - Python can send `add_distance_measurement`, `add_angle_measurement`, and `add_dihedral_measurement`,
    - JS reconstructs them through Mol* `StructureMeasurementManager`,
    - they are tracked as `measurement` layers and replayed across rebuild/export.
    - `view.measurements` now also has a minimum inspection surface:
      - `count()`
      - `records()`
      - `info()`
  - `_build_export_messages()` now has an integral regression over the current reproducible workbench surface:
    - `create_region`
    - `set_region_representation`
    - `add_label`
    - `update_label`
    - `add_distance_measurement`
    - `add_angle_measurement`
    - `add_dihedral_measurement`
    - `set_camera_snapshot`
  - measurement APIs now also have nominal argdigest coverage for their explicit
    atom-pick arguments (`atom_indices_a` ... `atom_indices_d`), removing the
    warning path that the integral export regression exposed
  - Region creation from active selection is now confirmed as a reproducibility
    operation first:
    - it creates a real region object and export messages,
    - but does not imply an immediate visual change unless a representation/show
      path is also applied.
  - Validation note:
    - JS regression remains green,
    - Python regressions for `tests/test_annotations.py` are green again after fixing layer-tag/delete replay bookkeeping in `molsysviewer`,
    - the latest hardening also added replay-safe label reanchoring with `view.annotations.set_group_index(...)`,
    - the `new_region_from_active_selection(...)` path required one contract fix so region representations are recorded explicitly as `set_region_representation` during replay/export,
    - the UI-to-Python bridge now executes `Create Region from Selection`, `Add Label from Selection`, and `Persist Last Measurement` directly from `interaction_context_action`,
    - broader Python validation outside the annotation slice may still see sibling-checkout instability in `../molsysmt`, so package-wide reruns should be treated separately from this local block.
  - A dedicated smoke runbook now exists in `devguide/smoke_test.md` so we can evaluate:
    - interaction correctness,
    - UX feel,
    - and exploration -> reproducible-state flows together instead of as disconnected features.
  - Current smoke automation result:
    - `pytest tests/test_annotations.py tests/test_reproducible_interaction.py tests/test_measurements.py tests/test_interaction_events.py -q` is green,
    - `PW_CHROMIUM_BIN=/usr/bin/google-chrome npm --prefix molsysviewer/js run test:e2e` is now verified as passing on this workstation.
  - Immediate smoke follow-up:
    - after the latest `Bond.Loci -> element loci` normalization, recheck `right click` on visible bonds/links in the main notebook canvas,
    - expected behavior: those clicks should now resolve to the same `group`-centric context target as atom clicks,
    - if not, inspect the exact Mol* loci returned for bond fragments in notebook embedding before broadening interaction further.

## Active Decisions

- Treat reproducibility as a primary product goal, not just a packaging/export concern.
- Prefer features that convert exploratory interaction into replay-safe, rebuild-safe, exportable state.
- Avoid growing interaction-only affordances without a credible path to:
  - Python representation,
  - replay,
  - rebuild,
  - export,
  - or explicit scientific state capture.
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
- Keep the first annotation slice narrow:
  - explicit text,
  - one `group` anchor,
  - no atom labels or free-point labels yet.
- Keep the first exploration -> reproducible-state bridge narrow and explicit:
  - active selection may become a region,
  - active selection may become a label when it resolves to exactly one `group`,
  - the last interactive measurement may become a replayable measurement artifact,
  - broader UI flows should come only after the Python-side contract is stable.
- Keep persisted measurements as explicit viewer artifacts:
  - persist picks, not opaque frontend state,
  - rebuild by replaying the same measurement op through Mol*,
  - keep them layer/tag aware like other non-element scene artifacts.
- Use Mol* rather than MolSysMT as the first engine for interactive distance/angle/dihedral:
  - Mol* already owns the live picked loci and the native measurement representations,
  - MolSysMT remains appropriate for later Python-side analysis or validation, not for the first interactive gesture loop.
- Keep measurement tool feedback local-first in JS:
  - active mode and pick progress should be visible in the canvas without requiring Python callbacks,
  - Python still receives state/result events for inspection, automation, and notebook use.

## Next Step

- Continue building out the interaction stack, but subordinate it to reproducibility.
- The next high-value work should increasingly convert exploration into explicit state:
  - selection -> region,
  - selection -> label,
  - measurement -> persistent/replayable artifact,
  - and then richer mixed-selection semantics only where they help that goal.
- The UI now exposes that direction explicitly in the active-selection context menu,
  and the Python-side bridge for the current narrow slice has been revalidated.
- The measurement branch has now advanced one step further than selection/label:
  - persisted measurement ops exist in the runtime,
  - the menu now exposes and executes a first explicit UI affordance for committing the last interactive measurement,
  - the current label-text capture path has already moved from `prompt()` to a small inline composer,
  - the remaining work is refining that composer UX and broadening reproducible interaction flows.
- Enrich `active_selection` beyond the current element/annotation/shape slices toward richer mixed behavior and metadata quality only when that improves reproducible scientific workflows.
- Grow `GroupStrip` from the current selection/focus/hover/context slice toward:
  - range selection,
  - region overlays,
  - tool-pick overlays.
- Formalize the path from current representation mechanics into the future `styles` model:
  - today the repository has real `representation`, `preset`, and `user_preset` support,
  - but it does not yet have a public first-class `Style` object or `Scene Style` / `Focus Style` runtime contract,
  - so the next design/implementation step should define that first narrow reproducible slice explicitly rather than treating the vision page as if it were already implemented.
- Decide the next annotation-interaction step carefully:
  - keep current label overlays on the strip,
  - keep the new strip-seeded `annotation` context + selection slices stable,
  - then choose between canvas annotation pickability or richer mixed-selection semantics before broadening the model further.
- Use the current active-selection section in the context menu to make selection useful before adding more target families:
  - `Focus Selection`,
  - `Clear Selection`.
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
- The core product risk is not lack of interactivity by itself.
  It is letting interaction outrun reproducibility.
- The next steps should therefore prefer features that preserve the project identity:
  exploration that can be captured, replayed, rebuilt, and shared.
- The support-library layer is now in active hardening, so regressions there should be caught early instead of worked around ad hoc.
- The second `smonitor` pass is now covering real traceability behavior, not just configuration/catalog presence.
- The current `smonitor` integration is now close to exhaustive on the main public orchestration surface.
- The next work should benefit from cleaner `argdigest` behavior on the public API instead of accumulating more migration warnings.
- The standard test entrypoint is again reliable for package-root imports, so export/import regressions can be exercised with plain `pytest`.
- `concatenate_structures(...)` was the correct first step because it opened `tools` with a pure composition primitive that reused stable contracts we already hardened.
- `merge(...)` is the correct second step because it defines the policy for multi-view composition explicitly instead of leaving regions/layers/shapes/tag collisions as ad hoc user work.

## Immediate Plan

1. Enrich `active_selection` from the current group-centric element-only slice toward the documented taxonomy:
  - `element`,
  - `shape`,
  - `annotation`,
  - `mixed`,
  - `empty`.
2. Keep lifting the current element-only selection semantics toward richer hierarchy coverage and metadata quality without inventing fake `component`/`molecule` semantics.
3. Broaden `GroupStrip` from the current narrow slice toward the documented interaction contract:
  - range selection,
  - overlays for regions/annotations/tool picks.
4. After that base is in place, use `active_selection` for:
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
  - `Done`: `active_selection` integration with `GroupStrip` and `GroupPanel`.
  - `Done`: annotation (label) synchronization between Mol* and `GroupPanel` (badge overlays).
  - `Next`: implement the richer contract now documented in the new interaction pages under `devguide/`.
- Keep `GroupStrip` in scope as the first strip-style companion view once `active_selection` is concrete enough.
- Continue visual and behavioral refinement of pockets and pharmacophore overlays.
- Add popup/popout sync regressions around camera/state replay if the harness can support them.
- Add export regressions that mix camera snapshots, visibility cleaning, and replay ordering.
- Expand JS tests from guards into more success-path and replay-sensitive behavior where seams are controllable:
  - `Done`: added `group-panel-interaction.e2e.ts` verifying load -> select -> label flow with Google Chrome.
- Add targeted `smonitor` refinements only when a new public orchestration path is introduced.

### Progress March 2026 (Mid-Month Update)

- **Interaction & E2E:**
  - Added `group-panel-interaction.e2e.ts` verifying load -> select -> label flow.
  - Added `measurements-interaction.e2e.ts` verifying Distance and Angle measurement tools from the context menu.
  - Added `hierarchy-interaction.e2e.ts` verifying hierarchical Molecule/Component selection in the GroupStrip.
  - Implemented Range Selection using `Shift + Alt + click` both in the 3D canvas and GroupStrip.
  - Added cross-view anchor synchronization for range selection.
  - Enforced usage of `google-chrome` for E2E tests to ensure WebGL availability.
- **Structural Rebuild Robustness:**
  - Fixed a critical gap where specialized history lists (shapes, annotations, measurements) were not updated with remapped indices during a structural rebuild.
  - Corrected `_record_shape_message` to prevent duplicate replaying of measurements and labels.
  - Verified that hierarchical metadata (Molecule/Component) survives structural modifications and is correctly re-emitted to the frontend.
  - Validated persistence of annotations, measurements, and saved selections across structural edits via stress test (`test_rebuild_persistence.py`).
- **GroupStrip Hierarchy:**
  - Implemented nested visualization (Molecule -> Component -> Group) in the `GroupPanel` using colored left-border lines.
  - Enabled hierarchical selection: clicking on the molecule or component border markers selects all child atoms.
  - Enriched the Python-to-JS payload with `molecule_index` and `component_index` data from MolSysMT.
  - Persisted hierarchical metadata in Mol* via custom `atom_site` columns.
- **Annotation Sync:**
  - Fixed gap where `add_label` messages were not notifying the `GroupPanel`.
  - Labels now show up as "L" badges in the `GroupStrip`.
- **ArgDigest Coverage (Shapes):**
  - Implemented missing digestors for complex shape arguments: `iso_levels`, `iso_colors`, `iso_alphas`, `eigenvalues`, `eigenvectors`, `tensors`.
  - Refactorized `PocketSurfaces` and `AnisotropyEllipsoids` to remove manual normalization, simplifying the Python API and improving robustness.
- **Testability & Infrastructure:**
  - Added data attributes to UI components for stable E2E selection.
  - Updated E2E harness to maintain a message history log (`__messages`).


## Current Panel Direction

The current adopted container direction is:

- `GroupPanel` docked laterally on the left
- collapsed by default
- the chevron tab is physically attached to the panel and remains visible as the only exposed part when collapsed
- the panel slides as one piece, so the tab behaves like a true sidebar handle
- the notebook embedding now clips viewer overflow explicitly so the sliding panel does not provoke output-cell scrollbars or canvas blink/reflow loops

This is preferred over a permanent lower band because it preserves canvas area while keeping the strip tool quickly reachable.

## Current Panel-Mode Convergence

- `Navigate` and `Workbench` already expose a shared minimal navigator in the drawer header chrome.
- The runtime can now jump directly:
  - `Navigate -> Workbench`
  - `Workbench -> Navigate`
- This is still an intermediate step before the final shared `panel mode` container and its definitive navigator (`tabs` first, `carousel` later if it still proves useful).

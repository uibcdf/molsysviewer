# Master plan: Regions, Whole, colour, ordering, state and performance

**Status:** proposed 2026-07-10. This document owns **the order, the gates, the decisions and
the audits**. `studio_region_subpanel_implementation_plan.md` and
`studio_whole_subpanel_implementation_plan.md` remain as per-subpanel task detail; where they
disagree with this file on ordering, this file wins.

**Who does what.** A collaborator implements. The maintainer's agent coordinates and **audits
after every phase**. No phase is closed by its implementer.

**Freedom.** MolSysViewer has **no external users**. `sandbox/Curso/` (26 notebooks), `docs/`
and `bloques.md` are provisional; they are expected to **break during Phases 0–12** and are
regenerated in Phase 13. Breaking changes are allowed, expected, and must be **explicit** —
declared in the migration table of `region_contracts.md`, never softened with a shim or a
deprecation period.

---

## 0. Reference documents

| Doc | Role |
|---|---|
| `region_contracts.md` | **Normative.** Representation states (A), colour + ordering (B/O), recipes (R), serialisation (C). Wins over everything. |
| `message_toll_performance.md` | The two performance defects and the harness. Phase 0. |
| `studio_region_subpanel.md` + `_ui_design.md` | Regions blueprint + UI spec. |
| `studio_whole_subpanel.md` + `_ui_design.md` | Whole blueprint + UI spec. |
| `studio_region_subpanel_implementation_plan.md` | Regions task detail. |
| `studio_whole_subpanel_implementation_plan.md` | Whole task detail. |

---

## 1. Decisions taken (do not re-litigate)

| # | Decision | Rationale |
|---|---|---|
| **1** | **A region is a recipe**, not a set of atoms. `atom_indices` is the cached result. Modes `static` / `dynamic`. | Makes dynamic regions expressible, makes rebuild exact instead of best-effort, shrinks state files, and prevents a `v3` format. `region_contracts.md` Contract R. |
| **A** | Recipes are evaluated **in Python, lazily, one consolidated message per frame**. Recipes carry `frame_dependent`; topological recipes never re-evaluate during playback. | Evaluating in TS would fork the MolSysMT grammar. Per-region messages would be ruinous. Contract R.4. |
| **B1** | Region undo/redo enters as **one scene-level command history**, absorbing the frontend selection history — not a second stack. | Two independent undo stacks are a bug factory. Phase 8. |
| **B2** | Colour precedence and render order unify into **one `order` per region**. | Two counters meaning "who is on top" would desynchronise. Contract O (`region_contracts.md` §B.2). |
| **B3** | Regions become members of `view.layers`: **model + serialisation now**, implementation in Phase 9. | If state v2 cannot express membership, we pay a v3. |
| **B4** | Dynamic-region **evaluation** is implemented in its own phase (10), after the model and the format exist. | Bounded once Decision A fixes where evaluation happens. |
| **2** | **OPEN — gate at Phase 1.** Exclusive atom ownership. | Reshapes Contracts A and B. Decision rule and the exact clause replacements are written in `region_contracts.md`. |

---

## 2. Standing rules (every phase, no exceptions)

1. **Never hand-edit** `molsysviewer/viewer.js` / `.map`. Edit TS under `molsysviewer/js/src/`
   and run `npm run build:runtime`. `npm run build` is only for release/version sync.
2. **API first.** A capability is a public Python method *before* it is a `core.py` handler, and
   a handler *before* it is a GUI control.
3. **The GUI never reaches past the public API.** No open-coded loops in TS over what a public
   method does.
4. **A test whose name claims an outcome must assert that outcome.** Visual claims assert against
   the simulated Mol\* plugin (`js/tests/unit/state-handler.test.ts` already drives one and
   captures `addRepresentation`). Never assert only the emitted message dict.
5. **No `as any` + `?.()` on internal APIs in tests.** That combination produced a green e2e that
   tested nothing (`message_toll_performance.md` §7).
6. **Breaking changes are declared** in `region_contracts.md` §Migration. No shims.
7. **Work directly on `main`; no phase branches** (decided 2026-07-10). One commit per phase.
   **Never commit `sandbox/Test.ipynb`.**
   Consequence, and it is not optional: without a branch there is no quarantine, so **the audit
   happens on the working tree, before the commit**, not on the commit afterwards. A phase that
   fails audit must never reach `main`'s history.
8. Green means all four: Python suite + `npm run test:js` + `npm run build:runtime` + (from
   Phase 0) `npm run test:perf`. **Run them. Do not report a suite whose result you did not
   observe.**

---

## 3. Phase order

```
P0  Performance: the handleMessage toll + the double component build   ← hard prerequisite of everything
P1  GATE: re-measure ownership, close Decision 2
P2  Contract A: representation states
P3  Whole's public API + two rebuild bugs
P4  Contract B/O: layered colour, decorator theme, one `order`
P5  Contract R: regions as recipes
P6  Contract C: state v2
P7  API completeness, symmetry, protocol rename, creation idiom
P8  Contract H: one scene-level command history (undo/redo)
P9  Layer membership for regions
P10 Dynamic-region evaluation
P11 Regions subpanel (GUI)
P12 Whole subpanel (GUI) + System colour-scheme migration
P13 Corpus regeneration (course, docs, bloques.md)
P14 Real browser E2E validation
```

**Why P0 first.** Every "is it fast enough" judgement is currently polluted by a
3-second-per-message toll, and Decision A's one-message-per-frame design is only viable once it
is gone. P0 is a prerequisite of Decision 1, not merely an optimisation.

**Why P1 is a gate.** Decision 2 replaces named clauses of Contracts A and B. Deciding it after
implementing them means implementing them twice.

**Dependencies.** P4 needs P3 (the base colour layer and the structural theme belong to `whole`,
which does not own them today). P6 needs P2, P4, P5 (it serialises what they define). P8, P9, P10
need P6 (history, membership and dynamic modes are all serialised state).

### The audit gate (before every commit)

Work happens on `main` (rule 7), so the gate sits **before** the commit. The implementer opens
the phase with the work **staged or in the working tree**: the diff, the new tests, the output of
the four green commands, and **a written statement of what was not done**. The auditor then:

1. Re-runs the four commands independently.
2. Verifies each acceptance criterion **against the code**, never against the report.
3. Runs the phase's mechanical criteria (they are chosen to be greppable).
4. Reads every new test and asks: *if the feature were deleted, would this test fail?*
5. Appends an audit note to the phase row in §5.

A phase is **not done** until the audit note says so.

---

## Phase 0 — Performance: the toll and the double build

**Size:** M · **Depends on:** — · Spec: `message_toll_performance.md`.

Two independent defects, both measured, neither previously known.

**Defect 1 — the toll.** At n = 95,000 atoms, on a 20-core workstation, with the rasteriser
paused, a message with an **unknown `op`** costs 3,183 ms; `hide_region` costs 3,159 ms; Mol\*'s
own empty state-tree update costs 0.4 ms. `refreshPanelWorkspaceChrome()` runs **twice** per
message (tail of both `refreshNavigatePanel()` and `refreshAddonsPanel()`), each calling
`groupPanel.setRuntimeVisible(null)` → `render()` → `systemPanel.rebuild()` → 19,000 DOM nodes.
DOM construction is single-threaded: **this is a best case, not a worst case.**

**Defect 2 — the double build.** `new_region` emits `create_region` carrying the representation
(JS builds the component and adds the representation), then immediately calls
`set_representation`, whose handler **deletes that component and rebuilds it**
(`state-handlers.ts:452`). Every region with a representation is built twice.

- [ ] **Layer 1:** `setRuntimeVisible` (`js/src/ui/group-panel.ts:574`) returns early when the
      value is unchanged.
- [ ] **Layer 2:** `refreshPanelWorkspaceChrome()` runs at most once per message.
- [ ] **Layer 3:** `handleMessage` stops refreshing both panels after every message. An explicit
      `op → refreshes` mapping, defaulting to **none**. An unknown `op` warns and does nothing.
- [ ] **Layer 4:** `SystemPanel.rebuild()` stops tearing down the strip — incremental
      reconciliation or virtualisation. State the approach and the resulting node ceiling.
- [ ] **Double build:** `new_region` sends the visual spec **once**. Preferred shape: create the
      component bare, then apply a visual only if requested — which is also what Contract A needs,
      since a region may legitimately have none.
- [ ] **Land the harness:** `js/tests/perf/message-toll.perf.ts` + `npm run test:perf`, with the
      budget table of `message_toll_performance.md` §5.1. Flags that matter:
      `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader` (with `--use-gl=swiftshader`
      alone Mol\* cannot create a WebGL context). Pause the rasteriser before timing. The
      structure accessor is `plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data`;
      the controller's public method is `getStructureData()`.
- [ ] **Fix `region-hide.e2e.ts`:** it calls `(controller as any).getStructure?.()`, which does
      not exist, gets `n = 0`, creates a region with an **empty** index array, and hides nothing —
      then passes green. Use `getStructureData()`, assert `n > 0`, assert the region exists before
      hiding.

**Acceptance:** unknown-`op` < 5 ms and `hide_region` < 20 ms at n = 95,000; a spy proves zero
`systemPanel.rebuild()` calls for a message that changes nothing; a spy proves **one**
`StructureComponent` commit per `new_region(representation=…)`; `npm run test:perf` exists and
fails on regression; `grep -rn "getStructure?.()" js/tests/` returns nothing.

**Audit focus:** that Layer 3 did not become an allow-list silently omitting an op; that Layer 4's
approach is measured, not assumed; that the perf budgets were **set from a clean run**, not
back-fitted to whatever the code does.

### Audit note — 2026-07-10, **passed** (third pass)

Verified by independent execution, not by reading the report.

| Metric, n = 95,000 atoms | Before | After |
|---|---:|---:|
| unknown `op` | 3,183 ms | **0.30 ms** |
| `hide_region` | 3,159 ms | **0.10 ms** |
| `load_structure_from_string` (harness) | 9,248 ms | 3,182 ms |
| component builds per `new_region(representation=…)` | 2 | **1** |

Layer 3's dispatch map was checked exhaustively: all 31 ops consumed by `applyWorkbenchMessage`
are present in the 49-entry map. No silent omission.

**Layer 4 is deferred, by agreement.** `SystemPanel.rebuild()` is now idempotent when the
structure has not changed, but it remains a full teardown on structure change and the strip still
holds one live DOM node per residue. Documented in `message_toll_performance.md` §4 with the
measured ceiling (`groupNodes <= 9,500`). Caveat for whoever picks it up: that ceiling is
`ATOMS / ATOMS_PER_RESIDUE` — a tautology for the synthetic PDB, so it asserts the O(residues)
shape and nothing more. Real virtualisation must replace it with an absolute number.

**Two rejections preceded this pass**, and both were necessary. The first attempt removed
`set_representation()` from `new_region()` without noticing that the call also converted
`color="red"` into a `molstar_color_theme` and emitted the visual-overlap warning: colours were
silently dropped at creation, `styles.focus()` broke, and nine Python tests were red — with the
suite never run. The second attempt fixed those but moved the `?? "cartoon"` default from
TypeScript into Python (`visual_representation or "cartoon"`), which would have let Phase 2's
mechanical criterion (`grep '?? "cartoon"' js/src/`) pass while the defect lived on, and it left
the rebuild path (`core.py`) still double-building.

**Both surviving fixes are guarded by mutation-tested regressions.** Reverting
`or "cartoon"` fails `test_new_region_with_visual_params_preserves_none_representation`; reverting
`_send_create(include_visual=False)` in the rebuild path fails
`test_apply_system_edit_replays_visual_region_as_bare_create_then_style`. Each was confirmed by
actually reverting the fix and running the suite.

**Landed as `68522ae6` on `main`,** verified independently after the fact: the rejected commit
`0c36549e` is not an ancestor; both formerly-untracked test files are tracked; `viewer.js` is
byte-identical after a fresh `npm run build:runtime`; and all four suites are green on `main`
(`pytest` rc 0, `test:js` 160/160, `build:runtime` rc 0, `test:perf` rc 0 with
`unknownMs 0.30`, `hideMs 0.10`, `groupNodes 9500`).

The landing also added a **plugin-level** regression the audit had asked for:
`state handler styles a newly-created bare region without rebuilding its component`. Confirmed by
mutation — replacing the component-reuse condition with `if (true)` fails that test and no other.

Housekeeping left open: `npm run test:perf` emits an untracked `tests/perf/message-toll.perf.js`,
while its `tests/e2e/*.e2e.js` siblings are committed. Pick one convention; ignoring both is the
better one.

---

## Phase 1 — GATE: close Decision 2

**Size:** S · **Depends on:** P0 · **Decided by:** the maintainer, on the auditor's numbers.

The question, what it buys, what it costs, the decision rule, and **the exact clauses of
Contracts A and B that get replaced** are all written in `region_contracts.md`
(§ *Open decision — exclusive atom ownership*). The implementer does not interpret; they measure.

- [ ] Re-run the ownership benchmark on the P0-clean baseline (both defects fixed) at
      n = 2k / 20k / 95k, rasteriser paused and live.
- [ ] Separate the cost of `buildSelectionFromAtomIndices`, `Bundle.fromSelection`, the
      `StructureComponent` commit, and `addRepresentation`.
- [ ] Measure the realistic interaction: toggle one region's visibility ten times.
- [ ] Report with a recommendation against the decision rule.

**Output:** the decision recorded in `region_contracts.md`; P2 and P4 shaped by it.

### Audit note — 2026-07-10, **passed** (third measurement)

**Decision 2: exclusive atom ownership is ADOPTED.** Worst case 32.1 ms per toggle at n = 95,000
with 90% ownership and a live rasteriser, against a 150 ms threshold fixed in advance. Picking is
safe on all three cases, through the viewer's own hover / click / context-menu paths, and the
mechanism is confirmed in Mol\*'s source (`mol-gl/renderer.ts`, `pickingAlphaThreshold` default
0.5; a masked atom has alpha 0 and is discarded by the pick pass).

**Two measurements were rejected before this one, and both rejections were load-bearing.**

1. The first implemented the mechanism this contract originally *prescribed* — rebuild the whole's
   component as the complement — and measured 1,029 ms. Its own per-stage instrumentation showed
   `addRepresentation` was 906 of 923 ms: it measured mesh generation, not ownership. **The
   prescription was the maintainer's error**, and it is now withdrawn from `region_contracts.md`.
2. The second switched to masking but passed `getComponents()` as the target, which **includes the
   region's component**. Probed independently: the only transparency node landed under the
   *region*. It faded the region instead of the whole. The report claimed the opposite of what the
   code did.

The third adds an `invariantProbe` that aborts unless the whole carries transparency `1` over
exactly the owned atom set and the region carries none. **Mutation-verified**: reintroducing
`wholeComponentsAfterRegion` makes the benchmark abort with `invariant failed`.

**A new requirement fell out of the picking probe.** `pickingAlphaThreshold` defaults to 0.5, so a
region at `alpha = 0.3` is not pickable. Under naive ownership its atoms would be masked to alpha 0
on the whole as well — invisible *and* unclickable, and lowering a region's opacity would reveal
emptiness instead of the structure behind it. **Ownership is therefore by opaque drawing only**
(`region_contracts.md` R-O1). Requirements R-O2 (delta mask updates) and R-O3 (composition with the
user's `atom_mask`) are conditions on Phase 2's implementation.

Residual: the invariant is asserted against the state tree, not against pixels. Confirm once on
screen in Phase 14.

---

## Phase 2 — Contract A: a region's representation is genuinely optional

**Size:** L · **Depends on:** P1 · Spec: `region_contracts.md` §A.

`const reprType = msg.representation ?? "cartoon";` appears in **both** `createRegion` and
`setRegionRepresentation`. Python believes the region has no visual; Mol\* paints a cartoon.
Three shipped bugs and a blind overlap detector follow from that one line, written twice.

- [ ] Remove **both** fallbacks. The frontend never invents a type.
- [ ] Three named states — **None** / **Inherit** / **Own** — never inferred from an empty params
      dict. `"inherit"` is a reserved sentinel: rejected as a Mol\* type, stored as state.
- [ ] State **Inherit** repaints when the whole's representation changes.
- [ ] `_region_has_visible_representation()` becomes true exactly for **Inherit** and **Own**
      while not hidden. Overlap detection then reports what Mol\* paints — for the first time.
- [ ] `hide()` / `show()` on state-**None**: no-op **that warns**. `show_only()` still works.
- [ ] Migrate `new_view.py:118-125`, `tools/basic/extract.py:65`, `merge.py:123` from hand-copying
      the whole's representation to `set_representation("inherit")`; they gain live tracking.
- [ ] **Audit `view.isolate()`** while here: it is what makes `show_only()` work, it is public
      surface, and Decision 2 changes its meaning. Document its contract or fold it in.

**Acceptance:** `view.new_region("protein")` on a visible whole adds **no** representation (assert
on the plugin's `addRepresentation` calls); `reset_representation()` removes the child rather than
adding `cartoon`; a base region overlapping a visible one now reports the overlap;
`new_view(selection=…)` still shows the selection under a hidden whole;
`grep -rn '?? "cartoon"' js/src/` is empty; `test_region_reset_representation_restores_base_visual_state`
is repaired or renamed (it asserts only the message dict today).

### Audit note — 2026-07-10, **passed** (second pass)

The three representation states, the two `?? "cartoon"` removals, the `"inherit"` sentinel, the
warn-only no-ops, `show_only` off `isolate`, and the composed transparency (one owner of the
transparency channel, closing the latent `setFocusFade`-vs-visibility bug) all landed. Confirmed in
Mol\*'s source that `setStructureTransparency` does `[...layers, layer]` — it **appends** — so the
delta path (R-O2) is complete, not the documented fallback.

**Rejected on the first pass: exclusive ownership had zero tests.** Two mutations left the whole
suite green — `isFullyOpaque → true` (a translucent region would own its atoms, the exact bug R-O1
prevents) and `ownedOpaqueAtomIndices → []` (ownership off entirely). The code read correct, but
"reads correct" is the failure mode that produced this plan's 29-bug ledger.

**Second pass verified by mutation**, each mutant failing its own test and no other:

| mutation | test that fails |
|---|---|
| `isFullyOpaque → true` | translucent regions do not own atoms |
| `ownedOpaqueAtomIndices → []` | opaque mask + delta + composition (3) |
| `requiresFullRebuild = true` always | ownership updates the whole mask by deltas |
| `show_only` whole mask neutralised | show_only masks the whole component |

Two minor points resolved: `extract`/`merge` copy whole→whole (not a region that inherits), so they
correctly do **not** use `"inherit"`; `view.isolate()` remains valid as the user-mask API and now
composes with ownership and the focus fade.

**Two truths now surface that were silent before.** Overlap detection begins warning about visual
overlaps unreported for months (guarded by `test_region_inherit_counts_as_visible_visual_overlap`),
and the focus fade no longer erases partial visibility. Neither is a regression.

**Residual, not blocking:** coverage is unit-level against the simulated plugin. State **None**
under a hidden whole, the opacity slider, and the ownership mask have not been seen to render.
Deferred to the maintainer's Jupyter smoke and to Phase 14.

---

## Phase 3 — Whole's public API + two rebuild bugs

**Size:** M · **Depends on:** P2 · Spec: `studio_whole_subpanel.md`.

`Whole` is **less complete than `Region`** and is not correct.

- [ ] Read-only properties `representation`, `preset`, `params`, `visible`. Migrate the **five**
      private readers: `new_view.py:120-122`, `viewer/molsysmt_interface.py:31-34`,
      `viewer/core.py:1848-1854`, `tools/basic/extract.py:64`, `merge.py:122`.
- [ ] **Remove the side effect**: `set_representation` sets `_global_hidden = False`
      (`whole.py:53-54`). Representation and visibility are orthogonal. No `keep_hidden` flag —
      delete the coupling.
- [ ] **Bug 1:** `viewer/core.py:1849` re-sends the representation during rebuild, resetting
      `_global_hidden`, so line 1858 never re-hides. **A hidden, explicitly-styled whole reappears
      after `apply_system_edit`.** Fixed by the above; add the regression test regardless.
- [ ] **Bug 2:** `_remap_atom_color_map()` (`core.py:1757`) remaps Python's map but **never
      re-sends it**, and `clear_all` does not clear the frontend map. After a system edit the
      browser paints the old index → colour map. The remap must resend.
- [ ] `Whole.reset_representation()` — revert to the **load-time** style, captured **on load**
      (`Whole` is re-instantiated on scene reset, `viewer/scene.py:409`).
- [ ] `Whole.set_color_scheme(scheme)` + `color_scheme` property. Today the structural theme is
      set in JS only, from the **System** subpanel (`system-panel.ts:394-402` →
      `viewer-controller.ts:975-980`): not in the API, not serialised, clobbered by any per-atom
      colouring.
- [ ] `Whole.set_color_by_attribute(..., structure_indices=…)`, `Whole.get_center(...)`,
      `Whole.set_color_by_values(..., replace=…)`. **`structure_indices` on both `Whole` and
      `Region`** — colouring by another frame's B-factor/RMSF must not be a region-only power.
- [ ] `MolSysView.reset_all_colors()` — the explicit canvas-wide wipe.
- [ ] Expose the active scene style for reading. `styles.apply()` writes
      `whole.set_representation()`, which calls `styles._clear_cached_name()` (`whole.py:64-65`):
      three writers, one state, no feedback.

**Acceptance:** `grep -rn '_representation\|_preset\|_repr_params\|_global_hidden' molsysviewer/`
finds no reader outside `whole.py`. Regression: hide + style + `apply_system_edit` ⇒ still hidden.
Regression: per-atom colours land on the correct atoms after `apply_system_edit`. Every `Region`
capability has a `Whole` counterpart, or this plan says why not.

---

## Phase 4 — Contract B/O: layered colour, decorator theme, one `order`

**Size:** L · **Depends on:** P3, shaped by P1 · Spec: `region_contracts.md` §B.

Two defects, both visible on screen, neither tested. `clearAtomColors` clears the map then
**re-applies** `msv-per-atom` over it, and `DEFAULT_COLOR` is `0xaaaaaa`: **`reset_colors()` paints
the system grey.** `_applyPerAtomColorTheme()` swaps the theme of **all** components: **colouring
one region greys out every other atom.** And `Region.reset_colors()` and `Whole.reset_colors()`
have byte-identical bodies; both wipe the canvas.

- [ ] `msv-per-atom` becomes a **decorator**: it takes a base theme and delegates on a miss. A
      component gets it only while a layer covers atoms it draws; clearing the last layer restores
      the component's configured theme.
- [ ] Replace the flat `_atom_color_map` (`core.py:267`) with ordered layers: a base layer owned by
      `whole`, one per region above.
- [ ] **One `order` per region** (Decision B2), governing colour precedence *and* render order,
      serialised, with `raise_to_front()` / `send_to_back()`.
- [ ] The four-level resolution order of §B.4 (owner's layer → owner's theme → whole's layer →
      whole's theme).
- [ ] `Region.reset_colors()` clears its own layer. `Whole.reset_colors()` clears the base layer;
      the screen may not change where a region covers, and that is correct.
      `view.reset_all_colors()` is the only wipe.
- [ ] `Region.set_color_by_values(replace=…)` acts **within** the region's layer.
- [ ] A state-**None** region may still carry a colour layer.
- [ ] Layer lifecycle: delete drops; rename carries; duplicate copies with a fresh `order`;
      boolean results start bare; `apply_system_edit` remaps **and resends**.
- [ ] `clear_atom_colors` gains optional `atom_indices`; colour writes send only affected atoms.
- [ ] Align `set_color_by_attribute`'s availability check with the summary probe: it calls
      `msm.get_attributes(...)` **without** `include_none=False`, while
      `_available_region_attributes` uses it.

**Acceptance:** colouring region A leaves the rest on its structural theme (no grey);
`reset_colors()` restores that theme; `whole.reset_colors()` leaves A's colours standing and hiding
A reveals the reset beneath; two overlapping coloured regions — the last updated wins, and
re-updating the other flips it; deleting a coloured region reveals what lay beneath.

---

## Phase 5 — Contract R: a region is a recipe

**Size:** L · **Depends on:** P2 · Spec: `region_contracts.md` Contract R.

- [ ] `Region.provenance` — public, read-only, **executable**. Nothing of it exists today.
- [ ] `Region.uid` — stable, immutable, non-user-visible. Recipes reference operands by `uid`,
      never by tag, so renaming an operand is invisible to the recipe (§R.6).
- [ ] `Region.mode` ∈ {`static`, `dynamic`}; recipes carry **`frame_dependent`**. A dynamic region
      whose recipe is not frame-dependent costs nothing during playback.
- [ ] `Region.atom_indices` becomes a **read-only property** — the cached result of the last
      evaluation (§R.2).
- [ ] Closure under composition (§R.5).
- [ ] Deleting an operand **freezes** dependents to `static` with `broken: true`; it never blocks
      and never cascades. `region.dependents` / `region.dependencies` expose the graph (§R.6).
- [ ] `apply_system_edit` **re-evaluates** re-evaluable recipes instead of remapping indices;
      remapping survives as the fallback for click-born regions.
- [ ] Regions born from a click are permanently `static`; `mode="dynamic"` on them raises.

Dynamic *evaluation* is Phase 10. The model, the API and the serialisable shape land here.

**Acceptance:** every creation path populates `provenance`; a query region survives a topology edit
by re-evaluation, not remapping; deleting an operand freezes its dependents and leaves them
working; `mode="dynamic"` on a click-born region raises.

---

## Phase 6 — Contract C: state v2

**Size:** M · **Depends on:** P2, P4, P5 · Spec: `region_contracts.md` Contract C.

`viewer/state.py` persists `{tag, atom_indices}` per region and nothing else. Representation,
preset, params, visibility, colours, provenance and the `whole` itself are lost. Transient tags
(`focus<n>`, `orientation-region<n>`, `plane-region<n>`) are **not** filtered on export, so a
`styles.focus()` overlay reimports as a permanent region.

- [ ] `version: 2`. Per region: `uid`, `tag`, `provenance`, `mode`, `order`, layer membership,
      visual state (`representation` incl. `"inherit"`, `preset`, `params`, `hidden`), colour layer,
      and `atom_indices` **as a cache** (re-derivable for re-evaluable recipes).
- [ ] Export the **whole**: representation, preset, params, visibility, structural colour theme,
      base colour layer.
- [ ] Restore in **topological order** (dependencies before dependents). An unsortable graph is
      corrupt: raise, never partially load (§R.7).
- [ ] Restore the **`order` high-water mark**.
- [ ] Filter `_TRANSIENT_REGION_TAG` **on export**.
- [ ] **No v1 reader.** No v1 files exist outside this repository. `import_state` on v1 raises.

**Acceptance:** `export_state` → fresh session → `import_state` reproduces regions, visual state,
visibility, colours **including the winner in every overlap zone**, provenance, mode and order. A
`styles.focus()` overlay does not survive as a region.

---

## Phase 7 — API completeness, symmetry, protocol rename

**Size:** L · **Depends on:** P6.

**Completeness**
- [ ] Variadic booleans: `a.union(b, c)`, `a.intersection(b, c)`, `a.difference(b, c)`.
- [ ] **Atomic overwrite** for create and rename, using the temp-tag pattern `compose_regions`
      already uses. Today the frontend emits `delete_region` + create/rename as two independent
      actions: if the second fails, the original region is lost.
- [ ] Complement of several regions (`new_region(complement_of_regions=[…])` already accepts a
      list; nothing surfaces it).
- [ ] `count_regions_by {element, selection}` so the GUI can size a `group`/`component` split.
- [ ] `new_tag` honoured for `create_complementary_region` and `duplicate_region`; `palette`,
      `value_range`, `element`, `structure_indices` for `color_region_by_attribute`. The handlers
      already accept all of these; nothing sends them.

**Symmetry**
- [ ] `Region`'s state becomes **read-only properties**. Today `representation`, `preset`,
      `repr_params`, `tag`, `atom_indices` are plain mutable attributes:
      `region.representation = "spacefill"` desyncs Python from Mol\*; `region.tag = "x"` breaks the
      registry key.
- [ ] `Region.visible` — today `_hidden` is private, read as `region._hidden  # noqa: SLF001` from
      `RegionsManager.info()` (`regions.py:921`).
- [ ] `Region.set_color_scheme()`, so `Whole` is not the only one with it.
- [ ] `RegionsManager` reaches `SelectionsManager` parity: `tags`, `contains`, `get`, `count`,
      `records`, `delete`, `clear`. It has four methods today; `SelectionsManager` has thirteen.
- [ ] **Unify the creation idiom**: `view.regions.add(...)` beside `view.selections.add(...)`.
      `view.new_region` is removed.

**Protocol**
- [ ] Rename `set_global_representation` → `set_whole_representation`, `show_global` →
      `show_whole`, `hide_global` → `hide_whole`, and the `target: "global"` payloads. Shipping 1.0
      with a protocol that contradicts the API is not acceptable.
- [ ] Add the whole's `PanelAction` family (there is **none** today) and the whole summary:
      `{representation, preset, params, visible, color_scheme, scene_style_name,
      available_attributes, inheriting_region_count, none_state_region_count,
      covering_layer_count}`.

**Acceptance:** `grep -rn "noqa: SLF001" molsysviewer/regions.py molsysviewer/whole.py` finds
nothing for state reads. `grep -rn "global" js/src/messages/viewer-messages.ts` finds nothing for
whole ops. Every `core.py` region/whole handler parameter is reachable from the GUI, or this plan
says why not.

---

## Phase 8 — Contract H: one scene-level command history

**Size:** L · **Depends on:** P6, P7 · **Decision B1.**

Selections have an undo/redo stack in the frontend (`activeSelection.canUndo()`). Regions have
none. Adding a second, independent stack would guarantee two divergent truths.

- [ ] A single **scene-level command history**: every mutating public operation (create, delete,
      rename, represent, colour, reorder, compose, layer-assign) is an undoable command.
- [ ] It **absorbs** the frontend selection history rather than coexisting with it.
- [ ] It is invalidated on `apply_system_edit` and on load, as the selection history already is.
- [ ] `view.history.undo() / redo() / clear()`, plus GUI affordances.
- [ ] It is **not** serialised into state v2 (session-scoped), and that is stated.

**Acceptance:** undo of every mutating operation restores the prior scene, verified by comparing
`export_state` before and after; there is exactly one history object in the codebase.

---

## Phase 9 — Layer membership for regions

**Size:** M · **Depends on:** P6 · **Decision B3.**

`view.layers` governs shapes, annotations and measurements — but not regions
(`molsysviewer/layers.py`). That asymmetry has no justification.

- [ ] `Region.layer` membership; `LayerHandle.members` includes regions; layer show/hide/delete
      applies to them.
- [ ] Serialised in state v2 (the field lands in Phase 6; the behaviour lands here).
- [ ] The Layers subpanel (today a `RoadmapPanel`) gains its first real content.

---

## Phase 10 — Dynamic-region evaluation

**Size:** L · **Depends on:** P0, P5, P6 · **Decisions 1 + A + B4.**

- [ ] Python evaluates `frame_dependent` dynamic regions **lazily**, on frame display, cached per
      `(region, structure_index)`.
- [ ] One **consolidated message per frame** carrying the atom-index deltas of all changed dynamic
      regions. Never one message per region.
- [ ] Non-`frame_dependent` regions re-evaluate on topology change only.
- [ ] Budget enforcement: if per-frame evaluation exceeds its budget, warn and **offer to freeze**
      the region to `static`. Never silently drop frames.
- [ ] Perf harness gains a "frame advance with a dynamic region" budget.

**Acceptance:** *"waters within 5 Å of the ligand"* tracks a trajectory; a `chain A` dynamic region
costs zero during playback; playback with N dynamic regions emits exactly one message per frame.

---

## Phase 11 — Regions subpanel (GUI)

**Size:** L · **Depends on:** P7 · Spec: `studio_region_subpanel_ui_design.md`.

- [ ] Create section: the **12 representations and real presets** from the backend
      (`setStyleOptions()` already delivers them; the Create dropdown is hardcoded to 7, with no
      presets — the very flaw the blueprint set out to fix). Offer **Inherit**, defaulting to it
      when the whole is hidden.
- [ ] Fourth origin: from a **saved selection**.
- [ ] Split over all elements and over the active selection, with confirmation above a threshold.
- [ ] `new_tag` for Complement and Duplicate; `palette` / `value_range` / `element` /
      `structure_indices` for colour-by-attribute; the attribute `<select>` shows the **active**
      attribute instead of resetting to "None" on every repaint.
- [ ] Multi-operand boolean composer over the variadic API.
- [ ] Inspect shows `provenance`, `mode`, `order`, broken-recipe state; hosts `contains` /
      `is_composed_of`.
- [ ] Reorder controls (`raise_to_front` / `send_to_back`).
- [ ] Disable `Hide` for state-**None** regions with a tooltip; `Isolate` stays enabled.
- [ ] **Four bugs:** the opacity slider is inert on a Base region (`regions-panel.ts:995`);
      `Apply Style` with both selects empty emits `reset_region_representation`, silently discarding
      the user's settings (`:963-967`); `regionBooleanAttention` is set on the ⚠ badge and never
      reset (`:47, :419`); the badge only ever prefills `overlap_tags[0]`.
- [ ] Section order Create → Regions → Boolean, matching the UI spec.

---

## Phase 12 — Whole subpanel (GUI) + System migration

**Size:** L · **Depends on:** P7 · Spec: `studio_whole_subpanel_ui_design.md`.

- [ ] Replace `RoadmapPanel("whole", …)` (`group-panel.ts:321`) with a real `WholePanel`.
- [ ] Extract the style composer from `regions-panel.ts` into a **shared component** *before*
      `WholePanel` consumes it. Two composers that drift is the mistake this effort corrects.
- [ ] Presence & camera, warning and confirming before hiding when state-**None** regions vanish.
- [ ] Representation, with the `N regions inherit` note and the `scene_style_name` row stating that
      editing clears the named scene style.
- [ ] Colour: migrated theme, uniform, colour-by-attribute, `Reset colours` (base layer, annotated
      `covered by N region layers`), and a visually distinct `Reset ALL colours`.
- [ ] Lazy Inspect: composition, frame-accurate centroid, `contains` / `is_composed_of`.
- [ ] Remove the *Colour scheme* dropdown from `system-panel.ts:394-402` and the
      `onChangeColorScheme` callback (`group-panel.ts:151,378` → `viewer-controller.ts:975-980`).
      **System** keeps strips, hover, pick and context menu.

**Acceptance:** no frontend path mutates the molecular colour theme without going through Python.

---

## Phase 13 — Corpus regeneration

**Size:** M · **Depends on:** P12.

The corpus is **expected to be broken from Phase 2 onward**. That is accepted, not an accident.

The dangerous changes are **semantic without syntactic change**: `reset_colors()` still runs,
still returns `None`, and now means something else. Notebooks stay green and do the wrong thing.
A grep cannot find this.

Current call sites: `view.new_region` ×46, `view.whole.set_representation` ×36, `view.regions[`
×30, `view.whole.hide` ×11, `.set_color_by_values` ×10, `.reset_colors` ×4 — across
`sandbox/Curso/` (26 notebooks), `docs/`, `bloques.md`.

- [ ] Audit **every** call site against the migration table, one by one.
- [ ] Regenerate the course units and `docs/` against the new API (`view.regions.add`, `"inherit"`,
      layered colour, `reset_all_colors`, recipes).
- [ ] Delete `bloques.md` or bring it in line.

---

## Phase 14 — Real browser E2E

**Size:** S · **Depends on:** P11, P12, P13.

Flags: `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`.

- [ ] `alpha` / `quality` reach Mol\* `typeParams` **on screen** — never yet confirmed.
- [ ] An inheriting region follows a change of the whole's representation.
- [ ] Uncoloured atoms keep their structural theme and **do not turn grey**.
- [ ] Hiding the whole makes state-**None** regions vanish; `Inherit`/`Own` remain.
- [ ] `Reset colours` leaves region layers; `Reset ALL colours` clears them.
- [ ] A dynamic region tracks a trajectory.
- [ ] Regions and Selection walkthroughs pass with no WebGL skip.
- [ ] Record browser version, GL environment, machine and results.

---

## 4. Bug ledger

Every defect found in the 2026-07-09/10 audit, and where it is fixed. All were verified in code;
none were reported by a failing test.

| # | Defect | Phase |
|---|---|---|
| 1 | `?? "cartoon"` in `createRegion` **and** `setRegionRepresentation` | P2 |
| 2 | `reset_representation()` renders `cartoon` instead of removing the visual | P2 |
| 3 | Opacity slider inert on a Base region | P2 / P11 |
| 4 | Overlap detection blind to base regions | P2 |
| 5 | `Region.reset_colors()` wipes the whole canvas | P4 |
| 6 | `Region.set_color_by_values(replace=True)` replaces the canvas map | P4 |
| 7 | `reset_colors()` paints the system grey (`DEFAULT_COLOR`) | P4 |
| 8 | Colouring one region greys out every other atom | P4 |
| 9 | `set_color_by_attribute` misses `include_none=False` | P4 |
| 10 | Hidden whole reappears after `apply_system_edit` | P3 |
| 11 | Per-atom colours go stale after `apply_system_edit` | P3 |
| 12 | `set_representation` silently shows the whole | P3 |
| 13 | `styles`' active name cleared silently by `whole.set_representation` | P3 / P12 |
| 14 | `export_state` loses all region visual state | P6 |
| 15 | `export_state` exports transient `focus`/`orientation`/`plane` regions | P6 |
| 16 | Non-atomic overwrite on create and rename | P7 |
| 17 | `Region` state is mutable public attributes | P7 |
| 18 | `Region` has no `visible` property (`_hidden` read with `noqa`) | P7 |
| 19 | `RegionsManager` has 4 methods; `SelectionsManager` has 13 | P7 |
| 20 | `handleMessage` toll: 3.1 s per message at n = 95k | P0 |
| 21 | Every region with a representation is built twice | P0 |
| 22 | 19,000 live DOM nodes in the group strip | P0 |
| 23 | `getStructure()` does not exist; `region-hide.e2e.ts` tests nothing | P0 |
| 24 | Create dropdown hardcoded to 7 representations, no presets | P11 |
| 25 | `Apply Style` with empty selects silently discards the user's settings | P11 |
| 26 | `regionBooleanAttention` never reset | P11 |
| 27 | ⚠ badge only ever prefills `overlap_tags[0]` | P11 |
| 28 | Colour-by-attribute `<select>` resets to "None" on every repaint | P11 |
| 29 | `make_regions_by`'s `selection`, `new_tag`, `palette`, `value_range` dead in the backend | P7 / P11 |

---

## 5. Progress dashboard

| Phase | Title | Size | Status | Date | Commit | Audit note |
|------:|-------|:----:|--------|------|--------|-----------|
| 0 | Perf: toll + double build | M | ☑ | 2026-07-10 | `68522ae6` | **Passed on the third pass.** See note below. |
| 1 | GATE: close Decision 2 | S | ☑ | 2026-07-10 | *(bench, pending commit)* | **Ownership ADOPTED.** 32 ms worst case vs a 150 ms threshold; picking verified. Two rejections first. |
| 2 | Contract A: representation | L | ☑ | 2026-07-10 | *(this commit)* | **Passed on the second pass.** Ownership had zero tests until mutation exposed it. See note. |
| 3 | Whole API + rebuild bugs | M | ☐ | — | — | — |
| 4 | Contract B/O: colour + order | L | ☐ | — | — | — |
| 5 | Contract R: recipes | L | ☐ | — | — | — |
| 6 | Contract C: state v2 | M | ☐ | — | — | — |
| 7 | API completeness & symmetry | L | ☐ | — | — | — |
| 8 | Contract H: command history | L | ☐ | — | — | — |
| 9 | Layer membership | M | ☐ | — | — | — |
| 10 | Dynamic-region evaluation | L | ☐ | — | — | — |
| 11 | Regions GUI | L | ☐ | — | — | — |
| 12 | Whole GUI + System migration | L | ☐ | — | — | — |
| 13 | Corpus regeneration | M | ☐ | — | — | — |
| 14 | Browser E2E | S | ☐ | — | — | — |

Size: **S** ≈ hours · **M** ≈ 1–2 days · **L** ≈ 3–5 days.

---

## 6. Why this order, in one paragraph

Nothing can be judged fast or slow until the three-second-per-message toll and the double
component build are gone, and Decision A's one-message-per-frame design depends on it, so P0 is a
prerequisite of the model and not merely of performance. The ownership model replaces named
clauses of two contracts, so it is decided before either is built (P1). Representation is the
root: one `?? "cartoon"` written twice explains three shipped bugs and a blind overlap detector
(P2). Colour and ordering belong to the whole, whose API does not own them (P3 → P4). Recipes make
regions re-evaluable, which is what makes serialisation worth doing once instead of twice
(P5 → P6). Only then is the API completed and symmetric (P7), and only then do history, layers and
dynamic evaluation become expressible (P8–P10) and the two panels get built on top (P11, P12). The
course and docs are regenerated last, because they should teach the finished API, not the one we
are leaving behind (P13). And the browser confirms what no simulation can (P14).

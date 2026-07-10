# Implementation Plan: Regions — contracts, API completeness, and subpanel parity

> ⚠ **The execution order lives in `scene_master_plan.md`, not here.** That document owns the
> phase order, the gates and the audits, across Regions *and* Whole *and* the performance work.
> This file is now a **task-detail source** for the Regions-specific phases. Where the two
> disagree on ordering, the master plan wins.
>
> In particular: master-plan **Phase 0** (the `handleMessage` toll) precedes everything here,
> and master-plan **Phase 1** (exclusive atom ownership) is an open gate that reshapes
> Contracts A and B.

**Status:** Phases 0–D of the *original* plan landed (2026-07-09) and delivered the
subpanel's structure. A 2026-07-10 audit against the code found that the delivery rests
on **three broken contracts** and that the GUI does not reach parity with the Python API.
This plan supersedes the original phase list. The original Phase 0–D completion notes are
preserved in §Appendix for provenance.

**Purpose:** make regions *right* — for the computational-biology user, from Python and
from the GUI alike — rather than merely feature-complete on the surface.

---

## Reference documents (read all before starting)

1. **`region_contracts.md`** — **normative**. The three contracts (representation, colour,
   serialisation), the evidence for each, and how they are tested. **This wins over
   everything else.**
2. **`studio_region_subpanel.md`** — architectural blueprint: lifecycle, layout, backend
   contracts, non-API additions.
3. **`studio_region_subpanel_ui_design.md`** — UI/UX + CSS spec.
4. **`studio_selection_subpanel.md`** — sibling contract: query composer, collision policy,
   rename idiom, design tokens. Reused, never forked.

Precedence on disagreement: (1) > (2) > (3). (3) never redefines backend calls.

---

## Guardrails (project rules)

- **Never hand-edit** `molsysviewer/viewer.js` / `.map`. Edit TS under
  `molsysviewer/js/src/` and run `npm run build:runtime`. Reserve `npm run build` for
  release/packaging version sync.
- Region ops go through the **public API** (`view.new_region`, `view.regions`, `region.*`).
  Do not regrow viewer mutators; do not let the GUI reach past the API.
- **API first.** A capability lands as a public Python method *before* it is wired as a
  `core.py` handler or exposed in the GUI.
- Backend ops resolve **on the Python side** so provenance and naming are known there.
- Prefer raw index lists / registry lookups over building query strings.
- **A test whose name claims a visual outcome must assert against the simulated Mol\***
  plugin, not against the emitted message dict. (This is *why* the defects shipped.)

---

## Closure criterion (new, adopted 2026-07-10)

> For every parameter accepted by a region handler in `core.py`, either the GUI exposes it,
> or this plan documents why it does not.

Applied retroactively, this criterion is what catches `palette`, `value_range`, `element`,
`new_tag` (complement, duplicate) and `selection` (split) sitting dead in the backend.

---

## Progress dashboard

| Phase | Title | Size | Depends on | Status | Date | Commit | Notes |
|------:|-------|:----:|:----------:|--------|------|--------|-------|
| 0 | Documentation truth reset | S | — | ☐ | — | — | correct the false "implemented" claims before building on them |
| 1 | **Contract A** — representation is optional | L | 0 | ☐ | — | — | removes the two `?? "cartoon"`; introduces the `"inherit"` sentinel |
| 2 | **Contract B** — layered, owned colour | L | 1, **Whole P1** | ☐ | — | — | decorator theme, colour layers, precedence, `color_order` |
| 3 | **Contract C** — provenance & state v2 | L | 1, 2 | ☐ | — | — | needs A and B closed to know *what* to persist |
| 4 | Public API completeness | M | 3 | ☐ | — | — | variadic booleans, atomic overwrite, counts, colour params |
| 5 | GUI parity | L | 4 | ☐ | — | — | mostly mechanical once the floor is firm |
| 6 | Real browser E2E validation | S | 5 | ☐ | — | — | Chromium + WebGL; still open since the original Phase D |

Size: **S** ≈ hours · **M** ≈ 1–2 days · **L** ≈ 3–5 days.
Status legend: ☐ Not started · ◐ In progress · ☑ Done · ✗ Dropped.

**Ordering is not negotiable for 1 → 2 → 3.** You cannot serialise a visual state whose
contract still lies, nor colour layers that do not yet exist.

---

## Risks & unknowns

| # | Risk | Phase(s) | Mitigation |
|---|------|:--------:|------------|
| R1 | **Silent invisibility.** A state-**None** region under a hidden whole renders nothing. `new_view(selection=…)` hides the whole. | 1, 5 | `new_view`/`extract`/`merge` switch to `"inherit"`; the GUI's Create control defaults to **Inherit** when the whole is hidden |
| R2 | **Live-tracking edge.** Regions in state **Inherit** must repaint when `set_global_representation` changes the whole's type | 1 | new edge in `StateHandlers`; unit test on the simulated plugin |
| R3 | **`hide()` on a state-None region** has nothing to hide | 1, 5 | documented no-op **that warns**; GUI disables the control with a tooltip |
| R4 | **Colour precedence is not reproducible** — `dict` order does not survive `import_state` | 2, 3 | materialise `color_order` per region and serialise it; round-trip test asserts the overlap winner |
| R5 | **Message size** — resolving layers in Python could resend large maps | 2 | send only affected atom indices; `clear_atom_colors` gains optional `atom_indices` |
| R6 | **Published-API semantic breaks** (`reset_colors`, `replace`, `reset_representation`) | 1, 2 | migration table in `region_contracts.md`; deliberate and documented, not silent |
| R7 | **v1 state files** in the wild | 3 | `import_state` reads v1 (identity only) and v2 |
| R8 | **Split explosion** — `group`/`component` can yield hundreds of regions | 4, 5 | new `count_regions_by` query; GUI confirms above a threshold |
| R9 | **Green tests that assert nothing visual** — the root cause of all three defects | all | the guardrail above; retrofit `state-handler.test.ts` coverage |
| R10 | **Index space** — atom sets live in `_molsys`; splits/composition/attribute colour must stay in it | all | subset-loaded regression test |
| R11 | **Overlap cost** — `_overlapping_visual_region_tags` is O(regions × atoms), and Contract A makes *more* regions count as visible | 1 | already optimised (one atom set per visible region, each pair once); re-measure after A |
| R12 | **The grey screen** — `msv-per-atom` replaces the structural theme instead of decorating it, so any colour write greys every uncoloured atom and `reset_colors()` greys everything | 2 | make the theme a decorator with a base-theme fallback; assert on the simulated plugin that uncoloured atoms keep their theme |
| R13 | **Whole coupling** — the base colour layer and the structural theme belong to `whole`, whose Python API does not own them today | 2, 3 | land `studio_whole_subpanel_implementation_plan.md` Phase 1 first; the two subpanels share Contracts A and B |

---

## Phase 0 — Documentation truth reset

**Size:** S · **Depends on:** — · Docs only, no code.

The three existing documents assert as *implemented* things that do not exist. Building on
them is how we got here.

- [ ] `studio_region_subpanel.md`: remove the §5 claim that regions store `_provenance`
      (grep returns nothing); mark provenance as **proposed**. Fix §6.1's path
      (`renderRegionsSection()` in `group-panel.ts` no longer exists — the panel lives in
      `ui/panels/regions-panel.ts` since the A–F refactor). Swap the inverted §6.5 / §6.6.
      Downgrade the header status.
- [ ] `studio_region_subpanel_ui_design.md`: the Inspect mockup (§2, §3.B) draws provenance
      that does not exist; §3.C describes a multi-operand checklist that is a single
      `<select>` in code. Mark both **proposed**. Correct the attribute names shown
      (`b_factor`, `occupancy`, `partial_charge`, `formal_charge` — the GUI lists canonical
      names; `bfactor`/`charge` are aliases internal to `set_color_by_attribute`).
- [ ] Reconcile the section order: the doc says Create → Regions → Boolean; `paint()` renders
      Create → Boolean → Regions. Decide and align **both**.
- [ ] Record the debt: `tests/regions/test_region_flow.py::test_region_reset_representation_restores_base_visual_state`
      asserts only the emitted message; its name claims a visual outcome it never checks.
- [ ] Link all three documents to `region_contracts.md` as the normative source.
- **Acceptance:** no document asserts, in the indicative, a capability absent from the code.

---

## Phase 1 — Contract A: a region's representation is genuinely optional

**Size:** L · **Depends on:** 0 · Refs: `region_contracts.md` §A.

This is the root fix. Three shipped bugs collapse into it.

**Python (`molsysviewer/regions.py`, `whole.py`, `viewer/regions.py`)**

- [ ] Accept the reserved `"inherit"` sentinel in `Region.set_representation()`. It is not a
      Mol\* type: `_normalize_representation_type` must reject it as a type and the region
      must store it as its representation state.
- [ ] `reset_representation()` means state **None**: no own visual. Its message must be
      distinguishable from "paint me with the default".
- [ ] `Region.hide()` on a state-**None** region: documented no-op **that warns**.
- [ ] Fix `_region_has_visible_representation()` to be true exactly for states **Inherit**
      and **Own** while not hidden — i.e. to describe what Mol\* paints. Overlap detection
      (and therefore the ⚠ badge) starts working as a consequence.

**Protocol / frontend (`js/src/managers/handlers/state-handlers.ts`)**

- [ ] Remove **both** `const reprType = msg.representation ?? "cartoon";` — in `createRegion`
      *and* in `setRegionRepresentation`. The frontend never invents a type.
- [ ] State **None** ⇒ component, no representation child.
- [ ] State **Inherit** ⇒ own representation using the whole's **live** type/preset, with the
      region's `params` on top.
- [ ] `setGlobalRepresentation` repaints every region in state **Inherit** (R2).

**Callers (`new_view.py`, `tools/basic/extract.py`, `tools/basic/merge.py`)**

- [ ] Replace the hand-rolled snapshot copy of the whole's representation with
      `set_representation("inherit")`. Behaviour is preserved and gains live tracking.

**Tests**

- [ ] `js/tests/unit/state-handler.test.ts`, against the simulated plugin: state **None** adds
      **no** representation; `reset_representation` removes the child; `inherit` uses the
      whole's current type; changing the whole repaints inheriting regions.
- [ ] Rename/repair `test_region_reset_representation_restores_base_visual_state`.
- [ ] Python: a base region that overlaps a visible one now reports the overlap.

- **Acceptance:** `view.new_region("protein")` on a visible whole adds no cartoon;
  `reset_representation()` restores the base look; the opacity slider is meaningful on an
  inheriting region; the ⚠ badge fires for a previously-invisible overlap;
  `new_view(selection=…)` still shows the selection under a hidden whole. Python suite +
  `npm run test:js` + `npm run build:runtime` green.

---

## Phase 2 — Contract B: layered, owned colour

**Size:** L · **Depends on:** 1 · Refs: `region_contracts.md` §B.

> **Depends on the Whole subpanel's Phase 1** (`studio_whole_subpanel_implementation_plan.md`):
> the base layer is owned by `whole`, and the structural colour theme beneath it must first
> become a Python-owned, serialisable property instead of a frontend-only dropdown.

- [ ] **Make `msv-per-atom` a decorator theme** (`region_contracts.md` §B.5). Today
      `per-atom-color.ts` returns a grey `DEFAULT_COLOR` on a miss and
      `_applyPerAtomColorTheme()` swaps the theme of **every** component. Consequences shipped
      today: `reset_colors()` paints the whole system grey, and colouring one region greys out
      every other atom. The theme must take a **base theme** and delegate to it on a miss;
      clearing the last layer over a component restores that component's configured theme.
- [ ] Replace the flat canvas-wide `_atom_color_map` (`viewer/core.py:267`) with ordered
      layers: a base layer owned by `whole`, one layer per region above it.
- [ ] Layer lifecycle (`region_contracts.md` §B.6): delete drops the layer; rename carries it;
      duplicate copies it with a **fresh** `color_order`; boolean results start with none;
      `apply_system_edit` remaps every layer through `atom_index_map`.
- [ ] Precedence: any region beats the base; between overlapping regions the **most recently
      created/updated** wins. Materialise a monotonic `color_order` per region, bumped on
      every colour write (R4).
- [ ] `Region.reset_colors()` clears **its own layer only**; what lies beneath reappears.
- [ ] `Region.set_color_by_values(replace=…)` — `replace` acts **within the region's layer**
      (redefinition of published behaviour, R6).
- [ ] `Whole.reset_colors()` clears the **base layer** across the system; regions keep theirs.
- [ ] New `view.reset_all_colors()` for the explicit canvas-wide wipe.
- [ ] A state-**None** region may still carry a colour layer (§B.4): colouring without
      representing must work.
- [ ] Protocol: `clear_atom_colors` gains optional `atom_indices`. Colour writes send only
      affected atoms (R5).
- [ ] Align `set_color_by_attribute`'s availability check with the summary probe: it calls
      `msm.get_attributes(...)` **without** `include_none=False`, while
      `_available_region_attributes` uses it. It can accept an all-`None` attribute and fail
      later in the value guard.

- **Acceptance:** colouring region A leaves the rest of the system on its structural theme (no
  grey); `reset_colors()` restores that theme rather than painting grey. Colouring region A then
  `whole.reset_colors()` leaves A's colours on screen; hiding A reveals the reset beneath. Two
  overlapping coloured regions: the last updated wins, and re-updating the other flips the
  winner. `Region.reset_colors()` never touches another region. Deleting a coloured region
  reveals what lay beneath. Suite/build green.

---

## Phase 3 — Contract C: provenance and state v2

**Size:** L · **Depends on:** 1, 2 · Refs: `region_contracts.md` §C.

- [ ] `Region.provenance` — new public read-only mapping. Populate it at **every** creation
      path: query, active selection, saved selection, split, complement, boolean, duplicate,
      import. Nothing of this exists today.
- [ ] `export_state` → `version: 2`. Per region: identity (`tag`, `atom_indices`, `selection`,
      `syntax`), `provenance`, visual state (`representation` incl. the `"inherit"` sentinel,
      `preset`, `params`, `hidden`), colour layer, `color_order`.
- [ ] Export the **whole**'s representation/preset/params/visibility and its base colour layer
      — none of which are exported today.
- [ ] **Filter transient tags on export** (`_TRANSIENT_REGION_TAG`). Today `styles.focus()`
      overlays are exported and reimported as permanent manageable regions.
- [ ] `import_state` reads v1 (identity only; regions restored in state **None**, no colours)
      and v2 (R7).
- [ ] Return `provenance` in `get_region_details`.

- **Acceptance:** `export_state` → fresh session → `import_state` reproduces the regions, their
  visual state, their visibility, their colours **including the winner in every overlap zone**,
  and the provenance rendered in Inspect. A `styles.focus()` overlay does not survive the
  round-trip as a region. A v1 file still loads. Suite/build green.

---

## Phase 4 — Public API completeness

**Size:** M · **Depends on:** 3 · Refs: blueprint §6.5, §8.

Everything here is additive, and each item is a **public Python method first**.

- [ ] **Variadic boolean operators**: `a.union(b, c)`, `a.intersection(b, c)`,
      `a.difference(b, c)` — evaluating `A − (B ∪ C)`. The Python user gets exactly what the
      GUI's multi-operand composer needs.
- [ ] **Atomic overwrite** for create and rename, using the temporary-tag pattern already used
      correctly by `compose_regions` in `core.py`. Today the frontend emits `delete_region` +
      create/rename as two independent actions: if the second fails the user loses the
      original region.
- [ ] **Complement of several regions** — `new_region(complement_of_regions=[…])` already
      supports a list; surface it (`create_complementary_region` accepts one tag today).
- [ ] **`count_regions_by {element, selection}`** — a cheap query so the GUI can confirm before
      a `group`/`component` split creates hundreds of regions (R8).
- [ ] **`new_tag`** honoured end-to-end for `create_complementary_region` and
      `duplicate_region` (the handlers already accept it; nothing sends it).
- [ ] **Colour-by-attribute full surface**: `palette`, `value_range`, `element` (the handler
      already accepts all three; the GUI sends only `attribute`).

- **Acceptance:** each method has a direct unit test *and* a handler test routing through it.
  The closure criterion holds: no `core.py` region parameter is unreachable. Suite/build green.

---

## Phase 5 — GUI parity

**Size:** L · **Depends on:** 4 · Refs: blueprint §4; UI spec §2–§3.

**Create section**
- [ ] Use the **12 representations and the real presets** supplied by the backend
      (`setStyleOptions()` already delivers them; only the style composer consumes them). The
      Create dropdown is still hardcoded to 7 options — the very flaw the blueprint §1.1
      criticised in the old implementation.
- [ ] Offer **Inherit** as an option, and default to it when the whole is hidden (R1).
- [ ] Fourth origin: **from a saved selection** (`create_region_from_saved_selection` exists in
      the backend and in `PanelAction`; only the Selection panel offers it).
- [ ] Split: all elements (`group | component | chain | molecule | entity`), with a
      confirmation above a threshold, driven by `count_regions_by` (R8).
- [ ] Split over the **active selection** (`make_regions_by` accepts `selection`; the GUI always
      sends `all`).

**Region cards**
- [ ] `new_tag` inputs for **Complement** and **Duplicate**.
- [ ] Disable **Hide** for state-**None** regions, with a tooltip (R3).
- [ ] **Bug:** the opacity slider is inert on a Base region (`regions-panel.ts:995`). Resolved
      by Contract A + Inherit.
- [ ] **Bug:** `Apply Style` with both selects empty emits `reset_region_representation`,
      silently discarding the opacity/quality/colour the user just set
      (`buildStyleAction()`, `regions-panel.ts:963-967`).
- [ ] **Bug:** `regionBooleanAttention` is set to `true` on the ⚠ badge and never reset
      (`regions-panel.ts:47, 419`) — the composer stays highlighted forever.
- [ ] **Bug:** the ⚠ badge only ever prefills `overlap_tags[0]`; with several overlaps the user
      cannot choose.

**Style composer**
- [ ] `palette`, `value_range`, `element` for colour-by-attribute; the `<select>` must reflect
      the **active** attribute instead of resetting to "None" on every repaint.

**Boolean composer**
- [ ] Multi-operand (checklist) for Union and Difference, over the variadic API from Phase 4.

**Inspect**
- [ ] Show `provenance`. Natural home for `contains` / `is_composed_of`, which have no GUI
      surface at all.

**Whole subpanel**
- [ ] `view.whole.reset_colors()` and `view.reset_all_colors()` land here — the first real
      content of what is today a `RoadmapPanel` placeholder.

- **Acceptance:** every capability of blueprint §1.2 is reachable from the GUI, and the closure
  criterion holds. Unit tests assert the emitted payloads. Suite/build green.

---

## Phase 6 — Real browser E2E validation

**Size:** S · **Depends on:** 5. Open since the original Phase D.

- [ ] On a host with a real Chromium/Chrome and working WebGL:

  ```bash
  cd molsysviewer/js
  npm run test:e2e:regions
  ```

- [ ] Confirm the walkthrough completes with no browser errors and no WebGL-related skip.
- [ ] Confirm on screen what no simulation can: `alpha` and `quality` reach Mol\* `typeParams`;
      an inheriting region follows a change of the whole's representation; the overlap badge
      corresponds to visible z-fighting.
- [ ] Manually inspect layout overflow, badge scroll/highlight, style controls, boolean
      composition, Inspect refresh.
- [ ] Record browser version, GL environment, command result and findings here.

This validates already-implemented code. A compile-only check or a headless skip does not
close it.

---

## Cross-cutting (every phase)

- [ ] Rebuild after TS changes: `cd molsysviewer/js && npm run build:runtime`. Never hand-edit
      `viewer.js`.
- [ ] Keep the Python suite + `npm run test:js` green; add tests **with** each phase.
- [ ] Update the dashboard row and the Risks table as each phase lands.
- [ ] Correct the reference documents **as you go**, not at the end.

---

## Appendix — the original Phases 0–D (2026-07-09)

The original plan delivered, in order: the public API additions (`reset_representation`,
`set_color_by_attribute`, `duplicate`, `overlaps`, `show_all`/`hide_all`), the backend event
handlers and batch context, the enriched region summary (`representation`, `preset`,
`overlap_tags`, `available_attributes`, transient-tag filter), the three creation origins with
the shared `ManualQueryComposer`, the lifecycle cards, the style composer, the ordered boolean
composer, lazy frame-aware Inspect, and the design tokens.

That work stands and is not being reverted. What the 2026-07-10 audit established is that it
was built on three contracts that were never written down and that the code silently violates
— which is why `reset_representation` never worked, why overlap detection never fired for base
regions, why per-region colour was never per-region, and why a session could never be reloaded.
Phases 1–3 supply the missing floor; Phases 4–5 finish the work the original plan intended.

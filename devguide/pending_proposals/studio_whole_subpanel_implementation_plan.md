# Implementation Plan: Studio → Whole subpanel

> ⚠ **The execution order lives in `scene_master_plan.md`, not here.** That document owns the
> phase order, the gates and the audits across both subpanels. This file is a **task-detail
> source** for the Whole-specific phases. Where the two disagree on ordering, the master plan
> wins.
>
> Note the interleaving changed: Whole's public API (master-plan Phase 3) now precedes the
> colour-layer work, and the `keep_hidden` flag proposed below is **superseded** — with no
> users to protect, `set_representation` simply stops touching visibility.

**Status:** proposed (2026-07-10). Nothing implemented; the subpanel is a `RoadmapPanel`
placeholder and the whole has **no JS → Python action channel at all**.

**Purpose:** give the baseline structure (`view.whole`) a complete Python API and complete GUI
control, and — because the two are the same contracts seen from both ends — unblock Phases 2
and 3 of `studio_region_subpanel_implementation_plan.md`.

---

## Reference documents

1. **`region_contracts.md`** — **normative**. Representation states, colour layers,
   serialisation. Governs both subpanels. Wins over everything else.
2. **`studio_whole_subpanel.md`** — blueprint: the API gap table, the coupling with Regions,
   the backend contracts.
3. **`studio_whole_subpanel_ui_design.md`** — UI/UX spec.
4. **`studio_region_subpanel_implementation_plan.md`** — the sibling plan. **Read its
   dependency notes**: its Phase 2 depends on this plan's Phase 1.

---

## Guardrails

- **Never hand-edit** `molsysviewer/viewer.js` / `.map`. Edit TS under `molsysviewer/js/src/`,
  run `npm run build:runtime`.
- **API first.** A capability is a public Python method before it is a handler or a control.
- Whole ops go through `view.whole.*` / `view.*`. The GUI never reaches past the API.
- **Do not fork the style composer.** Extract the one in `regions-panel.ts` into a shared
  component first, exactly as `ManualQueryComposer` was extracted.
- **A test whose name claims a visual outcome must assert against the simulated Mol\* plugin**,
  not against the emitted message dict.

---

## Closure criterion

> Every capability `Region` has, `Whole` has too, unless this plan documents why not. Today the
> subordinate object is **more** capable than its base: `Region` has
> `set_color_by_attribute`, `reset_representation`, `duplicate`, `get_center`; `Whole` has
> none of the first three and no `get_center`.

---

## Progress dashboard

| Phase | Title | Size | Depends on | Status | Date | Commit | Notes |
|------:|-------|:----:|:----------:|--------|------|--------|-------|
| 1 | Public API for the whole | M | Regions **P1** | ☐ | — | — | **unblocks Regions P2**; state becomes public, theme becomes API-owned |
| 2 | Action channel + whole summary | M | 1 | ☐ | — | — | the whole has no JS→Python actions today |
| 3 | Shared style composer extraction | S | Regions P1 | ☐ | — | — | one composer, two consumers |
| 4 | The subpanel | L | 2, 3 | ☐ | — | — | replaces the `RoadmapPanel` |
| 5 | Colour-scheme migration out of System | S | 4 | ☐ | — | — | removes the frontend-only control |
| 6 | E2E validation | S | 4, 5 | ☐ | — | — | Chromium + WebGL, alongside the Regions walkthrough |

Size: **S** ≈ hours · **M** ≈ 1–2 days · **L** ≈ 3–5 days.

### Interleaving with the Regions plan

```
Regions P0 (docs)
Regions P1 (Contract A: representation)   ← both plans need this
   ├── Whole  P1 (public API)             ← unblocks ↓
   └── Whole  P3 (shared style composer)
Regions P2 (Contract B: colour layers)    ← needs Whole P1
Regions P3 (Contract C: state v2)         ← serialises the whole too
   ├── Whole  P2 (actions + summary)
   ├── Whole  P4 (subpanel)
   └── Whole  P5 (System migration)
Regions P4, P5  ·  Whole P6  ·  Regions P6
```

Contract A (Regions P1) comes first because both subpanels depend on the meaning of
"representation". Contract B cannot start until the whole publicly owns the base layer and the
structural theme, which is Whole P1.

---

## Risks & unknowns

| # | Risk | Phase(s) | Mitigation |
|---|------|:--------:|------------|
| W1 | **Private-state readers** — `new_view.py:120-122`, `viewer/molsysmt_interface.py:31-34` read `_representation` / `_preset` / `_repr_params` via `getattr` | 1 | land the public properties, then migrate all three call sites in the same commit |
| W2 | **Semantic break** — `whole.reset_colors()` stops wiping the canvas | 1 | migration table in `region_contracts.md`; `view.reset_all_colors()` is the replacement |
| W3 | **The grey screen** — the per-atom theme replaces the structural theme instead of decorating it | 1, Regions P2 | fixed once, in Regions P2 (`region_contracts.md` §B.5); Whole P1 only has to make the base theme *addressable* |
| W4 | **Hiding the whole silently deletes regions from view** — every state-**None** region disappears | 4 | the summary carries `none_state_region_count`; the panel warns *and* confirms |
| W5 | **Two style composers drift** | 3 | extract before the second consumer exists, not after |
| W6 | **Wire-op naming debt** — `set_global_representation` / `show_global` / `hide_global` predate the Global → Whole rename | — | explicitly **out of scope**; recorded in the blueprint §5.3 so it is not rediscovered |
| W7 | **System subpanel regression** — removing the Colour scheme dropdown changes a shipped surface | 5 | migrate, do not delete: the control reappears in Whole with the same two options plus more |
| W8 | **Load-time style is not recorded** — `reset_representation()` needs a baseline to revert *to*, and `Whole` is re-instantiated on scene reset (`viewer/scene.py:409`) | 1 | capture the baseline **on load**, not in `__init__`; assert it survives a rebuild and a reset |
| W9 | **`set_representation` silently shows the whole** (`whole.py:53-54`). It also **breaks the rebuild**: `core.py:1848` re-sends the representation, resetting `_global_hidden`, so line 1858 never re-hides. A hidden, explicitly-styled whole reappears after `apply_system_edit` | 1 | add `keep_hidden=False`; the rebuild path passes `keep_hidden=True`; regression test: hide + style + `apply_system_edit` ⇒ still hidden |
| W10 | **Per-atom colours go stale on rebuild** — `_remap_atom_color_map()` (`core.py:1757`) remaps Python's map but never re-sends it, and `clear_all` does not clear the frontend map (`clearPerAtomColors` is only called from `clear_atom_colors`) | 1, Regions P2 | the remap must resend; generalise to layers in Regions P2 (`region_contracts.md` §B.6); regression test on the message history |
| W11 | **Three writers of one state** — `styles.apply()`, `whole.set_representation()` and this panel all write the whole's representation, and the second clears `styles._last_applied_name` | 1, 4 | expose `scene_style_name` in the summary; the panel displays it and warns that editing clears it; never re-apply a name implicitly |

---

## Phase 1 — Public API for the whole

**Size:** M · **Depends on:** Regions P1 · Refs: blueprint §1.2, §5.1.

This is the phase that **unblocks Regions Phase 2**.

- [ ] Public read-only properties on `Whole`: `representation`, `preset`, `params`, `visible`.
      Migrate **all five** private readers: `new_view.py:120-122`,
      `viewer/molsysmt_interface.py:31-34`, `viewer/core.py:1848-1854` (rebuild),
      `tools/basic/extract.py:64` and `tools/basic/merge.py:122` (W1).
- [ ] `Whole.set_representation(..., keep_hidden: bool = False)` — make the implicit "show"
      opt-out. **Fix the rebuild bug** by passing `keep_hidden=True` from
      `_rebuild_view_from_current_molsys` (W9).
- [ ] **Fix the stale-colour rebuild bug**: `_remap_atom_color_map()` must resend the remapped
      map to the frontend (W10).
- [ ] Expose the active scene style: a public read for `styles._last_applied_name`, surfaced as
      `scene_style_name` in the summary (W11).
- [ ] `Whole.reset_representation()` — revert to the **load-time** style. Requires capturing
      that style at load, not in `__init__`, since `Whole` is re-instantiated on scene reset
      (W8).
- [ ] `Whole.set_color_scheme(scheme)` + a `color_scheme` property — the structural theme
      becomes Python-owned state instead of a frontend-only dropdown (blueprint §1.4). This is
      the base beneath the colour layers, and Regions P2 needs it addressable (W3).
- [ ] `Whole.set_color_by_attribute(attribute, *, element, palette, value_range)` — mirrors
      `Region.set_color_by_attribute`, writing the base layer.
- [ ] `Whole.set_color_by_values(..., replace=…)` — `replace` acts within the base layer.
- [ ] `Whole.reset_colors()` — clears the base layer only (W2).
- [ ] `MolSysView.reset_all_colors()` — the explicit canvas-wide wipe.
- [ ] `Whole.get_center(structure_indices)`.
- **Acceptance:** every closure-criterion item holds. `grep -rn '_representation\|_global_hidden'
  molsysviewer/` finds no reader outside `whole.py`. A `whole.reset_colors()` leaves region
  layers standing. **Regressions:** a hidden, explicitly-styled whole is still hidden after
  `apply_system_edit` (W9); per-atom colours survive a rebuild on the correct atoms (W10).
  Python suite + `npm run test:js` + `npm run build:runtime` green.

---

## Phase 2 — Action channel + whole summary

**Size:** M · **Depends on:** 1 · Refs: blueprint §5.2; UI spec §5.

The whole currently has **no** entry in the `PanelAction` union and no handler in `core.py`.
`set_global_representation` / `show_global` / `hide_global` are Python → JS only.

- [ ] New actions, each routing through a Phase-1 public method: `set_whole_representation`,
      `reset_whole_representation`, `set_whole_visibility`, `focus_whole`,
      `set_whole_color_scheme`, `color_whole_by_attribute`, `reset_whole_colors`,
      `reset_all_colors`, `get_whole_details {request_id}`.
- [ ] Extend the `PanelAction` closed union (`ui/panels/types.ts`).
- [ ] **Whole summary** echoed on every change: `{representation, preset, params, visible,
      color_scheme, available_attributes, inheriting_region_count, none_state_region_count,
      covering_layer_count}`. The last three exist so the panel can state the coupling instead
      of guessing (UI spec §5.4).
- [ ] `get_whole_details` returns composition + centroid **in the current playback frame** +
      `contains` / `is_composed_of`, request-id scoped, never streamed.
- **Acceptance:** each action has a handler test routing through the public method; the summary
  reports the three coupling counts correctly for a scene with mixed region states. Suite/build
  green.

---

## Phase 3 — Shared style composer extraction

**Size:** S · **Depends on:** Regions P1 · Refs: blueprint §5.4.

- [ ] Extract `regions-panel.ts::renderStyleComposer` into a shared component (representation
      select, preset select, opacity on `change`, quality, colour theme, Apply/Cancel),
      parameterised by its target. `RegionsPanel` consumes it; `WholePanel` will too.
- [ ] The component understands the three representation states of Contract A, including the
      `"inherit"` sentinel — which is meaningful for a region and **not** for the whole; the
      component hides it for the whole.
- **Acceptance:** Regions behaves identically before and after; unit tests unchanged except for
  import paths. Suite/build green.

---

## Phase 4 — The subpanel

**Size:** L · **Depends on:** 2, 3 · Refs: UI spec §2–§3.

- [ ] Replace `RoadmapPanel("whole", …)` (`group-panel.ts:321`) with a real `WholePanel`
      extending `BasePanel`, registered in the same one-line registry entry.
- [ ] **Section A** — presence & camera, with the state-**None** warning and confirmation
      before hiding (W4).
- [ ] **Section B** — representation via the shared composer, with the `N regions inherit`
      note.
- [ ] **Section C** — theme, uniform colour, colour-by-attribute (`palette`, `value_range`,
      `element`), `Reset colours` (base layer, annotated `covered by N region layers`), and a
      visually distinct `Reset ALL colours` with confirmation.
- [ ] **Section D** — lazy Inspect: composition, frame-accurate centroid, `contains` /
      `is_composed_of` — which have no GUI surface anywhere today.
- **Acceptance:** every capability of blueprint §2 is reachable from the GUI; hiding the whole
  warns when regions would vanish; changing the representation visibly repaints inheriting
  regions. Unit tests assert the emitted payloads. Suite/build green.

---

## Phase 5 — Colour-scheme migration out of System

**Size:** S · **Depends on:** 4 · Refs: blueprint §1.4.

- [ ] Remove the *Colour scheme* dropdown from `system-panel.ts:394-402` and the
      `onChangeColorScheme` callback threaded through `group-panel.ts:151,378` into
      `viewer-controller.ts:975-980`.
- [ ] The theme is now set through `set_whole_color_scheme` → `whole.set_color_scheme()` →
      Python state → message. It becomes serialisable (Contract C) and survives a reload.
- [ ] **System** keeps the strips, hover, pick and context menu. It loses only this control
      (W7).
- **Acceptance:** no frontend path mutates the molecular colour theme without going through
  Python. Suite/build green.

---

## Phase 6 — E2E validation

**Size:** S · **Depends on:** 4, 5.

- [ ] On Chromium + WebGL, alongside the Regions walkthrough: set a representation and see
      inheriting regions follow; drop the opacity and see a region show through; colour the
      whole by `b_factor`; verify **uncoloured atoms keep their structural theme and do not
      turn grey** (`region_contracts.md` §0.3); `Reset colours` leaves region layers standing;
      `Reset ALL colours` clears them; hide the whole and confirm the state-**None** regions
      vanish while `Inherit`/`Own` regions remain.
- [ ] Record browser version, GL environment, results and findings here.

---

## Cross-cutting

- [ ] Rebuild after TS changes: `cd molsysviewer/js && npm run build:runtime`.
- [ ] Keep the Python suite + `npm run test:js` green; add tests **with** each phase.
- [ ] Update the dashboard and Risks table as each phase lands.
- [ ] Correct the reference documents as you go.

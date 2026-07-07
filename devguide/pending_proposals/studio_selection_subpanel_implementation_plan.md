# Implementation Plan: Studio → Selection subpanel

**Status:** not started.
**Purpose:** a meticulous, checkable, phase-by-phase plan to implement the Studio →
Selection subpanel. Update the checkboxes, the **Progress dashboard**, and the **Risks**
table as work lands.

---

## Reference documents (read all three before starting)

The implementation is defined across three documents; each phase points to the
relevant sections:

1. **`studio_selection_subpanel.md`** — the **architectural blueprint**: the *what /
   how / why*, the interaction model (§3), the design layout (§4), reproducibility
   (§5), and the **verified backend contracts** (§6). Source of truth for Python calls
   and behaviour.
2. **`studio_selection_subpanel_ui_design.md`** — the **UI/UX + CSS spec**: the ASCII
   layout, component details (§2–§3), and the CSS design system / tokens (§4). Source
   of truth for the visual/interaction surface.
3. **`interaction_targets_and_selection.md`** — the **shared contract**: the
   `active_selection` state, the cross-cutting **set-operation vocabulary**, the
   **pending Subtract/Intersect extension**, and the temporal-dimension note. Owns
   anything shared across the five surfaces.

When these disagree, (1) and (3) win over (2); (2) never redefines backend calls — it
delegates to (1) §6.

---

## How to use this plan

- Each task is a checkbox: `- [ ]` open, `- [x]` done. Strike through (`~~task~~`) only
  if dropped, with a reason.
- A phase is **Done** only when its tasks are checked **and** its **acceptance
  criteria** pass **and** the Python suite + `npm run test:js` + `npm run build` are
  green.
- After each phase: update its **dashboard** row (status, date, commit SHA, notes) and
  the **Risks** table if anything changed.
- Report blockers inline under the phase (`> Blocker: …`).
- **Execution order = numeric order** (0 → 8). Dependencies are listed per phase; a
  phase should not start until its dependencies are ☑.

### Guardrails (project rules)

- **Never hand-edit** `molsysviewer/viewer.js` / `.map`; edit TS under
  `molsysviewer/js/src/` and run `npm run build`.
- Selection ops go through the public API (`view.active_selection`, `view.selections`);
  do **not** regrow viewer mutators.
- Backend ops resolve **on the Python side** so provenance is known there.
- Prefer **raw index lists** over building query strings for index-based ops
  (expansion, composition) — blueprint §6.2.

---

## Progress dashboard

| Phase | Title | Size | Depends on | Status | Date | Commit | Notes |
|------:|-------|:----:|:----------:|--------|------|--------|-------|
| 0 | Shared set-operation model | M | — | ☐ | — | — | foundational |
| 1 | Query composer + live preview | L | 0 | ☐ | — | — | |
| 2 | Modifier legend | S | — | ☐ | — | — | trivial; ride with any UI phase |
| 3 | Expand-to-level + spatial | M | 1 | ☐ | — | — | UI in Section B |
| 4 | Saved-selections manager | L | 0 | ☐ | — | — | |
| 5 | Guided chips + cheat-sheet | M | 1 | ☐ | — | — | typeahead optional |
| 6 | Undo / redo | M | — | ☐ | — | — | needs active_selection payload |
| 7 | Reproducibility (provenance) | L | 0, 1 | ☐ | — | — | |
| 8 | CSS design system | S | 1, 4 | ☐ | — | — | cosmetic layer |
| 9 | Feature-complete / integration | M | 0–8 | ☐ | — | — | e2e + docs closeout |

Size: **S** ≈ hours · **M** ≈ 1–2 days · **L** ≈ 3–5 days.
Status legend: ☐ Not started · ◐ In progress · ☑ Done · ✗ Dropped.

---

## Risks & unknowns

Update mitigations/owners as they are resolved.

| # | Risk | Phase(s) | Mitigation |
|---|------|:--------:|------------|
| R1 | **Live-preview cost** — spatial predicates (`within … of …`) resolve slowly; every debounce is a full `view.select` (count = resolve + `len()`, *not* cheaper than applying) | 1 | debounce ~250 ms + **cancelable** requests; consider skipping/limiting preview for heavy predicates; never block the kernel |
| R2 | **Index-space mismatch** — `active_selection` and `set()` operate in the molecular-system index space; when a subset is loaded the `IndexMapper` shifts indices | 3, 7 | use `view.molsys` + the `active_selection` level getters consistently; add a test with a subset-loaded system |
| R3 | **Reproducibility is best-effort** — composed replay may not perfectly reconstruct across large topology edits; shapes/annotations are **not** restored | 7 | default = frozen indices + stored expression; live/dynamic deferred; document the shapes/annotations limit; graceful, not silently wrong |
| R4 | **`Ctrl+Z`/`Ctrl+Y` clash** with browser/Jupyter shortcuts | 6 | bind only when the panel is focused; careful `preventDefault`; keep `↶ ↷` buttons as the primary affordance |
| R5 | **Set-op refactor regression** — replacing `additive: boolean` with an `op` enum touches shipped canvas interaction | 0 | keep `add` = the exact current toggle behaviour; unit tests on `setItems` before/after |

---

## Phase 0 — Shared set-operation model *(foundational)*

**Size:** M · **Depends on:** — · Refs: contract §"Set-operation vocabulary"; blueprint §3.

The set-operation vocabulary (Replace / Add / Subtract / Intersect / Invert) is
contract-owned and used by Phases 1, 3, 4, 7. Land it first.

- [ ] Contract: promote **Subtract / Intersect** from "pending extension" to decided in
      `interaction_targets_and_selection.md` (define exact semantics on `items` **and**
      the aggregate index arrays).
- [ ] Frontend (`js/src/managers/active-selection.ts`): replace the `additive: boolean`
      in `setItems(...)` with an `op: "replace"|"add"|"subtract"|"intersect"` enum
      (keep `add` = the current toggle behaviour; `range` stays a separate flag).
- [ ] Frontend (`js/src/managers/viewer-controller.ts`): thread `op` from
      `onSelect` / panel actions.
- [ ] Python (`molsysviewer/active_selection.py`): a `_combine(current, incoming, op)`
      helper returning the result per op — reused by every backend op below.
- **Acceptance:** `js/tests/unit/` covers `setItems` under each op (and `add` still
  toggles); `tests/test_active_selection.py` covers `_combine` for
  replace/add/subtract/intersect/invert.

---

## Phase 1 — Query composer + live preview *(biggest capability gain)*

**Size:** L · **Depends on:** 0 · Refs: blueprint §4B, §6.2–§6.3; UI §2 Section B, §3.B.

- [ ] Frontend (`js/src/ui/group-panel.ts`, `renderSelectionSection`): build **Section
      B** — query input + syntax dropdown (`MolSysMT | Indices`) + operation buttons
      `Select / +Union / −Subtract / ∩Intersect / ⤩Invert`.
- [ ] Frontend: **live validation badge** — debounce ~250 ms, **cancelable** request
      (discard stale responses), render `✓ N atoms` / `0 atoms` / `✗ invalid syntax`.
      Note: preview = resolve + count, same cost as applying minus the `set` (see R1).
- [ ] Backend (`molsysviewer/viewer/core.py`): op `apply_selection_query
      {expression, syntax, op}` → resolve via `view.select(...)` (MolSysMT) or pass raw
      indices for `syntax="Indices"` → `_combine` with current per `op` →
      `view.active_selection.set(result)` → echo `set_active_selection`. Errors →
      inline message, no state change.
- [ ] Backend: a **preview** op returning only the match count (no `set`, no echo) for
      the badge.
- **Acceptance:** each op from a query updates the active selection + strips/3D; an
  invalid query surfaces inline without changing state; `tests/test_active_selection.py`
  / relevant Python test covers `apply_selection_query` per op + the error path.

---

## Phase 2 — Modifier legend

**Size:** S · **Depends on:** — · Refs: blueprint §3.2–§3.3.

- [ ] Frontend: a small **modifier legend** near the strips (Replace / `Shift`=Add-
      toggle / `Shift`+`Alt`=Range). **No click-path code change** — the canvas idiom
      already exists in `active-selection.ts`.
- **Acceptance:** legend renders; clicks behave exactly as before.

---

## Phase 3 — Expand-to-level + spatial expander

**Size:** M · **Depends on:** 1 · Refs: blueprint §6.2 (verified call); UI §3.B.

- [ ] Frontend: **hierarchical expanders** `Group · Component · Molecule · Chain ·
      Entity` (the five supra-atomic levels), in Section B.
- [ ] Backend (`core.py`): op `expand_selection {level}` — **index-based, no query
      string**: `msm.get(view.molsys, element=level, selection=<level>_indices,
      atom_index=True)` (returns **list-of-lists** → flatten) →
      `active_selection.set(list)`. Operate in the molecular-system index space (R2).
- [ ] Frontend + backend: **spatial expander** — distance input (Å) → build the native
      MolSysMT query `"all within <X> angstroms of (current)"` → route through
      `view.select` (**not** contacts).
- **Acceptance:** expanding a partial selection to `group` returns whole groups;
  large-selection expansion does not stall; spatial expansion matches a manual `within`
  query. Python tests per level + spatial + one **subset-loaded** case (R2).

---

## Phase 4 — Saved-selections manager

**Size:** L · **Depends on:** 0 · Refs: blueprint §4C; UI §2 Section C, §3.C.

- [ ] Frontend: **Section C** rows — `Activate · +Union · −Sub · ∩Int · Rename ·
      →Region · →Label · Delete`, sorted by tag, count + level per row.
- [ ] Backend ops (`core.py`): `rename_selection {tag,new_tag}` →
      `selections[tag].set_tag`; `compose_saved_selection {tag, op}` → `_combine` saved
      indices with active per `op`; promote from a saved selection → `new_region` /
      `add_label`.
- [ ] **Name-collision policy:** backend already raises `ValueError` on a duplicate tag;
      frontend catches and offers **Rename / Overwrite / Cancel** (Merge secondary).
      Programmatic path may auto-increment (`pocket_1`).
- **Acceptance:** save/rename/compose/promote/delete all work; a duplicate tag triggers
  the collision UI, not an unhandled error. `tests/test_selections.py` covers the new
  ops + collision.

---

## Phase 5 — Guided chips + cheat-sheet

**Size:** M · **Depends on:** 1 · Refs: blueprint §4B, §6.3; UI §3.B.

- [ ] Frontend: **preset chips** `protein · water · backbone · sidechain · ligand` that
      inject the exact MolSysMT string into the query input.
- [ ] Frontend: collapsible **cheat-sheet** (`[?]`) with common examples.
- [ ] *(optional)* **system-value typeahead** — suggest residue/chain names present in
      the loaded structure after `group_name in` / `chain_name ==`.
- **Acceptance:** a chip fills the exact syntax; cheat-sheet toggles; the injected
  strings validate against `view.select`.

---

## Phase 6 — Undo / redo

**Size:** M · **Depends on:** — (needs the `active_selection` payload) · Refs: blueprint §4A, §5; UI §3.A.

- [ ] Frontend: **bounded history** (~10 states) of `active_selection`, managed **in
      TS** (zero-latency); `↶ ↷` buttons + `Ctrl+Z`/`Ctrl+Y` **only when the panel is
      focused** (R4).
- [ ] Frontend: **History Invalidation** — clear the history stack on
      `apply_system_edit` / load, so stale indices are never restored.
- **Acceptance:** undo/redo restore prior selections; an accidental clear is
  recoverable; a system rebuild empties the stack. `js/tests/unit/` covers the stack +
  invalidation.

---

## Phase 7 — Reproducibility (provenance)

**Size:** L · **Depends on:** 0, 1 · Refs: blueprint §5, §6.2; contract (temporal note).

- [ ] Backend: **extend persistence** — the `save_selection` op + `_store_selection_record`
      + the `Selection` record gain an optional `(expression, syntax)` provenance field
      (index-only today, `molsysviewer/selections.py`).
- [ ] Backend: **recipe model** on `active_selection` — an ordered list of steps (each
      `op` + source: expression | static indices); replay re-applies **each step with
      its own operation** (query steps re-evaluate; interaction steps remap via
      `atom_index_map`).
- [ ] **Persistence limit** (R3): saved selections reactivate by atom indices and do
      **not** restore shapes/annotations as objects — ensure this is graceful.
- **Acceptance:** a query-based named selection re-evaluates after `apply_system_edit`;
  a composed selection replays each step correctly; `tests/test_selections.py` /
  `tests/test_active_selection.py` cover provenance round-trip + replay.

---

## Phase 8 — CSS design system

**Size:** S · **Depends on:** 1, 4 · Refs: UI §4.

- [ ] Frontend: apply the **tokens** (`--bg-sidebar`, `--accent-indigo`,
      `--accent-indigo-glow`, …), glassmorphic active card, focus glow on the query
      input, saved-row hover/active animations.
- [ ] Ensure the **dark-mode aesthetic** matches the rest of the viewer.
- **Acceptance:** the subpanel matches the UI spec's look and renders in the viewer's theme.

---

## Phase 9 — Feature-complete / integration

**Size:** M · **Depends on:** 0–8 · The global closeout.

- [ ] **End-to-end walkthrough** (ideally an e2e in `js/tests/e2e/`): build a selection
      by query → compose with a click and a saved selection (union/subtract) → expand to
      chain → save → rename → promote to region → undo/redo. All green.
- [ ] Update the **three reference documents**: flip the contract's Subtract/Intersect
      from "pending" to "done" (Phase 0); tick blueprint §10 slices; note the subpanel
      as implemented.
- [ ] Full Python suite + `npm run test:js` + `npm run build` green; `viewer.js`
      regenerated.
- **Acceptance:** the subpanel delivers the five capabilities of blueprint §1.2 end to
  end, on a real system, with tests guarding each.

---

## Cross-cutting (every phase)

- [ ] Rebuild the bundle after TS changes: `cd molsysviewer/js && npm run build`
      (regenerates `viewer.js`); never edit it by hand.
- [ ] Keep the Python suite + `npm run test:js` green; add tests with each phase.
- [ ] Update the dashboard row + Risks table as each phase lands.

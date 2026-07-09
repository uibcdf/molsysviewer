# Implementation Plan: Studio → Selection subpanel refinements (A + B)

**Status:** implemented (2026-07-09). Runtime rebuilt and unit tests green; browser
execution of the Selection E2E remains deferred to the broader Phase 9 validation.
**Purpose:** a meticulous, checkable, phase-by-phase plan to implement the two
refinements in `studio_selection_subpanel_refinements.md`:

- **Part A** — replace the per-keystroke debounced query preview with **manual
  verification** (`Check` button / `Enter`; idle while typing).
- **Part B** — move the hierarchical + spatial **selection expanders** out of the
  sidebar into the canvas right-click **context menu**.

The checkboxes, **Progress dashboard**, and validation notes below reflect the
implemented state.

---

## Reference documents (read before starting)

1. **`studio_selection_subpanel_refinements.md`** — the proposal: the two problems,
   Part A / Part B design, and the interaction flows. Source of truth for *what/why*.
2. **`studio_selection_subpanel.md`** (+ its UI spec) — the Selection subpanel blueprint:
   query composer, set-operation vocabulary, expansion semantics.
3. **Implemented code** — after the Studio panel-per-module refactor and this
   refinement:
   - `molsysviewer/js/src/ui/query-composer.ts` — the shared **`ManualQueryComposer`**
     (Check/Enter, no traffic while typing, stale-response rejection). Used by both
     `RegionsPanel` and `SelectionPanel`.
   - `molsysviewer/js/src/ui/panels/selection-panel.ts` — uses the shared manual
     composer and no longer renders the sidebar expander panel.
   - `molsysviewer/js/src/ui/context-menu.ts` — exposes active-selection expanders
     and spatial presets.
   - Backend action **`expand_selection`** already exists (`core.py`).

---

## Guardrails (project rules)

- **Branch first.** `main` is the current branch; create a feature branch before any
  commit (the refactor merged to `main`, so start clean off it).
- **Never hand-edit** `molsysviewer/viewer.js` / `.map`; edit TS under
  `molsysviewer/js/src/` and run `npm run build:runtime`. Reserve `npm run build` for
  release/packaging.
- Selection ops go through the public API / existing actions (`apply_selection_query`,
  `expand_selection`, `selection_query_preview_request`); do not invent new backend ops —
  both actions already exist.
- **Reuse the shared `ManualQueryComposer`**; do not fork a second manual composer.
- Keep behavior identical except the two deliberate changes (manual preview; expanders in
  the context menu).
- Each phase: `npm run build:runtime` + `npm run test:js` green before the next.

---

## Design decisions (resolved)

1. **Chips → `setExpression` on the shared composer.** Extend `ManualQueryComposer` with
   `setExpression(expression, syntax?)` so preset chips inject text. Reusable (Regions
   could adopt chips later); cleaner than wrapping.
2. **Data-attrs = the shared composer's** (`data-molsysviewer-query-*` with
   `scope="selection"`) for input/check/syntax/status. The **operation buttons**
   (`data-molsysviewer-selection-query-apply`), **chips**, and **cheat-sheet** keep their
   own attrs. Only input/check/syntax/status attrs change → tests updated accordingly.
3. **Apply does not require Check.** `Check`/`Enter` only drives the **preview**; the
   operation buttons apply by reading `composer.value()` (the backend validates on apply).
   Minimal, faithful to the proposal (which only changes the per-keystroke preview).
4. **A and B in one branch, separate phases/commits** — independent, each testable.
5. **Preview request IDs.** `ManualQueryComposer` uses a global static counter
   (starts at 1,000,000), so the Selection and Region composers never collide; the
   existing `GroupPanel.updateSelectionQueryPreview` routing (region first, else selection)
   keeps working.
6. **Operation-button gating (Part A).** Apply never requires `Check` (Decision 3); the
   operation buttons are enabled whenever the input is **non-empty** (independent of
   verification), matching today's behavior.
7. **Spatial expander in a menu (Part B).** A context menu is a click list, not a form.
   Ship the **distance presets (3 / 5 / 8 Å) as menu buttons** first; a **custom** value
   uses the menu's existing inline-composer/input affordance and is an optional, second
   iteration. Do not block Part B on the custom input.
8. **Reuse existing actions in the menu.** `Clear Active Selection` maps to the existing
   `clear_selection` action; `expand_selection` already exists. No new backend ops.

---

## Progress dashboard

| Phase | Title | Size | Depends on | Status | Date | Commit | Notes |
|------:|-------|:----:|:----------:|--------|------|--------|-------|
| A0 | Extend shared composer (`setExpression`) | S | — | ☑ | 2026-07-09 | pending | enables chip injection; styled Check/syntax controls |
| A1 | Migrate Selection to the shared composer | M | A0 | ☑ | 2026-07-09 | pending | op buttons/chips/cheat-sheet re-wired; debounce removed |
| A2 | Tests (unit + e2e) for manual verification | S | A1 | ☑ | 2026-07-09 | pending | unit attrs updated; E2E source switched to Check/Enter and compile-checked |
| B0 | Confirm context-menu selection plumbing | XS | — | ☑ | 2026-07-09 | pending | ActiveSelectionPayload and emit path reused |
| B1 | Add expanders to the context menu | M | B0 | ☑ | 2026-07-09 | pending | Expand-to-level + 3/5/8 Å spatial presets + empty-canvas Clear |
| B2 | Remove sidebar expander panel | S | B1 | ☑ | 2026-07-09 | pending | sidebar test replaced by absence check; context-menu test covers actions |
| B3 | Closeout | S | A2, B2 | ☑ | 2026-07-09 | pending | `npm run test:js`, `npm run build:runtime`, and E2E esbuild compile passed |

Size: **S** ≈ hours · **M** ≈ 1–2 days.
Status legend: ☐ Not started · ◐ In progress · ☑ Done · ✗ Dropped.

---

## Risks & unknowns

| # | Risk | Phase(s) | Mitigation |
|---|------|:--------:|------------|
| R1 | **Query-test churn** — data-attrs + debounce→manual flow | A2 | scoped to the ~5 Selection query unit tests + the e2e query step; mechanical |
| R2 | **Apply parity** — re-wired op buttons must emit identical `apply_selection_query {expression, syntax, op}` | A1 | assert the emitted payload in unit tests before/after |
| R3 | **Context menu selection state** for the empty-canvas case | B0 | **already satisfied**: `context-menu.ts` receives `ActiveSelectionPayload` and has an active-selection section keyed on `count_groups`; B0 is confirm-and-reuse, not new wiring |
| R6 | **Spatial custom distance in a menu** — menus are click lists, not forms | B1 | presets (3/5/8 Å) as buttons first; custom value via the existing inline affordance, optional (Decision 7) |
| R4 | **Preview routing** — both composers share the `selection_query_preview` channel | A1 | rely on the global static request-id (region ≥ 1,000,000); verify each composer only accepts its own id |
| R5 | **Cross-product** — same `viewer.js` runs in Jupyter and standalone | all | no product-specific code; verify once, benefits both |

---

## PART A — Manual query verification

### Phase A0 — Extend the shared composer

- [x] `query-composer.ts`: add `setExpression(expression: string, syntax?: QuerySyntax)` —
      set the input value, update internal expression, reset the preview to `idle`, and
      optionally force the syntax.
- [x] `query-composer.ts`: apply CSS styling to `checkButton` and `syntaxSelect` in the constructor
      to match the dark glassmorphic design system of the Studio panel (secondary button styles
      for Check, styled border/background for the syntax dropdown).
- **Acceptance:** a unit test asserts `setExpression` updates the input and resets status
  to idle; controls are styled consistently with the rest of the application; `npm run test:js` green.

### Phase A1 — Migrate Selection to the shared composer

- [x] `SelectionPanel`: cache a `ManualQueryComposer("selection", details =>
      this.ctx.onAction("selection_query_preview_request", details))` (mirroring
      `RegionsPanel.getRegionQueryComposer`).
- [x] Rebuild `renderSelectionQueryComposer` to use `composer.element()` as the core
      (input + Check + syntax + status) and re-wire around it:
  - **Operation buttons** (Select/Union/Subtract/Intersect): on click, read
    `composer.value()` → emit `apply_selection_query {expression, syntax, op}`. Enabled
    whenever the input is non-empty; no forced `Check` (Decision 6).
  - **Preset chips**: `composer.setExpression('molecule_type=="protein"', "MolSysMT")`.
  - **Cheat-sheet `[?]`**: kept (Selection-owned), injects via `setExpression`.
- [x] `SelectionPanel.updatePreview(preview)` → delegate to `composer.updatePreview(preview)`
      (like Regions); drop the `selectionQueryPreviewRequest` routing.
- [x] Remove the debounced composer: `scheduleSelectionQueryPreview`,
      `selectionQueryPreviewTimer`, and the `selectionQueryExpression / selectionQuerySyntax
      / selectionQueryPreviewRequest / selectionQueryPreview` fields.
- **Acceptance:** typing sends no requests (idle); `Check`/`Enter` shows
  `✓ N / 0 atoms / ✗ invalid syntax`; operation buttons apply; chips inject; JS
  tests and runtime build are green.

### Phase A2 — Tests

- [x] Unit (`group-panel.test.ts`): update the Selection query tests to the shared
      composer's attrs and the manual flow (Check/Enter, not debounce). Explicit attr
      mapping: input/check/syntax → `data-molsysviewer-query-{input,check,syntax}="selection"`;
      status → `data-molsysviewer-query-status-value` (idle/pending/ok/empty/error). The
      operation buttons keep `data-molsysviewer-selection-query-apply`. Affected tests:
      "query composer emits apply", "query preview pending/error", "presets inject",
      "cheat-sheet toggles", "query preview uses dedicated action".
- [x] E2E (`selection-subpanel.e2e.ts`): switch the query step to Check/Enter.
- **Acceptance:** `npm run test:js` green; `npm run build:runtime` green.

---

## PART B — Expanders to the context menu

### Phase B0 — Confirm the context-menu selection plumbing *(mostly already there)*

- [x] Confirm (verified during planning): `context-menu.ts` already receives
      `ActiveSelectionPayload` and already renders an active-selection section keyed on
      `count_groups`, and already emits actions via `makeActionButton(label, action,
      extraDetails?)`. So the state + emit plumbing exists; this phase is confirm-and-reuse.
- **Acceptance:** no code change needed beyond confirming the payload/emit path; the menu
  can gate the expanders on active-selection emptiness and emit `expand_selection`.

### Phase B1 — Add the expanders to the context menu

Reuse the existing **section + `makeActionButton(label, action, extraDetails?)`** pattern
(the same one used for `Distance (Representative Atom)`).

- [x] `context-menu.ts`, **structure** target (atom/residue): an **"Expand Selection to…"**
      section with `Group / Component / Molecule / Chain / Entity` →
      `makeActionButton(level, "expand_selection", { level })`.
- [x] A **"Spatial Expansion…"** section: `within X Å` **preset buttons (3 / 5 / 8 Å)** →
      `expand_selection {level: "spatial", distance_angstroms}`. Custom value is optional
      (Decision 7 / R6) via the menu's inline affordance — not required to ship B1.
- [x] **Empty-canvas** target with a non-empty active selection: the same sections plus
      `Clear Active Selection` (reusing the existing `clear_selection` action).
- **Acceptance:** right-click shows the expanders; they emit `expand_selection` (backend
  action already exists) and, on empty canvas, `clear_selection`; context-menu unit tests
  cover them.

### Phase B2 — Remove the sidebar expander panel

- [x] `SelectionPanel`: remove `renderExpander` / the `data-molsysviewer-selection-expander-panel`
      block (levels + spatial).
- [x] Move the "selection expanders emit hierarchical and spatial actions" test from the
      sidebar (`group-panel.test.ts`) to the context-menu tests.
- **Acceptance:** the Selection sidebar is cleaner; expanders work from the menu; tests green.

### Phase B3 — Closeout

- [x] `npm run test:js` + `npm run build:runtime` green,
      `viewer.js` regenerated.
- [x] **Doc consistency:** update `studio_selection_subpanel.md` §4B to reflect the
      **manual verification** composer (no live per-keystroke preview) and the **expanders
      relocated to the context menu** — the blueprint currently describes the sidebar
      live-preview composer and sidebar expanders.
- [x] Flip `studio_selection_subpanel_refinements.md` status to *implemented*.

---

## Cross-cutting (every phase)

- [x] Rebuild the bundle after TS changes: `cd molsysviewer/js && npm run build:runtime`;
      never edit `viewer.js` by hand.
- [x] Keep `npm run test:js` green; add/adjust tests with each phase.
- [x] Update the dashboard row + Risks table as each phase lands.

**Execution order:** A0 → A1 → A2 (Part A closed & committed) → B0 → B1 → B2 → B3.

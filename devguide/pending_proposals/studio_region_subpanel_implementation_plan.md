# Implementation Plan: Studio → Regions subpanel

**Status:** implemented (Phases 0-D complete; post-Phase-D browser E2E validation pending).
**Purpose:** a meticulous, checkable, phase-by-phase plan to implement the Studio →
Regions subpanel. Update the checkboxes, the **Progress dashboard**, and the **Risks**
table as work lands.

---

## Reference documents (read all three before starting)

1. **`studio_region_subpanel.md`** — the **architectural blueprint**: *what / how / why*,
   the lifecycle model (§3), the design layout (§4), the **verified backend contracts**
   (§6), non-API additions (§8). Source of truth for Python calls and behaviour.
2. **`studio_region_subpanel_ui_design.md`** — the **UI/UX + CSS spec**: ASCII layout,
   component details (§2–§3), CSS tokens (§4), sync notes (§5). Source of truth for the
   visual/interaction surface.
3. **`studio_selection_subpanel.md`** (+ its UI spec) — the **sibling contract**: the
   query composer, collision policy, rename idiom, and design tokens this subpanel
   **reuses**. Do not fork them.

When these disagree, (1) wins over (2); (2) never redefines backend calls — it delegates
to (1) §6. Region-specific vocabulary aligns with (3) so the two subpanels feel like one.

---

## How to use this plan

- Each task is a checkbox: `- [ ]` open, `- [x]` done. Strike through (`~~task~~`) only if
  dropped, with a reason.
- A phase is **Done** only when its tasks are checked **and** its **acceptance criteria**
  pass **and** the Python suite + `npm run test:js` + `npm run build:runtime` are green.
- After each phase: update its **dashboard** row (status, date, commit SHA, notes) and the
  **Risks** table if anything changed.
- **Execution order = numeric order** (A → C, with 0 first). Dependencies are listed per
  phase.

### Guardrails (project rules)

- **Never hand-edit** `molsysviewer/viewer.js` / `.map`; edit TS under
  `molsysviewer/js/src/` and run `npm run build:runtime` for development rebuilds.
  Reserve `npm run build` for release/packaging version sync.
- Region ops go through the public API (`view.new_region`, `view.regions`, `region.*`);
  do **not** regrow viewer mutators.
- Backend ops resolve **on the Python side** so provenance/naming are known there.
- **Reuse** the Selection subpanel's query composer, collision policy, and CSS tokens —
  do not fork them.
- Prefer **raw index lists / registry lookups** over building query strings for
  index-based ops (composition, split).

---

## Progress dashboard

| Phase | Title | Size | Depends on | Status | Date | Commit | Notes |
|------:|-------|:----:|:----------:|--------|------|--------|-------|
| 0 | Public API + backend ops + summary | M | — | ☑ | 2026-07-09 | — | public API, handlers, batch protocol, optimized enriched summary, lazy details and acceptance coverage complete |
| A | Create, isolate & lifecycle | L | 0 | ☑ | 2026-07-09 | — | shared manual query composer; three create origins; lifecycle cards; explicit collision choices; global batch actions |
| B | Enriched style composer | M | 0 | ☑ | 2026-07-09 | — | backend-provided reps/presets; release-only opacity; quality; curated/uniform/attribute color |
| C | Boolean composer & inspection | M | 0, A | ☑ | 2026-07-09 | — | ordered boolean composer; overlap prefill; safe overwrite; lazy frame-aware inspect |
| D | CSS + integration / e2e | S | A, B, C | ☑ | 2026-07-09 | `6f66da07` | shared tokens; inspect refresh; overlap focus; E2E walkthrough implemented; docs updated |
| Post-D | Real browser E2E validation | S | D | ☐ | — | — | run the Regions walkthrough on Chromium + WebGL and record the result |

Size: **S** ≈ hours · **M** ≈ 1–2 days · **L** ≈ 3–5 days.
Status legend: ☐ Not started · ◐ In progress · ☑ Done · ✗ Dropped.

---

## Risks & unknowns

| # | Risk | Phase(s) | Mitigation |
|---|------|:--------:|------------|
| R1 | **Overlap computation cost** — `_overlapping_visual_region_tags` is O(regions × atoms); recomputing on every summary could get heavy with many large regions | 0, A | resolved for summaries: build each visible atom set once and compare each pair once; only consider manageable visible represented regions |
| R2 | **Index-space** — region atom sets live in the `_molsys` index space; splits/composition/attribute color must stay in it | 0, A, B, C | use `view.regions[...]` atom sets and `_molsys` consistently; add a subset-loaded test |
| R3 | **Transient-region leakage** — `orientation-`/`plane-` **and `focus`** regions would appear in the list (`styles.focus()` registers `focus<n>` regions, verified) | 0, A | filter tags `^(orientation-\|plane-\|focus)\d+` from the summary/list; test that overlay + `styles.focus()` do not add a manageable card (P1) |
| R4 | **Color-by-attribute mapping & availability** — attribute may be absent for the format (`.xyz`/`.gro`/`.xtc`) or None for some atoms | 0, B | expose only **present** attributes via summary `available_attributes` (load-time probe); reuse `expand_values_to_atoms`; guard None; auto-range; test with bfactor present/absent (P3) |
| R5 | **Composer staleness** — Section C dropdowns must track create/delete/rename | C | rebuild dropdowns from the live region list on every summary update |
| R6 | **Preset vs representation precedence** — choosing a preset supersedes representation; UI could send both | B | mutually exclusive controls; preset clears representation selection and vice-versa |
| R7 | **Opacity IPC flood** — dragging the slider fires dozens of `input`/s → message backlog/lag | B | update readout on `input`; **fire `set_region_representation` on `change` (mouseup)** — one message per release; optional throttle only for live 3D preview (P2). NB: per-keystroke debounce is *wrong* for the query composer but `change`/mouseup is *right* for a slider (all values valid) |
| R8 | **Bulk-op flicker** — `show_all`/`hide_all`/split emit one message + summary per region | A | backend **batch context** (`_batch_updating`) suppressing per-item signals (incl. `@signal`), one consolidated summary; medium priority, non-blocking (P6) |
| R9 | **Inspection cost** — centroid/composition per region on every summary is expensive and frame-dependent | C | fetch lazily via `get_region_details {tag}` on `ⓘ` open; centroid in current frame; keep out of the summary (P5) |
| R10 | **Shared query composer vs paused Selection** — Region implements the manual-verification composer (Option B) that the paused Selection refinements (Part A) will inherit; risk of divergence if Selection is later changed independently | A | build it as **one shared component**; when Selection resumes it adopts the component instead of re-implementing; do not fork the debounced version |

---

## Phase 0 — Public API + backend ops + summary *(foundational)*

**Size:** M · **Depends on:** — · Refs: blueprint §6.2–§6.5, §8.

Complete the **public Python API first** (so the GUI routes through it, never past it),
then land the event handlers and the extended summary; the UI phases build on these.

- [x] **Public API (`molsysviewer/regions.py`) — new methods (§6.5)**, each
      `@signal @digest`, operating in the `_molsys` index space (R2):
  - [x] `Region.reset_representation()` — revert this region to the base representation.
  - [x] `Region.set_color_by_attribute(attribute, *, element="atom", palette="viridis",
        value_range=None, replace=False)` — `msm.get(attribute)` → `set_color_by_values`;
        guard missing/None values (R4).
  - [x] `Region.duplicate(*, tag=None, representation=None, **repr_params)` — clone atoms
        + representation.
  - [x] `Region.overlaps()` → `list[str]` (public wrapper over
        `_overlapping_visual_region_tags`).
  - [x] `RegionsManager.show_all()` / `hide_all()` — batch visibility.
  - [x] extend `make_regions_by` to `group | component` as an
        **API-only** extension (not a one-click GUI action; §6.5 note).
- [x] Backend (`core.py`): add ops `create_region_from_query`, `make_regions_by`,
      `show_only_region`, `create_complementary_region`, `compose_regions`,
      `reset_region_representation`, `color_region_by_attribute`, `duplicate_region`,
      `show_all_regions`, `hide_all_regions`, and `get_region_details {tag}` (lazy
      inspection, P5/R9) — **each routing through the public API method above** (existing or
      new), echoing an updated region summary (blueprint §6.2).
- [x] Backend: **batch-update context** (`_batch_updating`, blueprint §6.6) suppressing
      per-item scene messages and intermediate summaries during
      `show_all`/`hide_all`/`make_regions_by`, while preserving SMonitor `@signal`
      breadcrumbs; emit one consolidated summary (R8, P6).
- [x] Backend/summary: extend the region summary with `representation`, `preset`,
      `overlap_tags` (via `Region.overlaps()`), and **`available_attributes`** (load-time
      probe of which structural attributes exist, P3/R4); **filter** transient tags
      `^(orientation-|plane-|focus)\d+` (R3, P1). Keep centroid/composition **out** of the
      summary (fetched via `get_region_details`, R9).
- **Acceptance:** `tests/test_regions.py` (new; today region tests live in
  `tests/regions/test_region_flow.py`) covers the **new public API methods directly**
  (reset repr, color-by-attribute, duplicate, overlaps, show/hide all) **and** each op
  routing through them (compose per operator, complement tag default `Global-<tag>`, split
  per element), plus the summary fields, transient-tag filter (incl. `styles.focus()`),
  `available_attributes`, `get_region_details`, and a **subset-loaded** case (R2).
  Python suite + `npm run test:js` + `npm run build:runtime` green.

  Completion note 2026-07-09: Public
  `Region` now exposes reset, color-by-attribute, duplicate, and overlap operations;
  `RegionsManager` exposes overlap and single-message show/hide-all operations. The
  frontend handlers accept `set_regions_visibility` and an authoritative runtime-only
  `set_region_summaries` payload. Context actions cover query creation, split,
  isolate, complement, boolean composition, reset/color/duplicate, global visibility,
  and lazy frame-specific details. Summaries include representation, preset,
  overlap tags, populated scalar attributes, and filter actual generated
  `focusN`/`orientation-regionN`/`plane-regionN` tags. Validation:
  `tests/regions/test_region_flow.py` passed (21 tests), `npm run test:js` passed
  (149/149), `npm run build:runtime` passed, and the full Python suite passed
  (3 skipped). `make_regions_by` now records one reproducible
  `batch_region_operations` message and emits one runtime summary; SMonitor
  breadcrumbs remain active because they are observability, not scene IPC.
  Summary overlap detection constructs each visible atom set once and compares each
  pair once. Handler coverage includes union/intersection/ordered difference, and a
  subset-loaded regression confirms `_molsys` local index-space behavior.

  Deliberate contract changes: `new_region(tag=...)` now raises on an existing tag
  instead of silently replacing the registry entry, matching the documented collision
  policy; overwrite remains delete-then-create. `RegionsManager` is now viewer-bound
  (`RegionsManager(view)`) so its public batch methods can send through the owning
  transport. Repository callers were audited; direct external construction was never
  a supported workflow.

---

## Phase A — Create, isolate & lifecycle *(biggest capability gain)*

**Size:** L · **Depends on:** 0 · Refs: blueprint §4A–§4B; UI §2 A/B, §3 A/B.

- [x] Frontend (`group-panel.ts`, `renderRegionsSection`): **Section A** — create composer
      with the three origins: from active selection; from query via the **shared
      manual-verification composer** (`Check`/`Enter`, `idle` while typing — Option B, **not**
      debounced preview; R10); split by hierarchy. Optional name + initial repr. Global
      `Show all` / `Hide all` fire a **single** action → public `RegionsManager.show_all()` /
      `hide_all()` → **single** consolidated summary (no per-region iteration; R8).
- [x] Frontend: **region cards** replacing the flat rows — header (focus, count, repr
      hint, visibility, delete), quick actions (Isolate, Complement, Rename inline,
      Duplicate, Reset repr), and the **⚠ overlap badge** (opens Section C pre-filled with
      Difference — Phase C wires the composer; here the badge + tooltip render).
- [x] Frontend: **name-collision policy** (Rename / Overwrite / Cancel) on **single**
      create / rename, reusing the Selection idiom; the **split path auto-increments
      silently** (no prompt — backend already resolves via `_unique_region_tag`, P4).
- [x] Frontend: `Show all` / `Hide all` apply the single consolidated summary from the
      backend batch context (R8) — one update, not one per region.
- **Acceptance:** create a region by each origin; split yields several cards **without a
  collision prompt**; isolate, complement, rename, duplicate, reset work; the overlap badge
  appears for overlapping visible regions; `styles.focus()` overlays do **not** appear as
  cards. `js/tests/unit/group-panel.test.ts` covers that each control emits the correct
  action; Python covers the handlers (Phase 0). Suite/build green.

  Completion note 2026-07-09: `ManualQueryComposer` is a reusable component with
  explicit `Check`/Enter verification, request IDs, stale-response rejection, and no
  traffic while typing. Section A supports active selection, verified query, and
  hierarchy split origins, optional tag and initial representation, plus single-action
  show/hide-all controls. Region cards expose focus, visibility, delete, isolate,
  complement, inline rename, duplicate, representation reset, style entry, and overlap
  metadata. Single create and rename collisions render explicit Rename / Overwrite /
  Cancel choices; split remains prompt-free. The active-selection handler now applies
  the requested initial representation. Validation: region flow tests passed (22),
  JavaScript tests passed (151/151), `npm run build:runtime` passed, and the full Python
  suite passed with 3 skips.

  Post-review refinements: the overlap warning is non-interactive until Phase C gives it
  a real destination; `Base` is the default initial style and omits `representation`
  from the action payload; Split hides the inapplicable name field. Selection still
  uses its existing composer while that subpanel is paused. Its later refinement must
  adopt `ManualQueryComposer`; Regions does not duplicate that implementation.

---

## Phase B — Enriched style composer

**Size:** M · **Depends on:** 0 · Refs: blueprint §4B (style), §6.3, §8; UI §3.B.

- [x] Frontend: replace the 5-representation composer with the **12** real types
      (`view.representations`) + a **preset** select (`view.presets`; mutually exclusive
      with representation, R6).
- [x] Frontend: **opacity** slider (`alpha`) and **quality** dropdown — sent as `params`;
      verified to pass through to Mol\* `typeParams` (blueprint §6.3, no protocol change).
      **Fire the opacity IPC on `change` (mouseup)** — one message on release, not per value;
      update the numeric readout live on `input` (R7, P2). Optional throttle only if live 3D
      feedback is later wanted.
- [x] Frontend: **color** — scheme select + uniform color picker, **Color by** attribute
      dropdown (`color_region_by_attribute`) **gated to `available_attributes`** so only
      present attributes are offered (R4, P3), and **Reset colors** (`reset_colors`).
- **Acceptance:** changing representation/preset/opacity/quality/color updates the region
  in 3D; an opacity drag emits a **single** `set_region_representation` on `change` (mouseup),
  not one per intermediate value; color-by-attribute colors by bfactor **and** the dropdown
  hides absent attributes; reset reverts. Unit tests assert the emitted
  `set_region_representation` / `color_region_by_attribute` payloads and the fire-on-`change`
  behaviour. Suite/build green.

  Completion note 2026-07-09: the style composer consumes the complete representation
  and preset vocabularies supplied by Python, including user presets, and keeps the two
  controls mutually exclusive. The runtime-only region summary now carries those
  vocabularies at message level and each region's `representation_params`, allowing the
  editor to preserve existing representation-specific settings. Opacity updates its
  readout on `input` but emits only on `change`; quality, curated structural schemes,
  uniform color, available-attribute coloring, and color reset are wired. The backend
  context-action handler now forwards `preset` to the public API. Validation: region
  flow tests passed (23), JavaScript tests passed (152/152),
  `npm run build:runtime` passed, and the full Python suite passed with 3 skips.

  Post-review refinements: the composer separates style controls committed by
  `Apply Style` from immediate adjustments. Opacity now applies only to the region's
  committed representation/preset and cannot accidentally commit a representation
  selected in the draft. Inspection of the authoritative local Mol* source
  (`~/repos@others/molstar/src/mol-plugin-state/builder/structure/representation-preset.ts`)
  confirms that preset `quality` and global themes are supported, while `alpha` is not
  a common preset parameter. `StateHandlers` therefore updates `type.params.alpha` on
  every representation generated by a preset in one state-tree commit. Unit coverage
  verifies both this update and draft isolation; JavaScript validation is now 153/153.

---

## Phase C — Boolean composer & inspection

**Size:** M · **Depends on:** 0, A · Refs: blueprint §4C–§4D; UI §2 C, §3.C.

- [x] Frontend: **Section C** boolean composer — Region A · operator (∪ ∩ −) · Region B ·
      output name → `compose_regions`; dropdowns refresh on create/delete/rename (R5).
      Difference labeled as ordered `A − B`.
- [x] Frontend: wire the **⚠ overlap badge** (Phase A) to open Section C pre-filled with
      Difference for the overlapping pair.
- [x] Frontend: per-card **Inspect (ⓘ)** panel — composition + geometric center fetched
      **lazily** via `get_region_details {tag}` on expand (not from the summary), centroid in
      the **current playback frame** (R9, P5).
- **Acceptance:** composing two regions creates the expected region (per operator); the
  overlap badge pre-fills Difference; inspect fetches on demand and shows composition +
  frame-accurate center. Unit + Python tests cover compose per operator and the
  `get_region_details` path (incl. centroid per frame). Suite/build green.

  Completion note 2026-07-09: Section C tracks the live region registry and exposes
  ordered union, intersection, and `A - B` difference with optional output naming.
  Overlap badges prefill Difference for the first overlapping pair. Composition
  collisions use an explicit Rename / Overwrite / Cancel flow; overwrite is executed
  safely in Python by composing under a temporary tag before deleting and renaming, so
  the destination may also be one of the operands. Inspect requests are lazy,
  request-ID scoped, and ignore stale or closed-panel responses. The panel shows atom,
  group, and chain composition plus the center and current frame. Validation: region
  flow tests passed (24), including a real `pentalanine` frame-1 centroid; JavaScript
  tests passed (155/155), `npm run build:runtime` passed, and the full Python suite
  passed with 3 skips before the final trajectory test was added (the focused region
  suite was rerun afterward).

---

## Phase D — CSS design system + integration / e2e

**Size:** S · **Depends on:** A, B, C · Refs: UI §4; blueprint §7.

- [x] Frontend: apply the **region tokens** (`.region-card`, `.region-overlap-badge`,
      `.region-opacity-slider`, `.region-style-composer`), reusing the shared Selection
      tokens; dark-mode/theme-aware.
- [x] **Implement and integrate the end-to-end walkthrough**
      (`js/tests/e2e/region-subpanel.e2e.ts`): create from
      query → split by chain → style (opacity + color-by-attribute) → isolate → compose
      (difference) → complement → rename → inspect → delete. Browser execution as
      feasible (Chromium/WebGL), otherwise transport-contract simulation like the
      Selection e2e.
- [x] Update the **three reference documents**: flip statuses to *implemented*; note the
      subpanel as done.
- [x] Full Python suite + `npm run test:js` + `npm run build:runtime` green; `viewer.js`
      regenerated.
- **Acceptance:** the subpanel delivers the five capabilities of blueprint §1.2 end to
  end, on a real system, with tests guarding each.

  Completion note 2026-07-09: Regions now reuses the Studio design tokens for cards,
  overlap warnings, style controls, and structured inspection. The overlap action
  scrolls to and highlights the prefilled boolean composer. Inspect remains
  intentionally non-streaming during playback and exposes an explicit current-frame
  Refresh action. The Playwright walkthrough covers query creation, split, opacity,
  attribute color, isolate, Difference, complement, rename, lazy inspect, and delete;
  it is integrated into the E2E scripts and compiles successfully. Per repository
  policy, browser/WebGL execution remains a manual environment validation rather than
  a local CI-style run. Final validation: region flow tests passed (24), JavaScript
  tests passed (155/155), `npm run build:runtime` passed, the dedicated E2E bundle
  compiled, and the full Python suite passed with 3 skips.

---

## Post-Phase D — Real browser E2E validation

**Status:** pending · **Depends on:** D.

- [ ] On a host with a real Chromium/Chrome installation and working WebGL, run:

  ```bash
  cd molsysviewer/js
  npm run test:e2e:regions
  ```

- [ ] Confirm the walkthrough completes without browser errors or a WebGL-related skip.
- [ ] Manually inspect the Regions subpanel for layout overflow, overlap-badge
      scroll/highlight feedback, style controls, boolean composition, and Inspect refresh.
- [ ] Record the browser version, graphics/WebGL environment, command result, and any
      findings in this section.

This is validation of already implemented code, not an additional implementation
phase. A compile-only E2E check or a controlled headless skip does not close it.

---

## Cross-cutting (every phase)

- [x] Rebuild the bundle after TS changes: `cd molsysviewer/js && npm run build:runtime`
      (regenerates `viewer.js`); never edit it by hand. Use `npm run build` only for
      release/packaging version sync.
- [x] Keep the Python suite + `npm run test:js` green; add tests with each phase.
- [x] Update the dashboard row + Risks table as each phase lands.

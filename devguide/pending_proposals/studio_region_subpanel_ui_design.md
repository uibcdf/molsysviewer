# Proposal: Studio → Regions Subpanel UI Design & Implementation Spec

**Status:** **partially implemented** (2026-07-09 structure; 2026-07-10 audit).
**Scope:** UI/UX styling, layout structure, and frontend-backend synchronization for the
**Regions Subpanel** of the **Studio** panel in MolSysViewer.

This document is the high-fidelity visual/UX specification, supplementing the
architectural blueprint in `studio_region_subpanel.md`. It reuses the design system
established for the Selection subpanel (`studio_selection_subpanel_ui_design.md` §4) so
both subpanels look and feel like one Studio.

> **Normative source:** `region_contracts.md`. This document never redefines backend
> behaviour. Where a mockup below shows something the code does not do, it is marked
> **(proposed)** and scheduled in `studio_region_subpanel_implementation_plan.md`.
>
> **Not yet built, though drawn below:** provenance in the Inspect panel (§2, §3.B) — no
> `provenance` exists in Python at all; and the multi-operand checklist of the boolean
> composer (§2, §3.C) — the code has a single `Region B` dropdown.
>
> **Section order:** this document specifies Create → Regions → Boolean. `RegionsPanel.paint()`
> currently renders Create → **Boolean** → Regions. The code is to follow this document
> (the composer operates *on* the list, so it reads after it).

The implementation uses stable `data-molsysviewer-region-*` selectors rather than
semantic CSS class names, while preserving the tokens and visual behavior specified
below. The overlap badge scrolls to and highlights the boolean composer. Inspect is
lazy, displays structured metrics for the response frame, and offers manual Refresh;
it does not stream updates during playback.

---

## 1. Motivation & Design Goals

Regions are the persistent, represented scene objects. The subpanel must let a user
build and manage them fully — create, style (12 reps + opacity + quality + color),
compose (∪ ∩ −), isolate, inspect — without touching Python, while keeping the same
glassmorphic, self-documenting, responsive feel as the Selection subpanel.

Key objectives:

1. **Parity with the API** — expose creation (selection/query/split/complement),
   faithful representation, boolean composition, isolate, inspect.
2. **Consistency** — reuse the Selection subpanel's query composer, collision policy,
   rename idiom, and CSS tokens.
3. **Safety** — surface region overlaps (z-fighting) and offer a non-destructive resolve.
4. **Performance awareness** — expose a render-quality control for large systems, and
   avoid heavy query strings (index-based paths where possible).

---

## 2. Interface Layout (ASCII Blueprint)

```
================================================================================
                     STUDIO workspace -> Subpanel: REGIONS
================================================================================

┌── [Section A] CREATE & GLOBAL ACTIONS ───────────────────────────────────────┐
│  Create region ▾                                                              │
│    ( ) From active selection            [ Create ]   (disabled if empty)      │
│    ( ) From query   🔍 [ MolSysMT query...      ] [Check] [ MolSysMT | Idx ▼ ]│
│                     Status: "Press Enter/Check…" → "✓ 45 atoms"    [ Create ] │
│    ( ) Split by     [ chain | molecule | entity ▼ ]   [ Split ]              │
│    Name (optional): [ .................. ]   Repr: [ cartoon ▼ ]              │
│                                                                               │
│  Global:   [ 👁 Show all ]   [ 🙈 Hide all ]                                  │
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section B] REGIONS (Glassmorphic Cards) ──────────────────────────────────┐
│  ▾ site  (128 atoms · cartoon)                   👁   🗑   ⚠ overlaps: backbone │
│    [ Isolate ] [ Complement ] [ Rename ] [ Duplicate ] [ Reset repr ]  [ ⓘ ] │
│    ── Style composer ─────────────────────────────────────────────────────    │
│      Representation: [ ball-and-stick ▼ ]     Preset: [ (none) ▼ ]            │
│      Opacity:  [========o----] 0.7            Quality: [ medium ▼ ]           │
│      Color:    [ Element | Chain | SS | Hydrophob. | Custom ▼ ]  [🎨]          │
│      Color by: [ (none) | b_factor | occupancy | … ▼ ] [palette ▼] [Reset col.]│
│    ── Inspect (ⓘ) ───────────────────────────────────────────────────────     │
│      128 atoms · 8 groups · 1 chain · center [1.24, 0.88, 2.10] nm            │
│      Origen: Consulta (MolSysMT) → "molecule_type == 'protein'"   (proposed)   │
│  ───────────────────────────────────────────────────────────────────────────  │
│  ▸ backbone (642 atoms · cartoon · hidden)      👁   🗑                        │
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section C] BOOLEAN COMPOSER (Math Composer) ──────────────────────────────┐
│  Base: [ site ▼ ]   Op: [ ∪ Union | ∩ Intersection | − Difference (A−B) ▼ ]   │
│  Target(s): [x] backbone  [ ] ligand  [x] water                              │
│  Output name: [ pocket_sidechains ....... ]                      [ Create ]   │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details & Interactions

### A. Create & Global Actions
* **From active selection:** `Create` calls `create_region_from_selection` /
  `new_region_from_active_selection`. Disabled (greyed, tooltip) when
  `currentSelection.count_atoms === 0`.
* **From query:** the **shared query composer** (Option B) — input + `MolSysMT | Indices`
  dropdown + a `Check` button (`Enter` also triggers). **Manual verification**: while typing
  the status is `idle` ("Press Enter or Check to verify"), **no** per-keystroke requests; on
  Check/Enter it shows `✓ N atoms` / `0 atoms` / `✗ invalid syntax`, and returns to `idle`
  when typing resumes. `Create` calls `create_region_from_query`. (This replaces the earlier
  debounced-preview model, per the Selection refinements lesson.)
* **Split by hierarchy:** dropdown `chain | molecule | entity` → `make_regions_by`.
  Produces several regions at once; the list refreshes. **Naming on split is
  auto-incremented** (`A`, `A__2`, …) — **no** collision prompt on this path (a batch
  split must never stall per-element); single creations still use the prompt.
* **Name & repr:** optional tag (collision policy, §below) and an optional initial
  representation applied on create. The dropdown must list the **12 real representations and
  the real presets** delivered by the backend via `setStyleOptions()` — today it is hardcoded
  to 7 entries and no presets, which is exactly the flaw the blueprint §1.1 set out to fix.
  It must also offer **Inherit** (`region_contracts.md` §A.1), and **default to Inherit while
  the `whole` is hidden**: a region created in state *None* under a hidden whole is silently
  invisible, and `new_view(selection=…)` hides the whole.
* **Global:** `Show all` / `Hide all` fire a **single** action → public
  `RegionsManager.show_all()` / `hide_all()` → **single** consolidated summary. The frontend
  does **not** iterate or send per-region messages; batch suppression on the backend avoids
  per-region flicker.

### B. Region Cards
* **Header:** tag (click → `focus_region`), atom count + representation hint,
  visibility toggle (`toggle_region_visibility` → `show`/`hide`), delete
  (`delete_region`). **The visibility toggle is disabled for a region in state *None*** — it
  has no visual of its own to hide (`region_contracts.md` §A.3) — with an explanatory tooltip.
* **⚠ Overlap badge:** shown when `overlap_tags` is non-empty for a *visible* region.
  Clicking opens **Section C pre-filled** with `Difference` between the pair (explicit,
  non-destructive). Tooltip lists the overlapping tags.
* **Quick actions:** `Isolate` (`show_only_region`), `Complement`
  (`create_complementary_region`), `Rename` (inline form, **not** dbl-click),
  `Duplicate` (`duplicate_region`), `Reset repr` (`reset_region_representation`).
* **Style composer (expandable):**
  * *Representation:* full 12-type list from `view.representations`.
  * *Preset:* `view.presets` (built-ins + user presets); choosing a preset supersedes
    the representation.
  * *Opacity:* slider `0.0–1.0` → `params.alpha` (passes through as Mol\* `typeParams`).
    The numeric readout updates live on `input`; the `set_region_representation` message is
    **fired on `change` (mouseup)** — one message on release, not per intermediate value — so
    a drag never floods the IPC. (Optional light throttle later if live 3D feedback is
    wanted; `change`/mouseup is the default.)
  * *Quality:* dropdown (`auto…highest`) → `params.quality`.
  * *Color:* scheme select + custom color picker (`<input type="color">`) → `color_scheme`
    / uniform color; **Color by** attribute dropdown → `color_region_by_attribute` — the
    dropdown lists **only attributes present** in the loaded system (from the summary's
    `available_attributes` flags), so files without them never offer a missing one. The names
    surfaced are the canonical ones — `b_factor`, `occupancy`, `partial_charge`,
    `formal_charge` — not the `bfactor` / `charge` aliases, which exist only inside
    `Region.set_color_by_attribute`. **(proposed)** the dropdown must also expose `palette`,
    `value_range` and `element` (the handler already accepts all three) and must display the
    **active** attribute rather than resetting to "None" on each repaint.
  * *Reset colors* → `reset_colors`. **Per `region_contracts.md` §B.3 this clears only this
    region's colour layer**, revealing whatever lies beneath. The canvas-wide wipe lives in
    the **Whole** subpanel (`view.reset_all_colors()`), not here. Today's shipped behaviour
    is the opposite — the button wipes the canvas — and is repaired in Phase 2.
  * *Apply / Cancel* commit via `set_region_representation`.
* **Inspect (ⓘ, expandable — lazy):** composition + geometric center + provenance. Fetched **on demand**
  via `get_region_details { tag }` when the panel opens (**not** in the static summary), and
  the centroid is resolved in the **current playback frame** for trajectories. Shows the structured
  origin metadata (`provenance`) in clear text (e.g. `Origen: Consulta (MolSysMT) → "molecule_type == 'protein'"` or `Origen: Composición booleana → site_A − (backbone | water)`).

### C. Boolean Composer

**(proposed — the shipped composer has a single `Region B` dropdown.)** Multi-operand
composition rests on the variadic Python operators (`a.difference(b, c)`) added in Phase 4;
the GUI must not open-code the chaining.

* **Multi-operand Layout:** Supports base region dropdown, operator selection (`∪ | ∩ | −`), and operand targets. For Union and Difference, targets render as a multi-selection checklist of existing regions. For Intersection, it remains a single target selection.
* `Create` calls `compose_regions` passing the list of operands. Dropdowns refresh whenever a region is created/deleted/renamed.
* Difference is **ordered**; base region is the positive term, and all selected targets are subtracted.

### Name-collision handling
When creating/renaming/composing, if the tag exists the backend raises `ValueError`;
the panel prompts **Rename / Overwrite / Cancel** (same idiom as the Selection subpanel).
Selections and regions are separate registries — a name may exist in both.

---

## 4. Graphic Style & CSS Design System

Reuse the Selection subpanel's tokens (`studio_selection_subpanel_ui_design.md` §4):
`--bg-sidebar`, `--bg-card`, `--bg-card-hover`, `--border-subtle`, `--accent-indigo`,
`--accent-indigo-glow`. Region-specific additions:

```css
/* Region card */
.region-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.region-card:hover { background-color: var(--bg-card-hover); }
.region-card.is-hidden { opacity: 0.55; }

/* Overlap warning badge */
.region-overlap-badge {
  color: #fbbf24;                      /* amber */
  border: 1px solid rgba(251,191,36,0.35);
  border-radius: 999px;
  padding: 1px 8px;
  font-size: 10px;
  cursor: pointer;
}
.region-overlap-badge:hover { background: rgba(251,191,36,0.12); }

/* Opacity slider accent */
.region-opacity-slider { accent-color: var(--accent-indigo); }

/* Style composer container (reuse existing dashed panel) */
.region-style-composer {
  background: rgba(255,255,255,0.03);
  border: 1px dashed var(--border-subtle);
  border-radius: 6px;
  padding: 8px 10px;
}
```

Dark-mode aesthetic and theme-awareness must match the rest of the viewer, as with the
Selection subpanel.

---

## 5. Programming & Backend Synchronization

0. **Contracts first:** `region_contracts.md` governs representation states, colour ownership
   and serialisation. Nothing in this document overrides it.
1. **Backend method contracts:** all region operations route through the verified
   Python methods in **§6 of the blueprint** (`studio_region_subpanel.md`) — never
   re-implement region logic in TS.
2. **Opacity / quality:** no protocol change — `set_region_representation`'s `params`
   already flow to Mol\* `typeParams` (blueprint §6.3). The UI only sends `alpha` /
   `quality`. **The opacity slider is only meaningful for a region with its own visual**
   (states *Inherit* or *Own*). On a state-*None* region it must be disabled, not silently
   inert as it is today.
3. **Region summary payload:** the frontend `RegionSummary` must be extended with
   `representation`, `preset`, `overlap_tags`, and `available_attributes` so cards can
   render the representation hint, the ⚠ badge, and the gated "Color by attribute" dropdown
   without extra round-trips (blueprint §6.2). Expensive metrics (centroid, composition)
   are **not** here — see (6).
4. **Transient-region filter:** the Regions list filters `orientation-` / `plane-` **and
   `focus`** tags (blueprint §6.4) so overlay/highlight-created regions do not appear here.
5. **Query composer reuse:** the create-from-query path uses the **shared** query-composer
   component with **manual verification** (`Check`/`Enter`, `idle` while typing) — **not** the
   old debounced-preview channel (retired per the Selection refinements). One component,
   inherited by Selection when unpaused (Option B).
6. **Lazy inspection:** the `ⓘ` panel fetches composition + centroid on demand via
   `get_region_details { tag }` (request-response), centroid in the current playback frame
   (blueprint §4D, §6.2). Do not stream these during normal playback; use the explicit
   Refresh action after changing frame.
7. **Batch suppression:** `Show all` / `Hide all` / split rely on the backend batch context
   (blueprint §6.6) to emit one consolidated summary; the frontend applies a single update,
   not one per region.

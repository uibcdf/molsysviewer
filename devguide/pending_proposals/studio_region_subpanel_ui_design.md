# Proposal: Studio → Regions Subpanel UI Design & Implementation Spec

**Status:** implemented (2026-07-09).
**Scope:** UI/UX styling, layout structure, and frontend-backend synchronization for the
**Regions Subpanel** of the **Studio** panel in MolSysViewer.

This document is the high-fidelity visual/UX specification, supplementing the
architectural blueprint in `studio_region_subpanel.md`. It reuses the design system
established for the Selection subpanel (`studio_selection_subpanel_ui_design.md` §4) so
both subpanels look and feel like one Studio.

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
│      Color by: [ (none) | bfactor | occupancy | charge ▼ ]  [ Reset colors ] │
│    ── Inspect (ⓘ) ───────────────────────────────────────────────────────     │
│      128 atoms · 8 groups · 1 chain · center [1.24, 0.88, 2.10] nm            │
│  ───────────────────────────────────────────────────────────────────────────  │
│  ▸ backbone (642 atoms · cartoon · hidden)      👁   🗑                        │
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section C] BOOLEAN COMPOSER (Math Composer) ──────────────────────────────┐
│  [ site ▼ ]   [ ∪ Union | ∩ Intersection | − Difference (A−B) ▼ ]  [ backbone ▼ ]
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
  representation applied on create.
* **Global:** `Show all` / `Hide all` fire a **single** action → public
  `RegionsManager.show_all()` / `hide_all()` → **single** consolidated summary. The frontend
  does **not** iterate or send per-region messages; batch suppression on the backend avoids
  per-region flicker.

### B. Region Cards
* **Header:** tag (click → `focus_region`), atom count + representation hint,
  visibility toggle (`toggle_region_visibility` → `show`/`hide`), delete
  (`delete_region`).
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
    `available_attributes` flags), so files without bfactor/charge/occupancy never offer a
    missing one; `Reset colors` → `reset_colors`.
  * *Apply / Cancel* commit via `set_region_representation`.
* **Inspect (ⓘ, expandable — lazy):** composition + geometric center. Fetched **on demand**
  via `get_region_details { tag }` when the panel opens (**not** in the static summary), and
  the centroid is resolved in the **current playback frame** for trajectories.

### C. Boolean Composer
* Region A dropdown · operator (`∪ | ∩ | −`) · Region B dropdown · output name → `Create`
  (`compose_regions`). Dropdowns refresh whenever a region is created/deleted/renamed.
* Difference is **ordered**; the label makes `A − B` explicit.

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

1. **Backend method contracts:** all region operations route through the verified
   Python methods in **§6 of the blueprint** (`studio_region_subpanel.md`) — never
   re-implement region logic in TS.
2. **Opacity / quality:** no protocol change — `set_region_representation`'s `params`
   already flow to Mol\* `typeParams` (blueprint §6.3). The UI only sends `alpha` /
   `quality`.
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

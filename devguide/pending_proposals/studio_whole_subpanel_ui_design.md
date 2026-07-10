# Proposal: Studio → Whole Subpanel UI Design & Implementation Spec

**Status:** proposed (2026-07-10). **Not implemented** — today a `RoadmapPanel` placeholder.
**Scope:** UI/UX styling, layout, and frontend↔backend synchronisation for the **Whole**
subpanel of the **Studio** panel.

Supplements the blueprint `studio_whole_subpanel.md`. Reuses the design system of the
Selection and Regions subpanels (`studio_selection_subpanel_ui_design.md` §4) so all of
Studio reads as one surface.

> **Normative source:** `region_contracts.md`. This document never redefines backend
> behaviour. Where it disagrees with the blueprint, the blueprint wins.

---

## 1. Motivation & design goals

The whole is the one object every session has. The panel must make three things obvious that
are invisible today:

1. **What the baseline currently looks like** — representation, preset, opacity, quality,
   colour theme. Today none of this is readable, not even from Python (the state is private).
2. **What depends on it** — how many regions inherit its representation, and how many would
   vanish if it were hidden.
3. **What its colour actually controls** — the base layer, beneath every region layer.

Plus the usual: ergonomics, consistency with the sibling subpanels, and no IPC flooding.

---

## 2. Interface layout (ASCII blueprint)

```
================================================================================
                      STUDIO workspace -> Subpanel: WHOLE
================================================================================

┌── [Section A] PRESENCE & CAMERA ─────────────────────────────────────────────┐
│  Whole structure     ● visible                                                │
│  [ 👁 Hide ]   [ ⊕ Focus ]                                                    │
│  ⚠ 2 regions have no representation of their own and will disappear.          │
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section B] REPRESENTATION ────────────────────────────────────────────────┐
│  Scene style: publication            (editing below clears this name)         │
│  Representation: [ cartoon ▼ ]          Preset: [ (none) ▼ ]                  │
│  Opacity:  [======o------] 0.55         Quality: [ medium ▼ ]                 │
│                                        [ Reset representation ] [ Apply ]     │
│  ℹ 3 regions inherit this representation and will follow it.                  │
│  ℹ Applying a representation shows the whole if it is hidden.                 │
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section C] COLOUR ────────────────────────────────────────────────────────┐
│  Theme:   [ Element (CPK) | Physicochemical | Chain | Sec. structure ▼ ]      │
│  Uniform: [🎨]                                                                │
│  Colour by: [ (none) | b_factor | occupancy ▼ ] [ viridis ▼ ] [ range … ]     │
│                                                                               │
│  [ Reset colours ]            base layer · covered by 2 region layers         │
│  [ ⚠ Reset ALL colours ]      clears every region layer too                   │
└───────────────────────────────────────────────────────────────────────────────┘

┌── [Section D] INSPECT (ⓘ, lazy) ─────────────────────────────────────────────┐
│  1 842 atoms · 231 groups · 2 chains · 1 molecule · 1 entity                  │
│  center [2.31, 1.04, 3.77] nm      frame 0        [ Refresh ]                 │
│  contains: protein ✓  water ✓  ions ✗                                         │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component details & interactions

### A. Presence & camera

* **Visibility toggle** → `set_whole_visibility {visible}` → `whole.show()` / `hide()`.
  The dot and label render from the summary's `visible`, never from local state — today
  visibility lives in `view._global_hidden` with no public accessor, which is exactly why the
  panel cannot be built before the API lands.
* **The Hide warning is mandatory, not decorative.** Hiding the whole makes every region in
  state **None** invisible, because nothing else paints their atoms
  (`region_contracts.md` §A.1). The panel reads `none_state_region_count` from the summary and
  shows the ⚠ line *before* the click, and a confirmation when the count is non-zero.
* **Focus** → `focus_whole` → `whole.focus()`.

### B. Representation

* Uses the **shared style composer**, extracted from `regions-panel.ts` before Whole consumes
  it (blueprint §5.4). Not a fork.
* *Representation* and *Preset* are mutually exclusive: choosing one clears the other.
* *Opacity* → `params.alpha`. Numeric readout updates live on `input`; the message fires on
  `change` (mouseup). A slider's intermediate values are all valid, so the concern is
  throughput, not incomplete input — unlike the query composer, where per-keystroke traffic
  was wrong.
* *Quality* → `params.quality`.
* *Reset representation* → `reset_whole_representation` → `whole.reset_representation()`,
  reverting to the load-time style. (`Whole` has no such method today.)
* **The inherit note** reads `inheriting_region_count` from the summary. Changing the
  representation here repaints those regions (`region_contracts.md` §A.2, rule 4).
* **The scene-style row.** `whole.set_representation()` clears the active scene-style name
  (`whole.py:64-65` → `styles._clear_cached_name()`), because `view.styles` writes the whole's
  representation and the two are the same state seen twice (blueprint §1.2.2, §3.3). The panel
  renders `scene_style_name` from the summary and warns that editing clears it. It never
  re-applies or invents a name.
* **The "applying shows the whole" note.** `set_representation` sets `_global_hidden = False`
  (`whole.py:53-54`). The user must not discover this by watching a hidden structure reappear.
  Once `keep_hidden` exists (blueprint §5.1), the panel passes it when the whole is hidden and
  the note goes away.

### C. Colour

This section is where Contract B becomes visible to the user, so its labels matter.

* **Theme** → `set_whole_color_scheme` → `whole.set_color_scheme(...)`. This control exists
  today as the *Colour scheme* dropdown in the **System** subpanel
  (`system-panel.ts:394-402` → `viewer-controller.ts:975-980`), where it bypasses Python
  entirely. It migrates here and becomes API-owned and serialisable.
* **Uniform colour** → `<input type="color">` → `params.color`, normalised into
  `molstar_color_theme` by `set_representation`.
* **Colour by attribute** → `color_whole_by_attribute {attribute, palette, value_range,
  element}` → `whole.set_color_by_attribute(...)`, writing the **base layer**. The dropdown
  lists only attributes present in the loaded system, using the same load-time probe as the
  Regions summary (`_available_region_attributes`), and shows the canonical names
  (`b_factor`, `occupancy`, `partial_charge`, `formal_charge`).
* **Reset colours** → `reset_whole_colors` → `whole.reset_colors()`, clearing **the base
  layer only**. The row shows `covered by N region layers` so the user understands why the
  screen may not change. Where a region covers, the reset surfaces only once that region is
  hidden or its own layer cleared.
* **Reset ALL colours** → `reset_all_colors` → `view.reset_all_colors()`. Visually distinct
  (amber border, like the overlap badge), with a confirmation. This is the only canvas-wide
  wipe, and it is the honest replacement for today's `reset_colors()`, which wipes everything
  from either object and then paints the system grey (`region_contracts.md` §0.3).

### D. Inspect (lazy)

`get_whole_details {request_id}` → composition, geometric centre in the **current playback
frame**, and `contains` / `is_composed_of`. Request/response with a request id and
stale-response rejection, identical to the Regions `ⓘ` panel. Never streamed during playback;
an explicit **Refresh** re-reads the current frame.

`contains` and `is_composed_of` have no GUI surface anywhere in Studio today. This is their
home.

---

## 4. Graphic style

Reuse the shared tokens (`--bg-card`, `--border-subtle`, `--accent-indigo`, …). Whole-specific
additions:

```css
/* Presence dot */
.whole-presence-dot        { width: 7px; height: 7px; border-radius: 999px; }
.whole-presence-dot.is-on  { background: #34d399; box-shadow: 0 0 8px rgba(52,211,153,0.5); }
.whole-presence-dot.is-off { background: rgba(244,244,245,0.28); }

/* Dependency notes (regions that inherit / would vanish) */
.whole-dependency-note {
  font-size: 10px;
  color: rgba(244,244,245,0.6);
  border-left: 2px solid rgba(99,102,241,0.4);
  padding-left: 6px;
}
.whole-dependency-note.is-warning {
  color: #fbbf24;
  border-left-color: rgba(251,191,36,0.5);
}

/* Destructive action */
.whole-reset-all {
  color: #fbbf24;
  border: 1px solid rgba(251,191,36,0.35);
  background: rgba(251,191,36,0.06);
}
.whole-reset-all:hover { background: rgba(251,191,36,0.14); }
```

Stable `data-molsysviewer-whole-*` selectors, matching the Regions convention rather than
semantic class names.

---

## 5. Programming & backend synchronisation

1. **Contracts first.** `region_contracts.md` governs representation states, colour ownership
   and serialisation. Whole and Regions are two views of the same contracts.
2. **Backend method contracts.** Every action routes through a public `Whole` / `MolSysView`
   method (blueprint §5.1). Nothing is re-implemented in TS. Several of those methods **do not
   exist yet** — the API lands first.
3. **There is no JS → Python channel for the whole today.** `set_global_representation`,
   `show_global` and `hide_global` are Python → JS only, and the `PanelAction` union contains
   nothing about the whole. The action family is new (blueprint §5.2).
4. **Whole summary payload.** `{representation, preset, params, visible, color_scheme,
   available_attributes, inheriting_region_count, none_state_region_count,
   covering_layer_count}`. The last three exist solely so the panel can tell the truth about
   coupling (§3.A, §3.B, §3.C) instead of guessing.
5. **Expensive metrics stay out of the summary.** Composition and centroid are fetched on
   demand via `get_whole_details`, in the current frame.
6. **Opacity fires on `change`**, not `input`. Colour-by-attribute fires on commit, not on
   every dropdown hover.
7. **Wire-op naming.** The ops still say `global`. Renaming them is deliberate, separate,
   mechanical work (blueprint §5.3), not part of this subpanel.

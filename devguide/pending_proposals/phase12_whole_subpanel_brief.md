# Phase 12 — Whole subpanel (GUI) + System colour-scheme migration · design brief

**Author:** backend contract owner · **For:** the collaborator implementing Phase 12.
**Size:** L · **Depends on:** P3, P7, P9 (all done). **Normative UI spec:**
`studio_whole_subpanel_ui_design.md` — read it first, it is the visual/UX source of truth.
This brief fixes the contract, the *verified* code pointers, and the split of work.

**Read §2 before you read the spec.** The spec was written on 2026-07-10, before Phases 3 and 7
landed. Several gaps it laments are already closed, and one behaviour it asks you to paper over
no longer exists. Implementing the spec literally would mean re-adding a bug we fixed.

---

## 1. What this phase is, in one paragraph

The Whole subpanel is still a `RoadmapPanel` placeholder (`ui/group-panel.ts:329-339`). The
Python API behind it is **complete**; the context-action handlers are **complete**. What is
missing is the *bridge*: **there is no whole summary at all** — Python never tells the frontend
what the whole looks like. So the panel has nothing to render from. Building that summary is the
first deliverable; the panel is the second; and killing the last frontend path that repaints the
molecule behind Python's back (the System *Colour scheme* dropdown) is the acceptance criterion
of the whole phase.

---

## 2. What already exists — verified today, do not rebuild

**`Whole` Python API is complete** (`molsysviewer/whole.py`):

| Surface | Where |
|---|---|
| `representation`, `preset`, `params`, `visible`, `color_scheme`, `scene_style_name` (properties) | `whole.py:27-56` |
| `set_representation` (accepts `color=` → normalised into `molstar_color_theme`), `reset_representation` | `whole.py:67`, `:109` |
| `show`, `hide`, `focus` | `whole.py:121`, `:129`, `:187` |
| `get_center` (frame-aware via `structure_indices`) | `whole.py:213` |
| `contains(selection, syntax, **kwargs)`, `is_composed_of(...)` | `whole.py:153`, `:170` |
| `set_color_scheme`, `set_color_by_attribute`, `set_color_by_values`, `reset_colors` | `whole.py:245`, `:266`, `:329`, `:378` |
| `view.reset_all_colors()` | `viewer/core.py:2408` |

**All nine context-action handlers already exist** (`viewer/core.py:941-995`):
`set_whole_representation`, `reset_whole_representation`, `set_whole_visibility`, `focus_whole`,
`set_whole_color_scheme`, `color_whole_by_attribute`, `reset_whole_colors`, `reset_all_colors`,
`get_whole_details`. The `PanelAction` union already lists them (`ui/panels/types.ts:61-69`).

**The canonical scheme list is `STRUCTURAL_COLOR_SCHEMES`** (`molsysviewer/styles.py:124-157`):
`element_cpk`, `secondary_structure_default`, `chain_default`, `physicochemical`, `residue_name`,
`molecule_type`, `entity_default`, `illustrative_default`. The panel **must not hardcode these** —
ship them in the summary (D1).

### 2.1 Where the spec is stale — do NOT implement these

* **§3.B "Applying a representation shows the whole if it is hidden"** and the `keep_hidden`
  parameter: **obsolete.** Phase 3 fixed that bug. `set_representation` (`whole.py:80-104`) no
  longer touches `_global_hidden`. Do **not** add the note, do **not** add `keep_hidden`. If while
  testing you observe a hidden whole reappearing on restyle, that is a *regression* — tell me,
  don't build a workaround around it.
* **§1.2 "no public read of its own state" / "no `reset_representation`" / "no
  `set_color_by_attribute`" / "no `get_center`"**: all closed. The table in §2 above is the truth.

---

## 3. What does not exist — this is the phase

### D1 · Backend: the whole summary (**start here, nothing else works without it**)

There is **no** `set_whole_summary` op anywhere: not in Python, not in TS. Build it mirroring the
region path (`viewer/regions.py:510` `_region_summary_records` + `:556`
`_sync_region_summaries_runtime`).

New in `viewer/` (a `whole.py` mixin module alongside `regions.py` is the natural home):

```python
def _whole_summary_record(self) -> dict[str, Any]: ...
def _sync_whole_summary_runtime(self) -> None:      # _send_runtime_only, never serialised
```

Payload:

```python
{
    "op": "set_whole_summary",
    "representation": str | None,
    "preset": str | None,
    "params": dict,                  # alpha, quality, color_scheme, molstar_color_theme…
    "visible": bool,
    "color_scheme": str | None,
    "scene_style_name": str | None,
    "available_attributes": [...],   # reuse _available_region_attributes() — do not fork it
    "color_schemes": [...],          # sorted(STRUCTURAL_COLOR_SCHEMES) — styles.py:463 already returns this
    "inheriting_region_count": int,
    "none_state_region_count": int,
    "covering_layer_count": int,
}
```

The three counters are the point of the panel — they are how it tells the truth about coupling
instead of guessing. Derive them from the **contracts**, reusing the existing helpers:

* `inheriting_region_count` — active regions whose representation state is **Inherit**
  (the `"inherit"` sentinel, Contract A).
* `none_state_region_count` — active regions with **no own visual** (neither representation nor
  preset). These vanish when the whole hides. There is already a predicate for exactly this
  (`_region_has_visible_representation` in `viewer/regions.py`, and `_has_own_visual` on the
  region). **Use it. Do not re-derive the rule** — two copies of "what counts as None" will drift.
* `covering_layer_count` — non-empty per-region colour layers in `_atom_color_layers`, excluding
  the `"whole"` base layer.

**The trap, and I will test for it:** the counters depend on **region** mutations, not only on
whole mutations. If you sync the whole summary only from the whole's own methods, the
`3 regions inherit` and `2 regions will disappear` notes go stale the moment a region is added,
deleted, or has its representation changed. Sync from the region summary path too (the region
batch already has a `summary_dirty` flag — hook there, and honour the batch depth so a bulk
operation still emits **one** message).

Emit on: load / rebuild / `import_state`, `set_representation`, `reset_representation`, `show`,
`hide`, `set_color_scheme`, `set_color_by_attribute`, `reset_colors`, `reset_all_colors`, and
every region mutation that moves a counter.

### D2 · Backend: enrich `get_whole_details`

Today (`core.py:983-995`) it returns only `atom_count`, `center_nm`, `structure_index`. Spec §3.D
needs, in the **current playback frame**:

* composition: atoms / groups / chains / molecules / entities (go through the existing MolSysMT
  path — do not open-code counting loops),
* `contains` and `is_composed_of` for a small probe set. **Check the accepted tokens against
  `msm` before choosing them** — do not invent `"ions"` because the ASCII mock-up says so.

Keep `request_id` and stale-response rejection, identical to the Regions `ⓘ` flow. Never streamed
during playback; **Refresh** re-reads the current frame.

### D3 · Backend: `reset_all_colors` must be undoable

`view.reset_all_colors` (`core.py:2406-2411`) has `@signal` and `@digest` but **not**
`@records_scene_history` — while `Whole.reset_colors` (`whole.py:375`) has it. So the canvas-wide
wipe is the one colour operation you cannot undo. Wiring a red "Reset ALL colours" button to an
un-undoable operation is a trap for the user. Add the decorator; test that colour → wipe → undo
restores both the base layer and the region layers.

### D4 · Frontend: extract the **shared** style composer (before the panel, not after)

`regions-panel.ts` owns a representation/preset/opacity/quality composer (≈`:1020-1100`). Whole
needs the same one. **Two composers that drift is the exact mistake this effort exists to
correct** (master plan, Phase 12). Extract it — e.g. `ui/panels/style-composer.ts` — driven by
config, not by an `if (isWhole)`:

* `allowInherit: boolean` — Regions **yes**, Whole **no** (the whole cannot inherit from itself).
* `opacityDisabled: boolean` — the "no own visual ⇒ opacity is meaningless" rule is a *flag*, not
  a hardcoded region rule.
* current values + option lists injected by the caller.

**Proof the extraction is behaviour-preserving:** the 175 existing JS tests stay green with
**zero edits to their assertions**. If you find yourself editing a Regions test to make it pass,
the extraction changed behaviour — stop and tell me rather than adjusting the test.

### D5 · Frontend: `WholePanel`

Replace `RoadmapPanel("whole", …)` at `group-panel.ts:329-339`. Sections A–D per spec §2/§3.

* **Everything renders from the summary.** Not from local state, and in particular not from
  `state-handlers.isWholeHidden()` — that function infers hidden-ness from `show_whole` /
  `hide_whole` ops and exists to drive Mol\*; the panel's dot and label read `visible` from the
  summary. One truth, one direction.
* **The Hide confirmation is mandatory** when `none_state_region_count > 0`: those regions are
  painted by nothing else and will disappear (`region_contracts.md` §A.1). Warn *before* the
  click (the ⚠ line) and confirm *on* the click.
* Opacity: readout updates on `input`, message fires on `change`. Colour-by-attribute fires on
  commit.
* `Reset colours` clears the **base layer only** — annotate the row with `covered by N region
  layers` so the user understands why the screen may not change.
* `Reset ALL colours` is visually distinct (amber, spec §4) and confirms.
* Uniform colour → `set_whole_representation` with `params: {color: "#rrggbb"}`
  (`set_representation` normalises `color` into `molstar_color_theme`; `core.py:942-948` already
  passes `params` through).
* The scene-style row **renders** `scene_style_name` and warns that editing clears it. It never
  re-applies or invents a name.
* Stable `data-molsysviewer-whole-*` selectors, as in Regions.

### D6 · Frontend: kill the last TS → molecular-theme path

This is the acceptance criterion of the phase: **no frontend path mutates the molecular colour
theme without going through Python.**

The System *Colour scheme* dropdown does **two** things today, and only one of them is
legitimate:

1. it recolours the **sequence strips** (`system-panel.ts:242` → `groupStrip.setColorScheme`) —
   a panel-local visual, legitimate;
2. it calls `onChangeColorScheme` (`system-panel.ts:416` → `group-panel.ts:159,378` →
   `viewer-controller.ts:1019-1023`), which calls
   `plugin.managers.structure.component.updateRepresentationsTheme(...)` — **it repaints the
   molecule from TS, bypassing Python entirely.** Not in the API, not serialised, silently
   destroyed by any per-atom colouring.

So: remove the dropdown (`makeColorSchemeButton`, `toggleColorSchemeMenu`, the two options),
remove `onChangeColorScheme` from the `SystemPanel` callbacks, from the `GroupPanel` constructor
and from the `viewer-controller` lambda.

**But do not delete strip colouring along with it.** Rewire instead: `GroupPanel` forwards the
whole summary's `color_scheme` to `SystemPanel`, which maps `physicochemical → "physicochemical"`
and everything else → `"neutral"` for the strips. Net result: the scheme is chosen **once**, in
Whole, through Python — and the strips *mirror the scene* instead of disagreeing with it, which
is strictly better than today. System keeps strips, hover, pick and context menu.

**Mechanical acceptance:** `grep -rn "updateRepresentationsTheme" molsysviewer/js/src` → **0 hits.**

---

## 4. Tests

This is where the last two phases bled, so it is specified, not left to taste.

**Python — `tests/test_phase12_whole_panel.py`:**

* the summary carries all fields, with the right types, and `color_schemes` matches
  `STRUCTURAL_COLOR_SCHEMES`;
* **the counters move when *regions* change, not only when the whole changes** — add a region in
  Inherit, assert `inheriting_region_count` goes 0 → 1 *in the message that was actually sent*.
  This is the test that catches the stale-note bug, and I will mutate the region-side sync hook to
  check it exists;
* `get_whole_details` returns composition + `contains` + a centroid that **changes when you
  advance the frame** (a centroid test that never changes frame proves nothing);
* `reset_all_colors` is undoable.

**JS:**

* style-composer unit tests in **both** configurations (`allowInherit` on/off);
* `WholePanel`: renders from the summary; Hide confirms **iff** `none_state_region_count > 0`;
  opacity emits on `change` and **not** on `input`;
* **the seam test.** Phase 9's lesson, and it cost us two bugs: drive `set_whole_summary` through
  `state-handlers` and assert every field arrives at the panel. A test that calls
  `panel.setWholeSummary({...})` directly bypasses both mapping seams and proves nothing.

**Mutation rule — apply it to yourself before handing off.** For each mechanism you add, delete it
and check that one of *your* tests goes red. Phase 10 shipped a test that still passed with the
feature removed; Phase 11 shipped a fix whose test only asserted the "on" half of a toggle and
never the reset. If a test survives the deletion of the thing it names, it is decoration.

---

## 5. Reminders

* **`npm run build:runtime` as the very last step**, after the final TS edit. Phase 11's
  `viewer.js` arrived ~10 KB out of sync with its own source; unit tests import from `src/` and
  cannot see it, but the real Jupyter widget would have run stale code.
* The **`tsc` baseline is 0**. Any error is yours.
* Green = `pytest` + `npm run test:js` + `npm run build:runtime` + `npx tsc --noEmit`
  (+ `npm run test:perf`). Report only what you observed.
* **Do not commit.** Leave the tree for audit, with a written statement of what you did **not** do.
* Never touch `sandbox/Test.ipynb` nor `devguide/course/`.
* API first: public Python method → `core.py` handler → GUI control. The GUI never reaches past
  the public API.

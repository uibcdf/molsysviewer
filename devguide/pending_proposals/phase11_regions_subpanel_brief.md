# Phase 11 — Regions subpanel (GUI) · design brief

**Author:** backend contract owner · **For:** the collaborator implementing Phase 11.
**Size:** L · **Depends on:** P7 (done). **Normative UI spec:** `studio_region_subpanel_ui_design.md`
(read it first — it is the visual/UX source of truth; this brief only fixes the contract, the
verified code pointers, and the split of pure-TS vs backend work).

The panel already exists (`src/ui/panels/regions-panel.ts`, ~1057 lines) and most region actions
are wired. Phase 11 is mostly **frontend polish + four real bugs**, plus **two thin backend touch
points**. I audit by mutation at the end (see *§6*).

---

## 1. What is already there (don't rebuild it)

- The panel renders Create / Boolean / Regions and wires: `create_region_from_selection`,
  `create_region_from_query`, `make_regions_by`, `toggle_region_visibility`, `delete_region`,
  `rename_region`, `show_only_region`, `create_complementary_region`, `duplicate_region`,
  `reset_region_representation`, `set_region_representation`, `compose_regions`,
  `color_region_by_attribute`, `reset_region_colors`, `get_region_details`,
  `create_region_from_saved_selection`, `show_all_regions` / `hide_all_regions`.
- The runtime summary (`set_region_summaries`) already carries everything the cards need:
  `tag, atom_indices, atom_count, selection, hidden, layer, mode, frame_dependent,
  representation, preset, representation_params, overlap_tags, available_attributes`.
- `setStyleOptions()` already delivers the **12 real representations + real presets**; the style
  composer uses them. `color_region_by_attribute` already accepts `element`, `palette`,
  `value_range`, `replace`. `create_complementary_region` / `duplicate_region` / `compose_regions`
  already read `new_tag`. **All of these are pure-TS wins — no Python needed.**

---

## 2. Four bugs (verified current line numbers, `regions-panel.ts`)

1. **Opacity slider is silently inert on a Base (state-*None*) region** — `opacity` `change`
   handler at **:994–995** does `if (!item.representation && !item.preset) return;`. Per spec §3.B /
   §5.2 the slider must be **disabled (greyed + tooltip)** on a state-*None* region, not silently
   swallow the drag. A region has its own visual when `representation` or `preset` is set.
2. **`Apply Style` with both selects empty discards the user's settings** — `buildStyleAction()`
   at **:966–968** returns `reset_region_representation` when neither preset nor representation is
   picked, throwing away the opacity/quality/colour the user *did* set. It should instead keep the
   region's current representation/preset (or Inherit) and apply the params, not reset.
3. **`regionBooleanAttention` is set and never reset** — declared `:47`, set `true` at **:419**,
   read at **:584–585**; there is no `= false` anywhere but the declaration. Once the ⚠ badge fires
   once, the attention state sticks forever. Reset it after the composer has been scrolled-to /
   consumed.
4. **The overlap badge only prefills `overlap_tags[0]`** — **:416** `this.regionBooleanB =
   item.overlap_tags![0];`. With the multi-operand composer (below) it should prefill **all**
   overlapping tags as the Difference operands.

## 3. Frontend feature items (pure TS, spec §2–§3)

- **Create dropdown:** replace the hardcoded 7-entry list at **:232–240** with the real 12
  representations + presets from `setStyleOptions()`, plus **Inherit** — and **default to Inherit
  while the whole is hidden** (a state-*None* region under a hidden whole is invisible; the spec
  explains why). The style composer already reads `setStyleOptions()`; reuse that source here.
- **Fourth create origin — from a saved selection:** `create_region_from_saved_selection` (wired).
- **Split over active selection**, and over all elements, with a **confirmation above a threshold**
  (batch split must not stall per element; auto-increment names, no per-element collision prompt).
- **`new_tag`** field for Complement and Duplicate; **`palette` / `value_range` / `element`** for
  colour-by-attribute (the handler already accepts them); the attribute `<select>` must show the
  **active** attribute, not reset to "None" on every repaint.
- **Multi-operand boolean composer** over the variadic `compose_regions` — base + operator +
  a **checklist** of operands for ∪ and −, single target for ∩. Do not open-code the chaining;
  the Python operators are already variadic.
- **Disable `Hide` for state-*None* regions** (tooltip); `Isolate` stays enabled.
- **Section order Create → Regions → Boolean.** `paint()` at **:135–139** currently renders
  Create → Boolean → Regions; the composer operates *on* the list, so it reads after it.

## 4. Backend touch points (thin — you add these in Python)

Two items need Python; both are small and mirror the Phase 9 pattern.

1. **Reorder controls.** `Region.raise_to_front()` / `Region.send_to_back()` exist
   (`regions.py:904 / :911`) but there is **no context-action dispatch** for them. Add two branches
   to the `interaction_context_action` chain in `viewer/core.py` (next to `show_only_region`):
   `raise_region_to_front {tag}` → `region.raise_to_front(skip_digestion=True)`, and
   `send_region_to_back {tag}` likewise. Then the TS buttons call them.
2. **Inspect metadata.** The Inspect panel must show `provenance`, `mode`, `order` and broken-recipe
   state (spec §3.B). The `region_details` response in `viewer/core.py` currently sends only
   `atom_count / group_count / chain_count / center_nm / structure_index`. Add `provenance`
   (`dict(region.provenance)`), `order` (`int(region.order)`), `mode` (`region.mode`) and the
   broken flag (`bool(region.provenance.get("broken"))`) to that payload. `mode` is also already in
   the summary, so the card can label a dynamic region without a round-trip; the full provenance is
   fetched lazily on Inspect open, in the current frame, per spec §6.

Nothing else in Phase 11 touches Python. Do **not** re-implement region logic in TS — route through
the existing verified methods (spec §5.1).

## 5. Standing constraints

- Never hand-edit `molsysviewer/viewer.js`; rebuild with `npm run build:runtime`.
- Never commit `sandbox/Test.ipynb`; leave `devguide/course/` alone. Commit/push only when asked;
  work on `main`. No "Co-Authored-By" / Claude mentions in commit messages.
- **Green** = `pytest` + `npm run test:js` + `npm run build:runtime` + `npx tsc --noEmit` with **0**
  errors (the pre-existing 8 were cleared — the baseline is now zero, so any new tsc error is yours).

## 6. What the audit will do (build for it)

I verify by **mutation** — revert a mechanism and its test must fail — and by **integration
tracing** (the Phase 9 lesson: a new field must survive *both* summary-mapping seams —
`state-handlers.setRegionSummaries` and the `viewer-controller` map that feeds the panel — and a
unit test that bypasses those seams will not catch a drop). Please land, mutation-provably:

- each of the four bug fixes (e.g. the opacity slider is `disabled` on a state-*None* region; an
  empty `Apply Style` does **not** emit `reset_region_representation`; the attention flag resets);
- the create dropdown is populated from `setStyleOptions()` (not the hardcoded 7) and defaults to
  Inherit under a hidden whole;
- the multi-operand composer sends **all** selected operands to `compose_regions`;
- the two new backend actions dispatch to the real Region methods;
- `region_details` carries provenance/mode/order/broken.

If a behaviour can't be pinned by a unit test, tell me — that usually means a seam is missing, and
it's cheaper to add it now than during the audit. A real-Mol\* E2E for the card interactions is
welcome but the group-panel chrome needs a loaded system to become visible (see the Phase 9 layers
e2e for the pattern) — otherwise the harness skips and a seam bug slips through.

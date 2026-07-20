# Changing color/representation silently toggles water visibility

**Status:** Observed during dogfooding (recorrido 2)
**Severity:** moderate — confusing, unpredictable scene state

## Problem

On `demo["1TCD"]` (protein in chains A and B; **all water is chain A**), waters
(HOH) appear and disappear as a side effect of operations that should not change
*what is visible*, only *how it looks*:

1. `whole.set_representation("cartoon")` → cartoon + waters still visible.
2. `whole.set_color_scheme("chain-id")` → waters **disappear**.
3. `regions.add("chain_id=='A'")` + `region.set_representation("licorice")` →
   waters **reappear**.

## Suspected cause

`set_color_scheme` does not just recolor: it re-applies the representation
(`set_representation(self.representation, ..., color_scheme=...)`). Re-applying
`"cartoon"` to the whole hides atoms with no cartoon (waters), so a *color*
change ends up changing *visibility*. Adding a region and restyling then rebuilds
the scene and the waters come back. The net effect is that visibility of
non-polymer atoms depends on the order of unrelated styling calls.

## Expected

A color-scheme change should change color only, not which atoms are visible.
Representation changes should have a defined, stable rule for atoms the
representation cannot draw (e.g. keep their previous representation, or a
documented default), applied consistently whether reached via
`set_representation`, `set_color_scheme`, or region creation.

## Notes

- Not to be confused with the (correct) behavior that `show_only()` on
  `chain_id=='A'` keeps all waters — waters legitimately are chain A here.
- Likely related to the same scene-rebuild path as
  `region_color_by_attribute_not_rendered.md`.

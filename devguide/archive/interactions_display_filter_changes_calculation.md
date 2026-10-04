---
summary: Interactions display filtering silently changes calculation atom scope
issue: uibcdf/molsysviewer#159
status: resolved
opened: 2026-10-04
closed: 2026-10-04
severity: high
verification: reproduced
area: [interactions, studio, scientific-scope]
guard: molsysviewer/js/tests/e2e/interactions-calculation.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Interactions display filtering silently changes calculation atom scope

## What

In the real pentalanine widget, Buch with a 4 Å cutoff gives 20 observations
at local frame zero. One is incident to atom 5. Staging `[5]` as A under
**Display filter and selections** and calculating instead restricts the analysis
internally to that atom and reports zero. Inspect confirms calculation scope
`internal`, `atom_count=1`, `universe_count=1`.

## How

`js/src/ui/panels/interactions-panel.ts` uses the same A/B state for display
filters and calculation requests. A becomes scientific `selection`; any staged
B becomes `selection_2` for supported families, regardless of display mode.
There is no separately labelled calculation atom-scope control.

## Why

The accepted pre-1.0 Interactions plan requires independent, labelled calculation
and display scopes, defaulting to all atoms/current frame. A display filter must
not silently narrow evaluated coverage or suggest an absence of observations
outside that coverage.

## What was refuted

The real Python API independently reproduces 20 whole-system observations, one
incident to `[5]`, and zero for an explicitly restricted calculation. Provider
geometry and filtering work; the wrong scope originates in the Studio request.
The probe initially used nonexistent `observations(limit=...)` and
`n_occurrences` attributes; using `relation(0)` and `n_interactions` resolved those
probe errors. They are not provider defects. No provider patch is needed.

## Resolution

Calculation now defaults to all atoms and has an explicit all/A/between-A-B
control, independent of display filters. Missing, empty, overlapping or
unsupported scientific A/B scopes stop dispatch. Overlap validation uses a Set
and scales linearly in staged selection sizes. A retained between scope after
switching to disulfide candidates is refused explicitly; it is not silently
reinterpreted.

The real browser guard stages display A=`[5]` and B=`[6]` in incident mode.
The emitted whole calculation has `selection="all"` and no `selection_2`;
the actual provider returns 20 observations while the real Mol* set draws one.
Explicit within-A calculation returns zero with scope `[5]`. An explicit between
calculation reaches the public provider with both staged selections. Missing,
overlapping and unsupported selections are exercised too. Reverting the original
emission fails the all-atoms/absent-second-selection assertions and the scientific
20-versus-1 checks. All 17 existing calculation forms also pass; final lane time
is 155.557 s, without an E2E skip or deadline override. This is source/browser
qualification, not installed-artifact or hosted release evidence.

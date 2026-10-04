---
summary: Interactions query dock cannot stage a successful query result
issue: uibcdf/molsysviewer#158
status: resolved
opened: 2026-10-04
closed: 2026-10-04
severity: medium
verification: reproduced
area: [interactions, selection, studio]
guard: molsysviewer/js/tests/e2e/interactions-calculation.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Interactions query dock cannot stage a successful query result

## What

In an actual JupyterLab widget, open Studio → Interactions → Display filter and
selections → Select by query. Check `atom_index==5`: the preview reports one
atom, but active selection remains unchanged. Returning to Active selection
therefore cannot stage the queried atom as A or B. The canvas is drawing real
pentalanine, with local structures extracted in order `[0, 8, 3]`.

## How

`js/src/ui/panels/interactions-panel.ts` accepts the correlated query preview
but never requests `apply_selection_query`. The shared selection dock commits
active or saved selections; its query card provides preview controls. Selection,
Regions, Measures and Annotations request active selection replacement after a
successful current preview. Interactions omitted that step.

## Why

The advertised query route cannot feed the interaction filter. It can leave a
whole-system filter in place despite the successful one-atom preview.

## What was refuted

The Python query owner resolves the expression correctly. Preparing the same A
through the Selection panel works. No MolSysMT change is required. An initial
automation locator expected a nonexistent query-card `Use as A` button; this
locator failure was separate from the reproducible missing activation.

## Resolution

Studio now requests the existing public selection owner after a successful
current preview. Its query button says Select, matching the other consumers.
The real browser lane checks queries for A and B, rejection of stale replies,
and subsequent atom staging against a real pentalanine view. Reverting the
activation leaves no `apply_selection_query` event and fails the assertion before
the scientific calculation. No selection grammar or scientific logic is copied
into TypeScript. The adopted bounded browser guard profile is documented in
`reporting_protocol.md`; normal browser failures remain errors.

---
summary: Studio Shape creation accepts missing anchors and clears drafts before backend success
issue: uibcdf/molsysviewer#191
status: resolved
opened: 2026-10-09
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio Shape creation accepts missing anchors and clears drafts before backend success

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Creating a link without anchors returns successfully with zero created objects. The frontend submits missing endpoints and clears staged anchors before receiving any result.

## How

Validate prerequisites, return correlated success/failure, retain the complete draft on failure and show inline feedback; prevent duplicate pending requests.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

Creation validates nonempty/range-checked anchors, finite coordinates, positive
radius and distinct link/arrow centers. Missing prerequisites disable creation.
Runtime-only replies carry a matching request ID; the form retains its name and
anchors on failure, clears them on success and refuses duplicate pending requests.
The real browser guard submits a duplicate tag to real Python, checks retained
name/anchors and the error reply, then succeeds and verifies the reset.

The same guard exposed missing canonical selection forwarding to Shapes in
`GroupPanel.updateSelection` and `setSavedSelections`. Both now forward to the
owning panel. Adding fixture projections alone did not repair that wiring bug.
Focused Python creation/catalogue/batch checks pass 32/32 and the final real
browser guard passes.

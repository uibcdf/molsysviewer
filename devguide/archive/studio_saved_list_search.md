---
summary: Add scene-preserving search to Studio saved lists and the addon manager
issue: uibcdf/molsysviewer#195
status: resolved
opened: 2026-10-09
closed: 2026-10-10
verification: reproduced
area: [studio]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Add scene-preserving search to Studio saved lists and the addon manager

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Large saved lists require scrolling and lack consistent search/count/no-match feedback.

## How

Provide an owned reusable list-search tool for native saved lists and addons, preserve query/focus, search relevant names/types/text and show matched/total counts without changing scene or molecular selection.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

`ListSearch` is the reusable owner of local query state. All seven native saved
domains, stored scientific analyses and the Add-ons manager use it. Each domain
supplies meaningful tag/type/text metadata rather than action captions. Search
shows matched/total counts and no-match feedback; it sends no molecular action.
The final real browser guard filters each native domain, retains queries through
updates and verifies that searching/marking does not change the molecular
selection or emit scene actions. The maintained contract records ownership and
boundaries; the real browser guard passes.

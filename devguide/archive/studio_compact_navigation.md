---
summary: Adapt Studio and addon navigation to narrow cards
issue: uibcdf/molsysviewer#184
status: resolved
opened: 2026-10-09
closed: 2026-10-09
verification: measured
area: [studio, layout]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Adapt Studio and addon navigation to narrow cards

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

At a 480 px canvas, the fixed 180 px sidebar leaves about 158 px for forms, making inputs and controls hard to use. The same two-column structure is used for addon workspaces.

## How

Offer a compact section selector in narrow panels, retaining sidebar navigation in wide panels and preserving selected sections.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

The reusable CompactPanelNavigation owner replaces the sidebar below 480 px of card body width. Studio and domain-addon workspaces share it while retaining their own section selection. Settings remains reachable and Studio order follows configured tabs. The real-browser guard switches narrow/wide layouts, selects sections including Settings and tests compact addon navigation; its layout assertions preserve editor room.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.

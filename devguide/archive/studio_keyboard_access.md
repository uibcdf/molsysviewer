---
summary: Studio switches and form controls lack consistent keyboard access and accessible names
issue: uibcdf/molsysviewer#182
status: resolved
opened: 2026-10-09
closed: 2026-10-09
severity: medium
verification: inspected
area: [studio, accessibility]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Studio switches and form controls lack consistent keyboard access and accessible names

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

Settings and addon enable toggles are clickable divs without keyboard semantics. Shared checkbox labels and several Whole, Shapes, Viewport and Export form labels are unassociated. Focus styling is suppressed on selects.

## How

Use native controls and shared labelled control builders, preserve visible focus, and test keyboard activation in a real browser.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

Shared controls use native buttons, labels, checkboxes and switches, with accessible names and visible focus. Shared panel replies retain focus on named selects and checkboxes while accepting canonical values. The real-browser guard activates controls by keyboard and checks focus after a real Python reply and an Interactions projection update. This does not certify arbitrary external addon content or all Mol* accessibility.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.

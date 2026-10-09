---
summary: Make Studio Interactions acquisition, calculation scope and display controls easier to follow
issue: uibcdf/molsysviewer#185
status: resolved
opened: 2026-10-09
closed: 2026-10-09
verification: inspected
area: [studio, interactions]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Make Studio Interactions acquisition, calculation scope and display controls easier to follow

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

The creation form dominates the saved sets, A/B selections are hidden beneath display filters even when calculations require them, and experimental status is absent. Raw metadata and advanced visual options add noise.

## How

Keep all scientific capabilities while separating acquisition, calculation and display concerns, collapsing optional details and exposing experimental status and evaluated structure scope.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

Saved sets precede the collapsed new-set form; optional visual identifiers and raw metadata use disclosures. Experimental status remains visible, structure coverage explains current/all/indices, and restricted calculations expose A/B staging. The real-browser guard checks form disclosure and names; the existing Interactions calculation/lifecycle guards additionally execute 17 real forms and verify independent calculation/display scope. Opening the form does not compute.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.

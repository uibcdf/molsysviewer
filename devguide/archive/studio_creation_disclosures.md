---
summary: Unify optional creation and advanced disclosures across Studio subpanels
issue: uibcdf/molsysviewer#197
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

# Unify optional creation and advanced disclosures across Studio subpanels

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Creation forms dominate saved lists and panels use inconsistent disclosure/optional-field behavior.

## How

Use reusable native disclosures with persistent open state, retain drafts across tab/projection changes and open contextual workflows deliberately. Separate creation, saved objects and advanced settings while keeping required inputs visible.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

`PanelDisclosures` owns native creation/advanced disclosure state. An empty
panel initially opens creation; canonical saved items collapse the default unless
the user made an explicit choice. Contextual creation deliberately opens its form.
Advanced annotation offsets/leader controls are optional; required inputs remain
visible. Saved-list batch management is separately collapsed by default.
The final real browser guard checks initial defaults, explicit opening, advanced
state across frame/tab changes and contextual shape creation. It passes with
real Python/Mol*. The maintained contract records those persistent rules.

## Existing guard adaptation — 2026-10-10

The full core campaign stops at the old Regions guard filling a now-collapsed
creation form. The guard now opens the native disclosure explicitly and passes;
the original timeout is retained in the review evidence.

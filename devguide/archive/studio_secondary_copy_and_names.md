---
summary: Secondary Studio actions retain old terminology and anonymous icon controls
issue: uibcdf/molsysviewer#194
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

# Secondary Studio actions retain old terminology and anonymous icon controls

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Saved-selection annotation editors still display Label text/Add Label. The addon manager entry says Settings. Several visibility/delete controls expose symbols instead of explicit accessible names.

## How

Use Annotation consistently, distinguish Add-ons manager from canvas Settings, name all native icon actions and associated form fields; keep visible focus.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

Saved-selection actions consistently say Annotation text/Add Annotation;
annotation details say Annotation style. Wide and compact workspace navigation
identify Add-ons manager separately from canvas Settings. Native icon actions
receive names from their explicit action/target, and otherwise unnamed fields
receive stable accessible labels. Keyboard focus remains visible.
The real browser guard checks native field names and the annotation action flow;
updated Add-ons/GroupPanel unit assertions guard manager wording. JS regression
and the final real browser guard pass. This is native Studio coverage, not a
complete accessibility certification of arbitrary addon or Mol* content.

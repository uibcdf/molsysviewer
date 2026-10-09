---
summary: Studio descriptions advertise unavailable controls and use inconsistent annotation terminology
issue: uibcdf/molsysviewer#187
status: resolved
opened: 2026-10-09
closed: 2026-10-09
severity: medium
verification: inspected
area: [studio, text]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Studio descriptions advertise unavailable controls and use inconsistent annotation terminology

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

Layers advertises rendering depth settings; Export advertises coordinates and system-state files; Settings advertises caches. The current panels do not offer those controls. Selection annotation entry still says Label text.

## How

Describe the controls actually available, use Annotation consistently and distinguish browser HTML views from the experimental Qt standalone host.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

Studio descriptions now name the available Layers visibility, PNG/HTML exports and controls visibility settings. Annotation creation consistently says Annotation. HTML views explain live-Python editing, separate from experimental Qt hosting. The real-browser guard asserts those actual tooltips/names and verifies delivery; GroupPanel interaction exercises the renamed annotation entry.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.

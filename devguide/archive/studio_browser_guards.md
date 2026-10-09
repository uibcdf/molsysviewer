---
summary: Browser guards use obsolete annotation labels and sample startup fades unreliably
issue: uibcdf/molsysviewer#188
status: resolved
opened: 2026-10-09
closed: 2026-10-09
severity: medium
verification: reproduced
area: [tests, studio]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Browser guards use obsolete annotation labels and sample startup fades unreliably

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

Hosted core E2E 37993286307 stops in controls-visibility: buttons must paint intermediate opacity. The guard samples the first startup fade during molecular initialization. GroupPanel interaction still searches Add Label after the context-menu terminology changed.

## How

Diagnose the fade measurement before changing it, retain behavioral fade assertions with controlled browser readiness, and update obsolete labels to the actual annotation workflow.

The prior Python 3.14 source-pair run `37993286211` additionally timed out on
the sphere's actual hover telemetry after a successful rendered pick. The
guard now approaches from a distinct position after two browser animation
frames, retaining the same real-input hover, selection and marker assertions.
Cached unchanged cursor input is a possible timing mechanism, not an established
product defect. The next hosted source gate retains its own verdict.

The new Studio guard's first shared-browser run rejected `download.path()`:
Playwright requires `saveAs()` for a connected browser. It now saves both
downloads into an owned temporary directory and checks their actual bytes;
the repaired shared-browser guard passes. The suite inventory grows to 45
entries, including 42 core cases and the three deferred remote scenarios.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

The controls guard waits for actual molecular drawing before sampling the startup transition and retains an intermediate-opacity assertion for the whole group. GroupPanel follows the actual Annotation from Selection workflow. Sphere hover approaches from a distinct cursor position after two animation frames while retaining actual hover/selection/marker assertions. The new Studio guard uses saveAs for connected-browser downloads and the runner inventory is 45 entries (42 core). Scoped repaired guards and all 42 core cases pass across the retained campaign; the original failures are preserved and the next hosted verdict remains independent.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.

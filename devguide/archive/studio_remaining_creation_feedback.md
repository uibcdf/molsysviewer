---
summary: Studio region, selection and addon registration forms discard drafts before success
issue: uibcdf/molsysviewer#207
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio region, selection and addon registration forms discard drafts before success

**Reported:** Final Studio review with the principal maintainer, 2026-10-10.

## What

Regions, Selections and Add-ons module registration clear and close their forms when sending, before the backend confirms success. A rejected action therefore loses the draft, unlike the corrected Shapes/Measures/Annotations/Layers flows.

Observed on main a699f5b52729631643759942440c2afcb82e39f6 in the principal maintainer’s final Studio review.

## How

Reuse correlated completion feedback, retain drafts on errors, prevent duplicate pending submissions and clear only on matching success.

## Why

Authorized pre-1.0 Studio closure. Candidate 0.25.0 remains unfrozen; both 1.0 publications remain paused. Preserve real Python/Mol*/Chromium regression evidence.

## What was refuted

A successful normal-path smoke check does not cover rejection, replacement or exported backend availability. Source and live browser evidence do not qualify a frozen installed artifact.

## Resolution

The reusable `CreationFeedback` owner now covers region creation, active-selection saving, saved-selection rename/conversion and module registration. Matching replies alone complete a request; pending controls are disabled, failure preserves drafts and success clears them. Cross-domain replies reach the owning saved-selection editor. Registration failures retain diagnostics and emit a correlated failed result instead of appearing successful.

The executed real-Python/Mol*/Chromium `studio-list-workflows` guard checks pending region/selection names, successful clearing, atomic overwrite and Undo/Redo, then a real retired-module rejection with retained enabled draft, corrected registration and a cleared form when returning from the newly opened addon workspace. The original guard wrongly expected an invisible old catalogue input to be cleared before returning; the corrected guard asserts backend success and the rebuilt catalogue. Python also guards the actual correlated failed reply in `tests/test_studio_replacement.py`.

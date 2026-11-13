---
summary: Keep the actual-Jupyter Movie export field selector aligned with Studio.
issue: uibcdf/molsysviewer#383
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: low
verification: reproduced
area: [testing, jupyter, movie]
guard: tests/test_movie_studio.py::test_live_movie_export_field_matches_studio
normative:
blocked_by: []
supersedes: []
---

# Actual-host Movie owner uses the earlier output label

Controlled profile 767 passes five authoring/camera/seek/preview and shared
Python–Studio pause cases, then expires while looking up the old export-path
label. Studio added the portable HTML format; its accessible label now includes
that extension. Export has not started: all three controllers and Python are
idle/coherent without pending work. No product export failure is established.

The exact selector is updated to the current label. An offline check extracts
the current accessible field label from Studio and verifies the actual-host
owner uses it. Receive the entire existing notebook workflow, preserving every
scientific, archive, session, owner/cancellation assertion and operation bound
before closing this report. The four original notebook/browser owners are
independently hash-matched to 767 and preserved. Its native exit is 1, inputs
are unchanged and cleanup is complete without a resource stop.

The complete all-state acquisition before filing has four pages/353 issues,
excluding PRs, and no equivalent focused report was found. The broader #372
review and full source/platform/installed/human gates retain their own scope.

## Resolution

Actual-Jupyter `770` completes all eight original Movie cases: shared
Python/Studio authoring and pause, seek, camera, two-frame PNG/ZIP output,
independent session restore and cancellation of a held reply without a late
mutation. Output is 320 x 180 px; source coordinates and recipe remain intact.
Native exit is 0 with unchanged selected inputs and clean process retirement,
without a resource stop. The failed `767` attempt and its four hash-matched
original owners remain retained.

The named offline guard derives Studio's accessible field label and requires
the actual-host exact locator to match it. It passes in `769` and in the
complete corrected Movie module within `771` (860 cases across overlapping
affected modules; four actual-host skips remain skips). No test deadline,
scientific assertion or product behavior is relaxed. Current full source
qualification under #372 remains open independently of this focused closure.

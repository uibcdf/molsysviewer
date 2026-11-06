---
summary: Player navigation leaves Studio measurement summaries on the previous structure
issue: uibcdf/molsysviewer#312
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: high
verification: reproduced
area: [measurements, trajectory, panels]
guard: molsysviewer/js/tests/e2e/coordinate-edits.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Resolved: player measurement-summary projection

The actual widget/canvas-popup guard for #308–#311 additionally opens Studio
from the canvas popup. After a forward step both canvases draw structure 1,
including its correct centroid distance, but the detached Studio row remains
at structure 0's `224.66 picometer` rather than `217.05 picometer`. Both canvas
controllers retain measurement settings `structureIndex: 0`. The pm/radian
application policy and independent numerical oracle are retained.

`Player.go_to_structure()` sends a frame and trajectory summary, but omits
measurement summaries. All its navigation wrappers and UI authority intents
share this route. The separate playback frame-feedback branch does send them.
The correction projects current measurements after accepting player navigation
and before callbacks, without adding a renderer clock or claiming rendering
completion from Python acceptance.

Initial receiving failures are retained in
`/tmp/msv-centroid-coordinate-e2e-studio-final-20261106.log` and
`/tmp/msv-centroid-panel-diagnostic-2-20261106.log`. The latter's diagnostic
request reads existing Python summaries only; it does not inject a replacement
frame into the test. A prior test-only mismatch expected `pm` where the existing
formatter preserves the canonical label `picometer`; fixing that expectation
then reproduced this distinct stale-value failure. After the missing authority
projection is restored, the complete browser guard passes in 81.83 s, including
both canvas directions and the Studio popup's independent pm/radian values.

Final scope, original diagnostics and retained source hashes are in the
[measurement receiving receipt](../measurement_geometry_receiving_20261106.json).
Source correction does not qualify public artifacts or postponed human review.

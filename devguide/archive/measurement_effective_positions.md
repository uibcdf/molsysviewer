---
summary: Measurement handles omit centroid endpoints or return unaveraged atoms
issue: uibcdf/molsysviewer#311
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: high
verification: reproduced
area: [measurements, api, camera]
guard: tests/test_measurement_geometry_integrity.py
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Resolved: effective measurement positions and focus

For a centroid distance `[0, 2, 4]` to `[5]`, the old whole-list fallback
flattens `[[], [5]]` into one atom. `get_coordinates()` returns `(1, 3)`
instead of the promised `(2, 3)`. With two centroid endpoints it instead
returns every raw atom. `focus()` repeats this fallback and always reads the
first structure, even when another is visible. Real pentalanine frame 2
places participants outside the old first-frame camera bounds.

The scoped correction resolves each endpoint through the same private
explicit-nm reader used by measurement values, reads only the visible structure,
and returns one effective position per endpoint in application standard units.
Focus includes every effective participant population at the visible frame.
Broken/retired handles cannot invent positions or dispatch camera changes.

The initial real-system guard reproduces both wrong coordinate shapes and the
focus bound failure; representative, multiplicity, nonzero-frame and extracted
broken-handle controls are included. Source profile matches #308–#310 and the
initial failure log is `/tmp/msv-measurement-geometry-before-20261106.log`.
The final affected Python scope passes 160 cases, including real independent
positions, visible-frame focus bounds and broken/retired-handle rejection.

Final scope, original diagnostics and retained source hashes are in the
[measurement receiving receipt](../measurement_geometry_receiving_20261106.json).
Source correction does not qualify public artifacts or postponed human review.

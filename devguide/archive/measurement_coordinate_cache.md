---
summary: Partial coordinate edits leave live measurement values at old coordinates
issue: uibcdf/molsysviewer#310
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: high
verification: reproduced
area: [measurements, editing, trajectory]
guard: tests/test_measurement_geometry_integrity.py
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Resolved: measurement coordinate-cache reconciliation

After translating pentalanine atoms `[0, 2, 4]` by `[1.3, -0.6, 0.9] Å` in
structures `[2, 0]`, a centroid-to-atom distance has an independent current
value of 1.2786537542 Å but `series()`/`info()` keep 2.2465548711 Å. The accepted
edit changes coordinates correctly. Atomic/angle controls expose the same
cache issue. The previous #118 correction protects interaction coverage and
geometry; this is its measurement-specific continuation, not a native failure.

The scoped fix repairs affected measures before summaries are emitted. With
a full cache, it reads only edited structures and preserves untouched entries;
without one, it derives a full live series. Hidden measures are repaired too.
An undefined calculation drops the stale value. Rejected edits preserve data
and cached records. Full `set_coordinates()` previously passed its controls
because scene reapplication re-derived measures; partial edits did not.

The real fixture and guards are in
`tests/test_measurement_geometry_integrity.py` and the registered coordinate-edit
browser lane. Initial reproduction is retained in
`/tmp/msv-measurement-geometry-before-20261106.log`. The final affected Python
scope passes 160 cases; actual Mol* coordinate updates and session recovery pass.
Source profile matches #308/#309: Viewer `a994f89c` / public `737f9bc3`, owner
`7c7b92a7c`, native `ed09f6453`, PyUnitWizard `02d0015`, Python 3.14.

Final scope, original diagnostics and retained source hashes are in the
[measurement receiving receipt](../measurement_geometry_receiving_20261106.json).
Source correction does not qualify public artifacts or postponed human review.

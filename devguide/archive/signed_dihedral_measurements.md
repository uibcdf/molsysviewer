---
summary: Python dihedral measurements reverse the native and rendered signed convention
issue: uibcdf/molsysviewer#309
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: high
verification: reproduced
area: [measurements, api, units]
guard: tests/test_measurement_geometry_integrity.py::test_signed_dihedral_matches_projected_bonds_and_native_atoms
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Resolved: signed dihedral measurements

The Python measurement formula crosses the first normal with the central
bond, reversing the sign relative to MolSysMT and Mol*. Real pentalanine
structures `[0, 8, 3]`, ordered atoms `[0, 5, 9, 18]`, give Python
`[-43.21056421, -134.60476654, -55.69917355]` degrees versus native
`[43.21056421, 134.60476654, 55.69917355]`. An independent projected-bond
atan2 oracle agrees with the native route. This is independent of #308's
centroid adapter; single-atom endpoints reproduce it without a browser.

Source profile: Viewer `a994f89c` (public Python `737f9bc3`), owner contribution
`7c7b92a7c` / native `ed09f6453`, PyUnitWizard `02d0015`, Python 3.14.
Evidence: `/tmp/msv-dihedral-sign-native-20261106.log`. The complete four-page
inventory plus #308 had no equivalent signed-torsion issue at opening.

The scoped correction reverses that cross product. State/session recovery
already re-derives live measures from their recipes; tests deliberately supply
legacy opposite-sign cached values to ensure they are replaced. Positive and
negative atomic/centroid cases use real coordinates and a pm/radian policy.
The initial guard gives eleven failures/two controls passing across the four
related measurement findings. The first corrected scope passes thirteen cases;
the broader scope and actual canvas receiving retain separate result identities.
The final affected Python scope passes 160 cases; the actual-browser coordinate
lane passes all three kinds through edits/session recovery and both popup hosts.
The receipt below keeps failed test-authoring attempts and their diagnoses separate.

Final scope, original diagnostics and retained source hashes are in the
[measurement receiving receipt](../measurement_geometry_receiving_20261106.json).
Source correction does not qualify public artifacts or postponed human review.

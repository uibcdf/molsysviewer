---
summary: Receive immutable Conda provider v2.3.0 in local publication routes.
issue: uibcdf/molsysviewer#293
status: resolved
opened: 2026-11-03
closed: 2026-11-04
verification: inspected
area: [packaging, ci]
guard: tests/test_release_route.py
normative:
blocked_by: []
supersedes: []
---

# Conda provider v2.3.0 adoption — resolved in source

## Resolution and guard

Both local build/upload uses and promotion now pin
`87c70b1443d5f22d738ee3ddf812bdbe0152f6c2` (v2.3.0), following MolSysSuite #87
delivery `95f693be10c9205ab9b912cb53453710a207bf45`. Reviewed action metadata
accepts our inputs and producer-evidence outputs; promotion retains its exact
identity/digest/label/receipt contract. Unused `mambabuild: false` is omitted.
The local noarch recipe, tar.bz2 format, conversion flags, triggers, mandatory
tests, staging/direct decisions and installed-pair gates remain unchanged.

`tests/test_release_route.py` guards the promotion pin, evidence gate ordering,
labels and receipt. `tests/test_conda_receptor_evidence.py` guards both build
pins, structured evidence and staging/direct/package-test boundaries. The
combined publication/dependency/source/distribution selection passes 91 cases;
exact evidence is in [the receipt](../public_provider_distribution_receiving_20261104.json).

No shared workflow replaces the local publisher. No build, upload, promotion,
release, credential change or suspended route is activated. Provider fixtures
are not real registry qualification; old producer receipts and immutable bytes
remain unchanged. Hosted checks and future installed/public qualification keep
their separate scopes.

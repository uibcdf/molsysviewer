---
summary: Align the build backend minimum with SPDX license metadata.
issue: uibcdf/molsysviewer#292
status: resolved
opened: 2026-11-03
closed: 2026-11-04
severity: low
verification: inspected
area: [packaging, dependencies]
guard: tests/test_distribution_artifact.py
normative:
blocked_by: []
supersedes: []
---

# SPDX-compatible build minimum — resolved in source

The project declares MIT as an SPDX string but previously admitted Setuptools 64.
MolSysSuite #162 supplies the migration reference at
`41698b982ff56983a49c0089b135ed769a38b9da`.

## Resolution and guard

Setuptools 77.0.3 is now the explicit pyproject, Conda-host and build/test/source
environment minimum, including no-build-isolation routes. `license-files` and
Conda `license_file` explicitly include LICENSE. Original MIT copyright and the
packaged font notice are unchanged. The wheel fixture copies the real LICENSE.

`tests/test_distribution_artifact.py` rejects incompatible declared backends,
builds real distributions from the actual package/configuration and checks SPDX
metadata, exact project/font notice bytes and required resources. A wheel
rebuilt from the sdist must retain them. Three selected checks pass with both
development Setuptools 84.0.0 and an explicitly imported 77.0.3 overlay on
Python 3.14.7. The guard fails for pre-SPDX declarations or missing payloads.
The original floor discrepancy was inspected against backend capabilities;
no build using an incompatible pre-feature backend was attempted. Executed
minimum/current builds qualify the repaired declaration and actual payloads.

An initial test-only failure parsed Conda `python=3.14` as PEP 440; the corrected
test reuses the existing Conda parser. The
[receipt](../public_provider_distribution_receiving_20261104.json) retains inputs
and JUnit hashes. Builds use a package source copy with development-version
fallback, not a release producer. No old archive is alleged to omit a license,
replaced or requalified. Future exact-candidate/platform/package gates remain.

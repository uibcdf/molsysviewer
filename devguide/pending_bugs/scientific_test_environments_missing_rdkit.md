---
summary: Scientific test environments omit RDKit and fail during collection
issue: uibcdf/molsysviewer#161
status: partial
opened: 2026-10-06
closed:
severity: high
verification: reproduced
area: [ci, testing, interactions]
guard: tests/test_distribution_artifact.py::test_scientific_test_environments_include_rdkit
normative:
blocked_by: []
supersedes: []
---

# Scientific test environments omit RDKit and fail during collection

**Reported:** 2026-10-06 from the pre-1.0 audit of hosted CI logs.

## What

CI run `37349173743` and Python 3.14 source-pair run `37192007930`
stop collecting scientific tests with:

```text
tests/test_interactions_projection_batching.py:12
devtools/interaction_family_fixtures.py:14
from rdkit import Chem
ModuleNotFoundError: No module named 'rdkit'
```

Six importing test modules fail before behavioral qualification can run.

## How

The shared real molecular fixtures construct topology through RDKit, but
`test_env.yaml` and `test_source_pair_py314.yaml` do not provision it.
Declare RDKit in both test environments and the development environment that
runs these fixtures. Protect those routes with a distribution-contract guard.

## Why

Collection failure prevents scientific/public API regressions from executing
on the hosted matrices. RDKit is a fixture dependency; this correction does
not add it to mandatory package runtime requirements.

## What was refuted

The independent hosted core-browser failure is not caused by RDKit: its public
MolSysMT lacks `molsysmt.h5msm`. Provisioning RDKit cannot establish compatibility
of that published provider. Source-pair qualification and public installed
qualification retain their separate evidence requirements.

## Resolution

RDKit is declared in both hosted test environments and the local development
environment. The distribution-contract module passes 19 tests. Removing RDKit
from each environment in an independent temporary copy causes the guard to
fail with the affected filename (three rejected mutations).

The real nine-family scientific module passes 30 tests in
`molsyssuite@uibcdf_3.14`, using the local MolSysMT source. This confirms that
the fixtures execute locally; hosted provisioning and collection still need
confirmation at the pushed commit. Keep the report partial until that evidence
exists. Compatible public-provider qualification is a separate open gate.

The once-run complete source suite executes all 2,844 cases without collection
errors: 2,820 pass, 23 skip and the single failure is the independent profiler
guard #162. That guard is corrected and its 22-case scene module passes; the
complete suite is not repeated. Retain the actual outcome in
[the receipt](../ci_environment_repair_20261006.json).

---
summary: Unbounded MolSysMT and ArgDigest versions can make MolSysViewer unimportable.
issue: uibcdf/molsysviewer#62
status: resolved
opened: 2026-08-14
closed: 2026-08-14
severity: high
verification: reproduced
area: [argdigest, dependencies, packaging]
guard: tests/test_distribution_artifact.py::test_distribution_manifests_bound_the_shared_alias_contract
normative: devguide/digestion_and_dependencies.md
blocked_by: []
supersedes: []
---

# Unbounded alias dependencies can break import

**Reported:** 2026-08-14, during the release-readiness audit for MolSysViewer 0.21.0
against ArgDigest 0.12.0 and the planned MolSysMT 0.22.0 release.

## What

MolSysViewer declared `argdigest` and `molsysmt` without version constraints in both
`pyproject.toml` and `devtools/conda-build/meta.yaml`. A resolver could therefore install
ArgDigest 0.12.0 together with MolSysMT 0.12.0, after which this import failed:

```python
import molsysviewer
```

MolSysViewer constructs `AliasTable` objects at import time from MolSysMT's attribute
synonym catalogue. MolSysMT 0.12.0 contains `constraints -> constraints`; ArgDigest
0.12.0 rejects the identity entry with `ValueError` because a self-alias cannot perform
a rename.

## How

The failing path is
`molsysviewer/_private/argdigest/normalization/attribute_synonyms.py`, which passes
`dict(molsysmt.attribute._attribute_synonyms)` to `AliasTable`. This is intentional while
the two packages share a single alias source, but it makes the minimum MolSysMT version
part of MolSysViewer's import contract.

Commit `7eaf39275` removed the malformed entry from MolSysMT on 2026-08-08. No released
MolSysMT version contained that commit at the time of the report. The current catalogue
contains 155 effective aliases, zero self-aliases, zero ambiguous sources and zero alias
chains.

## Why

This affects the package import, not one optional viewer feature. Every public API is
unavailable even though the dependency resolver reports a valid environment. It also
blocks honest Conda dogfooding because source checkouts conceal the incompatible released
combination.

## What was refuted

The ArgDigest rejection is not over-strict. Its self-alias check is deliberate and has a
regression test; accepting the entry would hide malformed producer data.

Filtering `source == target` inside MolSysViewer was rejected. It would make this one old
catalogue load, but would falsely imply that MolSysViewer supports the rest of MolSysMT
0.12.0's substantially older molecular-system contract.

The declarative alias design itself is not defective. With current ArgDigest and
MolSysMT source, all 21 MolSysViewer normalization tests pass across `viewer`, `Region`
and `Whole`, and unrelated `atom_indices` arguments remain outside the alias scope.

## Resolution

MolSysViewer now requires `argdigest>=0.12.0` and `molsysmt>=0.22.0` in both its wheel
metadata and Conda recipe. A distribution guard fixes both floors as one compatibility
contract, and a normalization guard explicitly rejects any future self-alias arriving
from the upstream catalogue.

The private cross-package import remains bounded technical debt rather than an unstated
API. Its replacement by a public MolSysMT provider is tracked independently by
`uibcdf/molsysmt#157` and documented in `devguide/digestion_and_dependencies.md`.

## Correction — 2026-08-14

The final paragraph above described the state when this report was archived. MolSysMT
issue `uibcdf/molsysmt#157` subsequently introduced the public, versioned
`molsysmt.attribute.get_argument_aliases()` provider. MolSysViewer now builds its
caller-scoped tables exclusively from that plain-data contract; the two private imports
named in this record have been removed. The dependency floor remains necessary because
0.22.0 is the first MolSysMT release that provides the supported integration API.

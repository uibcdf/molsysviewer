---
summary: Dependency audit mistakes evidence actions for source checkouts.
issue: uibcdf/molsysviewer#136
status: resolved
opened: 2026-10-01
closed: 2026-10-01
severity: medium
verification: reproduced
area: [dependencies, ci, packaging]
guard: tests/test_dependency_contract.py
normative: devguide/dependency_contract.md
blocked_by: []
supersedes: []
---

# Evidence actions mistaken for source checkouts

**Reported:** 2026-10-01, while preparing a clean publication of the release and
dependency tools after upstream shared-governance changes reached main.

## What

`python devtools/audit_dependency_contract.py` returns exit 1 for the current
promotion and read-only installed-pair workflows, reporting an unclassified or
duplicate `uibcdf/molsysmt` source checkout. Both fields belong to evidence
actions; neither checks out the provider's code.

## How

The source-route scanner uses every step's `with.repository`, without first
checking the selected action. Restrict checkout classification to
`actions/checkout@...`; keep environment and runtime VCS-route checks independent.
Real undeclared or duplicate provider checkouts must still fail.

## Why

The false positive would block metadata CI and packaging when publishing the
auditor introduced under `uibcdf/molsysviewer#106`. The clean publication tree
and the primary working tree reproduce the same diagnostic.

## What was refuted

Adding evidence actions to the source-provider inventory would invent a source
installation route and incorrectly require checkout identity and environment
exceptions. Their repository input identifies external evidence, not local code.

## Resolution

Resolved. The scanner classifies provider source routes only for
`actions/checkout@...`. Other repository-valued actions still undergo their
applicable environment/VCS checks, but do not invent provider checkouts.
`tests/test_dependency_contract.py` passes 32 tests, including acceptance of an
evidence action and rejection of real undeclared or duplicate checkouts.

The clean publication tree passes 272 focused release/dependency/reporting
checks against public MolSysMT 0.22.4. Its single full Python run passes
2,284 tests with 15 skips, exit 0 in 250.97 seconds. Ruff checks/formatting,
the read-only metadata auditor and whitespace checks pass. Log:
`/tmp/msv-release-tools-public-full-20261001.log`.

This qualifies the independent publication block, not the larger scientific
working tree or a 1.0 artifact. The first isolated test launch lacked the ignored
generated `_version.py`; the configured Versioningit writer produced it before
the successful focused qualification. No runtime source or provider was altered.

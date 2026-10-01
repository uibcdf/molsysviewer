---
summary: Audit dependency floors and exact source pins before release builds.
issue: uibcdf/molsysviewer#106
status: resolved
opened: 2026-09-26
closed: 2026-10-01
verification: reproduced
area: [dependencies, packaging, ci]
guard: tests/test_dependency_contract.py
normative: devguide/dependency_contract.md
blocked_by: []
supersedes: []
---

# Audit dependency floors and exact source pins before release builds

**Reported:** Issue #106, attended on 2026-10-01 before freezing a 1.0 candidate.

## What

Add a read-only audit derived from `pyproject.toml` for the Conda recipe, all
runtime-bearing environments and exact source-pair CI providers. Classify
packaging-only exclusions explicitly. Verify installed controlled-source
versions and local checkout provenance before scientific consumers run.

## How

The route inventory belongs to `devtools/dependency_contract.toml`; it does not
repeat package floors or source SHAs. `devtools/audit_dependency_contract.py`
owns Viewer-specific comparison and release orchestration, using Packaging and
PyYAML rather than importing the scientific libraries. The recipe must match
canonical runtime requirements and Python bounds. Environment constraints may
narrow supported intervals but cannot widen them. Unsupported constraint
semantics fail closed. New recipes/environments or sibling source checkouts
require classification. Local-source checks bind installed distribution version,
`direct_url.json`, clean checkout and the requested full commit.

The audit runs before the wheel/Conda build, in the first release-gate step and
in metadata-only CI. Source-pair CI runs it after installation and before native
resource or scientific checks. The development environment is missing several
direct requirements and floors; correct them without changing public floors.

## Why

Past releases discovered incompatible source providers after costly builds.
Agreement among metadata files catches drift early but cannot establish that
the declared minimum version implements the API. Installed compatibility and
the experimental Interactions qualification remain separate gates.

## What was refuted

Inspected the existing owner tools before implementing: MolSysMT's pilot
`uibcdf/molsysmt#245` audits its own route schema, form registry, controlled
source file and native packaging. It is a repository-local script, not a
published cross-component audit API. MolSysSuite's repository-policy checker
owns shared policy, not this Viewer's packaging-route comparison. Reuse their
contract approach with a local inventory; do not copy native checks or add a
runtime dependency on a sibling development checkout. Public provider floors
are not inferred from a successful source pin.

## Resolution

Implemented the read-only audit and inventory, corrected the development
environment's missing requirements/floors, bounded the test environment's Python
range, and added explicit metadata readers to the packaging environment.
Public runtime floors and the existing exact MolSysMT CI pin were not changed.

The audit runs before wheel/Conda construction and upload, first in the local
release gate, and in an independent metadata-only CI job. Source-pair CI adds
installed version/local-origin/clean-commit checks immediately after installing
the pair and before native-resource or scientific consumers. A disabled check is
rejected even when YAML parses `if: false` as a boolean; the first focused run
caught that bug and the corrected predicate requires absence of any condition.

The guard passes **29 tests**: real subprocess reads of canonical and mutated
metadata, read-only checks, missing/weak floors, Python bounds, duplicate or
unclassified routes, disabled source checks, and real Git/distribution-metadata
fixtures for installed source version and origin. Related distribution, release,
promotion and shared-verifier checks pass **62 tests**. The actual local
`release_gate.py --only dependencies` also passes and explicitly reports that
the complete release gate was not run.

The single full source regression passes **2,464 tests, 23 skipped**, exit 0
in 316.90 seconds. It uses the previously qualified isolated MolSysMT export at
`ece35e622fc3f26c57f5261088fa07a39f081aca` and real Chrome selected at
`/usr/bin/google-chrome`. The checkout is still a development tree, not a frozen
release candidate. No workflow was dispatched and no package was published.
The new hosted source-audit invocation has not yet been observed on GitHub.
Installed fixture provenance does not authenticate installed scientific bytes;
the separate candidate/artifact and published Interactions gates remain required.

Logs: `/tmp/msv-dependency-contract-corrected-focused-20261001.log`,
`/tmp/msv-dependency-contract-packaging-focused-20261001.log`, and
`/tmp/msv-dependency-contract-full-python-20261001.log`. The durable contract is
`devguide/dependency_contract.md`; no sibling checkout was modified.

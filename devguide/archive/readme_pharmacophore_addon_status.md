---
summary: README addon maturity drifts from PharmacophoreMT's declared status
issue: uibcdf/molsysviewer#248
status: resolved
opened: 2026-10-20
closed: 2026-10-20
severity: low
verification: reproduced
area: [addons, docs]
guard: tests/test_readme_addon_table.py
normative:
blocked_by: []
supersedes: []
---

# README addon maturity drifts from PharmacophoreMT's declared status

**Reported:** 2026-10-20 during the single full Python core run for #247.

## What

`tests/test_readme_addon_table.py::test_the_reported_level_is_the_one_the_addon_declares[molsysviewer_pharmacophoremt]`
fails because the README reports `skeleton`, while the actual installed addon
declares `minimal`. The table vocabulary guard does not yet admit the provider's
observed declaration. README also describes a two-word shared vocabulary,
although the accepted #37 decision defines four levels.

## How

The readonly table is maintained in `README.md`; provider declarations are read
from `AddonSpec.meta['status']`. Update that row and recognize the provider term
in the existing guard, preserving its exact-provider comparison. Align the prose
with `experimental`, `development`, `beta` and `stable`, while reporting other
provider terms verbatim. This does not change the addon or promote its readiness.

## Why

The host reports each provider's declaration. It does not grade the scientific
or visual integration. Keeping the old word fails the existing test and misleads
readers about what the currently installed provider declares.

## What was refuted

The closed [uibcdf/molsysviewer#37](https://github.com/uibcdf/molsysviewer/issues/37)
settled ownership/vocabulary, and its [archived decision](../archive/addon_maturity_and_ownership.md)
remains unchanged. This later README drift does not reopen the host design or
assert production readiness. The Welcome correction's dedicated guards pass
independently; this failure was exposed by the broader installed-provider run.

## Resolution

Resolved on 2026-10-20. The row now reports `minimal` verbatim; the allowed
provider-description vocabulary includes that actual declaration, and prose
names all four accepted shared levels. Provider-specific words retain their
provider's meaning. No addon implementation, grading rule or production-readiness
claim changes. The existing exact-provider comparison, vocabulary and no-production
assertions pass with the real installed PharmacophoreMT addon. The combined
affected regression modules pass 14/14; the original global failure remains
preserved in [#247's receiving receipt](../initial_welcome_validation_20261020.json).

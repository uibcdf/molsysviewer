---
summary: Six emitted SMonitor catalog codes have no templates.
issue: uibcdf/molsysviewer#107
status: resolved
opened: 2026-09-26
closed: 2026-10-01
severity: medium
verification: reproduced
area: [diagnostics, smonitor]
guard: tests/test_smonitor_integration.py::test_every_catalog_entry_has_a_template_smonitor_can_resolve
normative:
blocked_by: []
supersedes: []
---

# Six emitted SMonitor catalog codes have no templates

**Reported:** Issue #107 opened on 2026-09-26; reproduced during the pre-1.0
public-surface closure on 2026-10-01.

## What

The catalog has 48 entries but only 42 renderable message templates. The six
missing keys are `addon_lifecycle_failed`,
`dynamic_region_evaluation_over_budget`, `index_map_degraded`,
`suppressed_exception`, `webgl_context_lost`, and `webgl_context_restored`.

```python
from molsysviewer._private.smonitor.catalog import CATALOG, MESSAGES
print(len(CATALOG), sorted(set(CATALOG) - set(MESSAGES)))
```

These entries are emitted by addon lifecycle, dynamic-region, index-mapping,
recovery and frontend WebGL event paths. Emission without caller text can
produce an empty message; fallback prose can hide the missing template.

## How

`CODES` in `molsysviewer/_private/smonitor/catalog.py` is derived from `MESSAGES`,
so a catalog entry without a message never reaches the profile dictionaries.
The existing integration guard iterates `MESSAGES`, silently excluding those
entries. The corrected guard must start from the full catalog, then verify
all profile fields. Templates must use the exact fields emitted by each call
site; the index-mapping and WebGL templates cannot require absent context.

## Why

Users and developers need readable diagnostics when addon lifecycle hooks fail,
dynamic selection exceeds its budget, atom mapping degrades, an exception is
recovered, or the browser reports WebGL context changes. Published code names,
levels, sources and recovery behavior must remain stable.

## What was refuted

This is not a missing-catalog defect: all six metadata entries already exist.
Passing the old guard did not establish catalog completeness. Modern SMonitor
profile fallback also cannot supply a template absent from every profile.
A generic index-map message must not promise a specific fallback, and a WebGL
restoration message must not claim full scene reconstruction.

## Resolution

The six messages now have templates using the actual emission fields. Code,
source, category, level and recovery behavior remain unchanged. The full-catalog
guard checks missing templates as well as the code and profile dictionary shape.
Five profile cases use real SMonitor emission for all six diagnostics and check
readable text, retained context and absence of unresolved placeholders.

Focused verification: `tests/test_smonitor_integration.py` passes **12 tests**
(exit 0, 5.36 seconds). The official SMonitor integration verifier passes
configuration, template coverage, rendering and reserved-field checks: **one
package checked, zero failures**. SMonitor is the clean local provider at
`b308ee08b4624e8f4029c08c5e61391b1b5714b1`.

The one complete regression attempt finished with **2,433 passed, 23 skipped,
one failure**, exit 1 in 317.91 seconds. The failure was the existing generic
template test supplying string sentinels to numeric `:.2f` placeholders. Its
context now supplies the actual numeric types, and expected substitution respects
standard format specifications and conversions. The five real-emission cases
already passed with those numeric types. After correcting that fixture, the
combined template and integration modules pass **95 tests, 14 skipped**, exit 0
in 5.15 seconds. The skips are the placeholder-substitution cases for templates
without placeholders. A second complete run was not performed, following the
repository's once-per-task test-run discipline; this record does not claim a
fresh all-green complete suite.
Log: `/tmp/msv-smonitor-templates-full-python-20261001.log`.

The guard starts from all 48 catalog entries, so removing any template fails
even if fallback text hides the defect at runtime. The profile cases separately
verify actual rendering. The full run uses the previously qualified isolated
MolSysMT export at `ece35e622fc3f26c57f5261088fa07a39f081aca`, with real Chrome
selected at `/usr/bin/google-chrome`. No sibling checkout was modified.
Focused logs: `/tmp/msv-smonitor-templates-focused-20261001.log` and
`/tmp/msv-smonitor-templates-corrected-focused-20261001.log`.

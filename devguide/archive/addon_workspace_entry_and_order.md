---
summary: Addon workspaces ignore declared panel order and entry panel
issue: uibcdf/molsysviewer#303
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: medium
verification: reproduced
area: [addons, navigation, studio]
guard: molsysviewer/js/tests/unit/addon-panel-lifecycle.test.ts
normative: docs/content/developer/addons.md
blocked_by: []
supersedes: []
---

# Provider-defined workspace navigation

The two-panel MolSysMT workspace opened Geometry and placed it before System,
although its provider declares System order 10, Geometry order 20 and
entry_panel=system. Real Jupyter receiving exposed the error; the earlier
single-panel workspace could not distinguish alphabetic fallback from the
provider contract. Closed #245 concerns endpoint lifecycle, not this mechanism.

Controller normalization discarded workspace/panel order and the entry-panel
field, sorted alphabetically and selected the first panel. Preserve finite
provider orders with deterministic ID/key tie-breaking, and use a valid entry
panel only when there is no valid remembered user selection. Missing or retired
entry IDs fall back to the first ordered available panel. No new spec API or
scientific algorithm is needed.

The frontend unit guard exercises actual normalization/selection methods without
DOM/molecular substitution: declared ordering, entry preference independent of
order, remembered choices, retired entries, empty workspaces and default order.
Real Jupyter System/Geometry/popup receiving passes on the corrected runtime;
exact-head CI and explicitly postponed human review remain separate.

## Resolution

The controller preserves declared order/entry metadata, prefers a valid entry
only at initial selection and retains valid user choices. The registered unit
lane passes; all three actual-Jupyter System/results/Geometry scenarios pass
on the rebuilt runtime, including canvas/Studio popups. The complete qualified
core selection passes 3,464 cases, with 21 justified skips and 15 deselected
Qt-runtime cases. The guard exercises ordering independently of entry preference,
remembered choices, retired/missing entries and deterministic defaults. Source
closure leaves hosted exact-head, owner, human and installed qualification
separate. See [the receiving record](../molsysmt_geometry_receiving_20261106.json).

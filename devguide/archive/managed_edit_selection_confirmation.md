---
summary: Managed edit confirmation blocks selection readback during preparation
issue: uibcdf/molsysviewer#302
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: medium
verification: reproduced
area: [addons, selections, system-edits]
guard: tests/test_managed_system_edits.py::test_saved_selection_revalidation_is_limited_to_synchronized_preparation
normative:
blocked_by: []
supersedes: []
---

# Managed selection confirmation

A reviewed selection can fail at confirmation before native science starts.
`execute` marks the coordinator editing before invoking its read-only plan
preparation. Saved selection membership uses guarded `SelectionsManager.get`,
`Selection.info`, manager info/records/contains; active selection readback uses
`InteractionMixin.get_last_active_selection_event`. Both paths are needed to
reject a changed selection atomically under the edit lock.

Reproduced on Viewer 3aa9b0f9/runtime 42234de8 with the MolSysMT PR #543 source
profile, native ed09f6453, Python 3.14 and the fixed PyUnitWizard 02d0015 source
receiver. Saved [2,4] can be reviewed, but confirmation raises
`SystemEditPendingError`. Subsequent consumer coverage isolated the same
mechanism for the active canvas selection. Regions do not use these readers.
The complete 300-record paginated issue/PR inventory contained no equivalent.
Closed #297 concerns addon metadata delivery, a separate boundary.

The fix grants only the named host readers a preparation-scoped permission,
only when the operation starts synchronized and under the coordinator lock.
It ends before native execution, resets after preparation failure and never
authorizes scene mutation. Pending/failed scene reads and normal concurrent
edit guards remain unchanged. No new public API or scientific implementation
is introduced.

## Receiving

The 13-case real-demo host coordinator file passes after the expanded active
selection guard (5.57 s, 14 retained legacy-H5MSM warnings). The owner System
panel file passes 50 cases (14.17 s, 48 retained legacy-H5MSM warnings), including
actual confirmation of saved/current/region selections, exact retained native
coordinates, one managed revision and single-use tokens. These are source
receiving, not installed-package or human GUI acceptance. The first consumer
run retained 49 passes and one active-selection failure; its diagnosis supplied
the additional exact host reader above.

Hosted exact-head validation remains separate. The owner contribution
retains the new regression in PR #543 and pins the published host fix.

## Resolution

Source fix 04db965b passes the complete qualified core selection: 3,464 passed,
21 justified skips and 15 deselected Qt-runtime cases (545.83 s). Native panel
receiving passes 83 shared System/Geometry cases; all three actual-Jupyter
scenarios pass, including confirmed saved/current selections. The guard asserts
preparation-only readback and prohibits mutations, science-time reads and pending
scene reads, with digestion enabled and bypassed. Source closure does not claim
owner integration, human acceptance or installed qualification. See
[the receiving record](../molsysmt_geometry_receiving_20261106.json).

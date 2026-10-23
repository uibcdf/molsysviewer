---
summary: Qualify the redesigned MolSysMT addon host and molecular-edit reconciliation.
issue: uibcdf/molsysviewer#264
status: partial
opened: 2026-10-22
closed:
verification: inspected
area: [addons, editing, api]
guard:
normative:
blocked_by: []
supersedes: []
---

# Receiving the redesigned MolSysMT tools addon

**Reported:** 2026-10-22, accepted maintainer direction after reviewing the
[addon plan](../molsysmt_tools_addon_plan.md).
**Status:** partial implementation: the new discovery route, closed-view boundary
and actionable state-factory failures are delivered for initial read-tool source
receiving. Editing/synchronization and installed qualification remain pending.

## What

Receive the provider-owned tools addon under `view.addons.molsysmt` with safe
host registration, lifecycle and molecular reconciliation. MolSysMT owns the
scientific facade and its tools under uibcdf/molsysmt#421. Viewer owns its
reusable host and scene correspondence boundaries. Its current backend remains
available independently of addon panels.

## How

The [receiving contract draft](../molsysmt_addon_receiving_contract.md)
specifies the state model, proposed facade integration controls, mapping and
failure cases to qualify. It extends the accepted plan rather than promising a
general observer or restoring the retired module wholesale. The provider source
ledger covers all 267 exports in its stability registry's tracked scopes at
`fe5036c1f4c145ec2eecf1627e80eb70fc995618`. It includes root aliases and support
objects; it is not 267 independent scientific tools or implemented wrappers.
Untracked namespace contents and per-function effects still require disposition.

Inspect Viewer at `e8ed36d3`:

- `molsysviewer/addons.py` refuses the legacy namespace/module and silently
  substitutes an empty namespace when a state factory fails.
- `molsysviewer/viewer/core.py::apply_system_edit` accepts atom correspondence,
  not general structure correspondence. Same counts declare unchanged structure
  order. The method installs the new system before finishing the rebuild.
- Interaction invalidation defaults conservatively to clearing coverage, and
  the rebuild clears scene history. Neither gives molecular rollback.
- `close` releases widgets/transport; addon calls need a qualified closed-view
  boundary, not inference from a browser window disappearing.

## Why

A scientific edit must not leave live controls addressing old indices. An edit
that succeeded must not run twice because synchronization failed. The API also
needs to remain usable headlessly, with cached tool references following later
loads, while panel activation remains a presentation choice.

## What was refuted

Reverting the legacy retirement does not supply the new expert API or lifecycle.
Passing every edit through unchanged `apply_system_edit` cannot certify frame
reorders, repeated structures or selective scientific invalidation. A new generic
observer is unnecessary; uibcdf/molsysmt#413 remains withdrawn and closed.
An integration flag does not provide molecular Undo or a universal transaction.

## Acceptance criteria

Close after compatible discovery and factory diagnostics, lifecycle guards,
headless reconciliation, pending-state safety, operation-specific maps and
scientific validity are implemented and tested with real systems. Include
replacement/cached facade, disable/close, partial writes, failed synchronization,
nonconsecutive/repeated structures, source records, anchored objects and recovery
without repeated science. Qualify actual Jupyter/popup receiving and installed
compatibility separately; do not substitute source/export counts for those gates.

## Dependencies and risks

Coordinate with uibcdf/molsysmt#421. The current backend minimum is unchanged.
The source-ledger baseline is not a release candidate or public dependency floor.
Generic factory-failure handling must retain actionable diagnostics for every
addon while preserving legitimate factories returning their intended values.
Do not include unrelated local work or change legacy guards before the new
compatibility route exists.

## Initial read-tool receiving

The host admits `molsysviewer_molsysmt.tools` while ignoring retired root entry
points before loading and refusing explicit legacy-module registration. The
provider declares the new entry point; no hardcoded known-module entry is added.
Addon state factories now record/propagate original failures, remain retryable
and clear their record after a successful retry. `view.closed` explicitly
exposes view lifetime for bound expert API calls and close is idempotent.

Provider `tests/molsysviewer_molsysmt/test_read_tools.py` receives actual basic
queries, signatures/defaults/help, native result/error parity, nonconsecutive
structure coordinates with units, replacement/cached methods, panel deactivation,
two views, empty/closed targets and standard metadata discovery in a fresh
process. These tests exercise the real provider and demos; they are not proof of
new edit/map APIs, task panels or installed artifact qualification. Viewer
`tests/test_addon_factory_failures.py` guards the failure/retry boundary and
`tests/test_view_lifecycle.py` guards explicit closure and widget release.

The [dated source receipt](../molsysmt_addon_read_receiving_20261022.json)
records the 46 provider read/packaging checks, host focused receiving and the
full core result: 3,235 pass, 21 skips and the known #263 fixture failure.
That full run is not green. Both Sphinx builds complete; provider warnings
remain visible. Development editable metadata now exposes the actual new entry
point, observed with a real dialanine view; this is not clean solver or release
artifact qualification. Preserved concurrent provider changes remain explicit
in the receipt's provenance.

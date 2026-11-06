---
summary: Inherited addon metadata transport is blocked during managed-edit recovery.
issue: uibcdf/molsysviewer#297
status: resolved
opened: 2026-11-05
closed: 2026-11-05
severity: high
verification: reproduced
area: [addons, scene]
guard: tests/test_addon_panel_pending_state.py::test_inherited_metadata_transport_survives_pending_state
normative: devguide/addon_panel_widget_contract.md
blocked_by: []
supersedes: []
---

# Addon diagnostic delivery during managed-edit recovery

## What

A consumer subclass cannot use inherited `push_state`/`set_state` while a
molecular projection is pending or failed. Reporting completed science then
fails with `SystemEditPendingError`, concealing the recovery instructions.

## How

Reproduced on Viewer 7d9f689c with real dialanine and the source MolSysMT panel.
The guard identifies management by the instance's module, so a consumer
subclass does not inherit the host transport exemption. The helpers also
unnecessarily try to acquire a molecular read lock. A real native removal
with an injected host projection failure exposes the same diagnostic failure.

## Why

Status/draft transport must remain usable while molecular commands are paused.
Allowing arbitrary same-named overrides would bypass the scientific boundary.
Pending addon actions must remain blocked; recovery belongs to the existing
canvas Update view control and must not repeat scientific computation.

## Resolution

The guard receives the actual decorated function and exempts only the two
host-owned implementations, independently of the consumer instance's module.
Three native-view guards cover pending transport, a foreign molecular read
lock and rejection of a same-named consumer override. Seventeen related host
tests pass. Thirty-two real addon panel tests additionally exercise completed
native removal plus failed projection and synchronization-only recovery.
The real-browser receiving flow verifies the existing canvas Update view path.
Endpoint/widget lifetimes and scene command guards remain unchanged.

This is source/runtime receiving, with separate hosted CI, live Jupyter/Qt,
popup and installed-artifact qualification. The owning source receipt is
linked from the current addon receiving checkpoint; no release is authorized.

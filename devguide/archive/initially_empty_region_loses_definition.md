---
summary: An initially empty region loses its renderer definition and cannot reappear.
issue: uibcdf/molsysviewer#341
status: resolved
opened: 2026-11-08
closed: 2026-11-08
severity: medium
verification: reproduced
area: [regions, trajectory, popup, restoration]
guard: molsysviewer/js/tests/e2e/region-hide.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Initially empty region loses its definition

## What

After the #340 callout correction, full moving receiving passes primary state
and session, then captures a popup state and rejects its native region count:
frame zero has zero atoms instead of one. The source uses an infinite dynamic
selection budget, so the #189 budget-freeze mechanism is excluded. Bootstrap
creates `moving-near`, but leaves no native tag, and later owned memberships
cannot restore its geometry. The run retains 4,330 unchanged selected inputs,
all thirteen owned processes closed and no resource stop. Later moving roles
and presentation do not execute.

`StateHandlers.createRegion` exits before registering a RegionEntry when the
initial evaluated selection is empty. `setDynamicRegionAtoms` skips an unknown
tag; it cannot recover the lost definition. Representation changes also return
before storing their style when no component exists. This differs from the
existing empty-after-update path, which retains the RegionEntry.

## How

An explicitly empty atom-index list keeps a complete region definition and no
native component. Reject invalid nonempty indices as before. Later valid
membership materializes components and representations from the retained
definition. Changes to representation, visibility, enablement and ordering
while empty remain effective. Repeated empty/nonempty transitions and deletion
must preserve their usual semantics.

## Why

Opening a popup or restoring a scene on an empty frame must not delete a dynamic
region. A scientific definition exists independently of its current selection.
The complete native region guard now includes real pentalanine initial-empty
and repeated membership controls, including latent style/hidden/disabled state
and a late reply after deletion. Its older direct dynamic-message fixtures now
declare the actual current frame, matching the #338 transport contract rather
than bypassing its stale-frame check.

## Receiving

The complete native region guard fails before correction specifically at the
missing initial definition (13.18 s), after all existing visibility/isolation
assertions pass. The working fix retains explicitly empty definitions while
preserving rejection of invalid nonempty indices. Representation changes update
their latent definition even without a component. The full guard then passes
in 13.90 s, including repeated cycles, hidden/disabled materialization and late
deletion replies, with 4,331 unchanged selected inputs and thirteen owned
processes closed. Strict builds and all 428 canonical Node cases pass. Full
combined moving receiving remains in progress.

The original full failure is
`A5-native-profile-20261108/endpoint-after-05`; its successful primary cases
do not qualify its failed popup or unexecuted roles. The full issue inventory
has pages 100/100/100/39. Closed #189 concerns Python's budget freeze, #332 the
restoration frame, and #338 query ownership; none retains an initially empty
renderer definition. #319 and publication remain open/paused.

## Resolution — 2026-11-08

Resolved in reviewed source. Explicitly empty regions retain identity and latent style without a component. Real native before/after lifecycle and final popup/detached moving restoration pass; invalid nonempty selection rejection and deletion behavior remain protected. The [final source receipt](../moving_capture_font_and_region_receiving_20261108.json) records commands, exact input witnesses, retained failures, resource limits and cleanup. Public capture capabilities remain v1; publication stays paused.

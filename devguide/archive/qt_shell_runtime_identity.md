---
summary: Qt shell and persistent scene owner use different runtime identities.
issue: uibcdf/molsysviewer#342
status: resolved
opened: 2026-11-08
closed: 2026-11-08
severity: medium
verification: reproduced
area: [qt, transport, trajectory, interactions, regions]
guard: tests/test_qt_live_capture.py::test_qt_live_capture_full_render_gpu
normative: devguide/transport_state_ownership.md
blocked_by: []
supersedes: []
---

# Qt shell runtime identity

**Resolved in source — 2026-11-08:** the shell borrows its persistent View,
the channel binds that owner's immutable identity, and actual Qt moving saves,
scientific query ownership, empty/frozen regions and construction-failure cleanup
pass. The [receipt](../qt_native_moving_identity_receiving_20261108.json) retains
original failures, exact inputs and private custody. A5 stays partial.

## What

The actual Qt continuous-capture guard receives four stopped-scene save/restore
cases and cancellation, then fails its scientific-query precondition. A second
directed native attempt proves that the frontend's query owner differs from the
persistent View's session. Python correctly rejects this foreign owner.
Both native attempts retain fixed inputs, complete owned cleanup and no resource
interruption. Two headless real-view controls independently fail the empty
Qt-channel identity and missing binding hook.

The complete 100/100/100/40 REST inventory contains 312 issues, including closed
records. #270 concerns absent live authority and #337/#338 per-request routing;
none owns this initialization mismatch. Original evidence is in the private
`A5-qt-moving-20261108` workspace. This is source receiving, not a package or
human observation.

## How

Before correction, the Qt constructor built HTML using a temporary empty View,
then constructed the real persistent MolSysView. `bootDocsView` retained that
temporary identity. QtViewChannel lacked the existing identity-binding hook.

The constructor now uses the persistent View through the existing borrowed-owner
HTML route. Project/add-on preparation remains before View construction and
is not repeated during borrowed HTML generation; the actual project-config
control receives Cinema on the correctly bound owner. Channel binding is atomic, idempotent and immutable, and rejects
closed channels. Shell-build failure closes the new View/bridge/page/profile
without persisting unfinished geometry. Strict query-owner rejection and the
ordinary targeted reply protocol remain intact.

## Receiving

The two directed identity controls fail before correction, then the affected
three-case selection passes. Actual Qt receives four stopped and four moving
state/session cases on the corrected owner. The final extended native guard
also receives an empty frame-1 state/recovery, a genuine budget freeze computed
at frame 0 but drawn with frame-1 coordinates, and a real shell-writer failure
without caller/state loss. It passes in 43.25 s with 4,587 fixed inputs, seven
owned processes closed, no resource stop and the real Wayland/NVIDIA WebGL2
renderer. Each moving save waits for two actual frame changes and genuine
scientific replies; its native interaction presence matches the scientific
query's occurrences. The 488-case headless boundary passes separately. The final record/identity
selection passes 409 cases; its four legacy-H5MSM warnings are retained.

The shared browser moving entry passes all seven saves/restorations and both
annotation projections in 92.13 s. The lifecycle entry passes in 92.29 s.
The broader native Qt workbench passes ten binary replacements, genuine file
input/Cancel/Open, exports and independent host lifetime in 30.26 s, after
the separately reopened #287 fixes modal activation in its fixture. Its
exact-source hosted qualification remains tracked there.

Continuous Qt saves preserve original deadlines, two actual frame changes,
native geometry, independent headless file recovery and source coordinates.
Native Qt popouts and independent-window file restoration are not received.
Actual Jupyter continuous capture and consolidated/installed acceptance remain
under #319; Qt stays experimental, v2 unadvertised and publications paused.

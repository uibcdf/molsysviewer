---
summary: Independent exported HTML starts slowly while other molecular canvases draw.
issue: uibcdf/molsysviewer#400
status: active
opened: 2026-11-16
closed:
severity: medium
verification: measured
area: [export, rendering, performance]
guard: molsysviewer/js/tests/e2e/trajectory-plot.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Independent HTML initialization with other live canvases

**Pre-1.0 under #315.** The numerical plot correction belongs to #321;
this report owns the separate initialization boundary reached before its
precision controls. Closed #391 corrected streamed reply ownership and
hidden-iframe polling; no recurrence of that mechanism is established.

Local canonical `959` and source run `43796373853` miss the unchanged
30-second exported-controller guard; first-controller observations arrive
at 37.23 and 42.392 seconds. The document is visible, a canvas exists and
there is no recorded page/request error. Current input is declared Mol*
5.13.1 and real Chrome/SwiftShader, with three other live molecular canvases.
The [receipt](../residual_four_issues_receiving_20261116.json) identifies each
Node version, native input, resource limit and distinct receiving scope.

Private Node-22 diagnostic `966`, at 4 CPU / 4 GiB, retains a native CPU
profile: state/extension/context initialization dominates, including 11.22 s
in `createState`. Bare unmodified Mol* control `969` initializes in 0.470 s,
but has different context attributes and no other live canvases. Do not
infer an upstream defect or universally slow initialization from either.

Diagnostic `972` stops the other three actual native draw loops during
initialization, then restarts them. With the same Node, resource ceiling
and profiler, the static profile takes 6.551 s and the complete plot entry
passes in 150.30 s, including all fifteen Decimal controls and independent
HTML/hidden-iframe coordinates. This discriminates draw-loop interference;
the scheduling intervention is not an accepted production fix or canonical
qualification. Original failures and setup-only errors remain preserved.

Investigate native scheduling and choose a bounded solution that preserves
the other views' ordinary interaction and animations. Do not silently stop
another view, prewarm the guard, change rendering quality, weaken numerical
or molecular assertions, or increase initialization's bound just to pass.
Receive the unchanged complete trajectory-plot entry, retaining physical
coordinates, authority, independent exports, popup behavior and raw values.

Duplicate review uses four complete pages, 371 issue/PR records and 345 issues,
including closed records. #47 is deferred editorial export review, #391 has
a different resolved mechanism, and #399 owns receiving preparation.
No release, native-GPU throughput or installed qualification is claimed.

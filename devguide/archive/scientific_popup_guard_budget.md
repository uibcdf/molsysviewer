---
summary: Expanded scientific popup guard exceeds the former 180-second CI suite budget
issue: uibcdf/molsysviewer#244
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: measured
area: [testing, ci, popup]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/reporting_protocol.md
blocked_by: []
supersedes: []
---

# Expanded popup guard exceeds its former CI budget

**Reported:** 2026-10-13 while receiving the exact `c9471fe3` source CI.

## What

Official core browser run 38442809908 fails with
`controls-visibility exceeded 180000 ms`. Its exported controls scenario passes
at 39 seconds, notebook controls at 57 seconds, then the runner kills the
scientific mirror before its completion report. The source result remains
failure; no hosted scientific completion is inferred from the timeout.

## How

The same bounded entry now executes three real scenarios with independent
Python bootstraps, calculated hbonds, native picking, camera and playback
receiving. Its outer runner still used the earlier two-scenario allowance.
The proposed correction gives only `controls-visibility` a 300-second default;
all other suites keep 180 seconds and explicit `E2E_SUITE_TIMEOUT_MS` overrides
retain their precedence. Phase timing identifies future scientific stalls.

## Why

The complete receiving guard must execute in canonical CI. Its expanded scope
must not be silently omitted or mistaken for a passed result after termination.

## What was refuted

The failed run contains passing first/second scenario reports; neither setup
failure nor an explicit assertion failure is reported as the termination cause.
Local receiving passes retain their own scope. The allowance correction is not
a claim that a real stalled assertion cannot exist: fresh hosted progress and
completion must still be received. Experimental Qt and uibcdf/molsysviewer#240
remain independent.

## Resolution

Runner correction and phase instrumentation are implemented; the specific
three-scenario guard passes through the shared runner, with scientific completion
at 83 seconds from its own start. Seven E2E-policy guards pass; other suite
defaults and explicit override behavior retain their existing code path. Fresh canonical hosted evidence was received below. No assertion, suite selection or explicit failure/skip policy
is weakened, and production runtime bytes do not change.

The tested correction is integrated at `9616b22c`; fresh canonical browser
38446898982 and source/core campaigns retain their own receiving identity in
`devguide/canvas_popup_mirror_validation_20261013.json`. The hosted closure below completes that requirement.

## Hosted closure — 2026-10-13

Exact source `9616b22c` finishes canonical browser run [38446898982](https://github.com/uibcdf/molsysviewer/actions/runs/38446898982) with 43/43 core suites. The full controls entry takes approximately 189 seconds and the scientific scenario reports completion at 132 seconds from its own start, within the scoped 300-second allowance. GH Run Receptor independently returns PASS/success. The retained log digest and exact receiving status live in [the mirror receipt](../canvas_popup_mirror_validation_20261013.json). The old 180-second failure stays preserved; this result does not qualify #240, installed packages or experimental Qt.

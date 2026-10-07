---
summary: Repeated Python cold starts make Interactions core E2E exceed its deadline
issue: uibcdf/molsysviewer#154
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: medium
verification: reproduced
area: [testing, interactions, ci]
guard: tests/test_e2e_reliability.py::test_all_interactions_scenarios_keep_default_deadlines_and_fresh_worker
normative:
blocked_by: []
supersedes: []
---

# Repeated Python cold starts make Interactions core E2E exceed its deadline

**Resolved — 2026-10-07:** the published producer contains the persistent
fixture transport and all three mandatory Interactions scenarios. Fresh worker
and runner guards pass against the public pair and source rules; the complete
39-suite hosted core passes within the normal per-suite deadline. Earlier dated
failed attempts retain their verdicts.

**Current qualification — 2026-10-06:** implementation is committed and
integrated in Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0. All
sixteen installed staging cells and 39 hosted core browser suites pass;
canonical-source Python 3.14 integration passes on all three native hosts,
with 25 documented notebooks passing on Linux. This report remains partial
for its public-provider/release qualification; staging evidence does not
close that gate. See the [current handoff](../checkpoints.md#resume-in-one-page)
and [exact candidate receipt](../stabilization_024_preparation_20261006.json).
Earlier dated sections retain their original scope.

**Reported:** 2026-10-03, during the integrated core browser lane.

## What

```bash
E2E_SUITE_TIMEOUT_MS=600000 node tests/e2e/e2e-runner.js --lane=core
```

The Interactions suite times out even with 600 seconds, after 20 preceding
suites pass. The default hosted deadline is 180 seconds. The canvas actually
draws replayed scientific fixtures and calculated interaction sets. The last
completed calculation is halogen bond, followed by hydrophobic-contact controls.
Evidence: `/tmp/msv-integrated-core-20261003.log`.

## How

`molsysviewer/js/tests/e2e/interactions-subpanel.e2e.ts` starts a fresh Python
interpreter for each fixture/replay request. Seventeen calculation forms each
start it twice, in addition to inspector and lifecycle scenarios. Scientific
imports recur: individual cases take around 19–20 seconds; the disulfide case
takes 49.856 seconds.

Retain a Python fixture worker for the suite, with bounded requests and cleanup.
Each request still creates and closes an independent real viewer and replays its
events. Files returned by earlier requests remain until shutdown. Imports can be
reused; molecular and scene state cannot. Preserve every rendering assertion.

## Why

The strict core release gate cannot finish under its existing CI contract.

## Measured follow-up

The persistent worker completes the original combined suite, preserving all
17 forms, but that aggregate still exceeds the normal deadline. Mandatory core
scenarios now separately own lifecycle, scientific geometry and calculation forms.
Lifecycle passes in 32.944 seconds. Geometry initially still exceeds 180 seconds:
twenty original/restored family scenes repeatedly reload the executable harness.
The harness now stays loaded while every previous controller is disposed and a
fresh Mol* scene is constructed; plugin disposal stops animation and disposes
the Canvas3D context. No molecular or graphical state is reused. Geometry then
passes in 155.852 seconds under the default deadline, including periodic images,
all ten fixtures and restoration. Evidence:
`/tmp/msv-interactions-default-deadlines-scene-reset-20261003.log`.

## What was refuted

Increasing the deadline to 600 seconds does not complete the suite and does not
qualify the default 180-second lane. No calculation case is removed.

## Resolution

Fixed and guarded in the local candidate. All 39 core suites pass with the
normal 180-second deadline and no skip opt-out. The complete core records
32.542 s lifecycle, 149.884 s geometry and 117.509 s for all 17 calculation forms.
The addressable Python guard pins the mandatory registered scenarios, persistent
fixture transport, independent scene disposal and normal deadline; the real
worker guard proves fresh scenario state, error recovery and file cleanup. Real
browser assertions retain all scientific/rendering cases. Product publication
and exact committed-candidate CI remain, so the issue stays partial.
Evidence: `devguide/integration_completion_20261003.json`.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).


## Public qualification and closure — 2026-10-07

The persistent fixture bridge, Python worker, scenario owner and core runner
match published Viewer producer `1a4c97a5`. Imports remain warm while each request
constructs/closes an independent real view; every previous Mol* controller is
disposed before the next scene. No deadline increase or scenario removal is used.

Seven fresh runner/reliability cases pass. The named guard keeps lifecycle,
geometry and calculation scenarios mandatory, pins the persistent request/close
transport and independent scene disposal, and retains the 180-second default.
The real worker case passes in the original promoted 0.24.0 / 0.23.0 installed
pair: hidden state does not leak into a fresh request, a bad family returns an
error, a subsequent request recovers identically, and EOF removes every unique
worker-owned fixture. Scientific origins are independently checked by the
installed qualifier before/after collection.

Existing core `37685752799` passes all 39 suites on these unchanged owners. Its
native timestamps bound start-to-success-marker intervals at 28.365 seconds
for lifecycle, 153.106 for geometry and 129.176 for all 17 calculation forms.
These are observations of one hosted execution, not universal latency promises.
Exact-source pair `37685753081` also passes Linux core, 25 notebooks and all three
native Python 3.14 suites. Completed public-pair `37587631519` qualifies 16/16
installed cells. This closure reuses verified unchanged-owner evidence; it does
not repeat the browser lane or convert the earlier timeouts into successes.

Guard: `tests/test_e2e_reliability.py::test_all_interactions_scenarios_keep_default_deadlines_and_fresh_worker`.
The behavioral companion is
`tests/test_e2e_fixture_worker.py::test_interactions_worker_keeps_fresh_views_and_cleans_files`.
[Exact provenance and preserved failures](../remaining_partial_closure_20261007.json).
Final 1.0 recertification remains separate. Published packages are unchanged.

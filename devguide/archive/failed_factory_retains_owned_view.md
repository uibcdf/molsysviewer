---
summary: Failed new_view initialization retains its unreturned View and widgets.
issue: uibcdf/molsysviewer#316
status: resolved
opened: 2026-11-06
closed: 2026-11-16
severity: medium
verification: reproduced
area: [factory, lifecycle]
guard: tests/test_new_view.py::test_failed_factory_releases_newly_owned_widgets
normative:
blocked_by: []
supersedes: []
---

# Failed factory initialization retains owned resources

## Source resolution — consolidated receiving, 2026-11-16

Owned Views close after failed initialization, preserving the original exception and caller-owned widgets. The causal failure and repeated real load-mode/error controls remain below.

The complete source checkpoint
[43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908)
receives MolSysViewer `3aff1d48a5a38fb9854efe2c95a9a8f35cadbccb` and
MolSysMT `bc5a9297a762d451742734f9e11c7f54c6a832a0`. The durable guard
is `tests/test_new_view.py::test_failed_factory_releases_newly_owned_widgets`.
Its containing module passes **19 cases on each of Linux, macOS arm64
and Windows**, without failures, errors or skips. The [closing receipt](../molstar_closeout_three_blocks_20261115.json)
checks original JUnit ZIP digests and native selected cases; the complete
checkpoint also receives all 25 notebooks.

This supplies the formerly pending consolidated **source** prerequisite.
Earlier causal runs, interrupted/failed receiving and dated pending claims
remain below with their original inputs. Installed artifacts, final producers,
experimental native Qt and postponed human acceptance retain their own owners
and gates under #315/#372; this closure does not declare them passed or
advance the original 40/46 source or 1/46 final-acceptance counters.

## Earlier investigation — original claims and scopes retained


**A4 — delivered in `611c1574`; hosted receiving/closure pending; P2.** Viewer
owns #316 under #315, for the covering artifact and accepted 1.0 scope. The next
gate is applicable hosted receiving. E0 custody is received separately. No
provider change is required.

## Observation and duplicate review

An invalid selection in `new_view` raises after constructing a View, but the
factory does not close the unreturned owner. Its viewer widget and Layout stay
registered and retain the View. Repeating an ordinary input error accumulates
resources. Test teardown can conceal the defect by closing them later.

The complete four-page inventory contained 314 records before #316. Closed
#210 addresses empty-selection visibility, not failure cleanup; #127 protects
session rejection and temporary validation owners. Neither covers this path.

## Required behavior and acceptance

Close only the newly constructed factory owner when initialization fails. Keep
the initial exception, with visible cleanup diagnostics if cleanup also fails.
Caller-provided Views and their unrelated widgets remain open. Receive both
loading modes, selection and conversion/load rejection, repeated failures and
successful creation using real demo systems. Inspect registry ownership before
global teardown. General `close()` failure resilience remains the separate A6
investigation; this correction must not claim to complete it.

## Correction and current evidence

`new_view` tracks ownership and closes its own View if `_load_initial_system`
raises, including interruption. It re-raises the original exception; an
additional cleanup failure becomes an exception note rather than replacing it.
General close-on-error resilience remains A6.

The guard first failed all six selection/missing-file/structure cases across
both load modes, observing two additional widgets before teardown. After the
repair it repeats each failure three times, compares the error with the
caller-owned native route and checks exact registry preservation. A separate
guard retains a live region handle, original system/scene and independent View
after a rejected caller-owned load.

The factory module passes 19 cases. The broader factory/lifecycle/session and
public API selection passes 73 cases in 17.20 s with 59 legacy-H5MSM warnings.
These scopes overlap. Ruff and formatting checks pass. The
[receiving receipt](../factory_lifecycle_receiving_20261106.json) retains commands,
source hashes and imported provider identities. This does not qualify an
installed artifact or another host. The original private audit evidence is
protected in E0's approved private custody. Reviewed source is delivered in
`611c1574aa82538d79e15b93667497fc1f27b9ce`; applicable hosted receiving is still
pending, so A4 has not entered the completed progress numerator.

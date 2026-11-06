---
summary: Failed new_view initialization retains its unreturned View and widgets.
issue: uibcdf/molsysviewer#316
status: partial
opened: 2026-11-06
closed:
severity: medium
verification: reproduced
area: [factory, lifecycle]
guard: tests/test_new_view.py::test_failed_factory_releases_newly_owned_widgets
normative:
blocked_by: []
supersedes: []
---

# Failed factory initialization retains owned resources

**A4 — implemented and source-verified; delivery/closure pending; P2.** Viewer
owns #316 under #315, for the covering artifact and accepted 1.0 scope. The next
gate is reviewed delivery and applicable hosted receiving, with E0 custody
acceptance retained separately. No provider change is required.

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
protected under E0; reviewed delivery and applicable hosted receiving remain
pending, so the overall progress numerator has not advanced yet.

---
summary: Partition controls and scientific popup receiving after aggregate timeouts.
issue: uibcdf/molsysviewer#244
status: active
opened: 2026-11-14
closed:
severity: medium
verification: reproduced
area: [ci, browser, popup, qualification]
guard:
normative:
blocked_by: []
supersedes: []
---

# Controls/scientific receiving partition — active recurrence

The [original #244 correction](../archive/scientific_popup_guard_budget.md)
and its successful exact-hosted 300-second scope remain historical evidence.
Current run `43616029893` passes all three Python 3.14 hosts on `22b51f89`
and MolSysMT `aee7aa65`, then exhausts the same 300-second aggregate entry.
Export controls finish at about 44 seconds and notebook parity at 70.
The separately initialized scientific mirror receives camera/motion at
208 seconds of its own clock and native picks/edited-label markers at 224;
the outer entry kills it before final layout/playback assertions complete.
This is incomplete receiving, not a passed mirror or established stalled step.

The three workflows have independent fixture authorities and lifetimes.
Move the existing complete scientific helper into a separate mandatory core
entry with the same 300-second budget; keep export/notebook controls mandatory
under their existing budget. Preserve every helper assertion and operation
deadline, explicit overrides and fail/skip policy. Record individual camera
phase timing so a slow phase cannot disappear behind a larger aggregate cap.
Update the reviewed build/core inventory to 65 total / 62 core suites and
make the controls guard require both registered owners.

Receive both entries through the unoverridden canonical runner before the
complete core lane. The original failure remains failed. The complete
four-page inventory identifies closed #244 as the same aggregate-budget
mechanism; #305's original hidden menu and #325's original native pick failure
retain distinct causal/disposition requirements. No runtime or scientific
algorithm is changed by this partition.

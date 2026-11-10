---
summary: Diagnose a recovered Jupyter canvas staying at structure zero after eight successful cycles.
issue: uibcdf/molsysviewer#354
status: active
opened: 2026-11-10
closed:
severity: medium
verification: measured
area: [jupyter, trajectory, persistence, lifecycle]
guard:
normative:
blocked_by: []
supersedes: []
---

# Recovered initial structure — diagnosis active

The E2 prolonged campaign `259` completes eight cycles in one scientific kernel
and fails during the ninth recovered frontend's 30-second wait for structure 1.
The native Python recovery already passes exact scene, coordinates, named
analysis, measurements/units and figure-context comparisons. The connected,
non-disposed frontend reports structure 0 with 5,000 available structures and
paused playback. Its canvas is entirely above the visible viewport
(`y=-550.25`, height 480, viewport height 1,200).

Viewer `cb326235b3377185b18a17c7f59c71fd53cdab2a` and owner receiver
`74aeffede` retain 10,890 unchanged inputs; the run exits 1 after 462.55 s,
has no resource stop and retires all 26 owned processes. The failed ninth
session and the eight successes remain original evidence. This is not thirty
cycles or the accepted 20–30 minute observation window.

Classify harness visibility/controller identity and Viewer initial-frame
application separately. Next receiving explicitly shows the target before
binding, checks its unique runtime viewer identity and records initial native
frame requests/results. Keep the exact saved/Python/frontend/geometry checks,
unchanged deadlines and the original failure; do not send a repair seek,
retry invisibly or assert a numerical-data defect without evidence.

The revised source receiver `66273e4d` observes the uniquely identified,
visible recovered widget reaching structure 1 in fifteen consecutive complete
cycles, including the former ninth-cycle boundary. Its scalar initial-frame
traces retain the actual successful requests without a repair seek. A shared
pressure stop interrupts cycle 16; [#356](retired_notebook_molecular_data.md)
tracks separate measured logical data retention. This narrows the failure to
the earlier unqualified hidden/binding observation, but does not prove its
original cause; the report remains active.

Related #331/#332/#314/#307/#224 and MolSysMT #615 concern different observed
mechanisms. [The active audit](../pending_proposals/pre_1_0_robustness_audit_and_action_plan_20261106.md)
keeps E2 open. Scientific-source, installed, Qt and postponed human acceptance
remain separate; no candidate or publication is authorized.

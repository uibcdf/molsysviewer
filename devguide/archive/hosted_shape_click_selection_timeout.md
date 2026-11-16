---
summary: Hosted shape click does not reach active selection after GPU and hover succeed.
issue: uibcdf/molsysviewer#388
status: resolved
opened: 2026-11-14
closed: 2026-11-16
severity: medium
verification: measured
area: [selection, picking, input, ci, qualification]
guard: molsysviewer/js/tests/e2e/context-menu.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Shape click-to-selection receiving


## Resolution — complete current-source receiving, 2026-11-15

The remaining complete-core prerequisite is received by
[43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908),
MolSysViewer `3aff1d48a5a38fb9854efe2c95a9a8f35cadbccb` and MolSysMT
`bc5a9297a762d451742734f9e11c7f54c6a832a0`. All 63 Linux core entries
complete in one uninterrupted run, including `context-menu` and
`native-picking-readiness`; all 25 notebooks and the three Python 3.14 host
jobs also pass in their separately recorded scopes. Original logs and six
ZIPs are hash-verified in the [terminal receipt](../molstar_closeout_three_blocks_20261115.json).

The guard `molsysviewer/js/tests/e2e/context-menu.e2e.ts` retains the same
rendered shape, native GPU pick, hover, single real screen click, active
selection and selected-marker assertions. On failure its bounded passive
DOM/native/plugin observations distinguish the failed phase. There is no
selection injection, repeated click, broader timeout or weakened predicate.
The independently reproduced pending-read/synchronous-pick defect is repaired
and guarded under #389. Its native two-controller control and this complete
consumer sequence receive the corrected implementation.

This closes the source receiving observation after its declared prerequisite,
not a claim that #389 caused the original hosted click. That original event
sequence was not captured and its exact cause remains unknown. Its failed run
and the subsequent local/hosted non-reproductions remain below. A recurrence
fails the mandatory core guard and must be triaged with the retained bounded
event sequence. Installed artifacts, final producers, native Qt and human
acceptance remain separate. This additional issue closure does not advance
the original 40/46 outcome counter.

## Earlier investigation — retained evidence and causal limits

Source-only run `43621650307`, MolSysViewer `a72c92ba` and scientific
provider `aee7aa65`, fails Linux's first context-menu entry at the unchanged
30-second active-selection predicate after clicking `menu-sphere` in the
second independent controller. Native GPU picking and the shape-hover
predicate have passed; the selected-marker check is not reached. The complete
job's original log is preserved privately. Local `804` passes this whole
entry before a separate resource interruption during Studio. Neither result
explains the other's cause.

Capture bounded DOM down/up/click targets, native input and plugin click
observations, active selection and measurement mode around the original single
screen click. Distinguish absent input, empty/stale click loci, projection and
layout timing. Inspect the actual original Mol* 5.13.1 input/interaction bytes.
Do not force selection, inject loci, blindly click again, increase deadlines
or weaken GPU/hover/marker assertions. Preserve fixture/subscription cleanup.

The complete four-page all-state history contains 358 non-PR issues. Closed
#179's former alpha/pickability correction, open #305's hidden menu and #325's
updated annotation GPU query concern different observed boundaries. #244's
aggregate budget is not reached in this attempt. No duplicate report is found.
The new issue belongs to #372/#369 and #315; no installed or publication
qualification is claimed. Keep the ongoing 30-cycle campaign's source inputs
unchanged before integrating passive diagnostics or a causal correction.

Passive diagnostics now record at most 32 DOM/native/plugin events, without
changing the original single-click action, GPU/hover/marker predicates or
deadlines. Build/537 source guards and Ruff pass in `810`. Initial `811`
passes the complete behavior but fails its newly added cleanup because the
shared browser facade intentionally lacks `contexts()`; that failed attempt
is retained. Ownership-scoped Page cleanup then receives the complete native
entry in `813`, with unchanged inputs and clean retirement. This is local
non-reproduction, not a repair of the original hosted observation. The bounded
source diagnostic now includes context-menu and both partitioned mirror owners;
it cannot qualify the complete core lane.

Hosted diagnostic `43626475247` and complete Linux prefix `43627876434`
both receive the complete context-menu entry on `1a8d630d`. An independent
original-native control then establishes a real pending-read/synchronous-pick
gap (#389), received by the exact-byte-gated repair and two-view GPU control
in `822`. The complete real-click context entry also passes in `820` before
an unrelated new-helper export failure. This removes a concrete relevant
native gap, but the original failing click's actual event sequence was not
captured. Keep that causal limit explicit and receive the next complete
current core checkpoint before final disposition.

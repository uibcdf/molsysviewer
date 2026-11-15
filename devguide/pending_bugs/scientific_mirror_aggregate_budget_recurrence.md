---
summary: Receive the complete scientific popup mirror after its independent aggregate budget expires.
issue: uibcdf/molsysviewer#244
status: active
opened: 2026-11-15
closed:
severity: medium
verification: measured
area: [testing, ci, popup]
guard:
normative:
blocked_by: []
supersedes: []
---

# Independent scientific mirror budget recurrence

The prior [partition](../archive/controls_scientific_mirror_receiving_partition.md)
keeps the controls and scientific mirror in separate mandatory core entries.
Its original receiving remains valid for those exact inputs. This recurrence
reopens #244 rather than assigning a new scientific or popup defect.

Full source run [43678661843](https://github.com/uibcdf/molsysviewer/actions/runs/43678661843)
on MolSysViewer `a8fc5273b6aa274cb5fc343b79ddf613b3458a54`, MolSysMT
`aee7aa65da56e896d1cb2d655bf73736f6453a43` and pandas 3.1.0 fails when the
outer runner kills entry 4/63, `canvas-popup-mirror`, at 300 seconds. Its three
preceding entries pass. The original log reports single motion-clock and
bidirectional camera convergence at 262 seconds and native shape/annotation
picks plus revised markers at 284 seconds. Local-layout and stopped-trajectory
completion have not been reported before termination. No inner assertion or
operation deadline fails before that cut; this does not establish that the
unreached checks pass or identify a rendering-performance cause.

The original source JUnit passes 4,744 cases, skips 42 explicitly and has zero
failures/errors; all 25 notebooks execute successfully. Both original ZIP
hashes match GitHub. The complete run remains failure. It does not reach the
later DataCard, static plot or Movie guards and cannot qualify them.

Measure the complete unchanged mirror with an explicit diagnostic allowance,
preserving every individual operation deadline and assertion. Do not call
that override canonical receiving. Select a bounded canonical route from the
observed scope and retain explicit caller-override precedence. Receive the
complete changed boundary and then the full applicable core lane; do not
assemble a complete pass from successful prefixes and later suffixes.

No production/runtime/scientific or dependency change is inferred from the
outer timeout. Installed, human and publication decisions remain separate.

## Measured correction

`mirror-budget-probe-875` completes the unchanged scientific workflow locally:
211.15 seconds for the browser owner, 234.14 seconds including native-input
verification and supervision. This measurement explicitly sets a 540-second
diagnostic aggregate allowance; it is not canonical receiving. All 6,356
selected native JS/declaration files match Mol* 5.13.1's original archive,
9,979 selected inputs remain unchanged, and all 16 owned processes retire.
There is no resource stop under the 8 CPU/4 GiB scope.

The new canonical default is 480 seconds only for `canvas-popup-mirror`.
The controls owner remains at 300 seconds and unrelated defaults, explicit
caller override precedence and all individual operation deadlines stay
unchanged. This bounded workflow allowance leaves room for Dock and the two
stopped-trajectory checks after the hosted 284-second milestone; it is an
engineering allowance, not an observed hosted completion or a promised
performance limit. Additional phase reports distinguish local Dock, shared
scene/playback settings and each stopped endpoint. No assertion is removed.

Canonical paired receiving and the next complete source/core run must still
receive this correction. Keep #244 open until its required hosted boundary
passes; the diagnostic override alone cannot close it.

The unoverridden paired attempt `controls-mirror-canonical-877` is incomplete:
controls and notebook parity pass, followed by scientific camera/motion
milestones, but the resource supervisor releases the execution after 243.35
seconds. The last five-second global sample reports 84,815,872 bytes swapped
out, 14.88 GiB available and zero memory-pressure avg10; its own cgroup has
no OOM and a sampled peak of 1,778,479,104 bytes. All 22 owned processes retire,
all 9,979 inputs remain unchanged and no product failure is assigned. The
child exit of zero does not override the supervisor's resource-stop failure.
Do not repeat heavy local work under shared swap activity. Receive the same
canonical boundary in the controlled hosted lane instead.

The canonical entry build and 474 reporting/link/E2E-policy cases pass, as do
Ruff and queue/diff checks. The initial clean-checkout link failure in `878`
is retained: the new report had not yet been staged. Registering that file
corrects the consumer setup, and `879` passes without changing assertions.
The [consolidated receipt](../molstar_qualification_followup_20261114.json)
preserves original profiles, ZIPs, hashes and approved private custody.

One complete Linux source recovery,
[43686277372](https://github.com/uibcdf/molsysviewer/actions/runs/43686277372),
now receives `b9f7dfb2` with the same scientific source/pandas and full core,
Python and notebook selection. Complete pre-dispatch inventories have no
active, queued or exact-head dispatch, and the subsequent exact-head inventory
contains only this run. Its first observation is pending; #244 remains open.

A smaller unoverridden attempt, `mirror-canonical-880`, follows a fresh quiet
resource assessment and selects only the affected scientific mirror. It is
also resource-interrupted, after 62.61 seconds: the final sample records
93,261,824 bytes of global swap-out in about five seconds, 15.61 GiB available
and zero memory-pressure avg10. Its own cgroup peaks at 1,120,768,000 bytes
without OOM; all 15 owned processes retire and all 9,979 inputs stay unchanged.
The child exit of zero remains subordinate to the supervisor's nonzero stop.
No complete mirror is credited. The hosted run now owns the remaining native
receiving; further heavy local retries are deferred during recurring shared
swap activity. Light documentation/evidence checks remain applicable.

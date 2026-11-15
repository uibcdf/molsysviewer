---
summary: Moving work-file receiving chooses its popup role before bootstrap is ready.
issue: uibcdf/molsysviewer#397
status: resolved
opened: 2026-11-15
closed: 2026-11-15
severity: medium
verification: measured
area: [testing, popup, lifecycle, ci]
guard: molsysviewer/js/tests/e2e/moving-capture-lifecycle.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Positive readiness before popup work-file controls

**Resolved in source — 2026-11-15.**

## Resolution

The receiver requires positive panel-role/navigation or initialized canvas-owner readiness before choosing its operation path. The combined lifecycle retains its qualified canonical 240-second aggregate, with original readiness/product bounds and all pending owner-close, transport-loss, late-reply, native freeze and View-close assertions unchanged. Actual original popup timing is not retrospectively inferred.

Exact source checkpoint [43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908),
MolSysViewer `3aff1d48a5a38fb9854efe2c95a9a8f35cadbccb` and MolSysMT
`bc5a9297a762d451742734f9e11c7f54c6a832a0`, passes all three native Python
3.14 jobs, all 63 mandatory core entries in one uninterrupted run and all
25 notebooks. Every original ZIP matches GitHub size/hash metadata; native
required-step and JUnit evidence are retained in the
[closeout receipt](../molstar_closeout_three_blocks_20261115.json). This
satisfies this report's complete-current-core prerequisite. The original
failed campaigns, setup failures, explicit skips and causal limits stay
preserved below; no successful prefix/suffix is substituted for that gate.

The durable guard is `molsysviewer/js/tests/e2e/moving-capture-lifecycle.e2e.ts`.
This closes receiving infrastructure in source, not the remaining installed,
actual-host, human, Movie #320 or whole Mol* #372 qualification. No runtime
algorithm, source dataset, candidate or publication changes in this closure.

## Earlier investigation and scoped receiving


Source run [43692655949](https://github.com/uibcdf/molsysviewer/actions/runs/43692655949)
on `21474b8c` / scientific source `aee7aa65` fails core entry 10,
`moving-capture-lifecycle`. Python passes 4,752 cases with 42 explicit skips;
all 25 notebooks and the first nine complete core entries pass. Original logs
and both hash-verified ZIPs remain separate from the full failed result.

The lifecycle workflow completes canvas-owner closure and late-reply cleanup.
In the following detached-panel case, `openMovingWorkFile` sees neither
`molsysviewer_init_options.isPanelOnly` nor `__mirrorController`, chooses its
canvas branch and throws at `controller.setPanelMode`. The preceding wait
only observes that `#molsysviewer-loading` is hidden. An absent node already
satisfies that predicate; it cannot establish a new window's role or owner.
The exact earlier popup bootstrap timing was not captured, so no molecular
state loss, disposed controller or product-code cause is inferred.

The shared receiving helper now waits for a positive role/owner condition:
the actual visible Studio navigation in a panel-only window, or the observed
initialized molecular controller in a canvas. The lifecycle case invokes it
from the earliest actual panel-window event, before using loader disappearance
as supplementary evidence. All original scientific holds, destination checks,
owner retirement, late replies, dynamic freeze/close and deadlines remain.
There is no fixed sleep, retry click, fabricated controller or timeout override.

Receive the complete native affected entry, then the required complete current
core lane. The [three-block receipt](../molstar_closeout_three_blocks_20261115.json)
keeps source, installed, actual-host and human scopes distinct. #378's request
retirement, #379's panel-only loop and #380's PNG source are related, different
failures. The complete all-state history contains four pages, 395 records and
367 non-PR issues. Parent #372/#369/#315.

## Complete receiving and aggregate allowance

The test-only entry build passes in `899`. Canonical `900` receives the
previously failed panel bootstrap, completes both genuinely pending owner
closures and transport loss, then starts the separate freeze/close fixture.
The runner cuts that progressing second fixture at the original 180-second
aggregate. No individual operation failure occurs before the cut. All 9,979
inputs remain unchanged and all 19 owned processes retire. This is not a pass.

Diagnostic `901` explicitly allows 300 seconds only for measuring that complete
entry. All original availability, closure, transport loss, native freeze and
pending-View-close assertions pass in 169.655 seconds for the browser owner;
supervised time is 195.187 seconds. All 6,356 native files match the reviewed
original manifest, all inputs remain unchanged and all 18 owned processes
retire. There is no resource stop. This override is not canonical acceptance,
and the two differently cached timings are not a performance comparison.

The proposed canonical aggregate becomes 240 seconds for this combined entry
only, leaving the general 180-second default, every operation/readiness
bound and explicit caller-override precedence unchanged. Its two independent
fixture initializations and observed second-fixture cut justify this bounded
workflow allowance. Receive it without an override, then the complete current
core gate. No assertion, core entry or failed original is removed.

Canonical `903` passes the complete affected entry without any override:
156.702 seconds for both browser fixtures and 159.805 seconds supervised.
Every original destination, missing/closed-owner, autonomous deadline,
late-reply, native freeze and pending-View-close assertion remains. All 6,356
native files match the original manifest, all 9,979 inputs remain unchanged,
and all 18 owned processes retire without a resource stop. Peak summed own
RSS is 3,662.4 MiB within the 8 CPU/4 GiB scope. Full current core receiving
is still required; no historical failure is relabeled.

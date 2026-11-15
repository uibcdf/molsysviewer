---
summary: Receive DataCard keyboard navigation after the applied trajectory notification.
issue: uibcdf/molsysviewer#394
status: resolved
opened: 2026-11-14
closed: 2026-11-14
severity: medium
verification: reproduced
area: [testing, datacards, trajectory, synchronization]
guard: molsysviewer/js/tests/e2e/datacard-lifecycle.e2e.ts
normative: devguide/engineering_rules.md
blocked_by: []
supersedes: []
---

# DataCard applied-frame receiving

Source CI `43662871581` on `ad470cdf` fails in entry 35/63 after the
Trusted Types popup-refusal/retry/dismiss control: native current structure is
2, but the immediately read source slider is `0`, expected `2`. Earlier card
lifecycle and sandbox controls pass. All three Python hosts and the 25 Linux
notebooks pass separately; the whole core gate remains failed.

The getter reads the native model index. The implementation then awaits its
post-model annotation work before publishing the trajectory subscription that
updates plot inputs. That is a possible receiving-boundary mismatch, not yet
proof of this historical ordering or a product defect. Receive the real native
update and completed subscription states, keep both expected native and slider
assertions and all original scientific, popup-policy and lifecycle controls.
No longer deadline, blind retry or synthetic success is appropriate.

Closed #345 owns the source lifecycle implementation. This newly observed
guard-boundary issue is distinct from #391's later plot inspector/static-page
bootstrap, which the failed run never reaches. Exact original CI files and
complete issue inventory are preserved. Broader #315/#372 qualification and
publication decisions retain their own scope.

## Source resolution

The original getter is an insufficient completion predicate. Passive probe
`865` reaches the correct final state but does not reproduce a mismatch; its
counterexample assertion fails and is retained. Probe `866` then applies a
real supported bottom-inset/layout reservation during native model application.
Native index 2 and slider 0 coexist while the application is pending; the
actual completed trajectory notification observes slider 2. No callback,
completion, delay or scientific input is replaced. This proves the predicate
hole without reconstructing the original hosted scheduling.

The guard now observes the actual trajectory publication before pressing
End/Home. One unchanged 30-second wait requires that publication, native index
and real slider value together. Its receiver-owned subscriptions retire in
`finally`. The complete original lifecycle/policy/geometry assertions remain;
the Trusted Types case additionally exercises actual concurrent layout.

The complete entry passes in `869`, with unchanged runtime/native inputs and
all 21 owned processes retired. The [receipt](../datacard_applied_receiving_20261114.json)
retains the six original CI artifacts with verified GitHub hashes, before
observations, controlled counterexample and full final guard. This closes the
source receiving defect, not complete current core/platform/installed/human
qualification; #372/#391 retain their required exits. No production fix or
exact historical event ordering is claimed.

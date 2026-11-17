---
summary: Receive focused DataCard keyboard navigation after refused popup cleanup.
issue: uibcdf/molsysviewer#394
status: resolved
opened: 2026-11-17
closed: 2026-11-17
severity: medium
verification: measured
area: [testing, datacards, keyboard, focus]
guard: molsysviewer/js/tests/e2e/datacard-lifecycle.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Current DataCard keyboard receiving

Full source `43823224361`, at MolSysViewer `303c9152` / MolSysMT `4b0b1f8a`,
passes all three Python hosts, then Linux entry35/63 times out at the real
Trusted Types End-key receiving. Lifecycle and sandbox controls pass. The
original job does not retain native frame, published frame, current input
value or actual document focus at failure. Its failure cannot be attributed
to the [earlier native-getter mismatch](../archive/datacard_applied_frame_receiving.md)
or to #400's separate paired-camera reset loop.

Private source `995` observes actual keys, delegated native requests and
publication, and completes the whole original entry in40.27s. That is an
instrumented positive, not a reproduction or covering qualification.

The maintained receiver now brings the originating page forward, focuses
the real slider and requires actual document/input focus before issuing its
one native End/Home key. Its existing completion predicate still requires
the publication, native frame and real input value together. It records
bounded booleans/counts/current state before retiring a failure, preserving
the original error. No retry, fabricated completion or changed scientific
assertion is introduced. Receive the unchanged complete entry and the
applicable covering checkpoint. This qualifies the real input precondition;
the original hosted event order remains unknown.

## Resolution — 2026-11-17

The complete maintained DataCard entry passes in `1004`, including ordinary
lifecycle, both real sandbox/Trusted Types refusals, retry/dismiss, real
End/Home navigation and concurrent layout. Its completion predicates,
operation deadlines and scientific/ownership assertions are unchanged.
The native mirror passes separately in the same invocation. The later
actual-Jupyter work-file case fails under #344; that outcome does not turn
this independently completed entry into a full checkpoint pass.

The [current receipt](../camera_peer_and_ipc_receiving_20261117.json) retains
the hosted negative, the instrumented non-reproduction and the maintained
input-precondition correction. This source receiving closes the missing
physical-focus precondition and diagnostic gap. It does not reconstruct
the original hosted key event, claim a product-frame repair or waive the
next covering and exact-candidate gates.

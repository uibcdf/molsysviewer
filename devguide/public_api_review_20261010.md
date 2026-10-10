# Final public Python API review — 2026-10-10

The principal maintainer authorized this round after accepting the canvas menu
and Studio refinements. It reviews reachable Python operations, argument
digestion, ownership, handle lifetime, query scope, units and persistence.
It does not freeze 0.25.0 or authorize either 1.0 publication.

## Scope and decisions

| Issue | Correction |
| --- | --- |
| uibcdf/molsysviewer#210 | Resolve empty factory selections through Whole before hiding it; retain selection provenance. |
| uibcdf/molsysviewer#211 | Honor annotation syntax and reject unsupported annotation kinds. |
| uibcdf/molsysviewer#212 | Reject foreign handles in membership, region booleans and camera focus. |
| uibcdf/molsysviewer#213 | Align live annotation/interaction focus with camera dispatch and reject retired targets. |
| uibcdf/molsysviewer#214 | Anchor saved-selection labels to their exact atoms. |
| uibcdf/molsysviewer#215 | Preserve explicit digestion bypass in general measurement construction. |
| uibcdf/molsysviewer#216 | Make identity fields read-only; validate region rename collisions. |
| uibcdf/molsysviewer#217 | Complete detached handle inspection, annotation edits, region rename vocabulary and named sphere anchors. |

The maintained rules are in [scene contracts](scene_contracts.md#public-handle-boundaries--2026-10-10)
and the [public API reference](../docs/content/developer/public_api.md).
No new provider detector, frontend message or runtime bundle is introduced.
Interactions remains experimental. The broader documentation round remains
later in the agreed sequence.

## Verification

The initial focused run passes 20/20 real-system cases in
`tests/test_new_view.py` and `tests/test_public_api_hardening.py`.
The related regression execution passes **376/376**, including the additional
focus guards with nm and angstrom output standards. The first new radius
assertion omitted the existing 0.1 nm minimum bounding radius; source inspection
corrected that test expectation before the successful run.
The regenerated inventory has 726 reachable callables, all decorated with
ArgDigest, no missing bypass arguments, no missing digesters and no exemptions.
The single complete Python execution reports **3026 passed, 30 failed,
23 skipped** (exit 1, 103.80 s). Two failures were integration bookkeeping:
the generated capability table needed regeneration and new linked documents
needed staging in Git's index. After those changes the reporting, links,
architecture and capability guards pass **433/433**.
Twenty failures were sandbox socket/Chromium launch restrictions; the five
affected modules subsequently pass **53 tests, 1 explicit GPU skip** with the
required permissions. All twenty failed cases pass in that scoped execution.
The remaining eight are the known experimental Qt transport/generation/context
failures; they are retained without workaround, waiver or a passing claim.
The full suite is not rerun or described as globally green. Applicable hosted
CI remains pending.

Development uses `molsyssuite@uibcdf_3.14` (Python 3.14.7) and real dialanine/pentalanine systems
from the source checkouts. This is source evidence; it does not qualify a clean
solver installation or any staged archive. Experimental Qt results retain their
own scope. The known Qt provisioning/context failures must not be counted as a
passing standalone host.

The provider checkout is `539633b77a4da51e9dd03c5edcd12c5658a4093a`, with its
owner's uncommitted benchmark/resource-guidance work preserved. Viewer changes
were tested from base `b946a2b502e51335abbbeb8b7414d3d3096b70f3` in this source
checkout; unrelated sandbox notebooks/design files remain outside integration.
The [source receipt](public_api_closure_20261010.json) retains command identities,
outcomes and full-log digests.

## Next boundary

Finish the source review and applicable CI, then continue the
[0.25.0 preparation](stabilization_025_preparation_20261009.md) after remaining
design work. Both public 1.0 releases remain paused and the producer is unfrozen.

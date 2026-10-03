---
summary: Compound interaction projection dispatches one center calculation per group
issue: uibcdf/molsysviewer#141
status: resolved
opened: 2026-10-02
closed: 2026-10-02
severity: medium
verification: measured
area: [interactions, performance]
guard: tests/test_interactions_projection_batching.py
normative:
blocked_by: []
supersedes: []
---

# Compound interaction projection dispatches one center calculation per group

**Done:** bounded public geometry batches remove per-group dispatch; the regression guard and full Interactions browser suite pass.

**Reported:** 2026-10-02, the fresh-process sparse scale qualification for
uibcdf/molsysviewer#140; related public geometry operations belong to
uibcdf/molsysmt.

## What

Current-frame Python projection of synthetic two-group interactions takes
416–424 ms for 100 observations and 4,226 ms for 1,000. These observations
exclude browser transport and GPU rendering; they are not latency guarantees.
The provider is the isolated wheel built from clean commit
`df1a298e70a419a8f04562f8fb9ffaa92abb3be1`, Python 3.14.7, Linux x86_64.

```bash
python devtools/benchmarks/interactions_residency.py --case medium --pattern reuse --layout rings
python devtools/benchmarks/interactions_residency.py --case large --pattern reuse --layout rings
```

The tool retains intact demo peptides and stores synthetic six-atom groups.
It measures the adapter; those groups are not chemically detected aromatic
rings. Every query/coverage and projected occurrence/segment count is checked.

## How

`InteractionsManager._frame` in `molsysviewer/interactions.py` caches group centers
within each set/frame but dispatches `msm.structure.get_center` separately for
every distinct group. The supported operation already accepts grouped selections.
Batch the required groups of the visible frame through that public operation,
keeping their membership/order, explicit nm output, invalid-coordinate and
periodic split-group refusal, occurrence identity and bounded materialization.
The optimization must not introduce a second scientific result or query a whole
trajectory to project one frame.

## Why

Synchronous frame preparation can stall Studio and trajectory playback after
the analysis has already been calculated. MolSysViewer owns this orchestration;
the public provider's grouped-center capability can be reused directly.

## What was refuted

Sparse numeric storage and correct query results do not establish responsive
projection. The measured path stops before transport and Mol* rendering, so
these costs cannot be attributed to a browser/GPU problem. Copying a centroid
kernel into the Viewer is unnecessary because the provider exposes grouped
centers already.

## Resolution

The fix uses bounded batches of at most 128 occurrences and 16,384 participant
atom references. Public `get_center` receives the required endpoint groups of
one frame, and public `get_distances(pairs=True)` checks periodic integrity using
linear explicit pairs instead of a Cartesian matrix. Centers remain untranslated;
each occurrence applies its declared relative images. Batch-local center caches
and lazy occurrence decoding avoid retaining a whole-frame collection of groups.
Scientific relations, participants, filters, occurrence IDs, counts and the
projection/inspection byte budgets remain intact.

The guard is `tests/test_interactions_projection_batching.py`. Its 16 cases
observe real public provider calls without substituting implementations; they
check nested selection/batch limits, requested frames, independent centroid/image
positions, nm extraction under nm/angstrom policies, both periodic/nonperiodic
charge/ring families, large member lists, nonfinite groups and refusal of split
periodic rings. All 71 existing family/scene/residency checks also pass.

Restoring scalar-per-group center calls in a separate process makes the many-group
guard fail: one expected pytest failure, exit 1, zero collection/runtime errors.
This mutation never edits the working-tree source. JUnit/log evidence is
`/tmp/msv-interactions-batching-mutation.xml` and
`/tmp/msv-interactions-batching-mutation.log`.

Fresh sequential process measurements retain every occurrence and segment:

| Observations / pattern | Before ms | After ms | Speedup |
| --- | ---: | ---: | ---: |
| 100 / reuse | 416.46 | 31.18 | 13.36× |
| 100 / churn | 423.89 | 31.34 | 13.53× |
| 1,000 / reuse | 4,226.36 | 280.94 | 15.04× |
| 1,000 / churn | 4,147.61 | 291.01 | 14.25× |

Same provider/interpreter/host and benchmark input as the initial measurements.
These are development CPU observations, not browser/GPU latency guarantees.
Raw phase readings and source hashes are preserved in
`devguide/benchmarks/interactions_batching_20261002.json`; the maintained record
is `devguide/interactions_performance.md`.

The complete Python suite was run once: **2,572 passed, 23 skipped, zero
failures/errors**, exit 0 in 428.46 seconds. The full real Mol* Interactions
subpanel E2E also exits 0, including scientific periodic geometry, 20 calculated/
restored family scenes and all 17 real calculation forms. Evidence is
`/tmp/msv-interactions-batching-full.xml`,
`/tmp/msv-interactions-batching-full.log` and
`/tmp/msv-interactions-batching-e2e.log`. The existing skips remain qualification
limits. Headless SwiftShader correctness does not certify GPU throughput or the
whole core browser lane. Ruff and whitespace checks pass.

The fix is in the local uncommitted product integration; coordinated publication
remains under uibcdf/molsysviewer#140. The isolated experimental provider is not
a compatible published dependency. Provider query work remains
uibcdf/molsysmt#288 and is independent of this resolved dispatch defect.

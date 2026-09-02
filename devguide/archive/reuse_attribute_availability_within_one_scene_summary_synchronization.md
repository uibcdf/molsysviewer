---
summary: One scene-summary synchronization asks the same attribute-availability question repeatedly.
issue: uibcdf/molsysviewer#32
status: resolved
opened: 2026-08-13
closed: 2026-09-02
verification: measured
area: [performance, scene]
guard: tests/test_phase12_whole_panel.py::test_one_synchronization_asks_the_system_for_its_attributes_once
normative:
blocked_by: []
supersedes: []
---

# Reuse Attribute Availability Within One Scene-Summary Synchronization

**Reported:** 2026-08-13, while independently re-auditing the causal diagnosis in
uibcdf/molsysmt#147.
**Status:** proposed; independent of the MolSysMT 1.0 release gate.

## What

Compute the loaded molecular system's attribute availability once per scene-summary
synchronization and reuse it while building both the region and whole summaries.

This is deliberately an operation-local value. It is not a persistent cache on the view,
the molecular system, or a form adapter.

## How

`_sync_region_summaries_runtime()` currently calls `_region_summary_records()`, which
calls `_available_region_attributes()`. It then calls `_sync_whole_summary_runtime()`,
whose `_whole_summary_record()` calls `_available_region_attributes()` again.

Refactor the synchronization boundary so it owns one immutable attribute inventory and
passes it to both consumers. Suitable shapes include:

1. an optional `available_attributes` argument on both summary builders; or
2. one private summary context object constructed at the outer synchronization boundary.

Do not cache across operations unless separate mutation-aware evidence later justifies
it. MolSysMT native objects are mutable, so persistent reuse would need invalidation for
topology, structures, mechanics, and loaded-form replacement.

## Why

The current representative region action computes the same inventory twice. The cost is
not boundary-grade ArgDigest validation in MolSysMT: every form-level predicate already
uses `skip_digestion=True`. It is the repeated inventory traversal itself.

Measured on `demo['dialanine'].regions.add(selection='atom_index < 3')`:

| observation | current | operation-local reuse probe |
| --- | ---: | ---: |
| form-level `has_attribute` calls | 510 | 229 misses + 141 reusable hits in the instrumented seam |
| unique `(form, attribute)` pairs | 229 | 229 |
| median action time | 46.71 ms | 26.62 ms |
| median saving | — | **20.10 ms, about 43%** |

The hit count is smaller than `510 - 229` because the controlled probe memoized at the
form-adapter seam and not every call reached the same patched module binding. The timing
is the relevant end-to-end evidence; implementation should remove the second inventory
construction structurally rather than reproduce the probe's generic memoizer.

## What Is Measured and What Is Assumed

Measured:

- 589 decorated calls: 21 ordinary and 568 fast-path;
- 510 form-level attribute predicates, all fast-path;
- zero molecular-system assessments in the operation;
- alternating 50-operation baseline/reuse campaign, discarding warm-up samples;
- baseline median 46.713 ms, standard deviation 1.050 ms;
- reuse median 26.616 ms, standard deviation 2.153 ms.

Assumption: sharing the inventory explicitly between the two summary builders will
capture most of the controlled probe's saving. The implementation must be benchmarked;
the probe demonstrates opportunity, not the exact final design cost.

## What Was Refuted

- Adding `skip_digestion=True` to form predicates cannot help; all 510 already use it.
- MolSysMT does not assess the molecular system 434 times in this workflow; it assesses
  it zero times.
- A permanent cache is unnecessary for the measured duplication and introduces stale
  state risk.
- The optimization does not belong in ArgDigest: the repeated semantic request is issued
  by MolSysViewer's two summary consumers.

## Scope and Exclusions

This proposal covers one synchronization transaction and the Python scene-summary
builders. It does not change the wire protocol, JavaScript runtime, region semantics,
MolSysMT API, ArgDigest, or persistent view state. It does not claim that every
`get_attributes()` call should be cached.

## Acceptance Criteria

1. One region-summary synchronization computes MolSysMT attribute availability at most
   once for the current molecular system.
2. Region and whole summary payloads are byte-for-byte or structurally equivalent to the
   pre-change payloads.
3. Changes to the loaded molecular system are visible on the next synchronization with
   no invalidation API.
4. Existing region, whole-summary, history, and state-serialization tests pass.
5. A deterministic call-count regression guards the single-inventory contract.
6. The representative timing is remeasured with the same fixture and command; absolute
   results and dispersion are recorded without turning a local measurement into a global
   performance promise.

## Provenance

Measured 2026-08-13 on the shared MolSysSuite development host with Python 3.13, editable
MolSysViewer and MolSysMT checkouts, and the bundled dialanine demo. The widget send path
was replaced with a no-op to isolate Python synchronization work. The audit scripts were
session scratchpads and are not product code.

---

## Resolution — 2026-09-02

Implemented as shape 1 of the two the proposal offered: `_sync_region_summaries_runtime`
builds the inventory once and passes it to `_region_summary_records` and
`_sync_whole_summary_runtime`, both of which keep computing it themselves when called
without one, so no other caller changes.

Measured on `demo['dialanine'].regions.add(selection='atom_index < 3')`, nine runs each:

| | median |
| --- | ---: |
| before | 46.64 ms |
| after | **26.76 ms** |

The proposal predicted 46.71 → 26.62. It was right to within the noise, which is worth
recording: the probe it was written from measured the real thing and not an artefact of
its own memoizer.

**Passed, not stored**, as the proposal insisted. A cache on the view or on the molecular
system would have to know when the system changes underneath it, and a live edit that adds
atoms changes exactly this answer. One synchronization is the longest the value is
provably still true.

Guard: `test_one_synchronization_asks_the_system_for_its_attributes_once`, which counts the
calls within one sync and is mutation-verified against restoring either traversal. It pins
the reuse *inside* a synchronization and deliberately says nothing about across them.

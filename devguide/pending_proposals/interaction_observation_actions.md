---
summary: Select and focus observation participants from the Interactions inspector
issue: uibcdf/molsysviewer#145
status: partial
opened: 2026-10-02
closed:
verification: measured
area: [interactions, selection]
guard: tests/test_interactions_public_completion.py::test_stale_observations_cannot_change_selection
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Select and focus observation participants from the Interactions inspector

**Reported:** 2026-10-02, public API review authorized by the principal maintainer.

## What

Offer selection and focus actions on individual observations in the Interactions inspector, through public Python operations and Studio controls.

## How

Resolve each observation using analysis name/revision, frame and complete-analysis occurrence index; reject stale identities before acting. Reuse active-selection and camera tools. Preserve all atoms of compound participants and provide selection/region workflows through existing managers. Verify real-provider observations, nonconsecutive frames, parallel observations and stale replies in Python and real Mol* browser tests.

## Why

The inspector displays participants as text while canvas picking already associates their atoms with scientific observations. Direct row actions complete the inspection workflow without introducing a new selection model or scientific computation. Pre-1.0 follow-up to uibcdf/molsysviewer#114/#140.

## What was refuted

Static inspection is not browser reproduction. Complete-analysis residency is distinct from bounded inspection and rendering. Provider-owned science and H5MSM serialization are reused through public APIs.

## Working-tree implementation and evidence — 2026-10-02

Native select_observation/focus_observation and Studio row buttons resolve the current-frame occurrence from one detached bounded latest inspector page. Analysis/filter/frame revisions and lifetime validation precede selection/camera operations; compound participants retain every atom. Mutating the returned inspector dictionary cannot change cached action participants. Focus uses canonical positions through the existing camera selection tool, without periodic unwrapping. The complete real Mol* Interactions subpanel suite passes, including the new row actions.

The implementation is locally verified against clean experimental MolSysMT commit `396e6979f3f686b110431f18bba0d41933ce71e2`, not a qualified public provider release. All new public functions carry ArgDigest and explicit `skip_digestion=False`; the regenerated inventory passes with 713 public callables and 437 declared digesters. Exact run counts, environmental failures, scoped corrections, source hashes and browser limits are retained in [the shared evidence](../public_workflow_completion_20261002.json).

**Partial:** source implementation and bounded regression evidence are complete. Product changes remain uncommitted; compatible published dependencies and exact-candidate installed/core CI qualification remain under uibcdf/molsysviewer#114 and #140. Public documentation is intentionally deferred to the final block. No full final-candidate pass or release is claimed.

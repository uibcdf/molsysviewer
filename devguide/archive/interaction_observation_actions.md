---
summary: Select and focus observation participants from the Interactions inspector
issue: uibcdf/molsysviewer#145
status: resolved
opened: 2026-10-02
closed: 2026-10-07
verification: measured
area: [interactions, selection]
guard: tests/test_interactions_public_completion.py::test_stale_observations_cannot_change_selection
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Select and focus observation participants from the Interactions inspector

**Resolved — 2026-10-07:** Python and Studio select/focus the participants of an observation in the latest inspected page of the visible frame. Analysis/query/frame identities reject stale or missing observations before acting. Compound participants retain every atom; focus uses canonical molecular positions rather than periodic image unwrapping.

The original compatible-public-provider/candidate boundary is complete in the
published Viewer 0.24.0 build 1 / MolSysMT 0.23.0 ABI3 build 0 pair. The user
guide now includes executable paging, named-file and observation-action examples.
The earlier dated sections retain their original source/publication scope.

**Current qualification — 2026-10-06:** implementation is committed and
integrated in Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0. All
sixteen installed staging cells and 39 hosted core browser suites pass;
canonical-source Python 3.14 integration passes on all three native hosts,
with 25 documented notebooks passing on Linux. This report remains partial
for its public-provider/release qualification; staging evidence does not
close that gate. See the [current handoff](../checkpoints.md#resume-in-one-page)
and [exact candidate receipt](../stabilization_024_preparation_20261006.json).
Earlier dated sections retain their original scope.

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

**Partial:** source implementation and bounded regression evidence are complete. Source changes are reviewed, committed and pushed at `0dea171d`; compatible published dependencies and exact-candidate installed/core CI qualification remain under uibcdf/molsysviewer#114 and #140. Public documentation is intentionally deferred to the final block. No full final-candidate pass or release is claimed.

## Final closure evidence — 2026-10-07

Viewer producer `1a4c97a58b68b69f3a836546c9e4ac6187c3efa2` and provider
`46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9` remain unchanged. Public installed
run `37587631519` passes all sixteen cells, independently verified from original
environment ZIPs/digests and exact public package coordinates. The exact-source
public gate passes; recorded browser/scientific evidence retains its own scope.
The successor documentation/domain-close commit `ebb1a925` also has successful
hosted core (`37594417204`), notebooks (`37594417273`) and Python 3.14 source-pair
(`37594417292`) workflow verdicts; its standard CI remained queued at inspection.

Fresh installed qualification passes **47 tests, zero failures/errors/skips**:
10 public-completion and 37 scene cases. Both scientific libraries import from
site-packages and match versions 0.24.0 / 0.23.0; no editable provider substitutes
for that pair. The unchanged canonical files originally qualified in staging are
now promoted unchanged; public channel availability is verified separately by
the sixteen-cell run, not inferred from this local environment.
Five user-guide Python blocks execute against the installed pair: calculation,
inspection, save/reload, paging and participant selection/focus. Strict Sphinx
passes with warnings as errors. Legacy H5MSM demo warnings remain visible.

Guard: `tests/test_interactions_public_completion.py::test_stale_observations_cannot_change_selection`. Real frame/filter/analysis changes and missing occurrences fail before altering the active selection. Related compound/parallel and nonconsecutive-frame cases exercise select/focus and Studio dispatch; mutation of a detached inspection reply cannot change cached participants.
Normative contract: `devguide/scene_contracts.md`.
[The closure receipt](../interactions_workflow_closure_20261007.json) records
exact evidence and the corrected example-validation assumption. No production
Python/TypeScript logic, runtime, tag or package is changed by this closure.
The final 1.0 candidate still requires its own normative recertification.

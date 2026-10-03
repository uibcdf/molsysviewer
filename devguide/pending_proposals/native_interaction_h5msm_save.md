---
summary: Save named interaction analyses through the native Viewer API
issue: uibcdf/molsysviewer#144
status: partial
opened: 2026-10-02
closed:
verification: measured
area: [interactions, export]
guard: tests/test_interactions_public_completion.py::test_save_refusals_preserve_destination_and_analysis_collection
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Save named interaction analyses through the native Viewer API

**Reported:** 2026-10-02, public API review authorized by the principal maintainer.

## What

Add `view.interactions.save(...)` to export explicitly selected named scientific analyses to an interactions-only H5MSM 0.5 file before 1.0.

## How

Delegate to public `molsysmt.h5msm.write_layers`, retain complete analyses and index domains, and define names, overwrite policy and atomic destination replacement. Use ArgDigest with explicit skip_digestion and validate before writing. Test named parallel/compound/PBC observations, empty evaluated frames, reloading/alignment and failure preservation with the real provider.

## Why

Completes calculate/store/save/load through the native Viewer API (uibcdf/molsysviewer#114/#140), without requiring users to manage the scientific backend. A scientific H5MSM file is distinct from a scene session or HTML artifact. The provider owns serialization and scientific representation.

## What was refuted

Static inspection is not browser reproduction. Complete-analysis residency is distinct from bounded inspection and rendering. Provider-owned science and H5MSM serialization are reused through public APIs.

## Working-tree implementation and evidence — 2026-10-02

The native save method delegates complete named analyses to public H5MSM write_layers. A private sibling directory allows the provider exclusive writer to finish before publication; explicit overwrite uses replace and non-overwrite uses a hard link to reject races. Real-provider tests preserve parallel/compound observations, sparse empty-frame coverage, periodic images and units, and preserve existing destinations and analyses after invalid names or failed publication.

The implementation is locally verified against clean experimental MolSysMT commit `396e6979f3f686b110431f18bba0d41933ce71e2`, not a qualified public provider release. All new public functions carry ArgDigest and explicit `skip_digestion=False`; the regenerated inventory passes with 713 public callables and 437 declared digesters. Exact run counts, environmental failures, scoped corrections, source hashes and browser limits are retained in [the shared evidence](../public_workflow_completion_20261002.json).

**Partial:** source implementation and bounded regression evidence are complete. Product changes remain uncommitted; compatible published dependencies and exact-candidate installed/core CI qualification remain under uibcdf/molsysviewer#114 and #140. Public documentation is intentionally deferred to the final block. No full final-candidate pass or release is claimed.

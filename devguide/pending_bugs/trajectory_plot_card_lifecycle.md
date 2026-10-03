---
summary: Trajectory plot cards lose state and disagree on hide and clear semantics
issue: uibcdf/molsysviewer#143
status: partial
opened: 2026-10-02
closed:
severity: medium
verification: measured
area: [trajectory, state]
guard: tests/test_trajectory_plot_lifecycle.py
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Trajectory plot cards lose state and disagree on hide and clear semantics

**Reported:** 2026-10-02, public API review authorized by the principal maintainer.

## What

Close the multi-card trajectory plot contract before 1.0. Source inspection finds that Python coalesces all cards into one scene-look entry, `clear()` without a tag removes only the browser's default card, and `hide()` deletes data despite its documented retention promise. Series are not checked against the loaded structure axis.

## How

Keep canonical per-tag data in Python, define hide versus clear, rebuild every retained card, and validate one sample per loaded local structure. Reuse canonical state/transfer mechanisms and test multi-card snapshots, tagged/all operations, rebuilds and scientific frame correspondence. Confirm the inspected defects with regression tests; do not present static review as browser reproduction.

## Why

These are gaps in existing public behavior, rather than new scientific analyses. The browser currently retains multiple cards while Python retains only the last command, so reconstruction can change the visible result. The accepted scope includes corrections and coherent persistence of plot cards, with public documentation finished last.

## What was refuted

Static inspection is not browser reproduction. Complete-analysis residency is distinct from bounded inspection and rendering. Provider-owned science and H5MSM serialization are reused through public APIs.

## Working-tree implementation and evidence — 2026-10-02

Canonical tagged card records now reconstruct all cards, retain hidden data, distinguish clear from hide and survive state/session/copy/extraction. Values, x and events follow repeated/nonconsecutive extracted frames. Axis-changing edits/append and mismatched first loads refuse before viewer-owned mutation; explicit clear permits the edit. Browser close mirrors hide. The real Mol* trajectory-card suite passes.

The implementation is locally verified against clean experimental MolSysMT commit `396e6979f3f686b110431f18bba0d41933ce71e2`, not a qualified public provider release. All new public functions carry ArgDigest and explicit `skip_digestion=False`; the regenerated inventory passes with 713 public callables and 437 declared digesters. Exact run counts, environmental failures, scoped corrections, source hashes and browser limits are retained in [the shared evidence](../public_workflow_completion_20261002.json).

**Partial:** source implementation and bounded regression evidence are complete. Source changes are reviewed, committed and pushed at `0dea171d`; compatible published dependencies and exact-candidate installed/core CI qualification remain under uibcdf/molsysviewer#114 and #140. Public documentation is intentionally deferred to the final block. No full final-candidate pass or release is claimed.

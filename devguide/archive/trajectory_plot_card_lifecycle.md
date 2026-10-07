---
summary: Trajectory plot cards lose state and disagree on hide and clear semantics
issue: uibcdf/molsysviewer#143
status: resolved
opened: 2026-10-02
closed: 2026-10-07
severity: medium
verification: measured
area: [trajectory, state]
guard: tests/test_trajectory_plot_lifecycle.py
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Trajectory plot cards lose state and disagree on hide and clear semantics

**Resolved — 2026-10-07:** the shipped multi-card implementation is qualified on
the public 0.24.0 / 0.23.0 pair. Six fresh installed lifecycle guards and two
executable hide/restore/clear examples pass; documentation is complete for this
contract. Earlier dated qualification sections retain their historical scope.

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


## Published qualification and closure — 2026-10-07

The provider/publication blocker is complete. Viewer 0.24.0 build 1 and MolSysMT
0.23.0 ABI3 build 0 are public; their independent public-URL matrix
`37587631519` passes all sixteen cells. Plot Python/TypeScript owners, the six-case
lifecycle module and the existing unit/browser guards match published Viewer
producer `1a4c97a5` byte for byte. Review requires no further production change.

Six fresh cases run through the isolated installed-science qualifier against the
original files promoted unchanged, with Viewer 0.24.0 and MolSysMT 0.23.0 origins
verified before/after collection. They cover detached retained records, tagged
hide/restore/clear and all-card clear, reconstruction of both cards, scene-state
and session round trips, copy, nonconsecutive/repeated extraction with remapped
values/x/events, conflict refusal/renaming and pre-mutation structure-axis checks.
The browser-close event case confirms that Python retains the card's data and
can restore its visibility. The prepared-empty-view case refuses a mismatched
first load without assigning a molecular system.

The unchanged real Mol* browser guard reconstructs two cards, hides and restores
both, retains hidden DOM/data and removes one card without affecting the other,
then clears the complete registry. It passes in the already recorded independent
core `37685752799` (39/39 suites) and exact-source pair `37685753081` (three native
Python 3.14 hosts, with Linux core and 25 documented notebooks). This is reuse of
verified evidence on unchanged owners/guards, not a new browser dispatch or
proof of a Python-to-browser close round trip. The public URL installations and
the original promoted-file local tests retain their distinct provenance.

The user guide now explains per-tag cards, restoring with `show(tag=...)`,
browser close as hide, detached `records()`, all-card operations and persistence.
Two new examples execute against the installed public-version pair. The final
narrative explicitly states that supplied data is not recalculated after coordinate
edits and that equal-length replacement declares correspondence to the new local
order. Sphinx builds with warnings as errors.

Guard: `tests/test_trajectory_plot_lifecycle.py`. The assertions above protect
canonical retention, reconstruction and structure correspondence; the existing
browser guard remains additional rendered evidence. The shared styles/plot
receipt retains the local restricted-executor full-suite failure and experimental
Qt startup failure (#35); neither is converted into a pass here. No full suite or
browser rerun is needed for this documentation/qualification closure.

[Exact closure record](../trajectory_plot_lifecycle_closure_20261007.json).
Final 1.0 recertification and packaging the source-only Movie #177 / styles #149
corrections remain separate work. Published tags and package files are unchanged.

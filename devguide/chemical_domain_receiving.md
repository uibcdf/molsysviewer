# Receiving independent chemical domains

**Role:** operational source-receiving guide for
[uibcdf/molsysviewer#269](https://github.com/uibcdf/molsysviewer/issues/269),
coordinated with `uibcdf/molsysmt#255` and `uibcdf/molsyssuite#155`.
This guide does not establish a new published dependency minimum or installed
artifact qualification.

## Current follow-up — 2026-11-03

The provider's exact-export repair `2797c5425` is published in checkpoint
`d8ea626a0ab6dbd976d0e04ad9299019e4ae0a42`. Consumer installed-source campaign
41690488611 receives that checkpoint against Viewer
`d72f93f7aa8a3d89b2848bef905a48a00102f8e1`, on Linux/macOS/Windows with Python
3.14. The [campaign receipt](chemical_domain_installed_receiving_20261103.json)
retains results separately from the previous failed inputs. This is a single
source-receiving dispatch, without version tags or release qualification.

Linux and Windows pass their full Python selections (3,347/25 skips and
3,320/52 skips), including all five copy cases, and Linux executes all 25
notebooks. The hosted browser failure is a positive context-menu fixture that
assumed chain membership absent from its legacy input. Test-only correction
`383721ea` declares that membership, preserves unknown/partial cases and passes
the affected suite and all 44 core suites locally with the exact provider
snapshot and unchanged reused backend. This local recovery does not rewrite
the hosted job's failure or qualify a new installed build. macOS has now passed
its whole cell: 3,320 Python passes, 52 skips and all five copy cases executed.
The three-host Python results are received; #269 remains open for the hosted
Linux recovery against the corrected fixture.

Recovery run [41714550124](https://github.com/uibcdf/molsysviewer/actions/runs/41714550124)
uses exact Viewer `c1137ebb21812c15d941fa3c5154bd655e329f85` and the same
provider `d8ea626a0ab6dbd976d0e04ad9299019e4ae0a42`. It has one Linux job,
queued without executed steps at this receipt. The three original artifact
ZIPs match their GitHub digests and their JUnit bytes; successful original
Windows/macOS results remain separate from the pending recovery.
This replaces run 41707479800, cancelled after local full regression exposed
two distribution guards still parsing the former YAML matrix. The corrected
guards read the actual default JSON matrix and retain all three platform/version
requirements. Seven coverage controls also pass with an explicit TAP reporter.
No production runtime changes are included in this recovery source; #291's
player changes remain an independent receiving scope.

For source-only platform recovery, dispatch
`ci-python-314-source-pair.yaml` with `source_receiving=true`, the exact
`molsysmt_sha` and `platform=ubuntu-latest` (or the named macOS/Windows runner).
The default `platform=all` retains the complete three-host matrix. Candidate
qualification rejects single-platform selection. The selected platform still
executes its entire installation/audit/test path; a scoped success is not a
new complete matrix or an installed-artifact release certificate. Retain the
original run and each still-applicable result alongside the recovery receipt.

Earlier scoped receiving of committed
`bd28d57f2b0b31a6215d206dea27602f5f72e70d` passes 164 real Viewer cases with
no skips, including the five independent-copy cases. Its extraction-label dtype
fix is received using an isolated committed-source snapshot and the unchanged
shared Rust backend; sibling worktree edits are excluded. This does not claim
a rebuilt or installed provider artifact. The
[follow-up receipt](chemical_domain_receiving_20261103.json) keeps exact inputs.

The original installed Rust-manifest mismatch is owned by
uibcdf/molsysmt#533; the broader #255 refactor is completed. Its identified
repair retains exact export equality. Do not repeat the original failing
inputs or filter the unexpected export. Old-provider public/source
Pandas4Warning failures remain separate from new-source compatibility and the
passing JavaScript coverage steps.

## Previous source receiving — 2026-11-02

Receive provider `de7ffad2aef18ff3bccd184133dc69e081cb506e` on
`dev/chemical-states-separation-255`, following the new request in #269. The
previous `97f6b58f` observations remain historical. The initial 265 affected
Viewer cases pass on Python 3.14.7, including native/JSON loading, unavailable
hierarchy, nonconsecutive interaction queries, extraction, composition and
session persistence. Five additional real-demo copy guards receive the native
protected-edit contract through View owners: changes to coordinates, box,
chemistry and visual objects remain independent; prior analysis/query handles,
units, source maps, periodic images and persistence remain meaningful.

`tests/test_native_copy_receiving.py` is conditional on the public native copy
capability in older-provider compatibility lanes. It must execute all five
cases without skips when qualifying this provider source. This does not adopt
a new published minimum or promise allocation sharing for View copying.

The source-pair workflow accepts `source_receiving=true` with an exact provider
SHA. This development route creates no candidate-version tags, builds the
development runtime, retains normal validation, and uploads original JUnit
results on each platform. Its candidate mode remains independent and unchanged
when the option is false. Do not pass development commits off as frozen release
versions. Hosted execution and broad source qualification remain due.

The latest preserved general/source runs 41148560029/41148560031 fail exactly
the three warning-strict documentation examples, with deprecated native pandas
operations in the retained public 0.23.0 provider; the six general jobs and three
source-pair jobs were inspected through original logs. This is the #431
dependency context, not a ChemicalStates failure or a reason to weaken warnings.
MolSysMT#524 owns dependency floors, not the original warning defect.

The shared editable environment has unrelated `pip check` failures in
packmol-memgen, proprep, ndfes, fetkutils and edgembar. Their actual missing or
incompatible dependencies are retained in the receiving receipt. No global
environment repair, clean-install claim or installed-Rust-wheel validation is
inferred from source execution. Sibling dirty changes are limited to maintained
documentation and are preserved; qualified runtime input uses the exact source.

The final local core invocation passes 3,344 cases, with 21 justified skips and
14 experimental Qt cases deselected. The provider had advanced to documentation
checkpoint `7ef48701` before this invocation; the diff from requested `de7ffad2`
contains no runtime changes, and 3,074 provider runtime file hashes remain stable
through execution. Exact hosted run 41577620754 fails all three platforms on
the missing `get_vectors` Rust-manifest entry before science. The
[active receiving report](pending_proposals/chemical_domain_source_receiving.md)
keeps that prerequisite open. Final Viewer metadata/diagnostic and tooling
receiving remains separately identified in the dated receipt; no full hosted,
installed-artifact or numerical JS-coverage claim follows.

## Projecting a molecular system

Topology supplies stable inventory. Read covalent bonds through
`molsys.chemical_states.get_bonds(chemical_state="reference")`, not through a
Topology facade. JSON and array-native serialization use the same static
projection. A declared nonzero reference is honored. An ambiguous reference
raises; no arbitrary state is selected. Missing chemistry, a zero-state
collection, unknown connectivity and complete empty connectivity remain
unchanged in the native system. No edges are inferred to make rendering succeed.
The static payload has no per-structure state-switching protocol.

Active selection queries only available hierarchy metadata and excludes missing
memberships from its per-level index lists. It retains the ordered atom
selection. A collection without chemical states does not provide component
metadata. Group and chain rendering fallbacks are not native assignments.

## Declaring composition and edits

Provide `[topology, chemical_states, structures]` when an operation needs all
three domains. `[topology, structures]` projects inventory and geometry without
recovering chemistry from a hidden owner. Appending independent molecular
systems currently needs the provider's supported state-alignment policy; do not
invent an unknown state in Viewer to bypass a rejected composition.

Use supported molecular extraction/removal to remap structures, chemical-state
associations and named analyses together. Replacing only Structures can leave
explicit associations or analyses on the previous axis and is correctly rejected.
When a workflow intentionally changes labels and then appends only coordinates,
pass the Structures source explicitly; do not request a merge of differently
labeled full molecular inventories.

Positive chain-composition fixtures declare their chain membership. The bundled
legacy pentalanine file stores unassigned atom-to-chain positions; those are not
silently repaired. Separate tests retain unknown and partial membership coverage.

## Executable receiving boundaries

- `tests/loaders/test_array_native_molsys.py` checks reference-state access,
  ambiguity, missing/empty chemistry, coordinate values/units and unchanged storage.
- `tests/test_active_selection.py` checks unknown and partial membership,
  unavailable domains and unchanged ordered atom selection.
- `tests/test_composite_load.py`, `tests/test_live_edit_rebuild.py`,
  `tests/test_managed_axis_growth.py` and
  `tests/test_structure_edit_correspondence.py` check composition, coherent
  scientific edits and retained scene/source maps.
- The provider's `tests/molsysviewer_molsysmt/` guards cover the scientific add-on,
  including scene-failure retries without repeating completed molecular edits.

Run the ordinary Python source lane:

```bash
python -m pytest --receptor=llm -m "not qt_runtime" tests
```

Experimental real Qt windows retain their separate lane.
For Chrome export tests, use a managed short temporary directory: Unix-domain
socket paths have a bounded length. Keep large pytest outputs on repository disk;
do not substitute skipped browser tests for actual rendering evidence.

Record exact provider/consumer sources and retained worktree changes. Source
compatibility, the independently versioned provider package floor, browser
qualification and installed/release gates remain different claims. The dated
Studio operation inventory retains its inspected historical symbols; current
scientific graph tools belong to `molsysmt.chemical_states`, while sequence tools
remain under `molsysmt.topology`. Quarantined historical code is not a current
receiving route.

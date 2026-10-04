# Scientific-use review — 2026-10-04

## Outcome

Reviewed source integration and developer-guide reconciliation are pushed at
`0dea171d` and `cdbf52b3`. A new minor version **0.24.0** is recommended, without
creating a tag. The scientific review confirms the bounded trajectory,
interaction and multiple-protein workflows, and finds two provider defects plus
one consumer preparation gap that must be addressed before their support promise
is closed. The results below are observations, not final 1.0 release evidence.

## Real workloads observed

| Workflow | Observation | Result |
| --- | --- | --- |
| Pentalanine trajectory | Original structures `[4999, 0, 73, 3]`; 62 atoms; evaluated local frames `[3, 0, 2]`; 56 calculated H-bond occurrences; incident/internal/cross/between queries checked independently | Pass |
| Periodic pentalanine | A real residue translated by the first box vector; 76 occurrences, including 16 with nonzero images; Å policy; invariant scientific distances and correct projected endpoints | Pass |
| Solvated villin | 4,369 atoms, one structure; 2,439 calculated occurrences, 299 with periodic images; 429,648 bytes of numeric interaction storage | Pass |
| 2HGR sulfur geometry | 55,628 atoms; eight candidates at 0.205 nm; independently checked sulfur pairs; bonds/topology unchanged | Pass |
| Four real PDBs | 1VII, 1L2Y, 1TCD and 1ATP, first structure of each; 7,953 atoms; four durable sources and four base regions; batch/progressive coordinates agree | Pass |
| Multiple-protein scene | Source coordinates/order/maps, first-box policy, base visibility independent of represented detail, explicit isolation, MSV session and rejected missing-file batch preservation | Pass |
| Public Interactions workbench | Calculate, inspect, native `view.interactions.save`, aligned import, and repeated extraction `[2, 0, 2]`; 18 observations in each repeated displayed frame | Pass |
| Scientific persistence | Complete and interactions-only H5MSM plus MSV round trips preserve sparse coverage, named analyses, occurrence indices, units and images | Pass |
| Real exported HTML | Self-contained pentalanine export opens offline in actual Chromium with WebGL2; one canvas, rendered marker and no console errors | Pass, bounded readiness observation |
| Direct SDF loading | `caffeine.sdf` structure-count getter rejects its dispatcher's `structure_indices` | Fail: uibcdf/molsysmt#312 |
| Protein plus converted caffeine | Public conversion and addition succeed; later atom group IDs/names raise on nullable/missing membership, breaking scene/history | Fail: uibcdf/molsysmt#313 and uibcdf/molsysviewer#157 |

These calculations use real molecular data and the actual scientific methods;
they do not substitute synthetic positive family fixtures for laboratory data.
The earlier nine-family browser qualification remains separate evidence.
An additional bundled caffeine MOL2 probe is rejected by this provider's public
argument contract. The presence of a fixture does not establish a supported
input route; no MOL2-loading qualification is claimed.
Disulfide candidates are geometric proximity observations, not certified
covalent bonds. The review does not claim chemical preparation, docking or
automatic correspondence/alignment of independent proteins.

## Findings and practical interpretation

Batch and progressive loading express the same intention, retain source identity
and make base-region isolation usable without separate representations. Different
input boxes produce explicit provider warnings; the first box is preserved.
The first PDB in this exercise supplies a 0.1 nm placeholder cell. Preserving it
is correct under the agreed contract, but does not establish its physical
suitability for periodic calculations on the composed proteins. Users must make
their scientific cell/PBC decision explicitly, using the box API where needed.

The independent proteins also keep their original coordinate origins. A common
Whole does not establish a physical complex: cross-source contacts become
scientifically meaningful only when the user has prepared consistent coordinates
and chemistry. Source regions provide atom scopes for internal queries; neither
composition nor a rendered line implies docking or chemical preparation.

The public Interactions workflow is coherent: calculation creates a named
scientific analysis, rendering has its own filter, and H5MSM storage preserves
the complete analysis. Repeated extraction now preserves both scientific and
visual copies. Independent import still requires the explicit correspondence
declaration; successful dimension validation is not source authentication.

Small-molecule composition exposes the remaining gap. Public conversion of SDF
avoids #312 but is not a complete workaround because #313 then breaks scene
identity. The consumer must prevalidate its scene prerequisites before accepting
the candidate (#157), while MolSysMT supplies correct partial-hierarchy getters.
Those issues were opened with minimal public reproductions and linked consumer
evidence. No provider implementation or fabricated hierarchy was added here.

## Evidence and limits

Development uses `molsyssuite@uibcdf_3.14`, Python 3.14.7. MolSysMT source HEAD is
`033c12b341abf6e986f9ae9ddd6c84bf167222c8`, with unrelated dirty files; the runtime
reports an older derived version. Commit provenance and workspace state, not that
version string alone, identify these observations. No provider files were edited.
Commands, outcomes, data hashes and diagnostic artifacts are retained in
[`scientific_use_review_20261004.json`](scientific_use_review_20261004.json).

The scientific method/query/round-trip checks use
`python devtools/qualify_interactions.py OUTPUT_DIRECTORY`. The additional public
workbench and four-PDB drivers live in `/tmp`; their receipts retain hashes and
the concrete sources and operations above. The first driver assertion mismatch
and each actual provider failure remain distinct evidence. Chromium initially
could not create sockets in the sandbox; the explicit rerun outside the sandbox
passed, without an E2E skip. The exported-page observation establishes offline
readiness and WebGL2 rendering, not visual legibility, interactive first-contact,
native-GPU performance or a full hosted core run.

The 851.37 MiB peak RSS belongs to the combined scientific process, including the
55,628-atom input and provider/runtime caches. It is not the memory footprint of
the sparse interactions alone or a scalability target. The trajectory selects
four samples from a 5,000-structure source; this review does not recalculate all
5,000 structures. Earlier large-workload measurements remain in their own records.

## Next steps

Resolve #157's candidate prevalidation and coordinate #312/#313 with MolSysMT.
Then repeat the affected mixed-source workflow against a fixed provider and its
eventual published artifact. Retain the existing #114/#140/#101 exact-package,
platform and hosted-candidate gates. Finish public documentation and obtain
human visual/first-contact observations before declaring 1.0 readiness. Freeze
and qualify the intended minor version under
[`version_assessment_20261003.md`](version_assessment_20261003.md).

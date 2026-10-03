# Minimal Interactions before 1.0

## Public workflow completion — 2026-10-02

The maintainer authorized four bounded additions/corrections after a public API
review. They are implemented in the working tree: public occurrence paging
independent of rendering (#142), coherent multi-card trajectory plots (#143),
native named-analysis H5MSM save (#144), and per-observation selection/focus from
Python and Studio (#145). Their contracts are in
[scene contracts](scene_contracts.md#observation-actions-and-scientific-save--2026-10-02).
No additional detector or trajectory statistics scope was introduced.

The real-provider regressions and two real Mol* browser suites pass. All 713
public callables have ArgDigest and explicit bypasses. The once-run Python suite
had sandbox socket/browser failures, all corrected by a scoped unsandboxed run;
the JavaScript suite exposed two obsolete hide expectations and a missing event
declaration, whose scoped corrections pass. The final plot-axis guards were
checked separately after that full run. Exact records, limitations and hashes
are in [the evidence](public_workflow_completion_20261002.json).
The four reports remain partial until the product changes are committed and
qualified on the supported published dependency. This source evidence does not
replace the compatible-provider and exact-candidate gates in #114/#140. Public
documentation remains the last development block.

## Family API update — 2026-10-01

The maintainer selected explicit family namespaces over a public generic
`compute(kind, parameters=...)`. The nine currently implemented experimental
MolSysMT families are exposed through named getters with explicit signatures:

| Family | Public calculation |
| --- | --- |
| `hbonds` | `get_hbonds`, `get_buch_hbonds`, `get_luzard_chandler_hbonds` |
| `disulfides` | `get_disulfide_candidates` |
| `ionic` | `get_ionic_interactions` |
| `pi_pi` | `get_pi_pi_interactions` |
| `cation_pi` | `get_cation_pi_interactions` |
| `halogen_bonds` | `get_halogen_bonds` |
| `hydrophobic` | `get_hydrophobic_interactions` |
| `metal_coordination` | `get_metal_coordination` |
| `water_bridges` | `get_water_bridges` |

Each operation binds the view's molecular system, requires a storage name,
defaults to `structure_indices="current"` and `pbc=False`, returns the complete
scientific result and attaches it atomically to `view.molsys.interactions`.
Scientific parameters/defaults belong to the matching public provider getter;
all wrappers carry ArgDigest and explicit `skip_digestion=False`. Output is
fixed to the sparse result. Cross-system calculation and legacy custom role
arrays unsupported by that sparse result are outside these wrappers.

```python
view.interactions.hbonds.get_hbonds(name="hydrogen_bonds")
view.interactions.ionic.get_ionic_interactions(name="ionic", distance_threshold="0.4 nm")
view.interactions.add("hydrogen_bonds", tag="hb")
```

The modern H-bond criterion requires a declared chemical graph. Old peptide
demo topology lacks some required bond-chemistry columns: that scientific
refusal is retained, without silently changing the method or inventing bonds.
Explicit Buch and Luzard–Chandler wrappers remain available. Calculation is
exposed only through the named family getters; the original `compute_hbonds`
and `compute_disulfide_candidates` routes have been removed and their consumers
migrated. No public generic `compute` exists. Studio calls the same named
family wrappers as Python.

Studio calculation now uses criterion selectors and typed family controls,
including length/angle units, angular intervals, ring geometry and water order.
Blank optional cutoffs delegate to the selected getter; mandatory cutoffs are
checked before dispatch. Drafts are isolated by family and criterion and remain
available across summary updates. Changing nm/Å or degrees/radians converts an
entered value, preserving its physical magnitude. Criterion-specific profiles
are explicit; inactive parameters are excluded from the request.

This bounded form covers ordinary geometric calculation. Explicit H-bond site
arrays, chemical-state overrides and execution/recognition limits remain
available through the Python family API. Its metadata inspector still displays
stored scientific parameters. No free-form parameter JSON is required for Studio
calculation; the broader post-1.0 UI specification remains separate.

Graphical support preserves complete roles and grouped participants. Charged
groups/rings receive identified centroid guides; ionic minimum-distance
measurements retain their definition. Halogen bonds draw halogen–acceptor but
retain four roles; metal coordination remains a candidate. Water bridges draw
two/three directed H–acceptor legs under one occurrence identifier. Counts
distinguish supported occurrences and graphical segments. No detector is
triggered by playback. PBC remains the provider's observed-image contract;
split compound groups are refused rather than internally unwrapped.

Work is tracked in uibcdf/molsysviewer#140, with the exact experimental provider
revision and verification record in
[the active report](pending_proposals/align_interactions_with_molsysmt_families.md).
This expands the working-tree integration; it does not certify a public provider
release or automatically make all nine families mandatory MolSysMT 1.0 gates.

## Earlier minimum and release qualification

**Status:** Working-tree implementation (2026-09-30) now includes the scientific
Python routes, tagged visual sets, current-frame Mol* geometry and the native
Studio subpanel. Six synthetic coordinate/interaction workloads are recorded in
[the performance observations](interactions_performance.md). Provider-release,
larger GPU workload qualification and final candidate validation remain open; #114 remains
partial. The [implementation record](pending_proposals/interactions_minimum_before_1_0.md#native-scene-and-studio-implementation-2026-09-30)
states the supported behavior and limits.

Bounded real detector, sparse-query, periodic-image and H5MSM/session checks
now pass, including a complete 5,000-frame calculation and actual calculated
Mol* links before/after session restoration. See
[the qualification record](interactions_qualification.md). Published MolSysMT
0.22.4 still lacks the required API; its compatibility probe confirms ordinary
viewing and explicit refusal, not qualification of Interactions.

The bounded viewer work is `uibcdf/molsysviewer#114`. MolSysMT owns the
analysis namespace and scientific result contract in `uibcdf/molsysmt#250`.
The broader viewer domain and UI remain in `uibcdf/molsysviewer#48` and
`uibcdf/molsysviewer#56` after 1.0. Updating Mol* is `uibcdf/molsysviewer#115`
after 1.0. This plan coordinates those records; it is not a queue entry.

The API design lives in the
[active proposal](pending_proposals/interactions_minimum_before_1_0.md#python-api-design-for-implementation-2026-09-29)
with its implementation record. Existing analyses, independent H5MSM import and native
calculation converge on `view.molsys.interactions`. Tagged scene objects
reference those data. MolSysMT is the scientific backend without requiring
addon registration; progressive retirement of its separate addon follows
migration of its useful workflows.

| Stage | Work | Exit condition |
| --- | --- | --- |
| 0. Shared result contract | Use the experimental sparse result and optional Buch/disulfide outputs. Verify producer versions, declared file correspondence, coverage, images and queries. Measure combined coordinate/analysis residency and identify when public file queries or chunked construction are needed. Consult likely TopoMT, PharmacophoreMT and DockingMT consumers. | Committed provider revision, documented public adapter and representative workload evidence. H5MSM 0.5 must preserve the supported analyses; stabilizing the complete modular format remains provider-owned work. |
| 1. Python domain | Implement analysis discovery, declared attachment/import, named calculations, queries and tagged displays. Add collection operations, style, layers, state/session fidelity and edit invalidation. | Real demo results across single, variable-count, empty and nonconsecutive structures; atomic failures; visual undo independent of scientific storage; exact state/session restoration. No addon registration. |
| 2. Browser realization | Project current-frame H···A and candidate S···S links using installed Mol*, adding explicit geometry where PBC images require it. | Real-browser evidence covers frame changes, empty versus unevaluated status, visibility, reconstruction, parallel picking and observed periodic geometry. |
| 3. Studio design | Recorded 2026-09-30 after source inspection of Shapes, Annotations, Regions and the selection dock. Three source routes share one display editor. | Implemented through public Python visual/inspection methods and checked against real Mol*. |
| 4. Studio implementation | Native subpanel implemented; misleading Shapes H-bond calculation entry removed. | Real Python/browser evidence covers stored-data creation, inspection, visibility and correlated actions; Python tests cover calculation and declared file import. |
| 5. Release evidence | Promote implemented rules into durable contracts and public docs. Run scientific, scene, static HTML, memory and core browser checks on the final candidate with the supported provider version. | The exact 1.0 candidate has validation evidence, explicit trajectory coverage, bounded payload behavior and a published dependency providing the required public APIs. |

The 1.0 slice includes native computation and loading, plus reconciliation of
the existing Shapes H-bond claim. It does not require full addon removal,
migration of unrelated molecular workflows, or a Mol* dependency update.

MolSysMT review commit `82bcb810e8c482a78142a7a19c70f68d72b42ba0`
provides an experimental result and H5MSM 0.5 path. The supplied synthetic
fixture and public workflow test passed on 2026-09-29. Follow-up commit
`0d1a2bf0aa9e507b546135b24d0368db10c50a0c` resolved occurrence
identity for picking and specified the periodic-image convention; five
focused provider tests passed against that commit.
Commit `2e79b5f290fa8e7cde5d4b8f9d4ed8110a006b69` adds the declared
correspondence policy and optional Buch/disulfide outputs; the four-file
targeted provider selection passed 27 tests. Producer-version changes were
committed in `04c6593cc`; consumer calculations, queries and session checks
now use clean provider revision `f9f4c1a5fe22124eee01e3ceb37d582c86aee0ac`.
The 2026-09-30 review and measurements used source HEAD
`a04a5e7aad508b0a50ca9f22043f8ca6084411c8`, preserving the provider's independently
dirty working tree. The clean revision above remains the earlier integration
checkpoint, not the current measured checkout.
Stage 0 now has initial synthetic joint memory/query measurements; real scientific
workload and supported dependency-release qualification remain open. These are
source-checkout results, not installed-release evidence. Ordinary views were also
checked against the published 0.22.4 package; that package lacks the experimental
interaction API and cannot qualify the feature. Public bounded occurrence pages
are requested in `uibcdf/molsysmt#264`.
The renderer uses explicit observed-position dashed meshes rather than relying
on the installed Mol* extension's two-endpoint/PBC assumptions.

The current implementation provides discovery, sparse queries, explicit
attachment and file import, named calculations, scientific session persistence,
and edit invalidation. It also provides tagged sets with filtering/style,
current-frame geometry, bounded inspection, state/session references, layers,
and visual undo. Studio uses those public workflows for all three sources.

Live playback queries the requested frame and never calculates interactions.
Standalone HTML embeds compiled frame projections with a 64 MiB interaction
budget; it raises when that budget is exceeded. This initial export repeats
geometry for overlapping visual sets; sharing compiled analysis geometry across
sets is a remaining optimization, not an implemented storage claim. Scientific
inspector pages require a live Python session.

After 1.0, add further scientific families and data sources only when their
MolSysMT criteria and result contracts are defined. The nine implemented
experimental families are covered by the update above. Persistence analytics,
advanced Studio controls, additional external formats, and a Mol* calculation
engine remain under `uibcdf/molsysviewer#48` and
`uibcdf/molsysviewer#56`.
Incremental scientific editing, dynamic calculations during playback,
automatic origin authentication, arbitrary subsystem embedding and public
file-backed queries remain growth work, with priorities informed by the
joint measurements. Native H5MSM import belongs to the initial slice.

## Scale qualification — 2026-10-02

Done: the expanded [performance record](interactions_performance.md#expanded-participant-and-family-qualification--2026-10-02)
and [structured measurements](benchmarks/interactions_scale_20261002.json)
cover 24 sparse adapter workloads and ten real detector probes, including both
water orders. All query identities, coverage and current-frame segment counts
pass. The 19 focused guards use actual demo/chemical systems and public H5MSM.

Retain named in-memory analyses and visible-frame queries for the initial slice;
these bounded observations do not require a new file-backed Viewer mode or
establish an arbitrary large-system promise. Done: compound projection now uses
bounded public grouped geometry batches (uibcdf/molsysviewer#141), reducing the
measured 1,000-observation preparation from about 4.2 seconds to 281–291 ms.
The 16 specific guards, 71 related checks, complete Python suite (2,572 passed,
23 skipped) and complete real Mol* Interactions subpanel E2E pass. See the
[comparison and limits](interactions_performance.md#compound-projection-batching--2026-10-02).
Qualification stays partial. Provider query review (#288) and Pandas 3 SMARTS
fix (#289) are now verified in the follow-up below; adapt the affected consumer
guard and complete compatible published-artifact/exact-candidate CI checks.
Both provider issues belong to uibcdf/molsysmt. Keep the existing sparse result, participant/
PBC semantics, explicit quantities and occurrence identities. Public documentation
remains the last implementation block.


## Installed pair qualification — 2026-10-02

Done: the current Viewer wheel and clean experimental provider wheel pass 91
bounded installed checks and six offline real Mol* geometry pages with Pandas
2.3.3. Both libraries import from site-packages, and the runtime/version validator
passes. The new installed runner reuses the existing scientific tools/tests and
checks scientific origins before and after pytest. See
[artifact identities, reproduction and limits](installed_artifact_qualification.md#installed-experimental-interactions-pair--2026-10-02).

Pandas 3.0.6 exposes a public provider SMARTS mutation of read-only storage,
reproduced without Viewer and reported as uibcdf/molsysmt#289. Keep that failure
explicit; the Pandas 2 configuration does not resolve it or change repository
dependency declarations. That initial failure is preserved; the current provider
review below verifies its resolution. Public documentation remains last.

## Provider #288/#289 review — 2026-10-02

Done: both issues are closed upstream and verified from clean `396e6979f`
compiled/installed with Python 3.14 and Pandas 3. The unchanged Viewer artifact
passes 90 cases, 15 provider guards and six offline Mol* pages. Explicit-frame
query timings and SMARTS chemistry now satisfy the reported defects. One existing
Viewer guard must deliberately reattach its malformed periodic observation after
the coordinate edit; public setters now invalidate the old analysis. Separate
invalidation and malformed-import probes confirm correct Viewer behavior.
See [evidence and limits](installed_artifact_qualification.md#provider-288289-review--2026-10-02).

The guard adaptation is completed in the follow-up below. Next qualify a compatible published provider, freeze/review the
product commit and run exact-candidate installed/core CI gates. Consider the new
public bounded `Interactions.to_page()` contract as a separate consumer integration
step; this review does not adopt it or claim selective H5MSM reads. Public
documentation remains last; #140 stays partial.

## Provider invalidation guards — 2026-10-02

Done: malformed-image projection is isolated from public setter invalidation,
and three real pi–pi cases verify edited-frame coverage, unchanged scientific
content, new occurrence identifiers and cache refresh. All 94 bounded installed
Interactions cases and three import guards pass with Pandas 3. Scientific tools
preserve installed discovery; source audits use their own checkout paths and
inventory source/digester paths follow the actual imported package.

The complete installed attempt remains failed (2,482 passed, 9 failed, 78 errors,
27 skipped). Diagnosed tooling and development-dependency cases are verified in
bounded corrections (309 unique passes, one skip); no second full suite is claimed.
See [the current evidence](installed_artifact_qualification.md#provider-invalidation-guards-and-installed-follow-up--2026-10-02).
No production implementation change was necessary. Compatible published provider,
proven feature floor and committed exact-candidate installed/core/hosted gates
remain next. Public documentation remains last; #140 stays partial.

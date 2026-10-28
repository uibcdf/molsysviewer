# MolSysMT tools add-on — implementation plan

**Status: partial source implementation; installed qualification pending —
2026-10-27.** The maintainer authorizes the Viewer development effort to implement
the integration in the owning MolSysMT repository. This is a new plan under
[the core/add-on boundary](core_and_addon_boundary.md). The withdrawn native
Studio expansion plan remains removed. The experimental source integration provides bound `basic` queries and read-only
comparison, independent extraction/copies/conversion and preflight, managed
retained-axis removal and coordinates/box setting, with root aliases and
synchronization controls. All eleven current native `topology` exports now have
explicit source wrappers, including chemical-graph and sequence analyses.
Eighteen `structure` calculations reuse the same host serialized reader;
native translation, proper rotation, plane reflection, least-RMSD fitting/alignment,
explicit centering, single-structure displacement, principal-axis alignment and both dihedral editors now receive independent outputs and managed in-place updates.
Native self-reference and numeric-selection repairs under uibcdf/molsysmt#452 /
uibcdf/molsysmt#453 are separately delivered by the scientific owner in a38c00d19;
combined exact-head CI is tracked in the receiving record. Reflection now
receives the default z normal and finite nonzero scaled normals through the
scientific owner's uibcdf/molsysmt#460 repair and the combined source CI. The new contained-source/initial-target
centering contract delegates to native center; uibcdf/molsysmt#451 now has its
requested final closure comment. All 28 reviewed structure function exports are
now exposed. Native torsion repairs under uibcdf/molsysmt#461 and
uibcdf/molsysmt#462 are delivered in 6f6ed6bf1, with the addon help and focused
receiver checks reconciled in the PBC integration. Complete exposure is not full scientific
or installed-package qualification. The scientific owner repairs native undefined-direction and partial-write
rejection under uibcdf/molsysmt#456 / uibcdf/molsysmt#457 in e6677e4c6.
The addon forwards those checks without a scientific workaround. Secondary-structure, symmetry-corrected RMSD and PCA readers
retain explicit engines, chemistry, units, result ownership and native limits.
The PCA weight-container repair uibcdf/molsysmt#448 is received from 306e91dda. Native endpoint/unit and
sequence-group corrections under uibcdf/molsysmt#439, uibcdf/molsysmt#440,
uibcdf/molsysmt#441 and uibcdf/molsysmt#442 are received
from their owning team, including the native keyword-only identity flag.
Maxima, contacts and RMSF are explicitly available in source. Minimum-distance
and neighbor wrappers now have authorized local receiving of provider repairs
under uibcdf/molsysmt#444 and uibcdf/molsysmt#445, now closed after the
scientific owner committed 5710cc0cff1f3f468823699104e51e6fe029c3b2.
The native pytest matrix and real-view references retain explicit scope; addon
exact-head CI and installed qualification remain separate. The addon
supplies no scientific formula or parameter substitution. No new host runtime
is needed. Broader scientific coverage,
installed compatibility, dependency floors and release remain separate.
All thirteen reviewed PBC exports have explicit source wrappers. Native repair
d7c82e92f supplies orthogonal omitted/None box angles, correct centered in-place
publication and the repaired course fixture under uibcdf/molsysmt#465 / uibcdf/molsysmt#466 /
uibcdf/molsysmt#467, with the native dictionary-axis repair under uibcdf/molsysmt#472. The
addon removes its temporary centered-in-place restriction and delegates the
repaired science. Twenty-four focused centered receiver combinations pass;
source qualification remains separate from installed artifacts.

Thirteen of the thirty reviewed physchem exports now have source wrappers:
the original seven property readers plus both ProtOr helpers and four
reference-table lookups (surface area, volume, area buried and buried fraction).
The first seven retain their completed six-control source CI on 2b777e554;
the additional six pass 67 focused cases. One broad local attempt finds a
corrected wrapper-forwarding error; all 329 affected-file cases then pass.
Producer 3c2dfcf65 passes all six source controls (1,576 native / 1,230 addon
cases). Native query repair 825a66d39 then passes 627 receiving cases and
40 inherited docstring examples. Producer 77657b030 adds positive syntax/
intended-population guards and completes fixed-ref smoke 40421689803
(2,011 native / 1,246 addon cases), with the other five exact-SHA controls
passing. The original main smoke cancellations remain cancellations. Raw
descriptors do not calculate conformational SASA/volume or assign chemistry. Native syntax/element repairs are received under
uibcdf/molsysmt#470 / uibcdf/molsysmt#471; uncertain Collantes units are uibcdf/molsysmt#473.
An additional conformational `physchem.get_sasa` wrapper now has bounded CPU
receiving, bringing source exposure to 14/30. It retains all-atom occlusion,
selected output axes, probe/sampling/execution parameters and native results.
Provider 9442e0df2 completes all six source controls, including smoke 40427400657
(2,011 native / 1,302 addon cases), at its original bounded scope. Native
repair d8bda65ec closes uibcdf/molsysmt#478 / #479 with squared working-length
units and explicit keyword-only `pbc` forwarding. Periodic MDTraj requests with
a box reject; native MIC excludes self-images. Sixty-one focused SASA receiver
cases pass on the incoming repair; combined source qualification remains separate.

Two additional stored-chemistry reports, `get_hydrogen_inventory` and
`get_chemical_readiness`, bring source exposure to 16/30. They retain detached
results, unknown-count markers, indexed/virtual H, coverage/evidence and explicit
single-structure/state selection without preparation or scene publication.
Native default-reference external readiness syntax is repaired under
uibcdf/molsysmt#480; no consumer selector compensation is introduced.
Provider d0563c61d passes 66 new-report cases, 61 focused SASA receiver cases
and one 1,760-case joint regression, plus 37 guide blocks / 53 inherited
examples. Native repair d8bda65ec also passes its five applicable source
controls (smoke 40429148780: 2,011 native / 1,307 addon cases). The final
combined producer d0563c61d completes all six source controls; smoke
40430386606 passes 2,033 native / 1,373 addon cases, zero failures/errors/skips.
Two aromatic participant/flag readers bring current source exposure to 18/30;
twelve reviewed exports remain pending. Provider eeaf1cab8 forwards native
scientific signatures/defaults and returns, preserving stored ring membership
versus optional RDKit perception, full-graph prerequisites, explicit chemistry
and state/frame scope. No assignments, preparation, scene objects or automatic
synchronization are added. Native repairs #480, #481 and #482/#483 are received;
default-reference external syntax and invalid resident frame guards are tested
without a consumer workaround. One 1,935-case regression preceded the incoming
repairs; 363 graph-repair checks and a final 910-case changed-area follow-up
retain their distinct source identities. All 38 guide blocks and 65 inherited
examples pass. Producer eeaf1cab8 completes all six exact-source controls;
smoke 40438923814 passes 2,117 native and 1,467 addon cases with zero failures,
errors or skips. The terminal provider receipt is published in 69b53456b.

Native 8cf8b0107 changes Collantes surface area to a standardized quantity using
a provisional Å² convention; the addon preserves it unchanged. Original-paper
units/normalization/values remain unverified under uibcdf/molsysmt#473. Installed
MDTraj >=/<= compatibility is tracked separately under uibcdf/molsysmt#484;
compact collection-count presentation is uibcdf/pytest-receptor#46. Neither
report changes the native pytest exit authority or adds a selector workaround.
GUI and installed qualification remain pending. No host runtime or dependency
floor changes; both 1.0 publications remain paused.

Three further chemical-feature readers add `get_charge_centers`,
`get_hydrophobic_sites` and `get_halogen_bond_sites`: current exposure is 21 tools. The producer receives the 31-export baseline
after bulkiness in af8264049; native 5681f5e78 then adds secondary-structure
propensities, bringing the inspected inventory to 32, with eleven pending addon
tools. The new reader is not qualified by the older source gate. The wrappers
preserve sparse whole-center versus ordered-pair membership, formal-charge
quantities, explicit chemistry/state/selection/model controls, match caps and
native results. Numeric-array independence and reference-metadata ownership
are distinct qualifications. Native #488 repairs the omitted SMARTS reference-selection
branch; positive default/None reference and a nonzero declared reference are
received without downstream translation. Explicit SMARTS state restrictions
remain native. No preparation, charge assignment, result adoption or scene
synchronization is introduced.

The frozen pre-repair regression passes 2,812 cases; the subsequent native
repair follow-up passes 390, including the expanded 81-case new reader file.
These distinct source observations are not two full-suite gates. All 39 guide
blocks and 83 inherited native-context examples pass. The actual imported
PyParsing is 3.3.2; stale 3.3.3 distribution metadata coexists, so this environment
is not claimed as a clean installed qualification. The five original source
controls and fixed-ref smoke 40446657873 complete for 02671792f: 2,293 native
and 1,548 addon cases pass with zero failures/errors/skips. Original main smoke
40445094772 remains cancelled; the independent same-source recovery retains its
ref and official evidence. Terminal receiving is published in cff1f8fe0.
That earlier source gate predates the two reference-scale wrappers now received
below. Continue the remaining seven readers/calculators, two transformations and
one explicit-input factory before designing graphical tasks.
Native reference-metadata aliasing under uibcdf/molsysmt#490 is repaired in
6eebcd4ec and separately received through 172 targeted local cases plus a bound
cross-reader mutation check. Small references are detached by the provider; no
wrapper copy is introduced. This does not relabel the older 02671792f hosted
gate or claim a new hosted/installed qualification.

### Bulkiness and propensity mirrors received — 2026-10-26

Provider `efc9b94f37bbad8af251b58f81bbb17db029793f` adds two explicit readers under
`view.addons.molsysmt.physchem`: `get_bulkiness()` and
`get_secondary_structure_propensity(conformation, ...)`. The facade now exposes
23 functions; native `97a8dc08c` has 33 public physchem exports, leaving ten
unreceived, including the newly added TPSA. These counts describe source
coverage, not equivalent scientific algorithms or installed compatibility.

The wrappers omit only the primary system, resolving current `view.molsys` at
call time. Native signatures, digestion, selection syntax/order/repetitions,
scalar/empty axes, strict group-only/name validation, units/results and optional
attribution are retained. Bulkiness is a reference area quantity, not a measured
molecular surface. Levitt weighted propensities are detached dimensionless
float64 frequency ratios with a required category; they are not probabilities,
predictions or coordinate-based secondary-structure assignments. No cap filtering,
parent substitution, sum, normalization, preparation, coloring or scene sync is
introduced. Rich selectors retain their native coordinate requirements.

The [provider receipt](https://github.com/uibcdf/molsysmt/blob/efc9b94f37bbad8af251b58f81bbb17db029793f/devtools/data/molsysviewer_tools_reference_scales_receiving_20261026.json) separates
119 focused cases and one 3,144-case frozen regression on `39bb09715` plus the
new readers from the subsequent 596-case focused receiving on incoming
`97a8dc08c`. All pass without failures/errors/skips. The native group-free repair
and reference-metadata ownership guard are included in the new bounded CI tier.
All 40 guide blocks and 90 inherited examples also pass after the incoming merge.
Two mistaken test expectations and an authored Markdown prefix were corrected
before integration; the receipt retains those attempts. No second full local
regression, TPSA receiving or universal scientific qualification is claimed.

All six exact-source controls now pass for this producer. Smoke
[40453242375](https://github.com/uibcdf/molsysmt/actions/runs/40453242375)
passes 2,576 native and 1,666 addon cases, zero failures/errors. Two native and
one addon attribution tests are skipped because optional Ackredit is absent in
CI; local receiving executes them without relabeling the hosted omissions.
Dependency, Ruff, guide integrity, suite policy and Conda governance pass on the
same source. The [terminal provider receipt](https://github.com/uibcdf/molsysmt/blob/c905d8ac753e98ec11959fac5ccbe049311d2068/devtools/data/molsysviewer_tools_reference_scales_source_ci_20261026.json) preserves
job/step identities, exact Viewer deaba4cbea source, counts, logs and complete
receptor-bundle file digests. The evidence-only closeout is c905d8ac7; it does
not change the qualified runtime. The independent scheduled Zenodo probe is
excluded from these six source controls. Viewer reporting/link/architecture
receiving passes 286 cases.

GUI, remaining native functions, installed qualification and both paused
publications retain their separate scope. No Viewer runtime or dependency-floor
change.

### Molecular TPSA receiving — 2026-10-27

Provider `f55d7c2f77057ae97b7cb0219d427f41132b8f0c` adds
`view.addons.molsysmt.physchem.get_tpsa(...)`. The experimental facade exposes
24 of 33 physchem exports in this reviewed committed baseline; nine remain
unreceived. Parallel native molecular-descriptor development is preserved and
has not been included or relabeled as qualified by this slice.

The thin reader retains the native signature minus current `view.molsys`,
digestion, molecule-order/repetition/scalar/empty axes, complete covalent
boundaries, declared chemical states and nonconsecutive structure context,
squared area units and explicit N/O versus N/O/S/P variant. The optional detached
report preserves molecule/atom maps, method, parameters and provenance. It adds
no H preparation, fragment capping, source hierarchy repair, selector translation,
aggregation, scene coloring, adoption or synchronization. TPSA is a topological
descriptor; it does not measure conformational exposure or predict permeability.

The [source receipt](https://github.com/uibcdf/molsysmt/blob/f55d7c2f77057ae97b7cb0219d427f41132b8f0c/devtools/data/molsysviewer_tools_tpsa_receiving_20261027.json) records 53 directed consumer cases and the one
3,294-case frozen regression on c905d8ac7 plus this wrapper, all passing with
zero failures/errors/skips and unchanged runtime/backend hashes. All 41 guide
blocks and 94 inherited native-context doctests pass. Bundled caffeine is
explicitly read with RDKit to supply its declared H inventory; native SDF input
with unspecified CTAB evidence retains rejection rather than hidden inference.
Initial fixture/selector/input observations and corrections are retained.

Two independently reproduced native defects have maintainer-authorized reports:
uibcdf/molsysmt#494 duplicates molecule rows when adding groups to a populated
builder; uibcdf/molsysmt#495 fails MDTraj selection of group-free topology with
NAType. The adapter adds no workaround and does not claim those repairs received.
Numeric/native-expression molecule selection is received; the external group-free
adapter remains a native limit. Continue owner repairs and their later receiving.

All six applicable exact-source controls pass for f55d7c2f7. Fixed-ref smoke
[40549539065](https://github.com/uibcdf/molsysmt/actions/runs/40549539065)
passes 2,645 native / 1,718 addon cases with three native and two addon skips
because optional Ackredit is absent. Those tests execute locally; the hosted
omissions remain omissions. Our automatic main smoke 40549383525 was intentionally
cancelled during setup to execute one canonical gate independently of concurrent
main pushes; it is not a pass. The [terminal source receipt](https://github.com/uibcdf/molsysmt/blob/69f357e7eb0f53151e60de294ea58791e2f2dd59/devtools/data/molsysviewer_tools_tpsa_source_ci_20261027.json)
retains both official runs, controls, source/ref/job/step identity and complete
log/receptor-bundle digests.

The owner then commits native refactor 4e2e18ce71d64256baf3c0a7fd52f89e6aa9b792,
sharing TPSA internals with the new get_lipophilicity. The TPSA wrapper stays
unchanged. A clean incoming-source snapshot passes 158 directed cases and all
41 guide blocks / 94 inherited examples, zero failures/errors/skips. No second
full regression is claimed. Owner smoke
[40549946055](https://github.com/uibcdf/molsysmt/actions/runs/40549946055)
passes 2,645 native / 1,718 addon cases with the same five optional skips; Ruff,
guide integrity, suite policy and Conda governance pass on that same source.
The unchanged dependency declarations and CI pins retain their earlier applicable
f55d7c2f7 check; no separate dependency-contract workflow ran for 4e2e18ce7.
The [incoming receipt](https://github.com/uibcdf/molsysmt/blob/69f357e7eb0f53151e60de294ea58791e2f2dd59/devtools/data/molsysviewer_tools_tpsa_refactor_receiving_20261027.json)
keeps this receiving separate from the frozen 3,294-case older-source regression.
The inspected inventory now has 34 native physchem exports; the addon stays at
24, with ten pending including lipophilicity. Its model is not automatically
exposed or scientifically qualified by this TPSA slice. Both original owner
issues #494/#495 remain unreceived repairs. New uncommitted molecular-descriptor
work stays outside these source identities. Evidence is published in 69f357e7e.

Viewer reporting/link/architecture checks pass 286 cases. GUI, optional-provider
absence, installed packages, universal model accuracy and publication retain
separate scope; both 1.0 publications stay paused.

The previously pending Viewer core browser run
[40454434547](https://github.com/uibcdf/molsysviewer/actions/runs/40454434547)
passes all 44 suites on 386ed937. This closes that earlier observation without
qualifying new TPSA source, installed artifacts or remote preview.

### Lipophilicity and descriptor contributions received — 2026-10-27

Provider `ea9fff3395157389b3a245cf70f58517973e76b8` adds
`view.addons.molsysmt.physchem.get_lipophilicity(...)` and receives the widened
TPSA/native contribution contract from 010c489aa. The experimental facade exposes
25 of 34 reviewed physchem exports; nine remain unreceived. Native science stays
in MolSysMT; the addon omits only the primary and resolves current view.molsys.
No host runtime or public dependency-floor change is introduced.

Both readers preserve seven native output levels, source order/repetitions,
scalar element axes, scalar system sums and typed empty selections. Complete
parent chemistry is evaluated before output filtering; element_* maps identify
outputs and molecular maps identify calculation contexts. Indexed H retains its
row; nonindexed H is attributed to its source attachment atom. TPSA retains
squared area units and explicit N/O versus N/O/S/P; lipophilicity retains
float64 dimensionless scores and charged-site metadata, including net-neutral
charged graphs. Contributions are not measured exposed areas, group properties,
mixture logP or pH/logD predictions. No source/H preparation, neutralization,
counterion stripping, fragment recalculation, implicit aggregation, color,
result adoption or scene synchronization is added.

The [provider receipt](https://github.com/uibcdf/molsysmt/blob/ea9fff3395157389b3a245cf70f58517973e76b8/devtools/data/molsysviewer_tools_molecular_descriptors_receiving_20261027.json) records all 122 directed cases and the one
frozen 3,589-case applicable regression on 010c489aa plus the wrappers, zero
failures/errors/skips and unchanged source/backend hashes. All 43 bound-guide
blocks and 98 inherited native-context doctests pass. Fixtures include reversed
explicit group/chain membership, native positive external syntax with real
hierarchy, H-presentation conservation, explicit state/structure associations,
charged sources, bundled caffeine, detached nested metadata, named coverage,
scene preservation and cached pending/replacement/lifetime behavior. Broader
predictive validity, optional-provider absence, GUI and installed artifacts are
not inferred from these source checks.

The initial fixed-source smoke
[40570840482](https://github.com/uibcdf/molsysmt/actions/runs/40570840482)
ended officially cancelled at the 15-minute maximum. Both pytest tiers had
completed successfully (2,807 native / 1,845 bound passes, four / three optional
Ackredit skips); that does not make the workflow green. Its GitHub timeout
annotation and original outputs are retained under uibcdf/molsysmt#501. Five
other source controls pass. The earlier automatic main run was separately
cancelled during setup to isolate that fixed-source run.

Owner source 3781031d0 repairs uibcdf/molsysmt#494/#495. Directed receiving
passes 324 cases with one strict expected failure for the separate native
atom-insertion defect uibcdf/molsysmt#499. Six positive bound MDTraj checks
(TPSA/lipophilicity at atom/molecule/system levels) preserve source hierarchy,
context and scene. All 43 guide blocks / 98 inherited examples pass again.
Owner CI 40571118517 fails because older fixtures group disconnected inherited
molecules together: six failures / 123 setup errors, with the bound tier not
reached. That failure remains recorded as such.

Correction 4ad988584 adapts both fixture factories to public molecule membership,
without changing scientific assertions or readers (210 focused cases pass).
It raises the bounded CI budget to 25 minutes without removing tests, under
uibcdf/molsysmt#500/#501, and adds the native hierarchy guards to both selected
tiers. Seven integration-tool checks, Ruff, shell syntax and devguide validation
pass. The [directed receipt](https://github.com/uibcdf/molsysmt/blob/4ad988584ec1409fb9f90e2e8ce2aab05a638473/devtools/data/molsysviewer_tools_descriptor_hierarchy_receiving_20261027.json)
keeps each source and result separate. The one 3,589-case local regression is
not repeated or relabelled as a later-source full regression.

The corrected-source gate
[40575948453](https://github.com/uibcdf/molsysmt/actions/runs/40575948453)
passes on fixed ref receiving/descriptor-ci-4ad988584: 2,847 native passes,
four optional Ackredit skips and one strict #499 xfail on that frozen source;
1,845 bound passes and three optional Ackredit skips. Five additional source
controls pass. uibcdf/molsysmt#500/#501 are closed with guard/normative records
and receipt 4a51f327e. The intentionally cancelled automatic run remains non-pass.
Later owner #499 repair ab165135e receives 80 native builder cases without
expected failures; it is not retroactively included in the earlier source CI.
Viewer E2E 40576276877 passes on a7dcd4cc. Source receiving does not qualify
installed packages. Both 1.0 publications remain paused.


### Explicit chemical readers received — 2026-10-27

Provider `63600396584f78aef05500cd13a1c5fd37b75728` adds the expert paths
`view.addons.molsysmt.physchem.get_autodock_atom_types(...)`,
`get_cip_stereochemistry(...)` and `get_partial_charges(...)`. This brings the
reviewed physchem facade to 28 of 34 native exports, six pending. The current
primary is implicit; required AutoDock scheme and charge method, keyword-only
CIP coordinate inference, scientific validation and skip_digestion remain native.
No host runtime or public dependency floor changes.

Full graph evaluation precedes sorted unique atom output. AutoDock labels remain
separate from element symbols and stored force-field types. CIP retains complete
context, S/R and E/Z labels, source atom/bond maps and declared versus coordinate
evidence; coordinate inference needs one explicit 3D structure. Partial charges
retain native units, Gasteiger-Marsili or explicit OpenMM force-field prerequisites
and full-source total checks. These readers do not prepare chemistry, place H,
select a visible structure implicitly, assign results, color or synchronize the
scene. Pending reads, cached primary replacement and closed/empty lifetimes use
the existing managed read boundary.

All 69 directed consumer cases pass within one frozen 3,819-case applicable
regression, zero failures/errors/skips, unchanged runtime and backend hashes.
A final test-declaration line wrap has an identical AST. Independent checks
include bounded chemical reference labels, reflected 3D conformers, pinned
Gasteiger values and real OpenMM alanine template charges, alongside native
parity. All 45 guide blocks and 109 inherited native-context doctests pass;
four course module-39 updates preserve code and outputs. Scoped Ruff, shell
syntax and devguide validation pass. The [provider receipt](https://github.com/uibcdf/molsysmt/blob/63600396584f78aef05500cd13a1c5fd37b75728/devtools/data/molsysviewer_tools_chemical_readers_receiving_20261027.json)
keeps the prior #499 receiving and earlier source CI separate.

Native uibcdf/molsysmt#503 remains open: CIP plain-reference author lists share
mutable canonical metadata, and edits can pollute later bibliography/attribution.
This is independently reproduced without Viewer and explicitly documented; the
addon adds no deepcopy. Numeric and scalar-metadata independence does not qualify
every nested reference. No predictive-accuracy, docking-readiness or installed
compatibility certificate is inferred.

Hosted smoke
[40580219002](https://github.com/uibcdf/molsysmt/actions/runs/40580219002)
ends officially failure, exit 126: the new consumer module was a standalone
shell command rather than a pytest argument. It completed 2,963 native passes /
nine optional Ackredit skips and 1,845 earlier consumer passes / three optional
skips, but omitted the 69 new consumer cases. Those partial successes do not
qualify the workflow or the omitted module. Its five other source controls pass;
the intentionally cancelled automatic counterpart remains non-pass. The command
repair and full-list guard are received in the next phase, without weakening tests.
This is not a candidate freeze; both 1.0 publications remain paused.


### Complete physchem and initial build tools — 2026-10-27

Provider `511fafb54708f34d55ca311c1a4fec0787210efd` completes all 34 reviewed
physchem function paths and introduces three build diagnostics. Whole indexed
water and bounded metal/ligand recognition return participants, not observations
or assigned bonds. Template assessment keeps explicit provenance, source/template
maps and context policies. Application and aromatic normalization return
independent native systems/reports and never adopt results into view.molsys.
Invalidation/history affects the returned copy. The peptide-template factory
keeps its explicit sequence/terminal/link inputs and can run before a system is
loaded, producing no coordinates or inferred stereochemistry. Forty directed
consumer cases pass, preserving native parameters, digestion and result contracts.

The build namespace exposes get_residue_chemical_coverage,
get_covalent_bond_candidates and get_peptide_bond_candidates, 3/30 native exports.
Eighteen directed cases pass with real demos, independent alanine edges and
positive 181L C/N geometry/units. Native atom/group selection axes and explicit
single-structure requirements remain intact. The legacy pentalanine demo has
atom-chain indices -1 and remains without peptide candidates; no chain is inferred.
The metadata absence is observed, but its origin is not established.

The initial eleven-scope provider audit records 108 exposed of 231 inspected
public paths. The final fourteen-scope audit adds attribute/supported metadata
and legacy molecular_dynamics declarations: 108 of 244 paths are exposed, 136
unexposed, including two explicit unimplemented native MD stubs. Callable
supported.syntaxes compatibility is retained despite import-order differences.
These paths include aliases/utilities, not independent scientific algorithms. Native classes, format adapters, configuration, datasets
and third-party bridges are excluded explicitly. The canonical expansion
inventory remains owned by uibcdf/molsysmt#421; the [dated source snapshot](https://github.com/uibcdf/molsysmt/blob/511fafb54708f34d55ca311c1a4fec0787210efd/devtools/data/molsysviewer_tools_api_inventory_20261027.json)
records every inspected signature, input kind, exposed route and missing path.
Complete topology/structure/PBC/physchem exposure does not finish the whole addon.

The one frozen 4,283-case applicable regression records 4,282 passes and one
source-file allowlist failure: _build.py was not yet admitted by the packaging
contract. The file is admitted without weakening the guard. All 32 focused
source/wheel/sdist/command/inventory controls then pass. No full regression
rerun is inferred. A subsequent help-only clarification passes all 115 selected
signature/help cases. All 49 guide blocks / 155 inherited native-context examples
pass; five course Markdown updates preserve code and outputs. Ruff, shell syntax
and devguide validation pass. The [receiving receipt](https://github.com/uibcdf/molsysmt/blob/511fafb54708f34d55ca311c1a4fec0787210efd/devtools/data/molsysviewer_tools_complete_physchem_build_receiving_20261027.json)
retains the initial failed run, later corrections, source/backend hashes and scope.

The CI command now includes every addon test module in one pytest invocation.
An early guard rejects orphan test-file commands and missing modules; real API
inventory and source package guards also run before science. All native/consumer
guards remain, with the finite 25-minute job budget. Five additional source
controls pass. Corrected exact-source smoke
[40585977458](https://github.com/uibcdf/molsysmt/actions/runs/40585977458)
passes on main/511fafb54, including cleanup: nine early controls, 3,365 native
passes / eleven optional Ackredit skips and 1,971 addon passes / four optional
Ackredit skips. All five additional source controls pass. The prior Viewer E2E
40580448080 passes on 196c47b0. Native uibcdf/molsysmt#503 remains open, without
a consumer metadata copy.
Additional CI/data reports have been offered; no new issue approval is assumed.
GUI tasks, broader edits, installed artifacts and both 1.0 publications remain
separate. Python remains the primary expert interface.

Follow-up 4e544cb12 expands only developer auditing/records, with no scientific
package/runtime binding changes from the qualified producer. Nine focused
command/inventory/package controls, Ruff, dependency and devguide checks pass.
The CI marker suppresses redundant scientific reruns for this bounded follow-up;
it neither relabels it as an exact scientific-head rerun nor clears whole-suite
debt. The [final inventory](https://github.com/uibcdf/molsysmt/blob/4e544cb12dd6bb7738da651827f3b69fa5847a9c/devtools/data/molsysviewer_tools_full_api_inventory_20261027.json)
and [CI closeout](https://github.com/uibcdf/molsysmt/blob/4e544cb12dd6bb7738da651827f3b69fa5847a9c/devtools/data/molsysviewer_tools_complete_api_ci_closeout_20261027.json)
retain the original 231-path snapshot, expanded callable/stub classification,
actual source identities and unsuccessful evidence. Do not add nonfunctional
wrappers for native MD placeholders merely to claim complete exposure.


## Accepted requirements

1. **Expert Python API:** mirror public MolSysMT module/function paths through
   `view.addons.molsysmt`, with broad scientific coverage. The maintainer
   explicitly confirmed the existing plural `addons` namespace.
2. **Bound primary system:** the primary molecular system is the actual current
   `view.molsys`; users do not supply it to every call. Resolve it at call time,
   including after loading/replacing the system. Preserve necessary additional
   systems, references, file inputs and scientific parameters.
3. **Thin scientific wrappers:** delegate to the real public MolSysMT functions.
   Preserve scientific names, choices, defaults, units, selectors, optional
   engines, native return values and exceptions unless an explicitly reviewed
   view-integration requirement justifies a documented difference. Additional
   integration arguments can control view behavior; they must not silently
   redefine the science.
4. **Task-oriented graphical interface:** design the add-on panels for users who
   may know neither Python nor MolSysMT. GUI organization is independent of the
   expert module hierarchy. Every graphical operation uses the same public
   scientific/add-on APIs and qualified Viewer integration.

Completeness means covering the scientific toolbox, not implementing only the
few methods needed by the first panels. Delivery can be phased, but every public
tool in the selected provider baseline must be accounted for. A deliberate
exception needs a concrete reason; experimental status alone is not an exclusion.

## Ownership and recovery of earlier work

MolSysMT owns the integration package, scientific delegation, expert facade,
panel adapters and its tests/documentation. Viewer owns add-on registration,
scene reconciliation, transport, generic pending-synchronization facilities
where required and the existing scene domains. The implementation can be done
by this development effort in both repositories under the maintainer's direction.
Keep MolSysMT's ordinary import/use independent of Viewer or a browser.

Implementation tracking is now open: uibcdf/molsysmt#421 owns the provider
addon and source ledger; uibcdf/molsysviewer#264 owns host and molecular-edit
receiving. The [technical receiving draft](molsysmt_addon_receiving_contract.md)
specifies the integration controls/state model and acceptance cases.
The first read-tool source implementation is tracked in these records; the
synchronization controls are implemented by the subsequent retained-axis receiver,
not by that initial read delivery.
See [its bounded source receipt](molsysmt_addon_read_receiving_20261022.json)
for executed reads, lifecycle/packaging scope and the retained #263 core failure.

Provider source was inspected at `35a9fc4919485dd0da987134cb5ec9a867d77916`
and Viewer at `697649d82419116d93715d37245e1e279b6e7e5c`. The previous integration
was removed by provider `dfdb31489c3a7dce921fa7b1df9e3fcd24c1f4f6`
(uibcdf/molsysmt#354, coordinated with uibcdf/molsysviewer#186).
Historical facade/adapters were inspected at provider `41d42449e` to identify
reusable mechanisms and limitations. Its public basic facade had four edit
methods; `structure` was an empty namespace and `show` combined calculations
with scene creation. That is not the complete scientific mirror required now.
Old validation counts do not qualify the new contract or current hosts.

The existing [169-export / 77-group inventory](studio_molsysmt_operation_inventory.md)
is a fixed earlier scientific source snapshot, not the complete current API or
an approved panel layout. Refresh coverage against an explicitly selected
provider commit before implementation. Reuse public scientific tools and current
Viewer owners; do not restore removed visibility APIs, private runtime aliases
or old compute-and-render routes by reverting the retirement commit wholesale.

## Expert API mapping

| Provider path / role | Proposed bound interface / rule |
| --- | --- |
| `msm.basic.remove(molecular_system, ...)` | `view.addons.molsysmt.basic.remove(...)`; primary system is implicit. |
| `msm.basic.get`, `select`, `set`, `extract`, `convert`, etc. | Same scientific names and options after binding the primary input. `basic.extract` returns the provider result; `view.extract` separately returns a View. |
| `msm.structure.*`, `topology.*`, `pbc.*`, `physchem.*`, `build.*` | Mirror the actual public module/function hierarchy, not a reduced GUI facade. |
| `msm.interactions.<family>.<function>` | Preserve scientific return/output choices. Calculation alone does not automatically attach, display or recalculate an analysis. Native `view.interactions` keeps its visual integration role. |
| `msm.molecular_mechanics.*` | Account for the full public surface with actual engine/parameterization limits; do not imply a stable or available optional engine. |
| An additional source/reference system | Keep the corresponding explicit input, such as `from_molecular_system` or `reference_molecular_system`. |
| A collection operation, e.g. `basic.merge(molecular_systems, ...)` | Review binding and ordered auxiliary systems individually. Specify per-source selections/order; do not guess that every first argument is a single target. |
| File readers, factories, classes, constants or configuration with no primary system slot | Preserve their meaningful public use or document the explicit exception. Never inject a MolSys into a filename/constructor/configuration argument. No implicit global configuration changes. |
| Provider root aliases | Keep alias behavior consistent where exposed; module paths are the primary expert navigation. Do not create a different algorithm for an alias. |

Start coverage with `basic`, `topology`, `structure`, `pbc`, `physchem`, `build`,
`interactions` families, `molecular_mechanics` and `h5msm`. Account separately for
public support types, aliases and useful additional namespaces. Private provider
modules/registries are not part of the mirror. Optional providers remain lazy.

Use an explicit per-function binding/effect inventory: provider callable,
bound slot, auxiliary inputs, scientific signature/defaults, return type,
read/calculate/edit/file effects, axes/maps, invalidation and update policy.
This metadata can reduce mechanical wrapper duplication; it cannot establish
scientific or mutation correctness by itself. No unrestricted runtime proxy
should silently expose new/unknown provider mutations. New public exports must
be received and classified rather than omitted or automatically certified.

Completion, `dir`, `help`, signatures, docstrings and type information must show
the real expert API. Integration parameters are explicit, preferably keyword-only
and collision-checked against provider parameters. Reject an attempted override
of the implicitly bound primary system. Keep ordinary public digestion and
diagnostic contracts; delegate scientific validation through the provider unless
all inputs have genuinely been normalized under its trusted delegation contract.
`skip_digestion` is not permission to bypass ownership/map/safety invariants.
Preserve provider ownership/aliasing contracts explicitly; a read wrapper must
not silently copy the complete system or trajectory. Uncoordinated writes
through returned mutable data remain outside automatic scene synchronization.

## Scientific edits and visual synchronization — accepted policy

The maintainer accepted the following distinction after reviewing this plan:
scientific mutation, adoption of an independent result and visual synchronization
are separate operations.

- Preserve provider mutation semantics, including the native `in_place` default
  and native return value. An independent output is returned without replacing
  `view.molsys`; an in-place operation edits the actual bound system. A native
  `None` return remains `None` on successful completion.
- Synchronize the view by default after an admitted edit of its bound system.
  The planned keyword-only `update_view=True` controls synchronization, not
  whether the scientific edit happens. Check parameter collisions per function.
  It does not turn an independent output into an adopted result.
- `update_view=False` leaves a declared pending synchronization state. Admit
  this option only where the operation and final reconciliation are qualified;
  reject unsupported deferral before starting the scientific operation.
- Read/calculation wrappers do not redraw, attach results or create scene
  objects merely because their outputs could be visualized. Classify actual
  effects, including provider caches or named-analysis writes, individually.

Do not introduce a second general candidate-preparation framework in this
implementation. Native operations producing independent systems already serve
that role. Incorporation is explicit through the qualified Viewer adoption/load
boundary, with its ownership and scene-transfer policies. A GUI adapter chooses
the native arguments required by its declared action; it must not accidentally
perform a copy-only calculation when the user asked to edit the displayed system.

### Reconciliation by effect

Complete this matrix with actual provider functions, before-state metadata,
authoritative maps and receiving guards before admitting each family:

| Effect | Required reconciliation contract |
| --- | --- |
| Attributes without identity/axis changes | Preserve identities; update affected labels/styles/data and retain scientifically unaffected results. Attribute names alone do not establish scientific independence. |
| Coordinates or box | Update affected geometry, frame/state scope and cell display; retain provider invalidation and invalidate dependent results as required. |
| Atom addition/removal/reordering | Authoritative old-to-new correspondence, treatment of new/deleted atoms, source accounting and remapping of regions, selections and anchored objects. |
| Structure addition/removal/reordering/repetition | Explicit correspondence and occurrence policy, current frame/navigation, source maps, evaluated coverage and all structure-bound objects/results. Counts do not prove identity. |

`apply_system_edit` accepts an atom map and an explicit new-to-old
`structure_index_map` for retained structures, including subsets, reordering and
repetition. Without that map, equal structure counts still declare unchanged
structure order. New/unknown structure origins are not admitted by this first
map contract. It conservatively invalidates interaction coverage by default
and clears scene history. This boundary alone does not certify arbitrary
scientific edits, pending synchronization or recovery after a failed rebuild.
Receive required core extensions separately, reusing existing extraction/remap
mechanisms with reviewed live-edit policies. Qualify same-object edits and
independent adoption separately. Unknown correspondence needs an explicit safe
policy, never guessed identity or silent preservation of stale references.

Do not replace complete scenes through `load(mode='replace')` after every edit.
Reuse/extend the qualified reconciliation owner, retaining source accounting,
representations and navigation where correspondence permits. Do not clear all
analysis coverage simply because an attribute changed; preservation also needs
scientific justification, not an unchecked `preserve` flag.

### Pending state and failures

Before a destructive operation, retain the metadata needed for its admitted
mapping contract. Deferred sequences compose maps from the last synchronized
scene to the current system. Pending state is inspectable in Python and visible
in the GUI. Prevent picks, selections and other actions from treating old
geometry indices as current; camera-only navigation can remain available where
safe. Reject an incompatible next edit before execution rather than losing the
ability to reconcile. A public headless reconciliation route must finish an
admitted deferred sequence; its exact API is specified with the core receiving
contract, not implemented as a private GUI-only button.

Distinguish scientific rejection/no-op, completed science, possibly partial
scientific writes and failed or pending display synchronization. A synchronization
failure after scientific success must identify that fact, retain the completed
operation's native result where one exists, and expose recovery status without
changing ordinary successful return types. Specify the diagnostic/result-access
contract before implementing this path. A retry of synchronization must not
repeat the scientific operation. Never claim rollback after a partial write
without evidence; conservatively mark uncertain state and require reconciliation
or explicit recovery. Transport disconnection does not undo completed science.

### History, recovery and resources

Scene history, molecular recovery and synchronization are distinct. Follow the
existing history boundary: do not retain scene Undo entries that refer to a
previous molecular identity. Molecular Undo is not a prerequisite for this
addon, and no rollback guarantee is added by the wrapper control flag. Optional
recovery needs explicit pre-edit retention, measured memory/copy costs, owners
and lifetimes. Do not copy a whole trajectory on every call or build a universal
transaction/observer framework to support ordinary edits. Direct external
MolSysMT/raw-array calls acquire no automatic observation through this addon.

## Bound API lifetime

A cached facade or module, such as `tools = view.addons.molsysmt`, resolves the
current system at the start of every call, including after `view.load(...)`.
One operation captures one target and its integration revision; it must not
switch systems halfway through calculation. An operation that finishes after
replacement cannot silently adopt/attach its result to the replacement system.
Define supported serialization or stale-completion rejection in the execution
adapter, without promising observation of arbitrary external writes.

Disabling/hiding graphical tools is distinct from using the installed expert
Python API: panel activation is not a prerequisite for a headless call. Release
GUI resources without deleting completed scientific results or invalidating a
usable bound facade. Closing the owning view makes bound operations fail with
an actionable diagnostic. Explicit addon unregistration and incompatible-package
replacement need a separately defined stale-handle policy. Qualify these states
through the host lifecycle rather than assuming current namespace caching is
sufficient.

## Coverage and completion

Freeze a provider commit and classify every public tool in its inventory as
implemented, conditional on a named engine/prerequisite, pending adaptation, or
excluded with a concrete justification. Record aliases/support types separately;
show source, binding, defaults/returns, effects, maps and parity evidence for
each entry. An exposed callable is not qualified merely because introspection
finds it. Pending adaptations remain visible and cannot count as completed
coverage. New provider exports require explicit receiving.

Broad expert coverage does not require a GUI form for every function. Select
graphical operations for understandable tasks over the same expert API. Each
GUI action must declare whether it changes the bound system, returns an
independent result, writes a file or creates a visual object, with its required
method, selection, structures, references and units.

### Worked contracts to qualify

These are acceptance examples for the planned facade, not currently executable
addon documentation. Supply actual arguments and real demo fixtures in the
receiving tests; preserve provider validation and units.

| Planned call / action | Expected behavior |
| --- | --- |
| `tools.basic.get(...)` | Read the current bound system, return the native result and preserve native ownership/aliasing; no scene update or trajectory copy added by the wrapper. |
| `tools.basic.remove(selection=..., in_place=False)` | Return the independent native result; keep the view's system and scene unchanged. This also exercises the inspected provider's default `in_place=False`. |
| `tools.basic.remove(selection=..., in_place=True)` | Edit the bound system, reconcile admitted atom correspondence by default and retain the native return. Preflight rejects unsupported integration requirements before mutation. |
| `tools.basic.extract(selection=..., structure_indices=[2, 0])` | Return the native extraction with requested structure order; do not replace the view or return a View. `view.extract(...)` remains the separate View-producing operation. |
| `tools.basic.set(..., coordinates=..., structure_indices=[2, 0])` | Apply the native coordinate setter, synchronize the affected geometry and respect scientific invalidation at the actual edited scope. Untouched frame identities remain intact. |
| `tools.basic.remove(structure_indices=[1], in_place=True)` | Require an admitted structure-removal mapping policy; remap navigation and structure-bound state. Do not route blindly through the current atom-map-only boundary. |
| Two admitted edits with `update_view=False`, followed by reconciliation | Compose correspondence, expose pending state and prevent stale-index actions; final synchronization reflects both edits without executing either scientific operation again. |

## Graphical interface

Use a clear MolSysMT tools workspace in Studio/Add-ons. Titles and action labels
describe user tasks: inspecting a system, removing chosen atoms, preparing
chemistry, transforming coordinates, comparing structures or saving results.
These are candidate task groups, not final tabs. The user should not need to
know that a function lives in `basic` or `physchem` to find it. Preserve calm
navigation, persistent drafts, keyboard access and both popup lifecycles.

Reuse active/saved/query/source/region selections and readable molecular
categories, with optional expressions/indices. Present meaningful method,
structure/state/reference and unit choices. Optional shortcuts prefill the same
general editor; water removal is a selection, not a separate removal algorithm.
Keep effect review appropriate to destructive GUI actions without imposing
interactive confirmation on expert Python calls.

A GUI adapter may deliberately supply arguments such as `in_place` according to
the explicit action, while the expert wrapper preserves the provider contract.
Show the intended target and scientific effects before execution. Missing
prerequisites/engines, evaluated-empty results, failure and possible partial
writes remain distinguishable. Expensive operations need qualified execution,
progress and only those cancellation guarantees actually supported by the engine.

Core Interactions, Measures, Shapes, selections, colors and plots remain shared
visual owners. Do not revive a parallel `show`/`overlays` scientific API merely
because the old add-on had one. Native visual conveniences can use the same
scientific tools; general add-on calculations retain their native results.
Attach/persist/display results through explicit owning operations where requested.
Deleting a visual object does not delete its underlying scientific result.

## Documentation ownership

Follow [the documentation ownership rule](core_and_addon_boundary.md#add-on-documentation-and-catalogue-ownership).
MolSysMT owns the complete reference for `view.addons.molsysmt`, alongside its
ordinary scientific API documentation: what the addon offers, expert API,
graphical use, scientific prerequisites, method/engine limits, examples and
migration notes. Viewer owns general addon management, the creation guide and
the catalogue with the third-party inclusion-request route. Do not duplicate the
complete provider reference in Viewer.

Viewer tutorials may demonstrate addons in a complete visualization workflow;
link provider parameter/method documentation instead of copying signatures and
scientific definitions. Cross-link both sites so users can move from the Viewer
catalog to the addon guide and back to host setup. Keep tested examples and
compatibility statements tied to their qualified source/package versions;
planned API examples remain explicitly marked until implemented. Documentation
ownership does not require a particular URL or separate hosting site.

## Implementation sequence and acceptance

1. **Freeze contracts and coverage.** Apply the accepted edit/update policy,
   map the selected provider exports and complete the effect matrix. Specify
   the pending-state/resynchronization API, completed-result access after sync
   failure, lifecycle and authoritative maps/outcomes before mutating wrappers.
   Create fresh provider/consumer implementation issues before source changes;
   keep the withdrawn general observer request uibcdf/molsysmt#413 separate.
   Tracking is filed as uibcdf/molsysmt#421 and uibcdf/molsysviewer#264. The first
   source ledger covers all 267 tracked-scope exports at provider `fe5036c1`;
   per-function effect qualification and untracked-namespace disposition remain
   pending. Counts include aliases and support objects, not 267 algorithms.
   The 2026-10-23 name-only refresh at provider `2d5fbb7d5` finds 271 exports
   across the same 21 scopes. Four newly added paths remain pending adaptation;
   this does not refresh every signature/effect in the original ledger.
2. **Restore qualified platform integration.** Reintroduce the integration
   package/spec, entry point, state factory and lifecycle in MolSysMT; qualify
   an explicit compatibility route in Viewer. Both current repositories guard
   legacy absence/refusal, including wheel/sdist/installed checks: update those
   guards to admit the new compatible integration without silently accepting
   unsupported old packages. Select actual version/capability floors after
   receiving; introducing a new magic marker or version guess is not validation.
   A failed state factory must produce actionable diagnostics rather than an
   apparently valid but empty expert namespace. Receive this behavior through
   the owning platform contract and track any required generic host fix.
3. **Implement the expert API first.** Build the bound namespace and common
   delegation/validation layer, then read/calculation tools and admitted edit
   families. Complete broad namespace coverage before calling the API complete.
   Keep no separate authoritative molecular system in add-on state; retained
   explicit candidates/recovery versions have declared owners and lifetimes.
4. **Qualify edits and lifecycle.** Begin with worked contracts for `get`,
   `remove`, `extract`, coordinate changes and structure removal. Real bundled
   systems: return/default parity,
   units and nonconsecutive structures, auxiliary references, no-op/rejection,
   partial writes, maps, result applicability, pending update and resync,
   independent copies, load replacement, cached handles, two views, GUI
   disable/close and stale completions. Fault paths distinguish science from
   display failures and demonstrate recovery without repeating the edit.
5. **Design and implement the GUI over that API.** Review task groups and forms
   before building panels. Demonstrate the same resolved scientific operation
   headlessly and through live widgets; retain view-specific integration effects
   explicitly. Verify actual Jupyter and canvas/panel popups, including real
   click-to-Python execution, not only a static panel screenshot.
6. **Document and qualify distribution.** Follow the documentation ownership
   above, with distinct expert and graphical audiences and working cross-links.
   Update provider course/examples and Viewer extension guidance, then qualify
   exact sources and installed packages, lazy
   imports and optional dependencies. Freeze tags/builds only under the separate
   release process; both 1.0 publications remain paused.

Use real provider/demo results for behavioral tests. Signature/export counts
are coverage checks, not substitutes for executed scientific parity. GUI
examples need not expose every expert argument, but cannot weaken the Python
API or hide decisions that change scientific interpretation. This document
plans the new add-on; it does not reintroduce the removed Studio expansion plan.


### Next expert API families

The reviewed physchem surface is fully exposed at 34 paths, and build is now at
11/30. The owning inventory under uibcdf/molsysmt#421 records the remaining
functional routes: basic 7, build 19, molecular_mechanics 6, canonical interactions
4, element helpers 57, H5MSM utilities 7, historical hbonds aliases 4, attribute
helpers 7, supported-capability reports 4 and legacy MD declarations 2.
These 117 unexposed paths include aliases/utilities and two native always-raise
stubs, not 117 independent implemented scientific algorithms. Keep classification and source-versus-qualification clear.

Read-only build audits are received at this baseline. Four nested hydrogen-bond
recognition/direction paths, four HB/sulfur detectors and three chemical contact
families are received; continue the four remaining canonical families, then
independent/basic map utilities. Receive molecular-mechanics diagnostics and
energies/forces with explicit providers and units. In-place minimization,
preparation and topology-changing basic/build operations need their own mapping,
reconciliation, invalidation and recovery contracts. Element/file/attribute/supported utilities keep
explicit inputs where no primary exists; collections and to/from-system targets
must not be guessed. Decide historical aliases and the basic.view bridge
deliberately. Class/adaptor/configuration APIs remain outside the functional
mirror inventory. Graphical tasks cannot narrow the expert API or advertise
unreceived operations. Native #503 remains a separate qualification limit.


### Eleven build audits received in source — 2026-10-27

Provider 11e7ab7f0 exposes all eleven reviewed read-only build audits; the
[receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#eleven-build-audits-received-in-source--2026-10-27)
retains the exact scope, 62 directed / 4,414 regression passes, executable
guidance and the completed fixed-ref hosted gate. Native uibcdf/molsysmt#504 tracks multi-structure
solvation, independently of CIP metadata #503. Keep group/atom/selected-subsystem
axes, explicit sequence/structure scopes and native outcomes visible. There is
no molecular repair or automatic source/scene publication in these readers.
Next: raw canonical interactions, followed by independent utilities and mechanics.


### Expert hydrogen-bond recognition and directions received — 2026-10-27

Provider b50edcc52 adds the four explicitly bound interactions.hbonds role/site/
direction methods. The [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#build-source-ci-completed-and-hydrogen-bond-sites-received--2026-10-27)
retains exact source identity, 44 directed / 4,536 regression passes, 52 guide
blocks / 184 inherited examples and current hosted gates. Inventoried exposure
is 120/244, canonical interactions 4/15. Native uibcdf/molsysmt#506, uibcdf/molsysmt#507,
uibcdf/molsysmt#508 and uibcdf/molsysmt#509 retain
rule ownership/language, empty graph and frame-validation limitations. No hidden
preparation or scene attachment occurs. Continue native raw detectors and their
own scientific/return contracts; do not substitute core visualization for the
expert mirror. Source receiving does not establish installed compatibility.


### Expert hydrogen-bond and disulfide detectors received — 2026-10-27

Provider 8d129124e adds three explicit hydrogen-bond detectors and the canonical
sulfur-candidate detector, preserving native tuple/sparse defaults and all
scientific parameters. Source exposure is 124/244 inspected paths, interactions
8/15. The [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#expert-hydrogen-bond-and-disulfide-detectors-received--2026-10-27)
retains 65 directed cases, 4,710 frozen regression passes, 54 guide blocks / 214
inherited examples and exact-source hosted status. Native uibcdf/molsysmt#511
tracks classic supplied-donor shapes; no consumer repair is added. There is no
automatic named storage, molecular edit or scene effect. The cancelled earlier
recognition smoke remains distinct from the new pending campaign. Next: the
seven remaining raw families, followed by independent utilities and mechanics.


### Ionic, hydrophobic and halogen families received — 2026-10-27

Provider 24ee46486fec5c19da847a61229f553f5200921e adds three explicit native family methods without
preparation, storage, edits or scene effects. The [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#ionic-hydrophobic-and-halogen-detector-families-received--2026-10-27)
retains 76 directed / 4,915 joint regression passes, 32 package/command guards,
57 guide blocks / 241 inherited examples and the exact-source hosted status.
Exposure is 127/244 inspected paths, canonical interactions 11/15. Ionic's
required cutoff and compound centers, hydrophobic pair identity and four-role
halogen geometry stay native. Legacy incomplete chemistry rejects explicitly.
Prior 8d129124e source CI completes with its optional-provider skips preserved;
five new source controls pass; scientific smoke 40618125703 is in progress.
Next: metal coordination, pi-pi,
cation-pi and water bridges; native #511 does not require a facade workaround.

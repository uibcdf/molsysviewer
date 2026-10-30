# Studio / MolSysMT operation inventory — proposed integration mapping

**Placement revision — 2026-10-22:** the approved
[core/add-on boundary](core_and_addon_boundary.md) supersedes this inventory's
earlier native-Studio panel placements. Keep the fixed scientific source
snapshot and operation counts; reclassify general molecular tools into the
proposed add-on interface, with qualified visual conveniences in scene domains.
No latest-provider behavior is inferred from this historical source snapshot.

**Status: proposed — source inventory completed on 2026-10-22; workflow
contracts and implementation remain pending.** This inventory was prepared
for the now-withdrawn native-Studio expansion. It remains a capability/source
reference under the [accepted product boundary](core_and_addon_boundary.md),
not an approved implementation or panel-expansion plan.
Python remains the primary API. General operations, explicit selections and
parameters organize integration; panel names are presentation, not new Python
namespaces or one wrapper per button. Related rows and composed acceptance
scenarios do not prescribe canned workflows.

The JSON source snapshot retains the names inspected at its recorded provider
commit. For the later independent-domain cutover, the nine chemical graph tools
move from `molsysmt.topology` to `molsysmt.chemical_states`; sequence tools remain
under topology. Use the [receiving guide](chemical_domain_receiving.md) for
current development-source routes. This migration note does not rewrite the
historical snapshot or certify a published feature floor.

## Evidence and limits

Inspected MolSysMT scientific/export source at
`b501bfd69ad3e692ceeb865ebcdbd0cd1deed173`, plus Viewer baseline
`d96b073f` with the current planning-only working changes. The companion
[source snapshot](studio_molsysmt_operation_inventory.json) records every
export in the reviewed tool namespaces, signatures, observed defaults, return
documentation, provider stability, source paths/hashes and workflow IDs. It is
source inspection, not executed scientific, installed-package or browser
qualification. Public compatibility remains separate: Viewer currently declares
`molsysmt>=0.23.0`; no minimum version is raised by this inventory.
The inspected scientific files and stability inventory match the provider
commit; concurrent edits to unrelated benchmark tooling were excluded.

The source pass accounts for **169 exports in 77 operation groups**, including
classes/rule data used as support. These are inventory counts, not a promise of
169 controls, 77 new APIs or already completed workflows.
The existing `workflows`/workflow-ID keys in the JSON snapshot identify related
operation groups; they are retained to preserve references, not as a public
workflow catalogue.

| Reviewed scope | Exports |
| --- | ---: |
| basic | 27 |
| topology | 11 |
| structure | 28 |
| pbc | 13 |
| physchem | 30 |
| build | 28 |
| Nine interaction families | 19 |
| h5msm | 7 |
| molecular_mechanics | 6 |

Of these, 162 are functions, three are classes and four are rule data. The
provider marks 68 stable, 95 experimental and six outside its stability
contract. These classifications do not certify Viewer integration.

Coverage is the exports of `basic`, `topology`, `structure`, `pbc`, `physchem`,
`build`, `molecular_mechanics`, `h5msm` and the nine `interactions` families.
Root aliases do not count as additional scientific operations. Native data
classes, builder methods and infrastructure are accounted for below rather
than mistaken for additional task buttons. This does not claim to inventory
every attribute/method of every native class or every third-party adapter.

All useful task rows are assessed for pre-1.0 integration; none is deferred
merely for being experimental. A row marked review is an unresolved integration
contract, not a post-1.0 decision. The provider's per-symbol classifications
come from its stability inventory and are retained in the snapshot; in
particular mechanics is outside its stability contract. A callable export or
default engine does not prove every engine, input form or parameter branch.

## Shared operation contracts

Rows specify the following profiles to avoid repeating the same cross-cutting
rules in every cell. Exact supported selectors, defaults and output definitions
are per-symbol in the snapshot, not inferred from the profile.

| Profile | Scope, output, validity, persistence and recovery |
| --- | --- |
| Q — inspect | Read declared molecular fields or a report, including missing/unknown coverage. Show source/state/frame where applicable. Temporary inspection need not create history; a saved report needs named provenance, validity and a persistence decision. |
| C — calculate | Explicit atom populations, structure/state scope and methods/units. Preserve returned axes, definitions and provenance. Tables/plots/scene overlays are consumers; their native result storage, save/checkpoint route and invalidation rules need design before delivery. No generic universal analysis store is assumed. |
| G — graph | Topological/chemical selections, pairs, graph or correspondence tables. Preserve whole-component context, original indices and state. Geometry changes alone do not automatically invalidate chemistry-only outputs; graph/axis/state changes require verification or recomputation. |
| E — edit | Prepare an independent candidate, review effects, commit through one Python reconciliation owner and record recoverable before/after state. Specify atom/frame maps and affected analyses/scene objects. Existing provider in-place defaults must never mutate the live source before the managed commit. |
| L — load | Source/format/independent-versus-complementary semantics, ordering, box policy and correspondence are explicit. Retain content for recoverable later loads; do not depend on fetching the original again. |
| F — file | Explicit content and atom/structure scope, writer capability, conversion losses and coherent captured revision. Studio remote/local delivery does not restrict Python path output. Runtime Undo and permanent work/session files have different lifetimes. |
| S — support | Reuse the public Python tool inside a user task. No extra panel/control is required for an implementation utility, class or alias. This is organization, not deferral or loss of Python functionality. |

Provider input signatures/defaults are evidence, not proposed Viewer defaults.
Do not silently pass Viewer selections to tools that lack that selector, apply
a single-frame operation to a whole trajectory, infer a chemical state, or
equate returned dimensions with source IDs. Preserve nonconsecutive/repeated
structure semantics where the individual operation supports them.

Selection builders reuse the existing active/query/saved/source/region owners,
with readable categories and optional expression/index inputs. Each operation
uses the provider's actual selection/state/frame contract. A shortcut supplies
visible arguments to the same general tool and cannot add unrequested science.
Private form adapters compose public MolSysMT tools and general Viewer APIs;
private coordination shares the existing reconciliation/history owners.

For new scientific outputs, persistence, compatible scene display, review of
edits, budgets/progress and headless public composition are explicit completion
criteria. A result cannot be called integrated merely because a form invokes
its function. Optional engines remain optional and report actual absence or
failure through the existing dependency/diagnostic owners.

## basic — System, Selections and export

All symbols in this table are under `molsysmt.basic`.

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| B01 | Inspect contents / System Contents | `info`, `get`, `get_attributes`, `has_attribute`, `where_is_attribute`, `get_label` | Q/S | Extend existing hierarchy/context inspection with composition and readable labels. Attribute availability is not proof of chemical completeness; preserve group terminology. |
| B02 | Recognize inputs and composition / loading and Contents | `get_form`, `is_a_molecular_system`, `are_multiple_molecular_systems`, `is_composed_of`, `contains` | Q/S | Reusable preflight and targeted summaries, not six new buttons. Preserve public return/diagnostic contracts. |
| B03 | Select atoms/elements / Selections | `select` | G/S | Existing Viewer selection owners remain canonical. Preserve state, frame, syntax and element-level semantics; active selection and reviewed edit target remain distinct. |
| B04 | Convert/save and review loss / Save & Export | `convert`, `get_conversion_report`, `ConversionIssue`, `ConversionReport` | F/L/S | Add molecular writer workflow; retain structured preflight evidence. Input format support does not imply output support; actual writers and published versions remain to qualify. |
| B05 | Remove atoms or retain an atom selection / System Edit | `remove`, `extract` | E | General operations with reusable active/saved/query, source/region, chain/group, category and index/expression targets; water removal only prefills that selection. Reuse existing extraction and public Viewer integration, qualifying correspondence/recovery instead of adding methods per recipe. The `remove` signature advertises `in_place=True`, but its body ignores the flag (uibcdf/molsysmt#406); ownership/remapping must be qualified. |
| B06 | Combine independent systems / System Load | `add`, `merge` | L/E | Reuse `view.load`; preserve current source regions and first/current-box contracts. `add` has in-place and attribute-intersection policies; review dropped attributes and generated identities. |
| B07 | Append or combine observations / System Load | `append_structures`, `concatenate_structures` | L/E | Reuse current load modes. Compatible atom identity/order, ordered frames, times and attribute policy stay explicit; no automatic alignment or broadcasting. |
| B08 | Work on an independent copy / System workflow or Python tools | `copy` | E/S | Existing Viewer copy tool uses public `msm.copy`. Complete-system independent-edit/revision receiving remains distinct from source copy support and published qualification. |
| B09 | Compare systems or populations / System comparison, placement to validate | `compare` | Q | Provide readable differences only for supported comparison attributes; identify both systems/populations and correspondence rather than assuming equal counts imply identity. |
| B10 | Open a viewer / integration support | `view` | S | Existing provider-to-Viewer entry route; no recursive Studio button that launches the same view without a user task. |
| B11 | Iterate observations / execution support | `Iterator` | S | Supports bounded calculations where the operation actually supports iteration. Not a standalone panel, universal out-of-core guarantee or replacement for preserved structure semantics. |
| B12 | Assign explicit attributes / canonical owning workflows | `set` | E/S | Use through typed operations such as existing coordinate/box assignment; design supported metadata edits by field. No generic raw setter grid or GUI-only mutation path. |

**Linked-edit refinement:** scientific assignment stays in MolSysMT. The
revised target is explicit reconciliation or coordinated integrated-tool
operations under uibcdf/molsysmt#413. General automatic observation is not
required. `view.set_box` references below describe current implementation
to migrate/receive, not a requirement to retain that public wrapper. Independent
outputs and unsupported raw writes have different integration responsibilities;
see the [linked-edit design](linked_molecular_edits_design.md).

## topology — Connectivity, Chemistry and Correspondence

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| T01 | Inspect connectivity / Topology Connectivity | `get_bondgraph`, `get_covalent_paths`, `get_covalent_blocks` | G | Graph/table and source-atom highlighting; removing graph edges for partition analysis does not remove molecular bonds. A NetworkX graph is not itself a persisted scene object. |
| T02 | Inspect rings / Topology Connectivity | `get_rings` | G | Retain selected chemical state, ring definition and connectivity completeness assumptions; a minimum cycle basis is not a list of every possible cycle. |
| T03 | Inspect torsions and rigid fragments / Topology Connectivity | `get_rotatable_bonds`, `get_rigid_fragments`, `get_dihedral_quartets` | G | Preserve classification method, explicit cuts and atom quartets. Deriving a fragment is not rotating it; link to Structure torsion editing. |
| T04 | Find chemical substructures / Topology or Selections shortcut | `get_substructure_matches` | G | SMARTS, graph completeness and match cap are explicit; preserve match populations and source indices. One canonical operation may have selection-entry links. |
| T05 | Compare sequences / Topology Correspondence | `get_sequence_alignment`, `get_sequence_identity` | G | Explicit reference input/selection and Biopython branch qualification; sequence alignment is distinct from coordinate superposition. |
| T06 | Establish atom correspondence / Topology Correspondence | `get_atom_correspondences` | G | Preserve selected and full chemical context, chemical states, anchors/candidate maps and bounded search scope. Mapping persistence and reuse require their source validity contract. |

## structure — Measures and Structure

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| S01 | Measure geometry / Measures | `get_distances`, `get_angles`, `get_dihedral_angles` | C | Existing scene measures and series remain canonical; extend supported batch analysis without replacing anchored measurement semantics. Keep atom endpoints/centers, pairs, PBC and units explicit. |
| S02 | Find closest/farthest distances / Structure Analyze | `get_minimum_distances`, `get_maximum_distances` | C | Preserve two populations, pair/group reduction and returned indices; default PBC differs from ordinary distance calls. |
| S03 | Inspect centers, vectors and planes / Structure Analyze | `get_center`, `get_vectors`, `get_least_squares_plane` | C | Weights, geometric versus mass centers and plane fit definition are explicit. Optional shapes represent results without pretending to be detectors or changing coordinates. |
| S04 | Find neighbors or geometric contacts / Structure Analyze; Selections links | `get_contacts`, `get_neighbors` | C/G | Preserve cutoff/count, pairs, PBC and center modes. A geometric contact matrix is not a typed chemical Interactions result; an adapter needs a separate contract. |
| S05 | Transform molecular coordinates / Structure Transform | `center`, `translate`, `move_away`, `rotate`, `flip` | E | Explicit moving/reference populations, frames, vectors/matrices and units; preserve method-specific scope. Camera center/rotation is separate; reflection can change handedness. |
| S06 | Edit torsions / Structure Transform | `set_dihedral_angles`, `shift_dihedral_angles` | E | Explicit quartets, movable blocks, angular units and frames. Show which atoms move; do not conflate absolute target with angular increment. |
| S07 | Analyze size and fluctuations / Structure Analyze | `get_radius_of_gyration`, `get_rmsf` | C | Rg is per observation; RMSF reduces over a population of structures. Weights and alignment preparation are explicit; no unrequested fitting. |
| S08 | Assign secondary structure / Structure Analyze | `get_secondary_structure` | C | Preserve MDTraj engine, simplified/full labels, group/frame axes and availability. Do not silently replace imported or Mol* visual assignments. |
| S09 | Compare coordinate deviation / Structure Analyze | `get_rmsd`, `get_least_rmsd` | C | Distinguish positional RMSD from optimal-superposition RMSD; identify atom correspondence and reference frame. Calculating fitted RMSD does not apply a coordinate fit. |
| S10 | Superpose systems / Structure Align | `least_rmsd_fit`, `least_rmsd_align` | E | Distinguish fitting and moved populations, explicit reference, optional sequence alignment and engine parameters; commit actual coordinate edits with recovery. |
| S11 | Analyze principal axes or PCA / Structure Analyze | `get_principal_axes`, `principal_component_analysis` | C | Inertia/geometric axes and Cartesian covariance PCA are different. PCA returns eigenvectors/eigenvalues, not trajectory projections; estimate covariance/output size before running. |
| S12 | Align principal axes / Structure Align | `align_principal_axes` | E | Explicit source axes/population, target axes, optional centering and frames; not a camera orientation tool. |
| S13 | Compare chemically equivalent poses / Structure Analyze | `get_symmetry_corrected_rmsd` | C/G | Requires valid chemical correspondences and explicit reference/state. Positional corrected RMSD does not fit, reflect or apply MIC automatically; retain constrained search scope and original producer data. |

## pbc — Structure PBC

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| P01 | Inspect cell / Structure PBC | `has_pbc`, `get_lengths_from_box`, `get_angles_from_box`, `get_lengths_and_angles_from_box`, `get_shape_from_box`, `get_shape_from_angles`, `get_volume_from_box`, `get_volume_from_lengths_and_angles` | Q/C/S | Reuse box inspection with explicit matrix/length/angle/volume units. Distinguish missing cell from zero/invalid cell and preserve structure alignment. |
| P02 | Construct and assign a cell / proposed add-on Structure PBC | `get_box_from_lengths_and_angles`, `get_box_with_shape` | C/E | Construction returns a box; scientific assignment belongs to MolSysMT. Qualify explicit reconciliation/coordinated tool integration (uibcdf/molsysmt#413) before any setter migration. Preserve units, source/structure selection, validation and cell-edge display. |
| P03 | Reimage or unwrap / Structure PBC | `wrap_to_pbc`, `wrap_to_mic`, `unwrap` | E | Keep box origin, MIC origin, compact grouping and structure scope distinct. These edit molecular coordinates; preserve identities and invalidate affected geometry evidence. |

## physchem — Properties, Chemistry and preparation

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| PH01 | Inspect mass and charge / Properties | `get_mass`, `get_charge` | Q/C | State the provider definition: tabulated/pH/force-field charge is not automatically an explicit formal or partial charge. Preserve element aggregation and units. |
| PH02 | Inspect atomic parameters / Properties | `get_atomic_radius`, `get_protor_atom_type`, `get_protor_vdw_radius`, `get_electronegativity` | Q/C | Named radius/type/scale definitions and missing entries are visible; a value lookup does not assign a force field or alter the rendered atomic radii implicitly. |
| PH03 | Compare group reference scales / Properties | `get_polarity`, `get_transmembrane_tendency`, `get_area_buried`, `get_buried_fraction`, `get_hydrophobicity`, `get_surface_area`, `get_volume` | Q/C | These include tabulated amino-acid reference scales, not all coordinate-based observables. In particular volume is Grantham side-chain scale and buried area/fraction are reference tables; labels/units must say so. |
| PH04 | Calculate solvent accessibility / Properties | `get_sasa` | C | Coordinate-based SASA with explicit engine, probe radius, sphere samples, group aggregation and frames. Native occlusion uses the full input system before filtering selected outputs; isolated-component SASA needs an explicit different input. Keep this separate from tabulated surface area. |
| PH05 | Inspect chemically defined sites / Properties; Interactions links | `get_charge_centers`, `get_aromatic_rings`, `get_halogen_bond_sites`, `get_hydrophobic_sites`, `get_metal_coordination_sites`, `get_water_sites` | G | Retain ordered participants, chemical evidence, full-graph context, state and matching limits. A recognized site is not an interaction occurrence. Reuse tools across consumers. |
| PH06 | Analyze aromaticity/stereochemistry / Topology Chemistry | `get_aromaticity`, `get_cip_stereochemistry` | G/C | Separate perception from stored flags; declared stereo versus coordinate-derived CIP and RDKit availability are explicit. Do not silently apply perceived assignments. |
| PH07 | Inspect chemical readiness / Build Inspect, Topology Chemistry link | `get_chemical_readiness`, `get_hydrogen_inventory` | Q/G | Distinguish explicit indexed H, stored virtual H and unassessed chemistry. Readiness assesses fields/coverage, not universal validity; method-specific single-frame limits remain visible. |
| PH08 | Calculate charges and atom types / Properties | `get_partial_charges`, `get_autodock_atom_types` | C/G | Explicit method/typing scheme, state, full-graph admission, optional force field/water model and returned report. Calculating labels/charges is separate from assigning them. |
| PH09 | Assess a declared template / Build Inspect | `assess_chemical_template` | G | Explicit template, exhaustive atom correspondence, provenance and connectivity policy; no identity inferred from equal counts or atom names. |
| PH10 | Apply chemical assignments / Build Repair | `apply_chemical_template`, `normalize_aromatic_bond_orders` | E | Produce independent candidates, retain assignment evidence and invalidate affected chemistry/geometry results. Normalization uses declared aromaticity, not automatic perception. |
| PH11 | Construct peptide chemical template / Build Construct | `get_peptide_chemical_template` | G/S | Explicit group sequence, terminal states and disulfide group pairs. A heavy-atom chemical template is not a completed 3D peptide; link to assessment/application workflows. |

## build — Inspect, Repair and Construct

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| BL01 | Inspect preparation needs / Build Inspect | `get_missing_heavy_atoms`, `get_residue_chemical_coverage`, `get_missing_terminal_cappings`, `get_missing_residues`, `get_missing_bonds`, `get_non_standard_residues`, `has_hydrogens`, `is_solvated` | Q/G | Reports, source groups and proposed fixes. Reference sequence/template availability and original file metadata matter. Solvation is a water-density/box heuristic, not proof of equilibration; provider names containing residue need user-facing group wording where appropriate. |
| BL02 | Review covalent candidates / Build Inspect | `get_covalent_bond_candidates`, `get_peptide_bond_candidates`, `get_disulfide_bonds` | G/C | Distinguish template candidates, backbone distance candidates and S–S candidates. Preserve frames/PBC/evidence; none proves that a covalent bond exists. Disulfide visualization reuses Interactions when appropriate. |
| BL03 | Infer or add connectivity / Build Repair | `infer_covalent_bonds`, `add_missing_bonds` | E | Explicit method/template and distance policies; review proposed bonds. Legacy add may be in-place; protect source and use one chemical-state authority. |
| BL04 | Complete heavy atoms and termini / Build Repair | `add_missing_heavy_atoms`, `add_missing_terminal_cappings` | E | Supported group templates/engines, caps, geometry and attribute retention are explicit. Template files existing on disk do not establish arbitrary group reconstruction support. |
| BL05 | Place H or reconcile protonation / Build Repair | `add_missing_hydrogens`, `reconcile_protonation` | E | Separate pH/template rules from fixed-state RDKit H placement; existing H removal is an explicit reconciliation operation. Honor single-state/frame and attribute-policy limits, engine selection and retained preparation evidence. |
| BL06 | Attach declared terminal atoms / Build Construct | `add_terminal_atoms` | E | Explicit parent mapping, new atom declarations and coordinates; added-atom maps and chemical/preparation history need provider-contract receiving. Not arbitrary de novo ligand generation. |
| BL07 | Resolve alternate locations / Build Repair | `solve_atoms_with_alternate_location` | E | Explicit occupancy/location policy and selected structures, with atom-axis consequences and recovery. Show unavailable source alternate-site information honestly. |
| BL08 | Mutate amino-acid groups / Build Repair | `mutate` | E | Explicit target group indices/names and replacement; native versus PDBFixer reconstruction limits require qualification. Preserve sequence and atom mapping without promising arbitrary chemistry. |
| BL09 | Construct biological assembly / Build Construct | `make_bioassembly` | E/L | Use actual source assembly operators and selected frames. Heterogeneous per-operator chain sets are unsupported in the inspected contract; generated copies/source identities and repeated chain labels require review. |
| BL10 | Build a peptide or water box / Build Construct | `build_peptide`, `make_water_box` | E/L | Sequence input versus declared periodic cell, actual output form and supported models are explicit. Building output does not automatically replace the current system; choose add/replace through the canonical load/edit owner. |
| BL11 | Solvate or remove overlaps / Build Construct or Repair | `solvate`, `remove_overlapping_molecules` | E | Explicit solvent/ions, box/model/clearance, neutrality/count/concentration and engine; overlap removal uses selected populations, one-frame geometry and molecule-level removal. Review generated/deleted atoms before commit. |
| BL12 | Assign charges or atom types / Build Repair | `assign_partial_charges`, `assign_autodock_atom_types` | E | Apply complete validated assignments to a detached system with declared state. Do not turn a partial calculation selection into a partly assigned current system silently. |
| BL13 | Stage explicit molecular construction / Build Construct | `editable` | E/S | Public builder owns atom/group/bond/parent construction; independent staging and build validation precede Viewer commit. The builder is not a drop-in holder for all analyses, mechanics and state/structure links. |

## interactions.hbonds — Interactions and site inspection

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| IH01 | Inspect donor/acceptor rules / Interactions | `get_acceptor_atoms`, `get_donor_atoms`, `acceptor_inclusion_rules`, `acceptor_exclusion_rules`, `donor_inclusion_rules`, `donor_exclusion_rules` | G/S | Legacy rule tools remain Python APIs; expose readable scientific criteria where useful, not mutable global rule editing as an implicit calculation default. |
| IH02 | Inspect H-bond sites and directions / Interactions or Properties link | `get_hbond_sites`, `get_hbond_site_directions` | G/C | Preserve state, recognition method, ideal versus observed geometry, ordered roles, matching limits and PBC. A direction glyph is not proof of a detected bond. |
| IH03 | Calculate H bonds / Interactions | `get_hbonds`, `get_buch_hbonds`, `get_luzard_chandler_hbonds` | C | Existing `view.interactions.hbonds.get_hbonds` and method-specific public routes retain explicit Viewer defaults and provider method/profile identity. Preserve optional legacy output types in Python; Studio consumes typed analyses rather than inventing new tuples. |

## interactions.disulfides — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| ID01 | Detect S–S candidates | `get_disulfide_candidates` | C | Existing family adapter; candidate geometry is distinct from covalent assignment in Build. |

## interactions.ionic — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| II01 | Detect ionic contacts | `get_ionic_interactions` | C | Existing adapter; explicit formal-charge centers and distance threshold, not electrostatic energy or implicit assignment of protonation. |

## interactions.pi_pi — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| IP01 | Detect aromatic ring geometries | `get_pi_pi_interactions` | C | Existing adapter; retain profile, ring/plane definition, geometry thresholds, planarity and compound participants. |

## interactions.cation_pi — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| IC01 | Detect cation–ring geometries | `get_cation_pi_interactions` | C | Existing adapter; formal cation identity, declared aromatic rings, profile and distance/angle/offset criteria remain explicit. |

## interactions.halogen_bonds — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| IX01 | Detect halogen-bond geometries | `get_halogen_bonds` | C | Existing adapter; preserve donor/halogen/acceptor/reference roles and both angular criteria, not just a connecting line. |

## interactions.hydrophobic — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| IN01 | Detect hydrophobic proximity | `get_hydrophobic_interactions` | C | Existing adapter; chemical site recognition plus distance observations, not hydrophobic free energy. |

## interactions.metal_coordination — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| IM01 | Detect metal–ligand candidates | `get_metal_coordination` | C | Existing adapter; geometric candidates retain actual chemical recognition limits and do not change covalent topology. |

## interactions.water_bridges — Interactions

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| IW01 | Detect water-mediated H bonds | `get_water_bridges` | C | Existing adapter; preserve order, underlying H-bond method/profile, all leg participants, coverage and images. |

All nine families reuse the existing named-analysis and visual-set owners.
Recheck calculation/display scopes, native query modes, sparse occurrences,
evaluated-empty coverage, paging and images under the
[consumer contract](interactions_compatibility_contract.md). Existing family
adapters do not qualify every new provider method/profile or published version.
This inventory does not replace established Viewer API/form defaults with
provider defaults; both routes require their own explicit compatibility review.

## h5msm — loading, molecular output and analyses

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| H501 | Read molecular domains or analyses | `read`, `read_layers` | L/F | Reuse native loading and analysis import. Partial domains do not imply renderable coordinates or authenticated source identity. |
| H502 | Save molecular domains or analyses | `write`, `write_layers` | F | Recommended molecular format and existing Interactions save owner. Preserve supported states/structures/analyses and explicit identity links; mechanics has no 0.5 layer. |
| H503 | Append file structures / file-management task, placement to review | `append_structures` | F/E | Mutates an external file, not just the view. Needs separate overwrite/recovery policy; ordinary molecular Undo cannot silently claim to reverse external filesystem effects. No deferral is declared here. |
| H504 | Migrate legacy files / loading or save conversion | `migrate_04_to_05`, `migrate_to_05` | F/S | Explicit migration output and loss/compatibility report; do not rewrite caller files as a side effect of opening them. Reuse one operation for equivalent migration aliases. |

## molecular_mechanics — explicit integration review

| ID | User task / placement | Provider symbols | Profile | Integration disposition and specific contract |
| --- | --- | --- | --- | --- |
| MM01 | Inspect energies / placement to validate | `get_potential_energy`, `get_non_bonded_potential_energy` | C | OpenMM parameterization, solvent/force-field/platform and selection semantics need a complete workflow. Preserve energy definition and units; coordinates alone are insufficient. |
| MM02 | Inspect forces and degrees of freedom / placement to validate | `get_forces`, `get_degrees_of_freedom` | C | Explicit parameterization, atom/structure support, force/vector units and constraints. Provider branch support must be qualified, not inferred from a generic signature. |
| MM03 | Choose engine force-field setup / setup support | `get_engine_forcefield` | S | Engine-specific force-field representation, not a portable scientific result or automatic complete parameterization. |
| MM04 | Minimize energy / preparation workflow, placement to validate | `potential_energy_minimization` | E | Explicit engine/method/platform, starting parameterized state, retained outcome and recoverable coordinate edit. No automatic minimization after another operation. |

These six exports remain outside the provider stability contract. Assess actual
functionality, complete parameterization and engine qualification before an
inclusion/deferral decision. H5MSM 0.5 rejects nonempty mechanics; session,
checkpoint and revision persistence need a supported route. The classification
is a concrete review requirement, not a blanket exclusion from Viewer 1.0.

## Maintaining the inspected snapshot

Capture exports from the reviewed modules' initialization files (and H5MSM's
explicit export list), resolve their defining source, and extract signatures,
default expressions and return documentation without importing the provider.
Join its per-symbol stability inventory and assign each export to exactly one
workflow row. The snapshot records the source commit and SHA-256 of inspected
files; verify they match that committed scientific source even when unrelated
work is present in a sibling checkout. Validate the symbol/row sets and source
hashes together after a refresh. Do not silently refresh to moving provider
main or turn a new source snapshot into a published capability claim.

## Native classes, builder methods and remaining namespaces

`Interactions`/`InteractionsDict`, `ChemicalStates`/`ChemicalStatesDict`,
`MolSysDict`/`TopologyDict`, native molecular/structure objects and
`MolSysBuilder` carry data or staging contracts. Use public queries and edits;
do not expose their raw tables as an unrestricted Studio editor. A Chemistry
view must show declared reference/structure-state association without pretending
that changing displayed frames necessarily chooses another chemical state.

The public builder actions reviewed for BL13 are `add_atom`, `add_group`,
`add_bond`, `remove_bonds`, `add_chain`, `assign_groups_to_new_chain`,
`add_molecule`, `add_entity`, `set_coordinates`, `set_box`, `set_time`,
`set_structure_id`, `build` and `copy`. These are reusable Python tools, not a
requirement for fourteen buttons. Define bounded construction tasks, explicit
parent/atom maps and staging validation. The inspected builder copy contract
does not alone qualify complete MolSys history or provider package receiving.

The historical `hbonds` namespace/root aliases are compatibility routes, not
additional families. `configure`, units, `supported`, `form`, `attribute`,
`element`, native query machinery and optional-engine declarations support the
owning workflows or Settings. Do not silently alter application-wide provider
configuration to accommodate a Studio form. Molecular dynamics is not exposed
in the reviewed root registry; no simulation panel is promised from directory
presence alone. Optional third-party adapters and domain libraries keep their
own scientific contracts and addon boundaries.

## Remaining design work after this inventory

The [six foundation workflow contracts](studio_foundation_workflow_contracts.md)
develop removal, preparation, correspondence/alignment, PBC, property series and
Interactions from these rows, including source-level ownership and context
questions found during deeper inspection. They remain proposed, not qualified.

The task families are now accounted for; individual public orchestration names,
result containers/persistence for new calculations, source/reference input UI,
capability-aware controls and headless/GUI parity remain design work. Determine
engine and writer routes from actual published artifacts before integration
claims. In particular review external-file editing (H503), full mechanics
workflows (MM01–MM04), single-state/frame preparation and source metadata that
may not survive conversion. These are named questions, not silent exclusions.

Next design the recovery/transaction foundation and its operation contracts,
using this inventory to include atom changes, geometry changes, state changes,
named results, later loads and external side effects. Navigation mockups should
use these real tasks. Open bounded owning issues when implementation/provider
work is scoped, following the [reporting protocol](reporting_protocol.md).
No runtime, dependency, candidate version or publication is changed here.

# Foundation operations and composed acceptance scenarios

**Status: proposed — source review and six operation/scenario groups prepared on
2026-10-22; implementation and scientific/browser qualification are pending.**
The approved [core/add-on boundary](core_and_addon_boundary.md) now assigns
general editing/preparation/analysis to tools/add-on interfaces. Earlier native
Studio placements below are comparison proposals to reassess, not approved
panel ownership. Visual scientific conveniences can retain their core scene
owner. The automatic-observer requirement is superseded.
This retains scenario inputs under the approved product boundary, with the
[operation inventory](studio_molsysmt_operation_inventory.md) and
[operation/recovery proposal](studio_molecular_operations_design.md).
These six groups exercise reusable general tools and their composition. The
`WF01`–`WF06` identifiers are retained as reference IDs, not a requirement for
six canned workflows or six new public methods. They do not limit pre-1.0 scope.

## Source and API boundary

Provider tools/signatures below were inspected against inventory baseline
`b501bfd69ad3e692ceeb865ebcdbd0cd1deed173`; defining files/hashes and return
documentation are in the [source snapshot](studio_molsysmt_operation_inventory.json).
Viewer baseline is `d96b073f` plus current planning documents. Concurrent
provider copy/benchmark development is not qualified or adopted here. Published
availability remains separate from source inspection and the existing Viewer
minimum `molsysmt>=0.23.0` is unchanged.

Python excerpts use existing public APIs and assume previously resolved inputs
such as `source`, `frames` and selected atom populations. They are source-checked
design examples, not executed tutorials or newly implemented Viewer workflows.
Provider examples prepare results; managed Viewer commit/history is still to
be implemented and named. Existing `view.set_box` and Interactions calls retain
their current behavior until reviewed contract changes land.
The revised [edit/reconciliation design](linked_molecular_edits_design.md) uses
explicit reconciliation and coordinated integrated-tool operations.
Independent results still require explicit incorporation. The proposed
retirement of redundant Viewer setters waits for a qualified general route.

Keep each provider's scientific return type and general selection/parameter
contract. Python users compose public MolSysMT tools with public Viewer
integration/domain APIs. Private Studio adapters resolve form inputs and use
those same boundaries; reconciliation/history mechanisms stay private. Reuse
`view.extract` and `view.apply_system_edit` first, reviewing their limitations
before extending them. Consider additional general view-aware tools only for
independently useful semantics. No public method per shortcut/journey or generic
`compute()` umbrella is selected. Public tools remain headless, digested and
explicit about recovery policy; Studio review is not a Python prerequisite.

## Common task experience

An ordinary form presents a general operation, a clear target and its scientifically
relevant choices. Use the existing active/query/saved selection tools and source
identity; users need not write a selection expression to choose waters, ions,
a loaded source or an interactively selected population. Technical controls can
be disclosed, while structure scope, reference, units and method remain visible.

The action progresses through validation, preparation, effect review when
needed, commit and display synchronization as specified in the technical
proposal. Preserve drafts and optional highlighting; Apply uses the reviewed
revision/parameters. A committed result must not be computed again because a
popup reconnects. Old scene handles remain retired under current manager checks.

Named results retain source/selection/structure/state identity, method and units,
actual producer provenance, applicability and persistent scientific content.
Native provider storage remains authoritative where present. For other result
types, select a lossless work/checkpoint representation before declaring the
workflow complete; do not assume H5MSM stores every array/table automatically.

## WF01 — Remove atoms or retain an atom selection

**Placement:** System Edit. **Inventory:** B01–B07, B12, H501–H502.

### Python scientific contract

Use public `select`, `extract` and their explicit atom/frame correspondence.
Removal retains the complement of the reviewed population; keeping a selection
retains that population. Both change the atom domain across all structures.
Selections are independent inputs: a water category, ions, a source, chain,
group, region, saved/query/mouse selection, indices or an admitted expression.
These are targets for the same operation, not separate removal algorithms.
For a resolved ordered, unique `retained_atom_indices`, preparation can use:

```python
candidate = msm.extract(
    source,
    selection=retained_atom_indices,
    structure_indices="all",
    copy_if_all=True,
)
```

Return the native molecular result according to the public tool contract;
apply a candidate through the public Viewer integration boundary, extending its
recovery and correspondence contract where required. `apply_system_edit`
currently reconciles state but clears Undo; this example does not qualify new
transactional behavior. Private coordination may prepare/review a candidate
without requiring a dedicated public remove-waters method. Verify the extraction route
retains the admitted order before deriving old-to-new maps from that population;
otherwise require authoritative public maps, not matching by atom names. Keep
frame identity and time/box ordering unchanged. Preserve valid extracted analyses only when their
provider remapping/coverage contract is verified; otherwise report invalidation.

**Provider contract question — uibcdf/molsysmt#406:** `basic.remove` advertises `in_place=True`, but
the inspected body never reads that argument and delegates to `extract` with
`copy_if_all=False`. This is an inspected signature/implementation inconsistency,
not a runtime reproduction. Do not infer ownership from that flag or use it as
a recovery guarantee. Resolve it with the provider before relying on it; the
explicit extraction candidate above avoids depending on that ambiguity.

### Studio experience

Offer **Remove atoms** and **Keep selected atoms**, each with a reusable target
selector. Removing structures has an explicit separate structure-axis scope;
it must not be confused with hiding atoms or editing coordinates of one frame.
Water/ion categories use provider classification, with readable group
names, counts, source and individual inclusion controls. For example, native
queries recognize `molecule_type=="water"` and `group_type=="ion"`; Studio need
not expose those expressions to operate the categories. Active/saved
populations, regions/sources, chains/groups and expression/index input feed the
same target contract. Optional Remove waters shortcuts only prefill that
visible selection in the general editor. Do not choose removal
of a metal automatically or imply that everything classified as an ion is
scientifically dispensable.

Show the retained/deleted counts and consequences for representations, anchored
objects and analyses before Apply. Hidden objects are not deletion targets by
implication. A reviewed selection does not track later clicks silently. Define
the all-atoms-removed case explicitly: empty molecular state, scene-only objects
and recovery must remain coherent rather than sending invalid empty geometry.

**Completion:** one managed Undo step; Redo restores the retained outcome;
save/reopen H5MSM and supported interchange output; no original files required
for recovery. Acceptance includes overlapping source regions, annotations on
removed atoms, a retained metal, no-op population and complete removal. Also
exercise arbitrary non-water atoms, mixed populations, index/expression targets,
and equivalent shortcut/manual arguments. Empty removal is a no-op; retaining
an empty population requires the explicit empty-system behavior and review.

## WF02 — Inspect chemistry and place hydrogens

**Placement:** Build Inspect/Repair; links from Topology Chemistry and
Interactions prerequisites. **Inventory:** PH07–PH11, BL01–BL06, BL12.

### Python scientific contract

Start with public readiness/inventory inspection, not silent repair:

```python
readiness = msm.physchem.get_chemical_readiness(
    source, selection=atoms, structure_indices=[frame],
    chemical_state="reference",
)
inventory = msm.physchem.get_hydrogen_inventory(
    source, selection=atoms, structure_indices=[frame],
    chemical_state="reference",
)
```

Readiness accepts one selected structure when structures exist. Its detached
report distinguishes present/partial/missing/conflicting/unassessed fields;
it is not a validity certificate or a prediction of missing H. State reference
and structure association are explicit; missing identity is not inferred.

Two different preparation contracts are available:

| Route | Current public composition | Limits to preserve |
| --- | --- | --- |
| Supported protein/template pH rules | `build.add_missing_hydrogens(..., pH=…, engine="MolSysMT" or an explicitly selected available engine)`; optional native `reconcile_protonation` is a distinct preceding action. | Fixed pKa/template approximation, not environment-dependent pKa prediction. Addition alone does not remove inconsistent existing H. The pH mode does not accept arbitrary selection/frame/state/report options from fixed-state mode. |
| One declared ligand chemical state | Explicit RDKit fixed-state placement on an isolated admitted component with one structure/state. | Requires complete declared connectivity and chemical assignments; no protonation-state search, receptor optimization, minimization or heavy-atom conformer generation. Multiple states/structures and unsupported chemistry must be rejected or routed explicitly. |

For the second route, after explicit extraction with retained source maps:

```python
prepared = msm.build.add_missing_hydrogens(
    component_one_frame,
    mode="fixed_chemical_state", pH=None, engine="RDKit",
    chemical_state="reference", structure_indices=[0],
    return_report=True,
)
candidate_component = prepared["molecular_system"]
report = prepared["report"]
```

The inspected implementation returns these `molecular_system` and `report`
keys. Retain that native return and its operation-index maps. Source-frame
mapping for local index 0 is essential. Adding the prepared component back into
a larger system needs a public provider composition/replacement contract, not
a private table splice.
If that reusable capability is missing, file the owning provider work before
offering seamless in-place ligand repair. Never broadcast generated H over a
trajectory to disguise single-structure support.

Adding atoms requires coordinates for the shared atom domain over every retained
structure. Preparing one extracted frame does not supply H coordinates for the
rest of a trajectory. Offer an explicit extracted single-structure workspace
using the existing extract-to-new-view route, or a genuinely qualified multi-frame
provider workflow; do not silently truncate the current trajectory or invent
coordinates in unevaluated frames.

Missing heavy atoms/termini are separately requested steps using supported
templates/engines. Native heavy-atom placement is bounded: multiple side-chain
gaps or unsuitable anchors can remain unassessed. Review the resulting report,
not just the new group name or atom count. Preserve observed coordinates,
chemical/source maps and preparation evidence; review any dropped attributes
or force-field parameters. Generated atoms have no fabricated original source.

### Studio experience

Inspection shows what is known, missing and not assessed, with links to eligible
actions. **Add missing hydrogens** is an explicit general operation with the applicable protein or declared-state
route in plain language. Explain pH, chosen engine, selected state/frame and
whether existing H will remain. Optional protonation reconciliation is a visible
operation with its own review of removals, never an implicit cleanup. Inspection
does not automatically run additions, normalization, protonation reconciliation
or minimization; a user may compose eligible operations deliberately.

Permit supported work without requiring chemical-state terminology everywhere,
but display it when ambiguity affects the result. If a route cannot assess a
ligand, say what information/engine is needed; do not label it chemically ready.

**Completion:** qualified source/candidate independence, generated-atom maps,
history and preparation-evidence persistence, evaluated coverage invalidation,
missing-engine and partial-reconstruction behavior. Undo/Redo preserves original
and generated chemistry without rerunning RDKit/OpenMM or losing old analyses.

## WF03 — Establish correspondence and align coordinates

**Placement:** Topology Correspondence and Structure Align/Analyze.
**Inventory:** T05–T06, S09–S13.

### Python scientific contract

Keep positional RMSD, optimal-fit RMSD, actual coordinate fitting, sequence
alignment and symmetry-corrected positional comparison distinct. The public
rigid fit separates the atoms that determine a transform from those it moves:

```python
candidate = msm.structure.least_rmsd_fit(
    source,
    selection=moving_atoms,
    selection_fit=fit_atoms,
    structure_indices=frames,
    reference_molecular_system=reference,
    reference_selection_fit=reference_fit_atoms,
    reference_structure_index=reference_frame,
    in_place=False,
    use_gpu=False,
)
```

These explicit options illustrate a native CPU candidate route; they do not
replace provider or Viewer defaults. Both fit populations need equal admitted
counts and at least three non-collinear points. Sequence-derived matching uses
`least_rmsd_align` and its Biopython route. Chemically constrained matching uses
`topology.get_atom_correspondences`, including complete-component context,
state/anchor restrictions and match caps; it is not automatically interchangeable
with sequence alignment or accepted merely because atom counts agree.

Verify how the actual fit route consumes correspondence/order before promising
an arbitrary map supplied by another tool. If an adapter is needed, extend the
scientific owner rather than reimplement Kabsch or reorder private native tables
in Viewer. Symmetry-corrected RMSD does not apply a superposition or MIC itself.

### Studio experience

Present **Moving system/region**, **Fit atoms**, **Reference** and **Structures**.
References can be a retained source/region/frame of the same view or an explicitly
loaded external reference. A merged Whole must not move the reference source
accidentally when the user intended to move only another loaded system.
An external reference is explicit scientific input, not a second editable
scene system or an implicit addition to Whole.

Offer a readable correspondence table/highlight when matching is nontrivial;
report unmatched or ambiguous populations. Separate **Measure deviation** from
**Apply alignment**. Camera reset/focus remains a view action, not coordinate
alignment. No pre-alignment or unwrapping is silently added to a metric.

**Completion:** explicit atom/frame identity, changed-coordinate scope and
affected-result validity, full recovery, saved fitted coordinates and reference
provenance. Include collinear/insufficient fits, different sequences, a stationary
reference source, nonconsecutive frames and stale-reference rejection.

## WF04 — Assign a periodic box and reimage coordinates

**Placement:** Structure PBC. **Inventory:** P01–P03, B12.

### Python scientific contract

Cell assignment and coordinate reimaging are different operations. Scientific
cell assignment belongs to MolSysMT; explicit reconciliation or an integrated
tool coordinates the view update under the discussion in uibcdf/molsysmt#413.
`view.set_box` is current implementation evidence, not the target API owner.
It accepts a unit-bearing matrix with box vectors as rows, a matrix
per selected structure, removal of the whole cell series, or an explicit source
system/structure pairing. It does not move atoms. Existing initialization and
removal require all structures; a partial replacement needs an existing series.
Source frames do not broadcast and available source/target times must agree.
Preserve or deliberately migrate those input/validation capabilities through
public scientific tools and shared private integration before retiring the
Viewer setter. Cell-edge representation remains a public Viewer responsibility.
Neither a new reconciliation API nor molecular recovery is implemented here.

Construct matrices with public `pbc.get_box_from_lengths_and_angles` or
`get_box_with_shape`. For coordinate reimaging, an existing provider route is:

```python
candidate = msm.pbc.wrap_to_pbc(
    source, selection=atoms, structure_indices=frames,
    compact="component", in_place=False,
)
```

Keep primary-cell wrapping, MIC wrapping and temporal unwrapping separate.
`unwrap` restores each atom's temporal continuity; it does not reconstruct a
split molecule inside a single frame. Component compaction uses declared
covalent connectivity and has its own validation. Nonconsecutive frame order
matters for temporal operations; do not describe continuity over skipped samples
as reconstruction of the unobserved trajectory. Missing/singular cells fail
without inserting an arbitrary default box.

### Studio experience

Show cell presence, lengths/angles/volume with units and selected structure scope.
Offer **Assign box**, **Load box from source**, **Remove box**, **Wrap into box**,
**Wrap around reference** and **Unwrap trajectory**, using explanations that
match the actual chosen provider operation. Box-edge visibility is separate.

Explain whether the action changes the cell or coordinates and which structures
will lose geometric-analysis applicability. Reuse the current first/current-box
policy for source composition; do not silently change it in this panel.

**Completion:** preserve atom/source identity, time/state associations and
nonaffected structure coverage; recover cells and coordinates together when
needed. Qualify multi-frame source pairing, partial update rejection, bad units,
invalid cells, split components and save/reopen without recalculation.

## WF05 — Calculate and retain a property or structure series

**Placement:** Properties and Structure Analyze. **Inventory:** S07–S11,
PH01–PH08, with the existing trajectory plot owner as a possible consumer.

### Python scientific contract

Keep provider quantities and their declared axes. Examples of current tools:

```python
rg = msm.structure.get_radius_of_gyration(
    source, selection=atoms, structure_indices=frames, weights=None,
)
sasa = msm.physchem.get_sasa(
    source, selection=atoms, element="atom", structure_indices=frames,
    engine="MolSysMT", probe_radius="1.4 angstroms", n_sphere_points=240,
)
```

Rg returns one length per requested structure; `weights=None` is not a request
for mass weighting. SASA returns area per requested structure and selected
atom/group. In the inspected native SASA route, occlusion uses the full input
system and selection filters the result afterward. Expose that context honestly:
the selected atoms' contribution in the full system differs from calculating an
explicitly extracted isolated component. Do not silently remove waters or other
occluders to produce a preferred value. Method/backend PBC behavior follows
actual cell support; the current SASA signature has no generic `pbc` switch.

Preserve each requested structure index/order/repetition in the result. RMSF
reduces over structures and PCA returns eigenvectors/eigenvalues, not per-frame
projections; they need appropriate tables/plots, not an invented scalar series.
Tabulated polarity, hydrophobicity, buried-area and volume scales remain labeled
reference properties, not newly measured coordinate observables.

### Studio experience

Use **Property/Analysis**, **Atoms**, **Structures** and a short method-specific
form. Show value/table first, with units and definition; offer a meaningful plot
or color representation when supported. Ordinary inspection must not silently
replace the user's existing color layer or create a permanent result.

For retained results, let the user choose a name and preserve source scope,
method, units and applicability. The current trajectory plot requires one scalar
per loaded frame. It cannot honestly display a sparse `[0, 8, 3]` result as a
three-frame timeline of the full view. Design an explicit index-aware consumer
or use a correctly indexed result table; never fill unevaluated frames with
zeros or erase missing coverage. Keep the full Python result available.

**Completion:** result ownership and a lossless work/checkpoint route are
required new foundations; a plot alone is insufficient. Validate alternate unit
policy, full-system/isolated SASA context, weighted/unweighted Rg, nonconsecutive
scope, stale results and meaningful reductions. Undo/Redo of result creation
restores actual retained values, not a rerun or merely the plot settings.

## WF06 — Calculate, inspect and display named interactions

**Placement:** existing Interactions. **Inventory:** IH01–IW01, H501–H502.

### Python scientific contract

Preserve the current explicit family API and distinction between scientific
analysis and tagged visual set. A current public composition is:

```python
analysis = view.interactions.hbonds.get_hbonds(
    name="hbond-review", structure_indices="all",
    method="baker_hubbard", pbc=False,
)
visual_set = view.interactions.add("hbond-review")
```

The Python family method defaults to `structure_indices="current"`; the example
requests all explicitly. It returns and attaches a named native analysis;
adding a visual set is a separate operation. Names are not overwritten
implicitly. A Studio **Calculate and display** action may compose these through
one managed history step without changing the individual Python methods.

Retain all nine current family adapters, actual methods/profiles, role and
chemical-state requirements, measured units and explicit PBC. Calculation
selection modes and display query modes are separate contracts. Changing
display structures must not claim those structures were calculated. An empty
evaluated result is different from an unevaluated frame, absent prerequisite or
engine failure; preserve provider diagnostics rather than interpreting every
empty list as proof of no physical interaction.

### Studio experience

Keep named analyses and visual sets clearly related. Offer explicit calculation
or file import, readable method/criteria and a prominent calculation structure
scope. A source can be Whole, a chosen source/region or active/query/saved atoms
when supported; do not discard cross-boundary participant semantics.

Users can inspect current-frame occurrences, select/focus participants, filter
display scope and change representation without recalculation. Preserve
compound participants, parallel occurrences, sparse query/paging budgets and
periodic images. Link unmet chemical prerequisites to Build inspection without
automatically repairing or recalculating.

**Completion:** extend history to named-analysis creation/deletion in addition
to existing visual objects; preserve sparse scientific data once and source
versions on restoration. H5MSM/session save, independent-import declarations,
stale occurrence/result rejection, named-analysis conflicts and both popups
remain acceptance cases under the
[consumer contract](interactions_compatibility_contract.md).

## Decisions and provider receiving to complete before implementation

| Topic | Current evidence | Next design/receiving action |
| --- | --- | --- |
| General tools and Viewer integration | Existing public MolSysMT tools, `view.extract` and `apply_system_edit` are available; unified molecular/result history is not. | Reuse public composition; qualify required general boundary extensions and private coordination. Assess new general tools by added value, without wrappers per journey or narrower selectors. |
| Edit reconciliation | Provider controlled scientific invalidation exists. The consumer withdrew the general observer request in uibcdf/molsysmt#413. | Qualify explicit reconciliation/tool coordination, scope/maps, deferred-update safety, outcomes and optional pre-edit recovery; report concrete gaps separately. |
| Current load-history boundary | uibcdf/molsysviewer#262 fixes and guards successful replacement clearing old scene Undo/Redo, with rejection and first-load controls. | Keep the current scene-only boundary distinct from future molecular recovery. |
| Native ownership/copy | Provider uibcdf/molsysmt#121 is closed; Viewer #259 remains open for consumer receiving. | Receive exact public contract/source and qualify independent edits, old handles and failure paths; no private copy helper dependency. |
| Remove ownership flag | Source advertises `in_place` but does not read it; reported as uibcdf/molsysmt#406. | Confirm provider intent; do not build a wrapper assuming the advertised mutation policy works. |
| Component repair/reinsertion | Fixed-state H placement returns a prepared isolated component and maps/history. | Verify a reusable public composition/replacement route preserving current source/frame/chemical domains; request it from MolSysMT if missing. |
| Atom-map consumption by fitting | Correspondence and fit tools are individually present. | Verify their admitted ordering/composition before promising arbitrary-map fitting in Studio. |
| Sparse result plotting | Existing scalar plot requires every loaded frame. | Design an index-aware result consumer or retain a table; no fictitious values or silent restriction of Python selectors. |
| New scientific result persistence | Existing scene/session and named Interactions are available; generic property/correspondence result persistence is not established by these calls. | Choose domain-native retained records and supported lossless save/checkpoint routes before exposing a complete retained-result workflow. |

These are concrete contracts to resolve, not exclusions from 1.0. Carry them
into the operation/recovery design and the
[wide/narrow task prototype](studio_task_design_review.md).
Qualify actual provider/engine/writer versions separately. Runtime tests and
human 1TCD walkthroughs follow implementation; this record does not claim them.

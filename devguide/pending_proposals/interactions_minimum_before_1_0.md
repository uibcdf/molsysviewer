---
summary: Introduce a minimal Interactions scene domain before 1.0.
issue: uibcdf/molsysviewer#114
status: partial
opened: 2026-09-28
closed:
verification: measured
area: [interaction, scene, api, ui]
guard:
normative:
blocked_by: [uibcdf/molsysmt#250]
supersedes: []
---

# Introduce a minimal Interactions scene domain before 1.0

**Current API update (2026-10-01):** the maintainer selected named family
wrappers (`view.interactions.hbonds.get_hbonds`, etc.) for the nine implemented
experimental provider families. The original two `compute_*` calculation routes
have been removed; the executable examples below use named family getters.
There is no generic public `compute`. The current contract and verification are maintained in
[the family update](../interactions_pre_1_0_plan.md#family-api-update--2026-10-01)
and [uibcdf/molsysviewer#140](align_interactions_with_molsysmt_families.md).
The older dated sections describe the original minimum, not a limit on the
new adapter's family support. Published dependency qualification remains open.

**Reported:** 2026-09-28, during the final review of the 1.0 public surface and
in coordination with `uibcdf/molsysmt#250`.

**Status:** Partial implementation (2026-09-30). Scientific discovery, queries,
attachment/import and calculation are implemented in the working tree, with
scientific session persistence and edit invalidation. Tagged displays,
browser projection and Studio are now implemented; the current bounded
behavior is recorded below. Initial synthetic joint memory/query measurements
are recorded in `devguide/interactions_performance.md`. Bounded real detector,
periodic-image, persistence and calculated-link browser qualification now pass
as recorded in `devguide/interactions_qualification.md`; a compatible published
provider, larger GPU workloads and the exact candidate remain pending. The experimental scientific and visual API is
callable in the working tree; this is not yet a qualified released feature.

**Publication checkpoint (2026-10-01):** a fresh GitHub Release inventory still
lists MolSysMT 0.22.4 as the latest publication. The scientific Python tests and
the Interactions browser bridge directly require the experimental result and
H5MSM-layer APIs. Publishing this whole source block into the ordinary public
dependency CI route therefore needs its provider qualification first; the
successful source-pin runs and independent release-tool publication do not
establish that compatibility. Retain the public-provider gate and the explicit
unsupported-backend behavior. No scientific tests or browser observations have
been skipped to make the publication block pass.

## What

Add a first-class `view.interactions` scene domain for hydrogen bonds and
disulfide candidates. It must be usable from Python and from a minimal
Interactions subpanel in the floating Studio card. Named scientific analyses
live in `view.molsys.interactions`; tagged scene objects reference them and
realize filtered occurrences across the structures actually evaluated.
This slice does not promise a general interaction
classifier or the full post-1.0 designs in `uibcdf/molsysviewer#48` and
`uibcdf/molsysviewer#56`.

## How

Agree a consumer result contract with `uibcdf/molsysmt#250` before fixing the
public Python signature. The result must retain participant roles and atom
index space, evaluated structure indices and their order, empty evaluated
results versus unevaluated structures, method and parameters with units,
inferred versus topology-declared provenance, and periodic-image identity
where it affects the observed participant. Hydrogen-bond data retain the
donor, hydrogen, and acceptor even if the renderer draws one link.

Implement the Python manager and scene-state semantics first. The minimum
surface creates and inspects named sets and supports visibility, deletion,
layers, frame changes, and reproducible replay/export. Exact creation methods
and the policy for edits to the molecular system are design decisions to
record before code. Use Mol*'s existing `CustomInteractions` and
`InteractionsShape` as the initial renderer, subject to real-browser checks
for frame changes and scene reconstruction. MolSysMT owns chemical analysis;
the viewer maps a scientific result into a visual representation.

Only after the API and state contract are established, inspect the current
Shapes, Annotations, Regions, and Selections subpanels, then design the
small Studio Interactions subpanel against those patterns. It must list and
control the same sets exposed by Python and offer only creation operations
whose scientific method and required inputs are explicit. The existing
Shapes H-bond action and its calculation claim need reconciliation with this
surface; source inspection suggests the action currently omits the required
`structures` argument, but that failure has not yet been runtime-reproduced.

MolSysMT becomes the scientific backend for these native workflows, without
addon registration or a separate MolSysMT panel. The existing addon computes
Buch H-bonds through `view.shapes.links.add_hbonds`; reconcile that overlapping
path with the native manager. Retire the addon progressively once its useful
capabilities have native replacements. Complete addon removal and migration
of its other scientific workflows are outside this first slice.

## Python API design for implementation (2026-09-29)

### Scientific storage and scene identity

The authoritative store is `view.molsys.interactions`, using MolSysMT's named
complete `Interactions` results. The viewer does not keep another scientific
store in its manager or addon. One analysis may have several visual objects:
`analysis_name` identifies scientific data, while `tag` identifies a scene
object and its filter, style, visibility and layer. Changing a tag must not
rename an analysis. Scientific names must be supplied explicitly; scene tags
use the existing per-domain allocation and collision rules.

Use an `InteractionsManager` and an `InteractionSet` scene object with kind
`interaction`, following the current Shapes/Measurements collection and
SceneObject conventions. Handles remain small; they contain an analysis
reference and visual state, not copied occurrence arrays. Attached results
are treated as immutable snapshots for this supported workflow. Direct
mutation of their arrays or unannounced mutation of `view.molsys` cannot be
tracked and is outside its cache-validity contract.

### Three entry routes

These are proposed signatures. Normal argument digestion, dependency checks,
diagnostics and history hooks are required at implementation time.

```python
# Discover data already retained when the molecular system was loaded.
view.interactions.analyses()                  # lightweight metadata records
view.interactions.get_analysis(name)          # complete msm.Interactions
view.interactions.add(
    analysis_name, *, tag=None, selection="all", selection_2=None,
    mode="incident", exclusive=False, structure_indices="all",
    interaction_types=None, syntax="MolSysMT", layer_tag=None,
)                                            # InteractionSet

# Attach an independently obtained complete result or load one named analysis.
view.interactions.attach(result, *, name, assume_aligned=False)
view.interactions.load(
    filename, *, analysis_name, name=None, assume_aligned=False,
    atom_indices=None, structure_indices=None,
)                                            # attached msm.Interactions

# Calculate against the current full MolSys axes, then attach with a name.
view.interactions.hbonds.get_buch_hbonds(
    *, name, selection="all", selection_2=None,
    structure_indices="current", distance_threshold="2.3 angstroms",
    pbc=False, syntax="MolSysMT",
)
view.interactions.disulfides.get_disulfide_candidates(
    *, name, selection="all", structure_indices="current",
    max_bond_length=None, group_names=None, pbc=False, syntax="MolSysMT", sorted=True,
)                                            # attached msm.Interactions
```

`analyses()` reports names, kinds, method, parameters, units, producer
versions when known, scope, axis sizes, evaluated coverage summaries and
occurrence counts. It must not expand all participant or occurrence records.
`get_analysis()` returns the scientific result; a missing name raises
`KeyError`. Adding a display of existing data does not require another
alignment declaration.

`attach` and `load` do not create a display. Computation returns and stores
the complete analysis but also does not create a display. This makes data
ownership and visual filtering explicit and keeps return types stable:

```python
# API-first design, now implemented; see the implementation record below.
view.interactions.hbonds.get_buch_hbonds(name="hbonds", structure_indices=[0, 8, 3])
hbonds = view.interactions.add("hbonds", tag="protein-hbonds",
                               selection="molecule_type == 'protein'")
hbonds.hide()
hbonds.show()

view.interactions.load("contacts.h5msm", analysis_name="buch",
                       name="imported-hbonds", assume_aligned=True)
view.interactions.add("imported-hbonds", tag="imported")
```

Studio may compose compute/load followed by `add` into one user action using
these public methods. It must report calculation/import success separately
from an unsupported graphical realization; a rendering failure must not
discard a valid scientific result.

### File loading and declared correspondence

The first native import route is a named analysis in H5MSM 0.5, from either
a complete system file or an interactions-only file. `load` reads that
selected analysis into memory, without replacing the viewer's molecular
system or loading an unrelated trajectory. Files lacking the requested
analysis fail explicitly. Other interaction file formats are later work;
the provider can already supply independent results to `attach`.

Importing data into an existing view requires `assume_aligned=True`, including
when the file also has a molecular system. It declares correspondence to the
target's atom order, structure order, coordinates and boxes; it is not an
automatic verification. By contrast, loading the entire stored system and
its associated analyses through the normal viewer loader relies on the
writer's declaration. Matching sizes, `source_id` and source maps are
insufficient evidence of molecular identity. Automatic origin fingerprints
remain future work.

For `load`, optional `atom_indices` and `structure_indices` describe source
axis extraction/reordering through public `Interactions.remap`, before the
explicit target declaration and attachment. Omission preserves that source
axis. The final axis dimensions must match `view.molsys`; these arguments are
not arbitrary source-to-target embedding maps. Importing a subsystem result
into a larger system is unsupported in this slice. Compounded source maps
remain provenance and are never used as an automatic join.

An interactions-only file supplies no rendering coordinates. Positions and,
for periodic observations, matching boxes come from the current `view.molsys`.
Validate dimensions, participant indices, coverage, measurements and declared
associations through public MolSysMT APIs. Attach only a complete analysis,
not a filtered query view. Existing analysis-name conflicts raise without
replacement; no implicit overwrite or merge is offered before 1.0.

### Calculation scope and publication

The first H-bond method is Buch, using the provider's optional
`molsysmt.Interactions` output. Its 2.3 Å threshold is hydrogen-to-acceptor
distance; do not imply an angular criterion. Disulfide candidates use the
provider's S–S geometry, with effective defaults 2.05 Å and CYS when the
arguments are `None`. They are candidates, not a topology edit or a claim
that a covalent bond exists. Unknown methods fail explicitly.

Resolve `"current"` once at calculation start. A scalar, a nonconsecutive
integer list, or explicit `"all"` selects other structures in the loaded
MolSys index space; remove duplicate query/calculation indices in first-seen
order. The analysis retains the full system axes and marks only the evaluated
structures, including empty results. Playback never silently computes missing
frames. Filtered calculation scope is recorded; an empty query outside that
scope must not be presented as proof that no interaction exists.

The viewer defaults to `pbc=False`; enabling it is explicit and requires valid
boxes for the requested structures and the provider's observed image vectors.
Do not advertise PBC while silently falling back to nonperiodic geometry.
Keep donor–hydrogen–acceptor roles, actual parameters, units, scope, evidence
and calculation-time software versions. Older imported analyses may have
unknown versions; the reader's installed version cannot fill that gap.

Compute and validate off the live scientific collection, then publish by
replacing MolSysMT's validated named-analysis mapping. Its current mapping
is read-only to item assignment; use its public setter. Validation failure,
cancellation, name conflict or a changed system generation leaves the existing
analyses untouched. No partially computed analysis is exposed. Changing only
the visible frame does not redirect a calculation already started.

Python calculation may be synchronous in this first slice. Studio must show
busy/error state and keep the canvas usable while a job runs; any worker must
publish on the owning Python execution path and reject stale results. Do not
promise incremental editing, streaming computation or cancellable native
kernels. Bulk requests need combined memory and latency measurements before
support limits are stated. Frame batching must preserve coverage, roles,
parallel observations and images if introduced; it is not a reason to publish
partial or ambiguously evaluated data.

### Queries, filters and display lifecycle

```python
view.interactions.query(
    analysis_name, *, selection="all", selection_2=None, mode="incident",
    exclusive=False, structure_indices="all", interaction_types=None,
    syntax="MolSysMT",
)                                            # lightweight msm.Interactions
```

The query exposes public provider views, never a dense pair matrix. It
resolves selections to local atom sets and delegates `incident`, `internal`
and `cross` to `Interactions.query`; `mode="between"` delegates to
`Interactions.between` and requires disjoint selections A and B.
`exclusive=True` is valid only for `between` and confines every participant
atom to A ∪ B. `selection_2` is rejected for the other modes. The complete
participant membership, including hydrogen or every atom in a group, governs
these predicates. Provider evaluation scope and evaluated coverage remain
available on the returned result alongside occurrences.

The display constructor accepts the same filters. Selection expressions are
resolved once and stored with their resolved indices; dynamic selection
recipes are later work. `structure_indices="all"` lets the display follow
playback over the analysis's evaluated coverage. `set_filter` on a handle
uses the same keyword fields and validates the new filter before replacing
the old one. An evaluated frame with no matches clears its geometry; an
unevaluated frame also clears geometry but reports a different status.

Manager collection operations follow the existing domain patterns:
`tags`, `contains`, `count`, `records`, `info`, `get`, indexing by tag,
`show`, `hide`, `show_all`, `hide_all`, `set_tag`, `delete` and `delete_all`.
`get` returns `None` for a missing tag; indexing raises `KeyError`. An
`InteractionSet` exposes `analysis_name`, tag, filter, visible state and layer,
plus `show`, `hide`, `delete`, `set_tag`, `set_layer_tag`, `set_filter`,
`set_color`, `set_alpha` and `set_radius`. Validate style updates as scene
transactions. Register interactions in layer membership, tag high-water
marks, scene ordering/identity and render-status acknowledgement machinery.

`delete` and `delete_all` remove visual objects only. Scientific data stay
available for another display or saving. `delete_analysis(name)` is explicit
and refuses while any scene object references the analysis. It clears scene
undo/redo history before dropping the data, so old snapshots cannot restore
dangling references. Scientific attachment/calculation is outside scene undo;
adding, deleting, filtering and styling its visual objects are scene undo
operations. Undoing creation of a display retains the calculated analysis.

### Rendering, persistence and edits

Live rendering queries only the visible structure. Picking identifies
`(analysis_name, analysis_revision, occurrence_index)`; the revision identifies
an immutable viewer snapshot and must change after remapping or invalidation.
Parallel observations remain separate even if their participant atoms match.
Frame caches and runtime projections have explicit byte bounds, with no
unbounded all-frame JSON history. Static export is a separate bulk projection.

Draw H-bonds initially as H···A dashed links, keeping D–H–A in the scientific
result and pick details. Draw candidate disulfides as dashed S···S links with
their candidate label. Apply the provider's image displacement relative to
the donor/first participant, using row-vector boxes in nm and one conversion
to the renderer's coordinate units. For H-bonds, both H and A are shifted
relative to D; do not shift just A. The installed Mol* two-loci extension
cannot express those image shifts directly, so periodic rendering needs a
verified scene geometry path. Retain an unsupported-render status for other
imported kinds/participant shapes rather than discarding their scientific
data or silently approximating a split periodic ring.

`export_state` includes interaction object identity, analysis references,
filters, resolved selection indices, style, visibility, layers and tag marks.
It also records a content signature of each referenced analysis, computed
once from its canonical scientific fields at registration, not on every
frame. This checks restoration against a changed analysis; it does not
authenticate correspondence to the molecular system. Encoding and hashing
costs must be included in the memory measurements.

State-only import requires matching analyses already in the destination
MolSys. Missing or mismatched references cause an atomic error before scene
mutation, never silent omission or recalculation. The signature and snapshot
serialization need a deterministic local schema. No occurrence arrays are
duplicated into every scene undo snapshot. `save_session` instead includes
the complete named scientific analyses through H5MSM 0.5, alongside the
scene state. Validate the actual Viewer session round trip; successful
provider conversion alone is insufficient. Reject a save if the selected
provider/file writer cannot retain the data. State schema/version handling
must reject unsupported interaction records rather than lose them.

Interactive HTML embeds each referenced analysis projection once, including
covered structures, roles, images and provenance needed for picking and
rendering. It must distinguish unevaluated frames and support its advertised
playback without Python. Export fails explicitly if required geometry,
boxes or data cannot be embedded within the chosen export policy. Reconnect
and popup rebuild from canonical registries with equivalent frame status.

Pure extraction or reordering relies on MolSysMT's public remapping and
reconciles display filters. Appended structures start unevaluated. Changed
coordinates or boxes invalidate affected frames; changed topology, chemistry
or participant definitions require conservative invalidation of affected
analyses, not just index remapping. If an edit does not identify affected
frames, invalidate all their evaluated coverage. Retain provenance and show
an explicit unevaluated/broken status; do not recompute implicitly. Molecular
edits still pass through `apply_system_edit`. Scientific domain methods here
attach analyses and do not introduce generic topology/coordinate mutators.

## Computational and result-shape requirements

The two independent scale axes are the number of structures and the number
of candidate participants. A trajectory may contain hundreds or thousands
of structures, while the number of observed interactions varies on every
structure. Design for storage proportional to evaluated structures plus
actual occurrences and distinct participant groups, not a dense
`structures × atoms × atoms` contact tensor or a rectangular interaction
array padded to the busiest frame. This is a design target; its memory and
latency must be measured on representative fixtures before implementation is
called complete.

The provider result needs indexed access to an evaluated structure and a
bounded way to iterate or compute structure ranges. The accepted experimental
`molsysmt.Interactions` separates relations and occurrences and provides
indexed in-memory queries; public incremental construction remains a separate
capability to agree and measure.
For each evaluated structure, zero occurrences is a real result. An absent
structure index means the analysis was not run there. Return empty arrays
with defined column counts, not shape-ambiguous arrays or `None` reused for
both states. Per-occurrence metrics must align with the same occurrence
order and carry explicit units.

The consumer query contract must support two independent filters, usable
together: one structure index or an explicit list of structure indices, and
one atom index or an explicit list of atom indices. For an atom set `S`,
`incident` means any participating atom belongs to `S`; `internal` means
every participating atom belongs to `S`; `cross` means `incident` minus
`internal`. These definitions include the hydrogen in a D–H···A result and
all member atoms of a group participant unless an explicitly named
projection chooses a different policy. Queries across several structures
retain each occurrence's structure index and deterministic order; duplicate
input indices do not duplicate results. Unevaluated structures must be
distinguishable from evaluated structures with zero matches. Kind/family
filters must combine with both axes. A single atom is the one-element-set
case.

Fast structure lookup alone is insufficient: asking for one atom across a
long trajectory must not scan all occurrences in every structure. A possible
physical design has a unique relation/participant table, a sparse occurrence
table with `evaluated_structure_indices` and per-structure offsets, and
secondary postings from atom to relations and from relation to occurrences.
Queries can intersect postings with selected structure ranges and then apply
the exact `internal`/`incident` predicate. The secondary indexes may be
built lazily rather than duplicated in persistence. The agreed contract
should specify measurable, output-sensitive lookup and memory behavior,
not mandate this particular container design.

Topology-derived participant definitions can be shared across structures:
hydrogen-bond donor/hydrogen/acceptor identities and later ring or group
memberships need not be copied into every frame record. A frame occurrence
then identifies the participants and any frame-dependent geometry or periodic
image. Its interaction identity must be deterministic so that the same
relationship can be recognized across frames. The viewer's runtime indices
refer to its converted `view.molsys`; if the caller selected nonconsecutive
source structures or a subset of atoms, mapping back to source indices is
explicit provenance rather than an implicit positional assumption.

The viewer must not send every frame's occurrences in every scene command.
Live rendering projects the current structure and discards stale work after
frame, system-generation, or criterion changes. Caches have a byte budget and
are invalidated when their scientific inputs change. The provider and viewer
must specify how calculation is chunked, how cancellation/errors are reported,
and what happens when the requested playback rate exceeds calculation or
rendering throughput; no unmeasured 25 ms region-evaluation budget is copied
onto interaction chemistry.

Static interactive HTML has no Python evaluator. If a set is presented as
covering a trajectory there, export must include a bounded, reproducible
all-frame result or explicitly reject that export. It cannot silently show
the first frame's interactions on later structures. Scene state retains the
recipe/provenance and the exact materialized coverage needed by its supported
restoration paths; large data cannot be slipped into append-only message
history or repeatedly expanded as nested JSON lists.

Results need a versioned, typed serialization boundary that maps to an
optional H5MSM interaction domain without a dense pair matrix or
one Python object per occurrence. The mapping must preserve atom/structure
index domains, occurrence-to-structure association, empty-versus-unevaluated
coverage, participant roles, per-occurrence measurements, units, criteria,
provenance, and PBC images. Slicing or reordering atoms and structures must
remap or invalidate results explicitly. H5MSM 0.4 has no interactions layer.
MolSysMT's review commit `82bcb810e8c482a78142a7a19c70f68d72b42ba0`
implements an experimental optional H5MSM 0.5 interaction layer; the viewer
1.0 slice must not depend on a claim that this experimental file path is
already a stabilized release contract.

TopoMT, PharmacophoreMT, and DockingMT may need the same query and sparse
result semantics. Ask those teams to validate the logical contract before
locking it to hydrogen-bond-specific arrays; this is a likely cross-suite
use case, not a claim that their current APIs already require it.

## MolSysMT consumer-review checkpoint (2026-09-29)

Reviewed MolSysMT commit `82bcb810e8c482a78142a7a19c70f68d72b42ba0`.
Its experimental `molsysmt.Interactions` and named `MolSys.interactions`
results cover the required sparse relation/occurrence split, variable-size
participants and explicit roles, evaluated-empty coverage, declared atom
search scope, local/source maps, parallel observations, periodic images,
`incident`/`internal`/`cross`/`between` queries, remapping, and H5MSM 0.5
round trips. The supplied fixture generator completed and the focused public
native/H5MSM workflow test passed (`1 passed`). A separate conversion of the
full fixture through `msm.convert(..., selection=[0, 1, 2],
structure_indices=[4, 1, 0])` retained and remapped its named analysis.
These are contract and synthetic parity checks, not viewer-rendering or
scientific-validation evidence.

The current public `read` and `read_layers` APIs materialize the selected
analysis. An indexed file reader exists internally but is not a public
file-backed query API, and its whole-trajectory atom query still scans frame
occurrences. For the 1.0 viewer path, full-load analysis may be acceptable
because the viewer already materializes its selected structures; measure
combined memory, multiple named analyses, and static export before settling
that choice. Public file-backed queries are a separate capability decision.
The existing viewer warning threshold is 256 MiB of raw coordinate bytes,
not an interaction-memory allowance. Candidate client workloads are 62 atoms
and 5,000 structures; 10,000 atoms and 1,000 structures; and 100,000 atoms
and 100 structures, with variable sparse counts, empty frames, high relation
reuse, and high relation churn. Measure initial result construction, first
index-building query, warm current-frame queries, nonconsecutive-frame lists,
one-atom trajectory queries, steady RSS, and simultaneous coordinate plus
analysis residency. MolSysMT's 100,000-atom/10,000-structure interaction-only
probe is valuable storage evidence but lies well beyond the viewer's current
materialized-coordinate warning threshold.

The provider now offers optional `Interactions` outputs for Buch and
disulfide candidates, preserving the established return defaults and leaving
attachment to the consumer. Luzard–Chandler is outside the viewer minimum.
Chemical detection and result semantics remain with MolSysMT; the viewer
coordinates calculation, attachment, queries and graphics.

The installed Mol* `CustomInteractions` extension accepts two endpoint loci
and has no periodic-image field. It can project a D–H···A relation onto a
visible link while the scientific result retains all three participants,
but periodic-image displacement and parallel-observation picking need a
real-browser proof or a scene-local geometry fallback. Do not claim generic
multi-participant or periodic rendering merely because the data model can
store those relations.

**Follow-up at MolSysMT commit `0d1a2bf0aa9e507b546135b24d0368db10c50a0c`:**
`query(...).to_dict()` and the H5MSM query projection now expose int64
`occurrence_indices` stable within a complete analysis, including parallel
observations. Remapping or editing creates a new analysis and may reassign
them. The focused public/HDF5 tests passed (`5 passed`), and the previous
synthetic H5MSM fixture yielded occurrence indices `[3, 4, 0, 1]` for a
nonconsecutive repeated-frame query. The provider also documented the
periodic convention: with box row vectors in nm, a participant position is
`r + image_vector @ box`; relative to the first participant, the shift is
`(image_vector_p - image_vector_0) @ box`. One vector moves every atom of a
compound participant together and does not internally unwrap a ring crossing
the box boundary. These settle the occurrence-identity and image-convention
questions; browser projection remains to be verified. Detector progress is
recorded below.

**Source-inspection risk (2026-09-28, Buch subsequently addressed):** the
then-current MolSysMT H-bond methods
construct per-structure occurrence lists and then call
`np.array(output_atoms)`. Different interaction counts across structures
cannot form a regular NumPy array (confirmed with NumPy 2.4.6 on a minimal
ragged example). The Luzar–Chandler path also indexes an empty
`tmp_atoms` as a two-dimensional array before filtering. These observations
were not a runtime reproduction of either MolSysMT method. The provider's
Buch follow-up and focused checks below address that path; this does not
certify Luzard–Chandler's empty or variable-count behavior.

**Provider checkpoint at commit
`2e79b5f290fa8e7cde5d4b8f9d4ed8110a006b69` (2026-09-29):**
attachment declares correspondence to the destination; indices, dimensions,
scope and declared associations are validated, while source labels/maps do
not authenticate origin. Public `msm.convert` persistence was reinforced with
two named analyses. Buch now preserves donor–hydrogen pairing and exposes a
sparse result; disulfide candidates expose their geometric evidence. Both
adapters recover observed PBC images rather than fabricating zero vectors,
and the disulfide path includes rotated-box minimum-image checks.

The following targeted provider selection passed before the subsequent
uncommitted provenance changes: `27 passed`, with two legacy-H5MSM warnings.
It is provider evidence, not a MolSysViewer integration or renderer result.

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider --receptor=llm \
  tests/interactions/test_public_molsys_h5msm_workflow.py \
  tests/interactions/hbonds/test_buch_results.py \
  tests/interactions/hbonds/test_donor_pair_integrity.py \
  tests/interactions/disulfides/test_get_disulfide_candidates.py
```

The `software` producer-version mapping subsequently landed in `04c6593cc`.
Consumer integration uses clean provider revision
`f9f4c1a5fe22124eee01e3ceb37d582c86aee0ac`, including calculation-time
versions through queries and session HDF5. Older data retain unknown versions.
Joint memory measurements and a supported published dependency remain open.

## Scientific implementation checkpoint (2026-09-30)

`molsysviewer/interactions.py` implements `analyses`, `get_analysis`, `query`,
`attach`, `load`, `compute_hbonds`, `compute_disulfide_candidates` and
`delete_analysis`. These methods use the public MolSysMT result, detectors,
named collection setter and H5MSM layer reader. No addon registration is needed.
Attaching or calculating data does not yet draw a scene object. The implemented
surface is documented in `docs/content/developer/public_api.md`.

The tests in `tests/test_interactions_api.py` use real demo systems for calculation,
selection, edits and sessions, plus synthetic sparse observations on those axes
for group roles, parallel occurrences, empty coverage and file remapping.
Independent attachment requires explicit correspondence, names cannot overwrite
existing analyses, and publication rejects a changed system revision. Mutating
these three guards makes the corresponding focused test fail. Removing the
session-signature check also makes its focused test fail; the test now requires
the specific scientific integrity error, rather than accepting any `ValueError`.

Scientific arrays live only in the system and its H5MSM session member. A compact
manifest stores content signatures, checked before touching a destination view.
Session restoration replaces an existing view's system, rather than merging it.
This correction was exposed by the integrity mutation and covered by a positive
reuse round trip. Coverage order and calculation-time software versions survive.
Signatures verify saved data; they do not authenticate molecular correspondence.

Full-axis native loading keeps immutable analyses unchanged. The provider's
generic full-axis conversion otherwise remaps and reorders evaluated coverage
even when no subset was requested. Subset loading continues to use provider
remapping. This boundary preserves exact scientific snapshots without accessing
private provider storage; coordinate arrays follow the usual conversion path.
The ordering finding should be handed back under `uibcdf/molsysmt#250`.

`apply_system_edit` invalidates evaluated coverage by default. Explicit
`interactions_policy="preserve"` declares that the incoming analyses are already
aligned and valid. Direct array mutation or unannounced edits are outside this
contract. Deleting scientific data clears visual undo; scene reference and
signature binding remain work for the tagged-display slice.

Validation of this scientific slice: 34 focused Python tests passed; the JS
unit runner passed; `npx tsc --noEmit` passed; 34/34 core browser suites passed
with `/usr/bin/google-chrome`. These browser suites guard existing behavior;
they are not evidence for an interaction renderer that has not been implemented.
Ruff and generated-index checks passed. No TypeScript source or distributed
runtime bundle was changed.

The one full Python run reported 2,200 passed, 18 skipped and three Qt worker
crashes. A focused serial invocation reproduced a native Qt import crash.
That Python 3.13 environment mixes PySide6/Qt 6.9.3 and 6.9.2 packages instead
of the agreed canonical 6.11.2 recipe. The qualification finding is recorded
under `uibcdf/molsysviewer#109`; the global suite is not green. The final
candidate still needs supported provider-release and qualified-environment
evidence, plus the scene/Studio work and joint memory measurements.

## Studio subpanel design (2026-09-30)

**Status:** Design reviewed and implemented in the working tree. The section
below retains the design rationale; the implementation record names the
current minimum and differences from the initial draft.
The independent, interactive [layout prototype](../../sandbox/interactions_panel_design.html)
uses synthetic data and performs no calculations or file access. It is a
review aid; this section owns the proposed behavior. Advanced UI remains in
`uibcdf/molsysviewer#56`.

### Reusing the current Studio patterns

| Inspected source | Pattern adopted |
| --- | --- |
| `js/src/ui/panels/annotations-panel.ts` | Visibility summary, creation card, saved cards, Focus/visibility/Edit/Delete, inline tag/layer/style editing. |
| `js/src/ui/panels/shapes-panel.ts` | Three-part layout, type-dependent controls, separate rendering warnings, small saved-card action row. |
| `js/src/ui/panels/regions-panel.ts` | Inline Inspect with request identity, authoritative detail responses, staged selection and continuous-edit history. |
| `js/src/ui/panels/selection-dock.ts` | Shared Active selection / Select by query / Saved selections dock with an explicit Set action. |
| `js/src/ui/panels/base-panel.ts` | Typed state setters, deferred painting of hidden tabs, preservation of input focus and caret. |
| `js/src/ui/group-panel.ts` and `floating-panel-shell.ts` | Native Core tab registration inside the existing shell, badge and source-of-truth projections; the same content works in drawer and floating layouts. |

The source paths above are relative to `molsysviewer/`. No new shell or separate
scientific workspace is needed. Insert `interactions` after Measures and before
Shapes in the default Core order. Preserve customized tab ordering when adding
the new key rather than resetting the user's entire order. Its badge counts
visual sets; a collapsed Stored analyses section reports scientific data.
Use the existing 10–13 px typography, 6 px card/button corners, subtle borders,
7–10 px spacing and purple selection accents. Green indicates enabled display
intent, amber warns about missing evaluation or invalidation. Text always states
the actual frame outcome. Rows wrap in the drawer; the content scrolls inside
the floating shell. Do not change global Studio styling.

### Organizing the panel

```text
Interactions                                         [3]
  2 of 3 sets enabled               [Show all] [Hide all]
  Frame 8 · 12 links drawn · 2 stored analyses

New interaction set
  [Calculate] [Stored analysis] [H5MSM file]
  Type              Hydrogen bonds
  Analysis name     hbonds_current
  Criterion         Buch · H···A distance
  Maximum H···A     0.23 nm
  Calculation atoms All atoms
  Structures        Current frame
  Periodic images   [ ] Use periodic boxes
  ▸ Display filter & style
  [Calculate & show]

Saved interaction sets
  site_hbonds                         Hydrogen bonds
  Analysis: buch_trajectory · selection A (24 atoms)
  Frame 8 · 12 observations · 12 links drawn
  [Focus] [Hide] [Edit] [Inspect] [Delete]

  cys_candidates                      Disulfide candidates
  Frame 8 · evaluated · no candidates in this filter
  [Focus disabled] [Hide] [Edit] [Inspect] [Delete]

▸ Stored analyses · 2
```

The summary counts enabled objects separately from geometry actually drawn.
An enabled set can be empty or unevaluated. Show/Hide all changes visual sets
only, without computing, importing or deleting scientific data.

Choose Calculate initially when there are no analyses. When analyses already
exist, choose Stored analysis; do not guess which analysis the user wants if
several are present. Keep local drafts for each source while switching modes.
Every source ends with the same display options and creates one tagged set.

### Creating and using analyses

**Calculate.** Offer Hydrogen bonds and Disulfide candidates. Hydrogen bonds
use Buch, with a visible H···A threshold of 0.23 nm and the sentence "Distance
criterion only; no angular cutoff." Disulfide candidates use S···S, default
0.205 nm and CYS, with "Geometric candidates; molecular topology is unchanged."
Use explicit quantities at the Python boundary; these thresholds are distinct
from visual link radius. There is no engine selector or editable criterion
until another scientific method is implemented and verified.

Require a visible analysis name; a suggested draft name is editable and never
overwrites an existing result. Calculation scope defaults to All atoms and
Current frame. Optional atom scope is a staged selection A; H-bonds also permit
two disjoint selections A/B through the existing provider route. Calculation
scope and display filtering have separate labels: restricting calculation
cannot certify the rest of the molecular system. Structure options are Current
frame, Structure indices and All structures. The index field accepts a comma
list of nonnegative local integers, including nonconsecutive indices; show
its resolved structure count, with 0-based index wording. All structures is an
explicit request with the system's count and a notice that it may take time.
PBC is off by default; the Python API validates every required box when enabled.

At accepted submission, resolve the current frame and staged atom sets once.
Include the accepted frame/scope in the result feedback even if playback has
moved meanwhile. Do not compute again on a frame change. While the synchronous
call is pending, show "Calculating…" and prevent duplicate submission; do not
invent percentages, cancellation or time estimates. Reset neither the draft
nor selection staging after a failed call. On success, show the authoritative
new analysis and set. No analysis is published after a failed calculation.

**Stored analysis.** List `analyses()` names and show compact selected metadata:
types, criterion and quantities, PBC, calculation atom scope, evaluated/total
structure counts and stored observation count. The count is not a persistence
percentage. The primary action is Create set. Reuse the immutable analysis
without a new alignment declaration or recalculation. Mixed/unsupported data
remain inspectable; creating a display requires a supported type/participant
shape, or an explicit supported type filter within a mixed analysis.

**H5MSM file.** Provide File path, Analysis in file and Store as. The path
belongs to the running Python session's filesystem; a browser input's
`C:\\fakepath` must never be treated as a usable Python path. The minimal form
accepts a path and an explicit analysis name; browser upload and automatic
file-analysis discovery need separate public capabilities before being offered.
The file may contain a full system or only interactions. Load just the named
analysis and keep current coordinates. An initially unchecked declaration
says "I confirm matching atom and structure order, coordinates and boxes."
Load & show requires it. A collapsed Source index mapping section exposes
ordered source atom/structure lists for extraction/reordering, including
repeated source structures; omitted lists keep that axis. This does not embed
a subsystem result in a larger system. Dimensions and associations remain
validated by Python. Source labels cannot precheck the declaration.

Calculation/import and visual creation are separate backend steps. If science
succeeds but display creation fails, retain the named analysis and report
"Analysis stored; display could not be created", with its reason and a way
to select it in Stored analysis. Do not silently repeat the calculation or
roll back valid data. Existing-name errors preserve the draft and collection.

### Filtering, styling and inspecting a saved set

The collapsed Display filter & style draft defaults to all participants,
following playback over the analysis's available structures. It permits
an optional set tag and layer. An empty tag uses existing domain allocation;
analysis names and scene tags remain separate. Basic style is colour,
opacity and a radius expressed in nm; links are dashed for both initial kinds.
The prototype's 0.025 nm radius/0.85 opacity are proposed visual defaults,
subject to checking legibility with the renderer.

Use the following readable labels for the public query predicates:

| UI filter | Public mode | Meaning |
| --- | --- | --- |
| All participants | `incident`, all atoms | No atom restriction. |
| Participating in selection A | `incident` | Any participant atom is in A. |
| Internal to selection A | `internal` | Every participant atom is in A. |
| Crossing selection A | `cross` | At least one atom inside A and one outside. |
| Between selections A and B | `between` | Participation in both disjoint sets; optionally confine every atom to A ∪ B with `exclusive=True`. |

Include hydrogen and every atom of a composite participant in these predicates.
Capture A/B with the shared selection dock; later active-selection clicks do
not rewrite a saved filter. Show staged atom counts and require the necessary
sets. Apply filter changes atomically through the public handle. The expanded
editor can also limit displayed structure indices or types from the analysis;
this neither expands calculation coverage nor discards the source result.

A saved card identifies its tag, type, analysis name, filter and layer. Focus
uses the current observed positions, including periodic shifts, and is
unavailable when that frame has no usable positions. Visibility, Edit, Inspect
and Delete follow the existing card patterns. Edit opens tag/layer, filter and
style controls. Scientific thresholds are read-only here: a different criterion
requires a new named calculation. Live colour/radius/opacity edits coalesce
history into one transaction; filters require Apply. Deleting a set is undoable
and keeps its analysis. Changing its tag does not rename scientific data.

Inspect reads details on demand, following Regions' request identity discipline.
Show coverage and atom scope, method, parameters with units, evidence, actual
calculation-time software versions, source maps and PBC convention. Older
unknown versions stay unknown. Current observations show occurrence ID and
participant roles, grouped atom indices, measurements and images. Parallel
observations with the same atoms remain separate. Page the observation list,
initially at 50 rows; never dump the whole trajectory into a panel response.
Reject stale detail replies after frame/system/filter changes. A pick targets
the full `(analysis_name, analysis_revision, occurrence_index)` identity.

### Reporting scientific and graphical state

| Condition | Required card wording/behavior |
| --- | --- |
| Evaluated, supported matches | "Frame 8 · 12 observations · 12 links drawn", using acknowledged renderer counts. |
| Evaluated, no matches in filter | "Frame 9 · evaluated · no matches in this filter"; clear old geometry. |
| Outside evaluated structure coverage | "Frame 10 · not evaluated"; clear geometry, never auto-calculate. |
| Outside calculation atom scope | Show the actual scope; zero queried observations do not establish absence outside it. |
| Outside the display's structure filter | "Frame excluded by display filter"; retain analysis coverage. |
| Hidden by set or layer | Report set/layer visibility separately from scientific matches; no drawn-link claim. |
| Unsupported or partially rendered result | Preserve data; explain unsupported kind, participant geometry or periodic images and state drawn/skipped counts. |
| System edit invalidates coverage | "Analysis invalidated by molecular edit" where the viewer knows that cause; generic unevaluated state otherwise. Offer a new named calculation, not implicit overwrite. |
| Missing/changed analysis reference | Broken reference with a reason; do not silently render stale geometry. |
| No system | "Load a molecular system to calculate or display interactions." Keep any local draft. |

Stored analyses is a collapsed management section with metadata, display
reference count and Use in new set. Its distinct Delete analysis action is
available only without references; state that it clears scene undo before
execution. This explicit deletion is separate from the saved-card Delete.
Display creation/filter/style/visibility are scene undo actions; computation,
attachment and scientific deletion are not scene undo actions. Session and
state restoration follow the analysis-reference/signature contract above.

### Implementing through public Python actions

| UI operation | Public Python route | Availability at this checkpoint |
| --- | --- | --- |
| List/get/query scientific data | `analyses`, `get_analysis`, `query` | Implemented, with compact summaries and bounded observation pages. |
| Calculate | Named family getter, then `add` | Implemented through scientific calculation followed by `add`; current routes are defined in the family API update above. |
| Load file | `load(..., assume_aligned=True)`, then `add` | Implemented through declared load followed by `add`. |
| Create from stored data | `add(analysis_name, ...)` | Implemented. |
| Focus, visibility, Edit/Delete | Public manager/InteractionSet operations | Implemented, including observed-position focus and visual undo. |
| Inspect/pick details | `inspect(tag, structure_index=..., offset=..., limit=...)` | Implemented bounded, paginated current-frame inspection through the live Python session. |
| Delete scientific data | `delete_analysis(name)` | Implemented and exercised with registered visual references. |

Add `InteractionsPanel extends BasePanel`, typed scientific/set/frame/operation
summaries and request-matched detail replies. Python publishes authoritative
summaries; TS owns drafts and presentation. A calculation result and a renderer
acknowledgement are different states. Queries and detail requests create no
history checkpoint. Commands use the existing action manifest, envelopes and
public-API handlers; no chemical calculation or open-coded filtering in TS.
Bound caches and inspection payloads; do not repaint hidden panels or copy
occurrence arrays on each trajectory update. Keep focused inputs and staging
stable during visible frame-status updates.

Static HTML follows the existing shell notice: panels remain readable, and
mutation attempts are answered by the established no-session seam. Embedded
geometry supports playback without new Python computation. Scientific inspector
pages require a live Python session; static exports do not embed the complete
scientific observation table. Popups/reconnect use the canonical summaries.

Remove Shapes' current "Hydrogen Bonds (H-Bonds)" calculation entry once the
native Interactions/Calculate route works. Keep Python's
explicit geometric H-bond link primitive for already computed shapes. The
present Shapes action claims calculation while its handler omits required
`structures`; do not retain two UI actions with inconsistent scientific meaning.
Persistence timelines, percentage filters, contact analytics, external formats,
additional criteria and background playback calculation remain post-1.0.

Acceptance requires real Python/Studio parity for all three entry routes,
multiple displays of one analysis, nonconsecutive and empty coverage, failed
import/calculation without draft/data loss, visibility/layers/focus/PBC,
parallel picking, visual undo, deletion reference guards, session/HTML/popup
restoration and bounded detail delivery. The mockup is not validation evidence.

## Why

`view.shapes.links.add_hbonds(structures=...)` accepts already-computed
donor/acceptor pairs and draws them. Its shape record does not preserve the
full chemical result, method, or parameters as an interaction domain object.
The MolSysMT provider proposal supplies a compatible scientific ownership
boundary without requiring the viewer to duplicate chemical perception.

## What was refuted

- Treating all future interactions as atom pairs loses hydrogen-bond roles
  and cannot naturally represent group participants or mediated relations.
- Treating S–S proximity as an authoritative covalent bond would erase the
  distinction between an inferred candidate and topology connectivity.
- Advancing the full post-1.0 UI or updating Mol* as prerequisites would
  widen the 1.0 release gate beyond this bounded slice. The dependency
  update is tracked in `uibcdf/molsysviewer#115`.

## Acceptance criteria

1. The shared MolSysMT result boundary and the viewer adapter are documented
   with real single-structure, variable-count multi-structure, empty-result,
   nonconsecutive-index, and large-trajectory examples.
2. Python and Studio operate on the same named scene sets, including empty
   evaluated frames, visibility, layers, deletion, and frame changes.
   Existing-data display, explicit independent H5MSM import and named
   calculation all use the authoritative `view.molsys.interactions` store,
   without requiring MolSysMT addon registration.
3. Replay, static HTML export, and molecular-system edits follow explicit
   scene contracts; trajectory coverage and memory use are measured, and the
   browser renderer is exercised against real Mol*.
4. Public documentation says which H-bond criterion and disulfide evidence
   each supported creation path uses. The Shapes H-bond claim is reconciled.
5. The 1.0 release candidate is recertified after the new code lands.
6. State-only import rejects missing or changed analyses atomically; a
   session preserves multiple named analyses and all visual fields. Scene
   undo does not duplicate scientific arrays or delete calculated results.

## Resolution

Implemented experimentally in the working tree. Provider-release and
representative workload qualification remain pending.


## Native scene and Studio implementation (2026-09-30)

The working tree now implements `InteractionsManager.add`, the canonical scene
collection operations and `InteractionSet` filter, style, visibility, layer,
tag and focus methods. The tagged domain is `interaction`; it does not collide
with identically tagged annotations or shapes. Named analyses remain in
`view.molsys.interactions`, independently of their visual references.

`js/src/ui/panels/interactions-panel.ts` extends the same BasePanel as the other
subpanels. It is registered after Measures, before Shapes, and reuses the
selection dock. Calculate, Stored analysis and H5MSM file forms dispatch
through public Python workflows. Calculation labels state Buch's H–A distance
criterion and geometric disulfide candidates. File paths address the Python
session, with an unchecked alignment declaration and optional ordered source
maps. Creation is correlated, disables duplicate submission, and retains a
successfully stored analysis if visual creation then fails.

Saved cards provide Focus, Show/Hide, Edit, Inspect and Delete. The inspector
pages current-frame scientific observations, including unsupported composite
participants, units, evidence, periodic images and unique occurrence indices.
Request identity, frame and analysis revision reject stale inspector answers.
The stored-analysis section gives metadata/reference counts and refuses to
delete referenced data. The misleading H-bond calculation entry in Shapes has
been removed; explicit Python pair primitives remain available.

Differences from the layout draft are deliberate: initial sets use the default
green style; color, opacity and radius are edited through an Apply form. Each
Apply is one undoable operation, with validation before mutation. No live
style sliders were added. The independent synthetic HTML prototype remains a
design artifact; it is not the runtime subpanel.

Python projects only the requested frame during live playback. The native
Mol* mesh uses dashed cylinders, with one geometry group per supported
occurrence. Observed periodic H and A positions are shifted relative to the
donor, using the frame's row-vector box convention. Picking carries the analysis
name, content signature, frame, occurrence index and participant atoms.
Stale frame/revision replies cannot replace newer geometry. Previous-frame
geometry is hidden immediately; no Python calculation is triggered by playback.

State v2 gains optional `interaction_state_version: 1` and `interactions`
references. A different scientific signature is rejected before scene clearing.
Complete scientific results remain in the session H5MSM payload. Damaged fixed
selections survive extraction as broken objects and can be explicitly repaired.

Bounds are explicit: 50,000 observations and 8 MiB of serialized geometry per
set/frame; 200 observations per public inspection page (50 in Studio); 64 MiB
for compiled static interaction export. Exceeding a live bound gives
`render-limit`; exceeding the export budget raises. Static projection currently
repeats geometry for overlapping sets. Shared analysis compilation and public
file-backed queries remain optimizations to decide with joint measurements.

### Verification ledger

- Real pentalanine axes and public MolSysMT results cover parallel H-bond
  occurrences, unsupported rings, empty and unevaluated frames, sparse filters,
  observed triclinic periodic positions, scene/session fidelity, domain tags,
  history, declaration gates and damaged-filter repair in
  `tests/test_interactions_scene.py`.
- The Chromium/Mol* suite `interactions-subpanel.e2e.ts` covers native panel
  rendering, geometry units, dashed links, parallel group identity, inspection
  and visibility through the real Python bridge, stale frames, static playback,
  file declaration controls and correlated creation.
- Guard mutations removed the state signature check and relative periodic
  origin; both were killed by their targeted tests. Removing damaged-filter
  marking made the real extraction regression fail when a summary queried the
  removed atom index. Original source bytes were restored in every case.
- The issue remains partial until representative combined residency/query
  measurements and the supported published provider revision are qualified.
  Local gate results follow; these do not certify a released provider.

### Observed local gate results (2026-09-30)

- `tests/test_interactions_scene.py`: **14 passed** on the final Python scene
  implementation, including explicit radius units, real calculation/file
  creation and validation before mutation.
- `npm run test:js`: **294 passed**, no skips, on the final TypeScript sources.
  `npx tsc --noEmit`, targeted Ruff checks and `npm run build:runtime` passed.
- `npm run test:e2e:core`: **35/35 browser suites passed** before the final
  localized unit/form checks. The final `interactions-subpanel.e2e.js` passed
  again with those checks, including inactive-form fields, invalid import maps
  and explicit radius units. The bridge imports its private serialization helper
  only after initializing the real viewer, avoiding a partial scene import.
- Browser guard mutations removing radius-unit validation and stale-frame
  rejection both failed the native suite as intended. Sources were restored
  before the final positive run and runtime build.
- `npm run test:perf` passed. The existing message-path workloads measured
  95,000 atoms loaded in **3,251.5 ms**, unknown-message handling in **0.30 ms**,
  hide handling in **0.20 ms**, and **0.000619 ms/frame** for the 1,000-frame
  dynamic-region workload. These are existing protocol workload observations,
  not representative interaction residency/query measurements.
- The full Python suite was run once: **2,212 passed, 18 skipped, 4 failed**.
  Three failures are real Qt worker crashes at `_import_qt`, tracked by
  `uibcdf/molsysviewer#109`. The fourth was the E2E inventory's old suite count;
  it was corrected from 37 to 38 and the targeted reliability/reporting
  selection then passed **130 tests**. The full suite was not rerun; it remains
  unqualified because of those Qt crashes. No Qt environment workaround was
  introduced by this implementation.


## Review corrections and measurements (2026-09-30)

The authorized review corrections are implemented in the working tree:

- Real Mol* picks normalize to the interaction domain. Context deletion/focus
  uses its public actions and leaves same-tag shapes and measurements intact.
- Inspector replies carry a filter/query revision in addition to the analysis
  signature. A same-frame filter change invalidates prior rows and late replies.
  Excluded frames return no observations; calculation scope is a compact summary.
- The adapter counts selected occurrences before the provider codec, then applies
  a conservative numeric-copy preflight. A 50,001-observation fixture is refused
  without calling `to_dict()`, demonstrated with a real-call profiling guard.
  Inspection replies have a 512 KiB budget and explicit compound-detail bounds.
  Oversized metadata reports its omission without changing the complete analysis.
  Public provider occurrence pages are requested in `uibcdf/molsysmt#264`; this
  fallback does not claim to bound complete-analysis or process memory.
- Basic viewing works against the real published MolSysMT 0.22.4 package, which
  lacks the experimental backend. Scientific creation reports compatibility
  explicitly; Studio receives feature availability. The reproducible probe is
  `devtools/interactions_provider_compatibility.py`. There is still no qualified
  published provider version for this feature; the base-view dependency floor
  is not a claim that Interactions ships in that version.
- Changing Between to Incident clears effective exclusivity. Native details
  sections retain their open state while changing the form; queued toggle events
  from detached elements cannot overwrite it. Render-limit wording includes both
  count and byte preparation budgets. Direct details-element references preserve
  this behavior without depending on incomplete unit-test DOM query emulation.
- Per-set lifetime tokens prevent a deleted set from reappearing after an awaited
  Mol* write. The browser test deletes through a real object-created event during
  the write and asserts that neither a registered ref nor an orphan mesh survives.
- A user concept page and executed notebook cover scientific calculation,
  stored analyses, local nonconsecutive indices, display filtering, declaration
  of named independent H5MSM import and session preservation. Current architecture
  and addon direction now describe the implemented native workflows.

### Scientific/runtime evidence

The source provider was at `a04a5e7aad508b0a50ca9f22043f8ca6084411c8`, with
independent dirty provider work explicitly preserved. Six fresh-process combined
coordinate/interaction measurements are recorded in
[the performance observations](../interactions_performance.md). Warm sparse
atom/frame queries took approximately 0.4–1 ms, while initial index construction
reached 647 ms with many new relations. Approximately 230 MiB of coordinates
corresponded to about 984–1,070 MiB of loaded process RSS. These synthetic adapter
observations do not certify realistic detector workloads, GPU throughput or a
released backend.

The Python materialization/metadata budget guards and the browser domain,
query-revision and render-lifetime guards were individually removed. Their real
focused tests failed in all five cases. Exact original bytes were restored in
finally blocks; the browser harness was rebuilt. The original details-toggle
failure also exercised the complete form before the production correction.

### Final local verification for the review fixes

- Focused scientific/scene/public-API selection: **68 passed** (18 scene tests).
- One full Python run using Python 3.14 and canonical PySide6/Qt 6.11.2,
  outside the sandbox with matching `CONDA_PREFIX`: **2,217 passed, 20 skipped,
  no failures**. This replaces the older local full-suite failure as current
  working-tree evidence; it does not count omitted real-window/GPU scenarios
  as validation.
- Final JS unit run: **294 passed**, no skips. TypeScript `--noEmit` passed.
- Final core browser lane: **35/35 passed**, including calculation, named H5MSM
  import, stored-data creation, same-tag domain deletion, stale-filter inspection,
  filter mode changes and deletion during rendering in the native Interactions case.
- The tutorial executed through `docs/execute_notebooks.py`; widget state was
  stripped by the tool. Sphinx built the new pages, but emitted seven existing
  public-reference warnings. A fresh-process `import molsysviewer.shapes` reproduces
  the reported circular import. These findings have their own report in
  `uibcdf/molsysviewer#117`; the overall documentation is not claimed warning-free.
- `npm run test:perf` passed: the existing 95,000-atom protocol fixture loaded
  in 3,357.9 ms; unknown/hide handling took about 0.20 ms, and the 1,000-frame
  dynamic-region probe took 0.000708 ms/frame. These are protocol regressions,
  not interaction residency measurements.
- Targeted Ruff checks and `git diff --check` passed. The runtime was regenerated
  from the final TypeScript sources with `npm run build:runtime`.

#114 remains partial for published-provider and exact-candidate qualification,
plus realistic scientific/GPU workload evidence. The provider paging request
and reference cleanup have explicit owners; no private provider-index adapter
or dependency upgrade was introduced.


### Public-reference closure after the review

The additional reference defect `uibcdf/molsysviewer#117` was corrected before
stopping for the agreed design review. Leaf-module imports no longer initialize
the viewer facade eagerly; the authored reference drops retired facade APIs,
includes Interactions and repairs the stale labels-page link. Cold imports and
all reference entries resolve in fresh processes. Three guard mutations failed
as intended. Sphinx regeneration followed by `make -C docs html SPHINXOPTS=-W`
passed without warnings. One required full Python run for that separate entrypoint
fix passed **2,235 tests, 20 skipped, no failures** with canonical Python 3.14/
Qt 6.11.2. Final inventory/reporting checks also passed **336 tests** before that
closure. The actual published 0.22.4 ordinary-view compatibility probe passed again.

The earlier seven-warning observation remains evidence of discovery, not the
current documentation state. Resolution and addressable guards are retained in
[the archived report](../archive/public_api_reference_stale_entries_and_cold_imports.md).

## Real scientific qualification and publication boundary (2026-09-30)

The [qualification record](../interactions_qualification.md) reports four
real/controlled scientific workflows, the complete 5,000-frame pentalanine
detector measurement and actual calculated-link Mol* geometry before/after
session restoration. `tests/test_interactions_qualification.py` guards the
scientific distances, queries, persistence, periodic reimaging and candidate
topology preservation. The existing browser suite includes the scientific
fixture without adding a new lane or replacing its domain/Studio checks.

The public channel still provides MolSysMT 0.22.4, which lacks this backend.
Its real compatibility probe passes for ordinary viewing and explicit refusal
of scientific creation. Keep #114 partial and the feature experimental. A
provider release containing the agreed `uibcdf/molsysmt#250` APIs is required
before installed-provider qualification and the feature dependency floor can
be settled. No dependency floor, provider code or issue prose was changed.

## Installed public-dependency boundary (2026-10-01)

The [installed artifact record](../installed_artifact_qualification.md) adds
the current wheel with public MolSysMT 0.22.4 and support packages in a fresh
Linux/Python 3.14 environment. Seven load, 108 selected public-workflow and
eight actual offline Chrome HTML tests pass. Both molecular libraries import
from site-packages; no sibling checkout substitutes for the provider. The
installed compatibility probe passes ordinary views and explicit refusal of
unsupported scientific creation. This does not close #114 or set a feature
dependency floor. Test collection imports are tracked separately as
`uibcdf/molsysviewer#131`. Public documentation remains deferred.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).

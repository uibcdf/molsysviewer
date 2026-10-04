---
summary: Define batch and progressive loading of multiple molecular systems
issue: uibcdf/molsysviewer#151
status: partial
opened: 2026-10-03
closed:
verification: measured
area: [load, api, studio]
guard:
normative:
blocked_by: [uibcdf/molsysmt#312, uibcdf/molsysmt#313, uibcdf/molsysviewer#157]
supersedes: []
---

# Define batch and progressive loading of multiple molecular systems

**Reported:** 2026-10-03, final pre-1.0 design review and principal-maintainer authorization.

## What

Discuss and resolve how users load four PDB files, four PDB IDs or mixed MolSysMT-compatible forms at once, and how they load one followed by additional systems to work with all of them together.

## How

Review existing load(mode='add'/'append_structures'/'auto'/'replace'), MolSysMT input-list semantics, load blocks and scene identity. An input list can describe complementary forms of one system; do not silently reinterpret every list as independent systems.

## Why

Principal maintainer request, 2026-10-03. The public interface needs explicit meaning for independent systems combined in one scene versus alternate structures of a shared topology, and consistent batch/progressive behavior.

## Acceptance

Agree Python and Studio entry points; system/load identifiers, provenance and index maps; same/different topology handling, atom correspondence and alignment policy; independent visibility/selection; structure-count/time/cell compatibility; interaction analysis naming and intra/inter-system calculation scopes; batch failure atomicity versus explicit partial success; mixed/remote input failures and memory limits. Decide the minimum before 1.0 and explicitly defer larger multiple-independent-system architecture. This issue records design work, not a new implementation promise.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Design questions to settle

The principal maintainer requests this discussion before the API freezes. The current progressive `view.load(source, mode="add", label=...)` combines systems into one MolSys with load blocks/regions. `append_structures` addresses another intention. The accepted entry decision below keeps one `view.load` with explicit `multiple=True` for independent sources. Lists of complementary topology/coordinate forms retain their existing one-system meaning. Do not let `auto` infer independent copies versus conformations merely from matching topology.

Agree examples for four files, four IDs and mixed forms; equivalent progressive/batch results; stable source/load identifiers and local/global index maps; repeated chain/residue IDs; independent selection/visibility; topology/atom-order validation; explicit alignment; frame counts, time, cell and broadcasting rules; analysis naming and intra/inter-system scope; acquisition errors, atomicity/declared partial success and memory budgets. Decide the bounded composite-MolSys minimum separately from any independent-system architecture. No new facade is implemented by this record.

The execution order and maintained decision context are in `devguide/final_design_closure_20261003.md`.

## Resolution

Loading preparation/composition, source persistence/remapping, controlled
box assignment and Studio loading controls are implemented locally. Integrated
qualification remains open. Evidence is recorded below; this issue is not ready
to close.

## Concrete proposal for discussion — 2026-10-03

**Entry spelling superseded by the accepted decision below; remaining scope is
still proposed.** Use the existing composite MolSys. Batch and progressive
loading should share preparation, validation and commit operations. With
`multiple=True`, the outer batch list means independent systems; each entry may
itself be a complementary group of forms describing one system. Preserve the
current one-system meaning of lists accepted by `new_view`/`load` otherwise.

The first supported case should be independent single-structure systems: four
PDB files, four identifiers resolved through MolSysMT, or compatible input forms,
including a declared selection of one structure from a multi-model input. No
automatic structural alignment is implied; retain submitted coordinates. Return
or expose detached source/load records with stable IDs, labels, origin form and
local/global atom correspondence. Regions may represent their independent
selection and visibility; they must not substitute for scientific source identity.
Agree preservation through session save/load and extraction before promising it.

Prepare every input and the composed system before committing a batch. On
conversion, acquisition, compatibility or naming failure, preserve the existing
scene and publish no batch success. Progressive additions commit individually.
Do not implement a batch by repeatedly calling the currently mutating public
`load` if that would leave half the sources attached after an error. Memory
budget checks must account for old coordinates, prepared sources and the composed
candidate, with no second long-lived coordinate store merely for provenance.

Multi-frame composition must be a separately explicit extension: validate frame
counts and the declared frame correspondence and time. The maintainer's proposed
cell policy below replaces the earlier reject-on-cell-disagreement suggestion.
Do not broadcast a static structure over a trajectory implicitly. Appending conformations
remains the separate `append_structures` intention and requires declared atom
correspondence. A multi-system object graph with independent trajectories,
periodic cells, players and removal/reordering is a larger architecture that
should be evaluated separately for post-1.0.

### Accepted single entry — 2026-10-03

The principal maintainer accepted retaining a single `view.load()` and explicitly
distinguishing independent sources through `multiple=True`. The default is
`multiple=False`, preserving existing single-system and complementary-form
semantics. No `load_many()` is introduced. The implementation and qualification
records below deliver this choice, including explicit multi-frame composition;
the earlier single-structure limit was not retained.

```python
view.load("first.pdb")
view.load("second.pdb")
view.load(["first.pdb", "second.pdb", "ligand.sdf"],
          multiple=True, labels=["Protein A", "Protein B", "Ligand"])
view.load(["topology.prmtop", "trajectory.xtc"])
```

`multiple` specifies how to interpret the input; `mode` specifies its operation
on the current system. Equal topology does not identify the user's intention to
combine independent copies versus append conformations. New independent-source
batch loading must not infer that intention from topology. The initial proposed
batch operations are `add` and `replace`, with preparation and validation before
commit; existing one-system `append_structures` remains distinct.

The structure-axis scope, shared/per-source selectors, labels, durable maps,
box ownership and region visibility now have implemented contracts in
`architecture.md`. Studio expresses the same input and operation intentions.
The local slices are recorded below; integrated/artifact qualification and the
partial-H5MSM provider boundary remain open.

### Source evidence and provider boundary

Inspection of the controlled MolSysMT source `396e6979f` shows that
`molsysmt.basic.merge` already supplies per-source selections/structure indices
and conversions. Native `Structures.add` requires equal structure counts, keeps
the target's time/structure axis, and warns while retaining the target cell on
box disagreement. The Viewer should express the agreed stricter user intention
before calling the provider rather than invent another scientific merge engine.

Native `MolSys.add` refuses an incoming system with named analyses without an
analysis-merge policy. Viewer `tools.merge` also refuses named analyses. Therefore
supporting arbitrary H5MSM/MolSys sources requires agreement with MolSysMT about
analysis embedding, naming, atom/structure maps and evaluated scope; it cannot be
promised by adding a list wrapper. Reject unsupported preservation explicitly
before mutation, and distinguish later intra-source queries from newly computed
inter-source analyses. Carry this provider question through uibcdf/molsysmt#250
after settling the Viewer contract; no cross-team message has been sent here.

The public `load_blocks` method in `viewer/core.py` returns a deep copy; the
earlier outer-copy observation described the overridden mixin property, not the
effective public implementation. Sessions still collapse load accounting.
Durable source identity remains acceptance work. These are source observations;
no multi-source qualification is claimed by this note.

## Detailed bounded contract candidate — 2026-10-03

**Loading, source-transfer, controlled-box and Studio slices implemented locally;
integrated qualification remains open.** The principal maintainer authorized proceeding with the
single `load` entry and the proposed execution order. The implementation record
below states what is tested; this complete candidate does not itself establish
complete installed candidate or a hard memory ceiling; executed Studio and
acquisition evidence is recorded in the latest local slice below.

### Input interpretation and selectors

Keep existing positional parameters and add keyword-only `multiple=False`,
`labels=None` and, provisionally, `structure_pairing=None`. All public additions
use the existing ArgDigest adapter and `skip_digestion` convention. New argument
validation must also protect the body when digestion is explicitly skipped.

With `multiple=True`, require a nonempty list/tuple of independent source items;
an item may itself be a complementary list/tuple for one system. Do not flatten
the outer list or infer multiple systems from identical topology. Initially
accept `mode="add"` and `"replace"`; reject batch `auto` and `append_structures`
before acquiring/converting sources. The legacy single-system modes remain
separate. An empty atom or structure selection is not a successful source load.

`label` names the composed load/scene as it does today; `labels`, when provided,
has one string/None per input source. Reject count mismatches and `labels` with
`multiple=False`. Source labels may repeat; their IDs must not, and generated
region tags resolve collisions deterministically. Explicit labels take priority;
any fallback from a file/identifier is presentation, not identity.

For batches, strings/flat integer collections remain shared selectors. A list
of selection expressions or nested atom-index collections explicitly supplies
one atom selection per source; nested frame-index collections supply one
structure selection per source. For example, `[0, 8, 3]` selects those frames
from every source, while `[[0], [8], [3]]` selects one frame from each of three
sources. Validate source counts, bounds and integer types without guessing from
list length; preserve frame order. This context-dependent extension is scoped
to explicit `multiple=True`, preserving one-system input behavior.

### Structures, correspondence and time

Permit one selected structure per source, including selection from multi-model
files. Also permit multiple selected structures when counts agree and the caller
explicitly declares `structure_pairing="by_index"`: selected structure k of each
source corresponds to structure k of whole. For progressive addition, the
destination's current structure axis is fixed; the incoming selected sequence
must match it. The initial load of a trajectory does not itself compose systems.

Do not broadcast, truncate, resample, align coordinates or concatenate frame
axes. Keep source-to-whole frame correspondence, including nonconsecutive and
reordered selections. If two sources have times, compare their selected times
with explicit unit normalization before accepting the pairing; incompatible
times fail rather than silently borrowing the first clock. Define and test the
numerical comparison tolerance in implementation. Missing time does not become
fabricated time: correspondence then relies on the explicit index declaration.
Whole retains the first/destination time axis, including absence of time; it
does not adopt a later source's times. The loading slice implements this policy
with comparison in ps and `rtol=atol=1e-9`.

### Durable source identity and regions

Extend the existing load-record owner instead of introducing another molecular
system store or a second public loader. Each successful source occurrence has
a stable ID, label, origin form/reference and original-source-to-current-system
atom/structure correspondence. Loading the same file twice creates two distinct
occurrences. Origin references describe provenance; they do not authenticate
source identity or require the original file to reopen a session.

Keep maps compact: contiguous loads can use intervals/runs, while extraction or
reordering may require explicit sparse index arrays. Never allocate atom-pair
matrices or retain another coordinate trajectory for provenance. Detached
`load_blocks` records must not expose mutable internal mappings. Store scientific
source metadata separately from editable region tags, linking the generated
region by its stable UID. A rename, hide or deletion of that region does not
erase or redefine its source; adding a later source does not recreate a region
the user deliberately deleted.

One initial source needs no generated region. At the second source, create base
regions for both; later sources receive one region each. Batch and progressive
loading have equivalent scientific composition, source accounting and initial
region membership, apart from generated IDs and any intervening user edits.
Repeated author chain/residue IDs do not collapse internal hierarchy indices.
No inter-source covalent bond is invented by composition.

Session save/load, copy and extraction retain surviving source identities and
remap both axes; sources with no surviving atoms can be omitted from the derived
system's source inventory. A state document applied to a different molecular
system must not replay unverified source maps. An external topology edit without
trustworthy atom correspondence cannot silently preserve the old accounting.
Define explicit invalidation and source-ID collisions in the existing scene
merge tool before claiming complete source-ledger coverage.

### Candidate preparation and scientific analyses

Prepare source conversions, selected maps, naming, frame/time checks and the
composed candidate before publishing it to the active view. Conversion,
acquisition, validation or analysis-policy failure leaves the current MolSys,
scene, history and source records unchanged. A batch has one commit; separate
progressive calls commit separately. Reuse MolSysMT conversion/addition/merge
operations; Viewer owns loading intent and scene/source bookkeeping.

Do not use native merge on named analyses: the inspected MolSys merge adapter
does not carry them. Native add rejects analyses on its incoming source, while
extending the destination analysis atom domain with explicit evaluated-universe
metadata. Until an incoming-analysis embedding policy is agreed, refuse those
unsupported additions before scene mutation. A single ordinary load of a system
with analyses remains supported. Existing destination analyses must not disappear;
preserve the current explicit geometry-invalidation policy rather than claiming
that old evaluation covers new atoms or new inter-source interactions. Any future
intra-source preservation policy belongs in coordination with uibcdf/molsysmt#250.

The composed candidate and temporary inputs contribute to peak memory. Apply the
existing scale diagnostics to the combined dimensions and account for temporary
residency when measuring; do not claim a bounded process footprint from the
current coordinate-wire warning. No new hard memory ceiling is proposed here.

### Implementation order and guards

1. Resolve this candidate's remaining selector, pairing/time and source-record
   decisions, then implement reusable preparation and source-map operations in
   the existing loading owner, with consumers sharing them.
2. Add the `multiple` route and reconcile progressive composition; protect
   failed additions/replacements before any scene/source change.
3. Preserve source records through session, copy, extraction and announced edits;
   qualify region rename/deletion, overlapping base visibility and isolation.
4. Add controlled box assignment from quantities or a declared source form,
   preserving the agreed first/current-box policy and scientific invalidation.
5. Reflect the same load intentions in Studio; document the public workflows
   after the code contract is closed, as requested by the maintainer.

Guards must cover batch/progressive equivalence with real demo-derived inputs,
mixed supported forms, one versus several selected structures, reordered frame
maps, time units/mismatch/missing time, absent/replaced boxes, repeated identifiers
and labels, named-analysis rejection/preservation, failure of a later source,
session and extraction, and callers requesting `skip_digestion=True`. Test PDB-ID
acquisition separately from deterministic local composition. No test or browser
qualification of a Viewer batch implementation is claimed in this planning step.

### Executed provider probe

`multiple_system_loading_probe_20261003.json` records a probe on real
`pentalanine`-derived MolSys objects in `molsyssuite@uibcdf_3.14`, provider HEAD
`e8e4fff22d0df0d26a3b91d80ea5a85c04981aef`. Three selected structures from each
source combine without coordinate alignment/reordering; the target's box remains
absent or retained as submitted, and a three-versus-one count mismatch raises.
Native add accepts different source times while retaining the target clock. This
is its atom-addition contract, not evidence of physical time correspondence.

Native MolSys.add already prepares candidate topology/structures before committing
the native object. The earlier observation that Viewer calls it in place is not
a claim that this provider primitive has a demonstrated partial-mutation defect.
Viewer batch atomicity still requires preparation of every source and scene/source
commit beyond that one native operation. The probe does not qualify a Viewer
loader, a published provider, PDB-ID acquisition or a memory/time ceiling.

## Accepted visibility slice — 2026-10-03

The principal maintainer authorized implementing region visibility independently
of the remaining batch-loading discussion. A region without a representation
can hide its atoms on whole only; represented regions retain independent
visibility. Overlapping base constraints compose, showing a base region does
not show a globally hidden whole, and hidden flags survive representation
changes. Layer actions delegate to the same operations. No region may use this
operation to hide atoms on another region's representations or scene overlays.
The normative contract is `devguide/scene_contracts.md` §A.3. This slice is
implemented locally and does not close #151. Python, renderer and Studio guards
cover independent visibility, overlapping constraints, whole visibility,
Own/Inherit/None transitions, dynamic membership, deletion, focus fade,
bulk/layer actions, state/session, history and rebuild. The obsolete
`RegionWithoutOwnVisualWarning` and its catalog entry are removed, because valid
base-region visibility no longer warns. Both region E2E suites and all 314 JS
cases pass; TypeScript and rebuilt source-runtime version validation pass.
After the once-run full regression exposed that unused warning and 22 sandbox
failures, 175 affected/catalog cases pass (14 placeholder-template skips) and
all 22 infrastructure failures pass outside the sandbox. There is no second
full-suite claim or new installed-wheel qualification. Commands, boundaries
and retained logs are in `devguide/region_visibility_20261003.json`.
### Explicit isolation follow-up

The maintainer chose to isolate a base region through whole, activating whole
when necessary and hiding other regions. This is distinct from ordinary
show/hide. Implementation now records the selected region through the additive
`show_only` field, validates it before import, and restores the mask without
repeating the visibility side effects. Rename, copy/extract, rebuild and dynamic
membership retain the selected region; normal visibility actions release
isolation. Dynamic recipes that currently select no atoms survive restoration
and rebuild, retaining isolation until their atoms reappear. The redo guard
also corrected restoration of an explicitly visible whole. The normative rules
are `scene_contracts.md` §A.4. Fifteen Python guards, the real-Mol* region browser
suite, all 314 JS cases, TypeScript and rebuilt runtime validation pass locally.
The once-run full Python regression passed 2,658 cases with 23 skips before the
last empty-dynamic preservation fix; the subsequent scoped check and boundaries
are recorded in `devguide/region_isolation_20261003.json`. No batch facade, new
box assignment, installed-wheel qualification or publication is implemented by
this slice; #151 stays open.

## Cell direction from the maintainer — 2026-10-03

Composition uses the first source's box if present; if absent, later sources do
not introduce boxes. Atom additions retain the destination MolSys's current
box, including any later explicit replacement/removal. This direction does not
solve frame correspondence and implies no wrapping, alignment or rescaling of
coordinates. MolSysMT supplies box extraction through `get(..., box=True)` and
assignment through `set(..., box=...)`; a controlled Viewer operation must also
synchronize the scene and scientific invalidation. No new Viewer box-assignment
API is implemented by the visibility slice.

## Local composite loading slice — 2026-10-03

Implemented in `viewer/load.py` with reusable private preparation/composition and
compact source-map operations in `loaders/_composition.py`. `load` retains its
existing positional arguments, digestion and explicit bypass, adding keyword-only
`multiple`, `labels` and `structure_pairing`. Independent sources use `add` or
`replace`; complementary forms retain their previous meaning without `multiple`.
Flat selectors remain shared even when their length equals the source count;
nested selectors are per-source. Boolean, fractional, negative, empty and
out-of-bounds index selections fail before scene mutation, including with digestion
bypassed and with another selection syntax. Labels may repeat.

Every source is converted and validated before candidate composition. Pairing
and selected time compatibility are checked before copying the active destination;
the entire composition happens on a detached MolSys. Invalid later files,
unsupported incoming analyses and incompatible structures/times preserve the
active system, scene, source records, messages and history. Existing query recipes
are preflighted on the candidate. This establishes preparation-failure atomicity;
it does not promise rollback after arbitrary frontend or unexpected runtime errors
during scene commit. Appending structures now also prepares a separate candidate.

Source occurrence IDs and run-encoded atom/frame maps are independent of region
tags. Detached records follow the generated region's UID through rename/deletion;
later additions do not recreate a deleted source region. A first individual load
creates no base region; the second backfills both, and four batch/progressive
sources produce equivalent scientific composition and region membership. Existing
destination analyses survive with geometry coverage invalidated; the original
analysis object is unchanged. Incoming analyses during composition are refused
until explicit embedding semantics are agreed with uibcdf/molsysmt#250.

The 41 final Python guards pass. Forty-nine existing load/rebuild/plot/API checks
passed before the final selection-digester hardening. The once-run full regression
passed 2,696 cases with 23 explicit skips (433.94 s), collected before those four
additional malformed-selection guards and that hardening. Final scoped digestion
and loading verification supplements that run; no second full run is claimed.
The real-Mol* `composite-load` browser suite verifies rendered coordinates for four
translated demo copies, equivalent batch/progressive composition, four base regions
and whole-only masking of the chosen source. It is registered in the core runner.
TypeScript and source hygiene pass. Exact evidence is retained in
`devguide/composite_loading_20261003.json`.

The follow-up below implements record transfer and source-ID handling in merge.
The later controlled-box slice below supplies assignment. Still open: Studio loading and separate
qualification of PDB-ID acquisition and memory/time goals.
Temporary conversions/candidates are not a hard memory ceiling. Provider structural
attribute/cell diagnostics remain visible. This is local source qualification in
`molsyssuite@uibcdf_3.14`, with the experimental editable MolSysMT checkout; no new
wheel, committed candidate, push, published-provider or standalone claim is made.

## Local source persistence and transfer slice — 2026-10-03

State v2 now carries `sources`, extension version 1, with compact occurrence
records and a separate system-content binding. Session, copy/extraction and
history restore those records, including deleted source-region links and
nonconsecutive/repeated frame selections. Sources with no surviving atoms drop
out; frame remapping visits selected indices through the sparse runs rather than
expanding a complete original index axis. Atom bounds enclose actual membership;
generated regions use the map, so separated runs do not select intervening atoms.
Merge retains distinct occurrences and, on repetition, creates a new ID with
`parent_source_id`, remapping both source/region links. First-source global
isolation remains authoritative when combining scenes.

The binding hashes topology, counts and ordered coordinates/time/box in canonical
units using bounded chunks. It is cached across scene operations and invalidated
by announced molecular edits; MolSysMT quantity wrappers cannot be cache markers
because a property read may return a new wrapper. It checks content correspondence,
not authenticity of the recorded original path. Ordinary state import retains
destination records on mismatch, on absent extension and for overlay-only
`clear_first=False`. Sessions refuse a binding mismatch before replacing an open
destination. The topological scene fingerprint remains separate and portable.

Explicit atom edit maps are checked for bounds/injectivity before mutation and
remap source records. Unmapped new atoms carry an explicit current-system origin.
Changed atom counts without correspondence collapse accounting; changed structure
counts clear frame maps as `unverified`. Equal counts declare unchanged index
order; extraction is the explicit frame-subset/reorder operation. Native
`load(mode="append_structures")` preserves the known prefix but gives old sources
no invented original-frame indices for added frames. Source maps can therefore
have declared partial frame coverage.

The public H5MSM 0.5 writer preserves submitted precision and analyses. Legacy
0.4 conversion requests double precision; that fallback is inspected, not
installed-provider qualified here. The failed attempt to pass `float_precision`
to current default conversion was refuted: 0.5 rejects that option, so the
consumer now uses its public writer directly.

All 22 new guards and 169 affected Python cases pass. The extended real-Mol*
composite browser suite checks session reopening, extraction, rendered coordinates
and source-region visibility; TypeScript and source hygiene pass. The once-run
full regression was interrupted in native HDF5 close, exit 139, while the root
temporary filesystem had no free space. Its 284 MB of failed-run temporaries were
moved, without deletion, to the repository filesystem. The 30 cases in the crash
file pass there with a task-specific temporary directory; this is scoped recovery,
not a second full run or a passing complete regression. Full/integrated candidate
qualification remains pending. Logs and exact source hashes are in
`source_records_20261003.json`.

The reproducible `devtools/benchmarks/source_records.py` measurement on a real
124-atom, 5,000-structure, two-source demo gives 855 bytes of source metadata,
77 ms cold hashing with allocation tracing, 0.035 ms median cached access over
20 samples, and about 1.03 MiB additional traced Python allocations. Coordinates
were already resident. These observations are not total RSS, a supported-system
ceiling or session-I/O throughput. Controlled box assignment and Studio parity
are the next implementation slices. #151 remains open; the existing unrelated
worktree and provider work are preserved and no publication is claimed.

## Local controlled-box assignment slice — 2026-10-03

`view.set_box` accepts a unit-bearing row-vector cell or an explicitly declared
MolSysMT-supported source; cell extraction uses public `get`, assignment uses
public `set`, and scene reconciliation uses `apply_system_edit`. It requires
finite, nondegenerate right-handed bases. A single quantity matrix applies
uniformly to selected destination structures; selected source cells must match
destination counts without broadcast. More than one source pair requires
`structure_pairing="by_index"`, with selected times compared in ps when present
on both sides (`rtol=atol=1e-9`). Source/quantity inputs are mutually exclusive.

Initialize or remove the complete series; replace a subset only when a complete
series exists. No missing-frame cell is fabricated. Nonconsecutive selectors
retain their order and reject duplicates, booleans, fractional or out-of-range
indices. Input/source preparation failures preserve science, scene, source
records, messages and history, including with digestion bypassed. Arbitrary
unexpected runtime/render failures have no rollback guarantee.

Coordinates/time and source correspondence remain unchanged. Named results
retain their original immutable observations; only edited frames lose evaluated
coverage in the attached analyses. Content binding, projection and displayed
interactions refresh, and scene undo/redo is cleared. Scientific cells survive
subsequent source additions, copying, extraction and session reopening. Removal
hides cell edges, and all system rebuilds now regenerate visible edges from
current data rather than replaying stale world coordinates. No visible edge
display is created automatically by assigning a cell.

All 43 specific Python guards pass; TypeScript and the extended real-Mol*
coordinate-edits browser suite pass. The browser checks cells/angles in all three
frames, including an oblique cell, replacement/removal and unchanged coordinates.
The once-run full regression completed with 2,764 passed, 23 skipped and one
failed in 464.30 s. The sole failure was the hardcoded E2E count left at 39 after
adding the composite suite; updating it to 40 preserves registration/build-set
checks, and all six reliability-file guards pass. This scoped recovery is not
a second full run or an all-green complete-regression claim. It also completes
the previously ENOSPC-interrupted coverage on a healthy temporary filesystem.

The native route currently rebuilds the molecular projection; incremental box
streaming and a hard memory/I/O ceiling are not certified. Exact source hashes,
commands and retained logs are in `devguide/box_assignment_20261003.json`.
Studio parity and integrated/published-provider/artifact qualification remain;
#151 stays open and no new wheel, product commit or push is claimed.

## Local Studio loading slice — 2026-10-03

Implemented and locally verified. The normative interface and boundaries are
in `architecture.md` under Studio loading; exact commands, source hashes and
retained logs are in `studio_loading_20261003.json`.

All 18 Python guards pass. The once-run complete Python regression passes with
2,783 passed and 23 explicit skips in 470.79 s, outside the sandbox in the required
Python 3.14 environment. This supersedes the earlier incomplete regression
qualification, without changing its preserved evidence. The JS run passes 320
cases; the final affected modules pass 39 after the loading visibility correction.
TypeScript, runtime builds and the extended real-Mol* composite browser suite pass.
Its actual form submits mixed PDB/H5MSM inputs, retries a missing-file failure,
adds progressively, replaces, combines complementary Amber topology/coordinates,
appends structures and pairs ordered nonconsecutive frames. It checks scientific
rendered coordinates, request-specific completion and absence of the Python load
form in a browser-only export. It also retains previous session/extraction guards.

Browser testing found that rebuilding a successful progressive addition clears
the hierarchy transiently and closed Studio before the next operation. The form's
pending request now supplies temporary visible content, while explicit workspace
visibility overrides remain authoritative. Increasing the fixture viewport alone
was refuted; measured ancestors were shifted left by the collapsed panel, rather
than the form merely exceeding the viewport. The final real click sequence guards
the correction without forced clicks or bypassing the scientific authority.

A separate public-provider acquisition probe loads 1CRN, 1UBQ, 1VII and 1BTA:
3,017 atoms, one structure and four sources/base regions. Subsequent addition of
native dialanine gives 3,039 atoms and five sources/regions. No automatic alignment
is applied; provider box/bioassembly/attribute diagnostics remain visible. This
is network-backed acquisition evidence, not a repeatable offline timing budget
or browser-upload qualification.

Partial H5MSM topology/chemical-state extraction initially failed with its
atom-axis identity association declared: MolSysMT dereferenced `structures=None`.
The original failed reproduction remains in the dated Studio evidence. The
provider closed uibcdf/molsysmt#307 and the direct reproduction now passes on
editable commit `eba166188a8740b9bde10e39f2ed4353448311a4`. This does not qualify
composition of separate partial H5MSM domains. The provider subsequently closed uibcdf/molsysmt#309 in commit
`3e1eea3cd1573983cac905313831055a58e55415`. Public conversion now composes declared
partial domains before selections. Six positive combinations pass through Viewer
loading: all/selected atoms with all/single/nonconsecutive structures. The direct
public-provider and Viewer routes agree in 12 checks. The older installed
experimental artifact still rejects this composition; its guards verify atomic
refusal. No published availability of the newer provider is implied.

Viewer retains provider validation for complementary inputs, avoiding the
previous bypass into partial native conversion internals. Six guards cover all
atoms versus selected atoms and all/single/nonconsecutive structures: unsupported
partial-H5MSM pairs raise the public provider diagnostic, preserving the live
MolSys and scene. The 65-case source loading/composition selection passes.
Complete H5MSM, native complementary forms and established Amber pairs continue
to work. No private scientific composer or provider modification is introduced.
The fixture's missing association and solvated Amber atom-count assumptions were
corrected separately. The isolated installed qualification uses its older
experimental provider artifact; the newer extraction repair is source evidence.

#151 remains open for integrated/core and installed/published-provider
qualification, and for an explicit disposition of the partial-H5MSM boundary.
No hard memory ceiling, new installed artifact, product commit or push is claimed.

## Integrated qualification follow-up — 2026-10-03

Main incorporates the remote governance changes through `924da3a3`; 402 preserved
local paths retain their hashes across synchronization. The new Viewer wheel is
`0.23.4+76.g924da3a3.dirty`, with a passing runtime-version check and 614 matching
packaged Python sources. Installed loading/worker guards pass 25 cases with
experimental provider `0.22.4+122.g396e6979f`. The isolated environment needed
OpenMM for Amber form recognition; installing ParmEd alone was refuted as a fix.
The once-run complete installed regression passes 2,791 tests, with 25 skipped,
in 579.31 s. Core qualification exposed uibcdf/molsysviewer#154, now fixed locally:
all 39 core suites pass under the default deadline. A later published-provider
check exposed #155: cell initialization could be silently ignored. The latest
wheel verifies the provider result; 68 installed loading/cell cases and its
published-provider preservation/error guard pass. The once-run source regression
after that correction passes 2,800 tests, with 23 skipped, in 489.46 s. Exact hashes
and boundaries are in `devguide/integration_completion_20261003.json`. #151 stays
partial for compatible publication and committed-candidate qualification.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).

## Real scientific-use review — 2026-10-04

Four real PDBs (1VII, 1L2Y, 1TCD and 1ATP) pass batch/progressive loading,
coordinate/map preservation, source visibility/isolation and MSV restoration:
7,953 atoms and four sources. The mixed SDF slice remains unqualified. Direct
SDF count dispatch fails (uibcdf/molsysmt#312); converting caffeine publicly
then adding it exposes missing-group getter failure (uibcdf/molsysmt#313) and
Viewer candidate prevalidation gap #157. The provider owns hierarchy semantics;
the consumer must refuse an unexportable candidate before active-state mutation.
See [`scientific_use_review_20261004.md`](../scientific_use_review_20261004.md).

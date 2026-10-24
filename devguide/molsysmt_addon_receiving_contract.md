# MolSysMT tools addon — receiving contract

**Status: partial source implementation — 2026-10-22.** The product direction and
edit/update policy are approved in the [implementation plan](molsysmt_tools_addon_plan.md).
This contract tracks receiving under uibcdf/molsysviewer#264 and
uibcdf/molsysmt#421. Source implements managed native removal, synchronization
controls, the coordinates/box routes of `basic.set`, and a generic host service.
Other effect families, task panels and
installed compatibility remain unqualified; no release follows from this work.

## Bound calls and integration controls

`tools = view.addons.molsysmt` is a view-bound facade, not a saved MolSys snapshot.
Resolve the current target once when a call starts. Keep provider scientific
returns/defaults, including copy versus in-place semantics. Auxiliary molecular
inputs remain explicit. Readers, factories and pure quantity tools receive no
invented molecular input. Collection tools require individual ordered-input
contracts; their exposed signatures must not silently prepend the current system.

Two facade controls complement the scientific module hierarchy:

| Control | Contract |
| --- | --- |
| `tools.get_sync_status(*, skip_digestion=False)` | Return detached metadata about this view's coordinated synchronization state. No scientific arrays, full-system copy or scientific calculation. |
| `tools.sync_view(*, skip_digestion=False)` | Reconcile admitted pending completed edits without repeating science; return `None` on success. No-op when already synchronized. Reject uncertain or replaced-target state requiring explicit recovery. |

These are addon integration controls, not new scientific aliases. Check their
names against the fixed provider exports. Every public wrapper/control follows
the ordinary ArgDigest and SMonitor contracts. Preserve provider validation;
`skip_digestion` does not bypass correspondence, ownership or revision checks.

`update_view=True` applies only to wrappers with admitted bound-system effects.
It is keyword-only and does not replace `in_place`. Independent returned outputs
are never adopted by this flag. Reject unsupported deferral or update-parameter
collisions before scientific execution. Do not add flags indiscriminately to
every read/factory function.

## Synchronization states

State is per view, shared across cached facades and windows. It tracks managed
addon operations only, not unannounced native calls or raw array writes.

| State | Meaning / allowed recovery |
| --- | --- |
| `synchronized` | Python scene projection corresponds to the last admitted scientific target revision. There is no pending managed edit. |
| `pending` | Completed managed science has not been reconciled. Compatible further edits can accumulate; old-index scene actions are unavailable. |
| `sync_failed` | Science completed, but scene reconciliation failed. Retain its correspondence and retry synchronization only. |
| `uncertain` | A scientific exception may have left partial writes or correspondence cannot be certified. Do not resume edits or declare synchronization successful automatically. |
| `closed` | Owning view is closed. Bound scientific calls fail before doing work. Closing only a popup does not close the view. |

`editing` and `syncing` are transient guarded states. Conflicting scene calls
are rejected before digestion/history, including `skip_digestion=True`. Browser
interaction pauses through a shared state projection; camera-only Python
snapshot/reset/mode calls remain available. A popup request during pending work
receives state only, never a lazy old-index molecular payload.

The status record contains state, operation identifier, target/integration
revision, pending operation count and a diagnostic/recovery reason where
applicable. It does not retain large completed return values by default. An
independent result returned to Python remains caller-owned.

`synchronized` describes the Python scene projection, not proof that every live
window has drawn it. Use existing transport/endpoint acknowledgements and replay
for delivery. A disconnected popup cannot undo science, force it to run again
or permanently prevent other endpoints from receiving canonical state.

## Execution and failure boundary

1. Resolve the live target and capture the managed revision/lifetime. Check the
   operation's binding, prerequisites and admitted integration branch, preserving
   the provider's scientific validation. Retain required before-state metadata
   before destructive writes; small map metadata is distinct from full Undo.
2. Serialize conflicting managed edits/replacement, or reject stale completion
   with the captured target/revision. Do not use a projection serialization
   counter as proof that arbitrary scientific writes were observed.
3. Call the native scientific tool once. Classify native rejection, no-op,
   completed effect or potentially partial write using the actual tool contract.
   An unchanged count or an exception alone does not certify a no-op.
4. For independent outputs, return the native result without adopting it. For a
   completed bound edit, record correspondence and reconcile immediately by
   default, or enter `pending` when qualified deferral was requested.
5. A scene rebuild/transport failure after successful science must identify the
   separate failure. The host integration exception exposes `science_completed`,
   `operation_id` and `scientific_result` (including native `None`) and chains
   the synchronization cause. It must not masquerade as scientific rejection.
   Ordinary successful returns are unchanged; result access is through the
   exception on this path, avoiding a second permanent result store.
6. Retry from retained correspondence/current target; never execute the native
   operation again to repair the scene. A partial scientific write enters
   `uncertain`; an explicit recovery/load may replace it, but no implicit rollback
   or recertification is promised.

While pending/failed, gate every scene operation that consumes molecular indices
at the Python authority, including actions from popups and notebooks. GUI
disabled buttons alone are insufficient. Camera-only navigation may remain.
Define the exact admitted actions with the receiving tests. Reads from the
current molecular system remain scientific reads, not reads of the old scene.

Replacement must reject unresolved managed work before it mutates the target,
or provide an explicit reviewed discard/replacement route. Never overwrite a
replacement with a late result. Cached facades follow the new target on later
calls. Disabling/hiding panels releases GUI resources without disabling the
installed headless facade or deleting scientific results. View close rejects
new work and prevents stale completion from recreating widgets.

## Correspondence and validity

Keep the mapping from the last synchronized scene to the current managed target.
Compose it across deferred operations. Reject a next operation before execution
if its required correspondence cannot be composed. No automatic scene reset
silently substitutes for preservation that the operation promises.

- **Attribute edits:** declare scientific dependencies by actual field/state,
  retain identity and update affected labels/styles. Avoid blanket interaction
  invalidation for scientifically independent metadata.
- **Coordinates/box:** retain atom/structure identity and record affected
  structure/state scope. Respect provider invalidation and refresh affected
  geometry, periodic cell and dependent scene objects.
- **Atom-axis edits:** retain authoritative old-to-new atom correspondence,
  explicit deleted/new atoms, and source maps. Qualify broken-anchor policy for
  regions, selections, labels, measures, shapes, colors and analyses.
- **Structure-axis edits:** use explicit new-to-old source positions or an
  equivalent relation capable of repetition. `[2, 0, 2]` cannot be represented
  by an ordinary old-to-new dictionary alone. Unknown/new structure origins are
  explicit; remap player position, visibility, sources, plots and analyses using
  each owner's reviewed policy. `apply_system_edit(structure_index_map=...)`
  now receives an explicit new-to-old sequence for retained structures, including
  repetition. It validates the sequence before adoption, remaps per-structure
  shapes, interaction display filters, plot values/events, player and compact
  source correspondence, and keeps scientific analysis transformation in the
  provider. New/unknown origins and automatic scientific edits remain outside
  this initial map contract. Clearing all structures while plot cards exist is
  rejected before adoption; remove those cards explicitly first.
- **Chemical-state edits:** distinguish payload changes from state-axis changes
  and structure-state association changes. Keep affected chemistry, attached
  analysis validity and rendered topology consistent. Atom/structure counts do
  not establish chemical-state correspondence.

Preserve scientifically unaffected results only with provider evidence. A generic
`preserve` flag is a declaration, not validation. Molecular edits retain the
existing scene-history boundary; automatic molecular Undo and complete trajectory
copies are outside this receiving requirement.

## First executed acceptance cases

### Implemented source receiver

`view.addons.manager.system_edits` is the generic host service. `read(callback)`
serializes bound readers with managed writes, without copying native returns.
`execute(callback, name=..., update_view=True, rejection_check=None)` receives a read-only provider
preparation callback returning a plan: `run`, explicit `changed`, optional
operation-relative retained atom/structure maps, `interactions_policy` and a
reviewed optional `failure_atomic` declaration. The native operation runs once.
The provider remains responsible for scientific validation and the truth of
these declarations. Initial receiving rejects added/unknown origins and an empty
atom/structure result before native execution; independent outputs remain native.

The host composes retained maps across deferral, checkpoints only scene metadata
and preserves existing handle objects. Retry restores that metadata before
applying the composed maps, avoiding a second remapping of already edited scene
indices. Molecular domains, coordinate/analysis arrays and arbitrary user
extensions are not copied into the checkpoint. Molecular Undo is not provided.

`synchronize()` retries projection only. `replace(molecular_system)` is the
explicit recovery route: it discards pending reconciliation and loads a new
system, without undoing the old scientific mutation. Ordinary `view.load` is
blocked while managed work is unresolved. Raw external edits are not observed.

The first provider writer is native `basic.remove`: its native False default
returns an independent result; True edits the bound MolSys and retains native
None. Its native candidate-publication contract plus unchanged state-dictionary
identity qualifies an atomic rejection. Other scientific exceptions are
uncertain even if atom/structure counts are unchanged.

Host guards: `tests/test_managed_system_edits.py`; provider receiving:
`tests/molsysviewer_molsysmt/test_remove_tools.py` in MolSysMT. The existing
`coordinate-edits.e2e.ts` lane includes actual public MolSysMT coordinate edits,
pending-state interaction blocking, a later second Mol* endpoint and a
browser-generated Update view request consumed by the persistent Python owner.
That two-controller check does not independently qualify popup bootstrap/relay;
the established popup lanes retain that responsibility.

### Remaining effect-family acceptance

Use bundled real systems with at least three structures where required:

1. Read through `basic.get`: native return/default/unit/aliasing parity; no added
   scene mutation or complete-trajectory copy.
2. Remove selected atoms with `in_place=False` and `True` separately: unchanged
   original versus actual mutation, native returns and authoritative remapping.
3. Extract atoms/structures `[2, 0]`: native independent output, unchanged view;
   distinguish this from `view.extract` returning a View.
4. Set coordinates for `[2, 0]`: correct affected scope, units, validity and
   unchanged frame identities. Preserve analyses unaffected by the edited scope
   only where their provider contract permits.
5. Remove a structure: preserve mapped scene state/player behavior; exercise
   repetition separately in an operation that actually supports it.
6. Two deferred edits and explicit synchronization: composed maps, no stale
   picks/commands, one final reconciliation and no scientific rerun.
7. Native rejection/partial-write and reconciliation failures separately: retain
   completed results where applicable, diagnose uncertain state and recover
   without repeating science. Add a qualified failure trigger in the receiving
   fixture; no fake successful scientific result substitutes for real execution.
8. Cached facade across load, conflicting completion, GUI disable, view close,
   two independent views, notebook actions and both popup lifecycles.

Passing these cases does not certify all functions. Receive each effect family
and optional route against the provider ledger before expanding coverage or
claiming installed compatibility. The source baseline and publication remain
separate; neither 1.0 release is authorized by this work.


## Geometry setting receiver — 2026-10-23

The provider's initial `basic.set` slice receives coordinates and box with the
current nonempty axes retained. Scientific signatures/defaults, units, order,
repeated-index write behavior and None return remain native. Unsupported effect
families are rejected before execution. Native setters own affected-structure
invalidation; host reconciliation uses preserve for the already-updated analyses.
A valid empty atom/structure selection is a native no-op, not new coverage.

`rejection_check(target)` is an optional explicit argument of the generic host
executor. The provider returns an immutable token before science and again on
rejection. Together with target/state-dictionary identity, an unchanged reviewed
token can certify no target writes; it does not declare a multi-attribute call
atomic. A changed token or failed token read instead enters uncertain state and
preserves the scientific exception. Old hosts reject this keyword before science;
an unrecognized plan field cannot silently disable the check. The provider's
geometry token covers protected coordinate/box storage and analysis snapshots.
No molecular data are copied or permanently retained to calculate that token.

Native attribute-name admission is reused through ArgDigest before integration
effect checks. Preflight uses provider units/selectors and rejects mismatched
retained axes, partial missing-box initialization and unsupported routes before
any write. No broadcasting, automatic chemistry, detector rerun or molecular Undo
is introduced. Coordinate clearing/initializing new axes needs separate receiving.

Current synchronize rebuilds the scene projection, even for a small geometry
edit. Native storage replaces affected blocks, but this integration does not yet
promise a scoped browser refresh or bounded trajectory transfer. Existing
incremental visual tools remain separate; optimize this receiver through their
projection owners after profiling, without repeating scientific setters.

Provider guards include actual Buch calculations and retained observations,
unchanged old snapshots, evaluated coverage, deferred edits and a real connector
failure followed by projection-only retry. Host guards test nested mutations
under an unchanged MolSys dictionary. The browser lane exercises the addon when
available and explicitly reports that route; the published-backend lane keeps
its generic host fixture and cannot count as addon qualification.


## Independent copies, conversions and file preflight — 2026-10-23

The provider extends its native `basic` mirror with `copy`, `convert` and
`get_conversion_report`. They use the existing serialized reader and return
native results without implicit adoption or scene projection. Converter options,
sharing, target order, reports, scientific validation and optional dependencies
stay native. Explicit filenames refer to the Python host; a file result is not
a browser-download protocol. A report's audited scope/exhaustiveness remains
explicit and does not certify all formats or atomic multi-file publication.

Local receiving exercises real H5MSM named analyses, nonconsecutive/repeated
structures, preflight destination-byte preservation, independent outputs,
full-axis live-reference policy, pending reads, replacement and closed-view
rejection. Native forms/H5MSM receiving does not qualify optional converters.
No new host runtime/API or frontend transport is needed for these reader routes.


## Composition and comparison readers — 2026-10-23

The provider adds `contains`, `is_composed_of` and the non-mutating comparison
route through the existing serialized reader. Comparison binds only its first
system: the second system and its atom/structure selectors remain explicit and
caller-owned. No cross-view locking or implicit molecular preparation follows
from binding a primary system.

Native `compare(redefine_indices=True)` rebuilds topology in both inputs and is
not received as a reader. Reject it before writes, even for trusted digestion
bypass; a future adapter must qualify both systems' effects and reconciliation.
The provider reuses its ArgDigest alias declarations before wrapper defaults are
forwarded, retaining native duplicate-name rejection. No new host runtime,
frontend transport or scientific comparison algorithm is introduced here.


## Identity and explicit collection utilities — 2026-10-23

The provider adds bound identity and attribute-owner readers through the existing
serialized read service. The attribute-location result preserves the native live
item/form pair; locating its owner is not a defensive copy or an external-write
observer. A resident-form query describes the current MolSys rather than the
original input's provenance.

The pure `are_multiple_molecular_systems` utility retains its explicit collection
instead of inventing a single primary slot. It can validate caller-supplied inputs
before a view loads any system, while retaining the owning view's lifetime check.
It neither prefixes the current system nor combines/adopts items. Inputs must be
caller-stable; no edit lock is acquired for them. Native input inspection/I/O
remains native. This classification utility does not define source-loading or
composition policy.

Where native identity/classification helpers deliberately omit digestion, the
addon supplies its own keyword-only skip_digestion and never forwards it or
redecorates the native helper. The ordinary scientific escape hatch on the
attribute-location reader remains native. No new host public API, runtime
transport or observation of external mutations is needed for these routes.


## Stored-topology readers — 2026-10-23

The provider's explicit `topology` namespace receives `get_bondgraph`,
`get_covalent_blocks`, `get_covalent_paths` and `get_dihedral_quartets`. Native
scientific signatures, outputs and exceptions remain authoritative. Graphs,
sets, paths and ragged quartet/block results remain scientific values; they do
not become regions, representations or attached analyses automatically.
`remove_bonds` on covalent blocks computes hypothetical graph cuts without
removing molecular bonds. A reference-state graph is not a graph per visible
structure; only native helpers declaring state/structure selectors receive them.

A common private provider delegate now serves admitted `basic` and `topology`
readers through the existing host serialized reader. It resolves the current
primary system, preserves pending-data access and rejects closed views; it is
not an unrestricted module proxy. No new host runtime, public API or frontend
transport is introduced. The native module has no root aliases for these four
functions, so the addon does not invent them.

Bond-graph/block helpers forward their declared native skip_digestion flag.
Path/quartet helpers have no declared native flag: their keyword-only addon
control governs addon digestion and is never inserted into scientific kwargs.
Native validation still runs. The additional graph/sequence receiving below
extends this initial four-function slice. Lazy lifetimes and mutating routes
still need separate receiving.


## Chemical-graph and sequence readers — 2026-10-23

The provider also receives rings, rigid fragments, rotatable bonds, SMARTS
matches, atom correspondences, sequence alignment and sequence identity. This
completes the explicit mirror of the eleven current topology exports at the
reviewed baseline. It does not establish scientific correctness for all inputs,
optional engines or unreceived namespaces.

The same serialized reader binds only the current primary system. References,
reference selections/states, scientific patterns, anchors/candidates and search
limits remain native and explicit. Auxiliary inputs are caller-stable; no
auxiliary-view lock, atom-order adoption or coordinate fit is implied. Missing
chemical declarations raise rather than triggering hidden preparation. Native
optional dependency gates remain lazy. Ring/fragment memberships, source bond
indices, query-column order, empty matrices, search evidence and prettyprint
stdout/None behavior are preserved without scene projection or attachment.

Current sequence identity declares a keyword-only native skip parameter;
the addon forwards it without changing historical native positional slots. The
native contributing-group mapping under uibcdf/molsysmt#439 is repaired and
received. Default capped self-comparison returns 100 percent and actual source
groups. Earlier source-only limitations remain in dated receipts; the addon
never supplied a second identity formula or hidden filtering.
No new host runtime/API, graphical panel or wire message is required here.


## Initial structure calculations — 2026-10-23

The provider's structure namespace receives get_distances, get_vectors,
get_center, get_radius_of_gyration, get_angles and get_dihedral_angles. They
reuse current-primary serialized reads and preserve physical quantities,
weights, periodic choices, output/index metadata, native engine and execution
controls. A second molecular_system_2 remains explicit with its own selectors
and caller-stable lifetime; there is no cross-view lock or inferred pairing.

Centers and angles are scientific returns, not coordinate edits or automatically
created scene measurements. Dihedral named flags remain separate from the
addon-only keyword skip_digestion, absent from the native signature. All other
declared skip controls remain native; no trusted-science bypass is invented.
No new host runtime, public API or message/scene protocol is needed.

Native heavy unit/endpoint defects under uibcdf/molsysmt#440,
uibcdf/molsysmt#441 and uibcdf/molsysmt#442 are
now repaired by the owning team and received against independent physical
references. Earlier parity-only scopes remain in their dated receipts. No addon
formula, unit relabeling or silent routing change substitutes for those fixes.
No general bounded-RAM, optional-GPU or complete structure qualification follows
from this receiving.


## Independent RMSD, axes and plane receiving — 2026-10-23

The provider adds raw RMSD, minimum RMSD, principal axes and least-squares planes
through current-primary serialized reads. References and their selectors/index
remain explicit, caller-stable inputs. No auxiliary-view transaction, chemical
correspondence inference or periodic coordinate reconstruction is introduced.
Raw RMSD uses the supplied coordinate frame; minimum RMSD optimizes the comparison
without fitting either input in place. Its quantity result is separate from any
coordinate edit, scene alignment or measurement. Native RMSD lacks a declared
skip control: the addon-only keyword is not forwarded, and native public validation
still runs.

Axes/moments retain native numeric arrays, row basis, eigenvalue ordering and
sign/degenerate-subspace conventions. Plane dictionaries retain sparse memberships,
structure order/typed empties, physical centers/deviations and numeric normals.
They do not create shapes, infer aromaticity or move the molecular system.
No host runtime, public API, frontend protocol or new molecule copy is added by
the wrappers; native calculation/cache ownership remains native.

The earlier wait for the scientific team on uibcdf/molsysmt#441 is satisfied
by its native endpoint repair and bound receiving. General rich selectors and
optional engines retain native execution dependencies; the earlier independence
checks were bounded scenarios. Minimum/neighbor wrappers now have authorized
local receiving of owner repairs under uibcdf/molsysmt#444 and
uibcdf/molsysmt#445, now closed with scientific fixes in 5710cc0cff1f3f468823699104e51e6fe029c3b2.
The addon does not substitute another distance algorithm, parameter or hidden route.


## Repaired native observables and relation readers — 2026-10-24

The provider adds get_maximum_distances, get_contacts and get_rmsf through the
same current-primary serialized reader. Maxima preserve native local endpoint
positions, entity/pair reduction choices and quantities; the wrapper's added
keyword-only skip control is not forwarded to a native helper lacking that flag.
Contacts retain threshold quantities, supported cell-list/dense and output/index
choices. RMSF measures the supplied coordinate frame without automatic fitting,
periodic reconstruction, coloring or result attachment. Nothing edits either
system, creates scene measurements or requests a projection update.

The native source repairs sequence group mapping/flag, radius/RMSF physical
units and both heavy distance populations. Bound receiving includes independent
NumPy references for physical values, indices, repeated structure axes, weighted
centers and contact maps. It does not merely compare a shared defective route.
No host runtime, protocol, extra scientific implementation or dependency floor
is introduced. Source support is separate from compatibility of published files.

The maintainer explicitly requests native pytest coverage across get_distances,
get_neighbors, get_minimum_distances and get_maximum_distances in
uibcdf/molsysmt#444 and uibcdf/molsysmt#445. It must account for public paths and critical parameter
combinations, sources, structures, weights, units/PBC, outputs/indices and errors,
with independent numeric oracles. This bounded addon receipt is not completion
of that whole-family review. Minimum/neighbor wrappers subsequently gain local
receiving of the scientific team's working-tree corrections, as specified below.


## Local minimum and neighbor receiving — 2026-10-24

The maintainer authorizes working against the provider repairs before their
commit. get_minimum_distances and get_neighbors bind only the current primary
MolSys and retain explicit secondary sources, selections, structure axes,
independent weights, quantities and native skip controls. Minimum positions stay
local to selected populations or pairs. Neighbor count/cutoff and supported
CSR/source-atom pair outputs remain native. The addon re-scopes the native
criterion admission declaration before forwarding defaults, omitting only absent
criterion values at delegation. It neither weakens incompatible-call checks nor
chooses a criterion or scientific algorithm.

The same serialized reader preserves current-primary binding through pending
edits and replacement, and retains view lifetime checks. Results are not attached
or visualized automatically. The provider receiving record retains source hashes
for this initial dirty-tree integration. Native fixes are now committed in
5710cc0cff1f3f468823699104e51e6fe029c3b2 and the two owner issues are closed;
addon exact-head CI remains distinct. No host runtime, wire protocol, package compatibility floor or release
promise is changed by this local receipt.


## Structural-analysis readers — 2026-10-24

get_symmetry_corrected_rmsd, get_secondary_structure and
principal_component_analysis use the existing serialized primary-bound reader.
Their explicit scientific inputs remain native, including secondary references,
states, constrained/cached chemical maps, structure indices, numeric weights
and execution controls. The secondary-structure wrapper adds a keyword-only
addon skip control without forwarding it to the native helper; native validation
remains active. Other native skip controls are forwarded unchanged.

The MDTraj DSSP route returns native group codes and sorted unique group scope;
numeric selections mean group indices here. RDKit-backed pose RMSD retains
declared chemistry, constrained search scope, raw-baseline applicability and
producer attribution, with no fitting or periodic reconstruction. PCA returns
row eigenvectors and squared-length eigenvalues of the native weighted covariance,
without trajectory projection or coordinate edits. Degenerate eigenspaces,
dense covariance memory and optional-engine boundaries remain explicit.

No molecular preparation, scene object, automatic analysis attachment, new host
runtime or protocol is introduced. Native PCA list weights fail at the Rust
boundary under uibcdf/molsysmt#448; the received CPU routes use default or float64
ndarray weights. The addon supplies no private normalization or algorithmic
repair. Source receiving and actual published-file compatibility remain separate.

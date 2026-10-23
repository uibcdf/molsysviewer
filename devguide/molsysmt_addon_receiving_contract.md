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

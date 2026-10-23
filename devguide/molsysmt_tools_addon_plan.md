# MolSysMT tools add-on — implementation plan

**Status: partial source implementation; installed qualification pending —
2026-10-23.** The maintainer authorizes the Viewer development effort to implement
the integration in the owning MolSysMT repository. This is a new plan under
[the core/add-on boundary](core_and_addon_boundary.md). The withdrawn native
Studio expansion plan remains removed. The experimental source integration provides bound `basic` queries and read-only
comparison, independent extraction/copies/conversion and preflight, managed
retained-axis removal and coordinates/box setting, with root aliases and
synchronization controls. Four native `topology` readers now have source
receiving without new host runtime: bond graphs, covalent blocks/paths and
dihedral quartets. Broader runtime coverage, installed compatibility,
dependency floors and release remain separate.

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

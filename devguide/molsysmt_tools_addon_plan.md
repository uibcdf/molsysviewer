# MolSysMT tools add-on — implementation plan

**Status: proposed implementation contract; product requirements accepted —
2026-10-22.** The maintainer authorizes the Viewer development effort to implement
the integration in the owning MolSysMT repository. This is a new plan under
[the core/add-on boundary](core_and_addon_boundary.md). The withdrawn native
Studio expansion plan remains removed. No runtime restoration, installed
compatibility, new dependency floor or release is claimed here.

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

## Scientific edits versus visual updates — decision still open

The maintainer requested an integration control for applying/updating edits.
The following distinction must be settled before implementing mutating wrappers:

- **Preserve provider mutation semantics and defer only reconciliation.**
  `in_place` retains its original meaning/default. For example, a provider call
  returning an independent MolSys still returns it without replacing the view;
  an in-place call changes the bound MolSys. A proposed `update_view=False`
  would defer display synchronization, not cancel the scientific edit.
- **Prepare a candidate without modifying the bound MolSys.** This requires an
  explicit preparation/adoption contract, ownership and a way to access/apply
  the candidate. It cannot be disguised as an identical in-place wrapper or
  silently change a provider `None` return into another type.

The choice is pending a maintainer answer. Do not collapse scientific mutation,
adoption of an independent output and redraw into one ambiguously named boolean.
Defaults and exact additional argument names are not frozen by this plan.
Read-only calculations do not redraw or create scene objects as a side effect.

Whatever route is selected, define atom/structure/state correspondence before
destructive changes where needed. Deferred updates/batching need accumulated
maps, a visible pending state, safe treatment of picks/selections on old geometry,
a final reconciliation operation and clear partial-write failure behavior.
An old scene cannot continue to act on changed atom indices as if synchronized.
Do not replace complete scenes through `load(mode='replace')` after every edit.
Reuse/extend the qualified reconciliation owner, retaining explicit source
accounting, existing representations and frame/navigation policy.

The current `apply_system_edit` conservatively invalidates interaction coverage
and clears scene history; it is not a generic lossless refresh or molecular
transaction. Qualify same-object edits and independent adoption separately.
Preserve provider scientific invalidation without gratuitously invalidating
unaffected results, and never promise rollback/Undo without retained prior state.
Define optional recovery and its measured resource policy independently of the
ordinary scientific return value. Direct external MolSysMT/raw-array calls do
not acquire automatic observation through this add-on.

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

## Implementation sequence and acceptance

1. **Freeze contracts and coverage.** Resolve the edit/update choice, map the
   selected provider public exports and identify authoritative maps/outcomes.
   Create fresh provider/consumer implementation issues before source changes;
   keep the withdrawn general observer request uibcdf/molsysmt#413 separate.
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
4. **Qualify edits and lifecycle.** Real bundled systems: return/default parity,
   units and nonconsecutive structures, auxiliary references, no-op/rejection,
   partial writes, maps, result applicability, pending update and resync,
   independent copies, load replacement, two views, disable/close and stale
   handles. A disconnected window must not repeat successful science.
5. **Design and implement the GUI over that API.** Review task groups and forms
   before building panels. Demonstrate the same resolved scientific operation
   headlessly and through live widgets; retain view-specific integration effects
   explicitly. Verify actual Jupyter and canvas/panel popups, including real
   click-to-Python execution, not only a static panel screenshot.
6. **Document and qualify distribution.** Expert API reference and graphical
   guide have different audiences. Update provider course/examples and Viewer
   extension guidance, then qualify exact sources and installed packages, lazy
   imports and optional dependencies. Freeze tags/builds only under the separate
   release process; both 1.0 publications remain paused.

Use real provider/demo results for behavioral tests. Signature/export counts
are coverage checks, not substitutes for executed scientific parity. GUI
examples need not expose every expert argument, but cannot weaken the Python
API or hide decisions that change scientific interpretation. This document
plans the new add-on; it does not reintroduce the removed Studio expansion plan.

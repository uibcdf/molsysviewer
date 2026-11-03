# Metadata utility contract prepared for addon receiving

**Implementation follow-up — 2026-11-03:** the four supported reports have a
separate source implementation at owner commit `4e1a06ee1`, with 2,527 addon
cases passing, including 74 new cases. Owner-branch exposure is 148/244; owner
main integration is pending. The [new receipt](molsysmt_supported_tools_receiving_20261103.json)
keeps this distinct from the frozen preparation evidence below. The seven
attribute helpers remain unimplemented in the facade.

**Status — 2026-11-03:** the inventory and consumer requirements for the next
expert-addon block are prepared under `uibcdf/molsysviewer#264` and
`uibcdf/molsysmt#421`. No new addon methods are implemented or qualified by this
review: exposure remains **144/244**. The owning implementation, usage reference
and course examples belong to MolSysMT. This document records Viewer receiving
requirements, not a new core API or user-facing addon reference.

Provider source is frozen at `f72ab0e649a9dd285a423822a215a6d56b1aecf6` for this
review. The owning inventory collector is reused; its observations, complete
unexposed-path disposition and native evidence are retained in
[the receipt](molsysmt_metadata_tools_review_20261103.json). The
[accepted addon plan](molsysmt_tools_addon_plan.md) remains the governing design.

## Inventory and order

The 100 unexposed paths comprise 19 build/preparation paths, six mechanics
paths, 57 element helpers, seven attribute helpers, four supported reports,
four historical hbonds aliases, `basic.view` and two native MD stubs. A path
count is neither an algorithm count nor evidence of supported execution.

The element group contains **21 primary-parameter candidates and 36 explicit-input
utilities**. They must not receive one generic binding policy: an input name
alone does not establish mutation, ownership or return behavior. Preparation and
mechanics also need per-tool engine/effect review. The two always-raise MD
declarations are not implemented functionality to mirror. Historical hbonds
aliases and `basic.view` retain separate explicit decisions; their native
targets or existing visual workflows do not justify automatic exposure.

Prepare `supported` and `attribute` first, then review the element tools by
actual input/effect. Keep installed-source receiving under #269 separate; its
Rust-manifest prerequisite is `uibcdf/molsysmt#533`.

## Common contract for the eleven selected utilities

The proposed namespaces are `view.addons.molsysmt.supported` and
`view.addons.molsysmt.attribute`. **None of these eleven tools takes a molecular
system.** An open empty view must work. Validate the owning view's lifetime,
then delegate with explicit inputs; do not call `_target()`, acquire the
molecular-edit reader, flush pending edits or inspect the primary system.

Preserve native names, parameter order, defaults, return types and errors.
Use the established addon ArgDigest/SMonitor boundary. For native functions
accepting `skip_digestion`, forward the caller's value unchanged; never force
trusted bypass. The two native functions without that parameter may add a
keyword-only, locally validated `skip_digestion=False` integration control,
without passing it to the native callable. Do not add `update_view`, selection,
structures or a hidden `molecular_system` argument to these utilities.

They must not load a system, edit chemistry/coordinates, change the scene,
recalculate analyses, alter history or change pending-edit status. Native lazy
registry initialization remains allowed. Explicit capability visibility and
caller-owned inputs must not be changed. Returned detached metadata remains
usable after closing the view; a subsequent call through a retained facade
must reject the closed owner. No per-view copy of the scientific registries is
introduced.

## Per-tool decisions

| Native route | Proposed receiving requirement |
| --- | --- |
| `supported.forms` | Preserve `form_type=None`, native ordering and visibility. Keep `output_type='styler'`; explicitly support the native dataframe/dictionary/list outputs without forcing presentation. |
| `supported.conversions` | Retain all explicit source/target/type/viewer filters and `as_rows`. Preserve both axes, empty axes, unknown-route false entries and the native false self-route diagonal. Do not infer filters from the loaded system. |
| `supported.dependencies` | Report the current provider environment; preserve the native output choices and ordering. A reported dependency is not a successful scientific operation or installed-pair certificate. |
| `supported.syntaxes` | Expose an explicit signature matching the canonical report: `(*, output_type='styler', skip_digestion=False)`. Native introspection can instead see `(*args, **kwargs)` after importing its callable compatibility module. Both import orders must yield the same report. Preserve selection-input and translation-output directions independently. |
| `attribute.get_argument_aliases` | Keep the versioned independent dictionary, including nested element aliases. Add only the locally consumed optional integration skip control. Do not apply its aliases globally to other addon methods. |
| `attribute.is_attribute` | Retain the native canonical-name membership predicate and native return/error behavior; do not turn unknown names into an inferred attribute or add automatic alias resolution. Its optional integration skip control is local. |
| `attribute.is_chemical_state_attribute` | Delegate the native state-dependency predicate with its existing validation. |
| `attribute.is_structural_attribute` | Preserve the native predicate, including shared atom-inventory attributes. |
| `attribute.is_topological_attribute` | Preserve native compatibility semantics: this predicate also includes nonstructural chemical-state attributes. It is not a promise that classification categories are disjoint or that pure Topology supplies chemistry. |
| `attribute.is_mechanical_attribute` | Preserve the native classification independently of engine installation or actual energy/force availability. |
| `attribute.bonds_are_required_to_get_attribute` | **Pending native semantics under MolSysMT#534.** Stable inventory queries work without bonds while this helper reports a requirement. Do not correct the result in Viewer or present it as a reliable domain-availability decision. |

Tables report declarations and current environment metadata. A true conversion
cell does not guarantee conversion of every system or qualify an optional
engine. Plain outputs must not construct a Styler; the default visual output
continues to have the native presentation prerequisites. A frontend task will
request a plain output explicitly rather than alter the expert API default.

## Native evidence and unresolved findings

The unchanged native `tests/supported` selection passes **23 cases**. Native
attribute tests pass ten cases and fail one existing alias-collision test:
importing the declaration table before the public attribute package can cache
an incomplete alias registry. Separate fresh processes reproduce seven versus
eight matching normalization tables and UnknownArgumentError versus the intended
ArgumentConsistencyError. Moving the unchanged source snapshot to a short
nonhidden temporary path does not fix it. This is now `uibcdf/molsysmt#535`;
do not prime registries or normalize keywords in a facade to hide it.

Independent contract probes pass eleven cases and fail four literal stable
inventory/bond-requirement expectations under #534. They cover actual Topology
queries from bundled pentalanine, classification overlap, fresh plain reports,
invalid outputs, directional syntax compatibility and independent alias data.
An initial probe used the noncanonical name `charge`; it was corrected to
`formal_charge` before the final four-failure result. That input error is not
reported as a provider defect. These are separate scopes, not an additive
complete-suite result, and do not execute new addon methods.

## Implementation acceptance

Implement in the provider-owned `molsysviewer_molsysmt` package, using explicit
wrappers and explicit namespace registration. Do not add scientific metadata
methods to the Viewer host or introduce a dynamic catch-all mirror.

The owner's future metadata-tool tests must exercise a real open empty view,
two views, a loaded view, retained handles after close, pending edits and
unchanged scene/history. Compare real native outputs/defaults and literal
semantic controls, including mutated nested reports, input lists, unknown
arguments, valid skip modes, invalid integration controls and compatibility
module import order in fresh processes. Test signature discovery and actual
calls separately. Preserve failure expectations for #534/#535 until corrected;
do not count unexposed or unreceived tools as completed coverage.

The inspected source contract is sufficient to prepare this block; installed
pair qualification still awaits #533, and the native metadata/bootstrap findings
have their own owners. No version floor, optional engine guarantee, GUI panel,
candidate freeze, tag or publication follows.

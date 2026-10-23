---
summary: Qualify the redesigned MolSysMT addon host and molecular-edit reconciliation.
issue: uibcdf/molsysviewer#264
status: partial
opened: 2026-10-22
closed:
verification: inspected
area: [addons, editing, api]
guard:
normative:
blocked_by: []
supersedes: []
---

# Receiving the redesigned MolSysMT tools addon

**Reported:** 2026-10-22, accepted maintainer direction after reviewing the
[addon plan](../molsysmt_tools_addon_plan.md).
**Status:** partial implementation: the new discovery route, closed-view boundary
and actionable state-factory failures are delivered for initial read-tool source
receiving. Explicit retained-structure maps now extend live adoption and
independent extraction. Retained-axis removal, coordinate/box setting,
copy/conversion/preflight, composition/comparison readers and synchronization
now have source receiving; other edit families, task panels and installed
qualification remain pending.

## What

Receive the provider-owned tools addon under `view.addons.molsysmt` with safe
host registration, lifecycle and molecular reconciliation. MolSysMT owns the
scientific facade and its tools under uibcdf/molsysmt#421. Viewer owns its
reusable host and scene correspondence boundaries. Its current backend remains
available independently of addon panels.

## How

The [receiving contract draft](../molsysmt_addon_receiving_contract.md)
specifies the state model, proposed facade integration controls, mapping and
failure cases to qualify. It extends the accepted plan rather than promising a
general observer or restoring the retired module wholesale. The provider source
ledger covers all 267 exports in its stability registry's tracked scopes at
`fe5036c1f4c145ec2eecf1627e80eb70fc995618`. It includes root aliases and support
objects; it is not 267 independent scientific tools or implemented wrappers.
Untracked namespace contents and per-function effects still require disposition.

Inspect Viewer at `e8ed36d3`:

- `molsysviewer/addons.py` refuses the legacy namespace/module and silently
  substitutes an empty namespace when a state factory fails.
- `molsysviewer/viewer/core.py::apply_system_edit` accepts atom correspondence,
  not general structure correspondence. Same counts declare unchanged structure
  order. The method installs the new system before finishing the rebuild.
- Interaction invalidation defaults conservatively to clearing coverage, and
  the rebuild clears scene history. Neither gives molecular rollback.
- `close` releases widgets/transport; addon calls need a qualified closed-view
  boundary, not inference from a browser window disappearing.

## Why

A scientific edit must not leave live controls addressing old indices. An edit
that succeeded must not run twice because synchronization failed. The API also
needs to remain usable headlessly, with cached tool references following later
loads, while panel activation remains a presentation choice.

## What was refuted

Reverting the legacy retirement does not supply the new expert API or lifecycle.
Passing every edit through unchanged `apply_system_edit` cannot certify frame
reorders, repeated structures or selective scientific invalidation. A new generic
observer is unnecessary; uibcdf/molsysmt#413 remains withdrawn and closed.
An integration flag does not provide molecular Undo or a universal transaction.

## Acceptance criteria

Close after compatible discovery and factory diagnostics, lifecycle guards,
headless reconciliation, pending-state safety, operation-specific maps and
scientific validity are implemented and tested with real systems. Include
replacement/cached facade, disable/close, partial writes, failed synchronization,
nonconsecutive/repeated structures, source records, anchored objects and recovery
without repeated science. Qualify actual Jupyter/popup receiving and installed
compatibility separately; do not substitute source/export counts for those gates.

## Dependencies and risks

Coordinate with uibcdf/molsysmt#421. The current backend minimum is unchanged.
The source-ledger baseline is not a release candidate or public dependency floor.
Generic factory-failure handling must retain actionable diagnostics for every
addon while preserving legitimate factories returning their intended values.
Do not include unrelated local work or change legacy guards before the new
compatibility route exists.

## Initial read-tool receiving

The host admits `molsysviewer_molsysmt.tools` while ignoring retired root entry
points before loading and refusing explicit legacy-module registration. The
provider declares the new entry point; no hardcoded known-module entry is added.
Addon state factories now record/propagate original failures, remain retryable
and clear their record after a successful retry. `view.closed` explicitly
exposes view lifetime for bound expert API calls and close is idempotent.

Provider `tests/molsysviewer_molsysmt/test_read_tools.py` receives actual basic
queries, signatures/defaults/help, native result/error parity, nonconsecutive
structure coordinates with units, replacement/cached methods, panel deactivation,
two views, empty/closed targets and standard metadata discovery in a fresh
process. These tests exercise the real provider and demos; they are not proof of
new edit/map APIs, task panels or installed artifact qualification. Viewer
`tests/test_addon_factory_failures.py` guards the failure/retry boundary and
`tests/test_view_lifecycle.py` guards explicit closure and widget release.

The [dated source receipt](../molsysmt_addon_read_receiving_20261022.json)
records the 46 provider read/packaging checks, host focused receiving and the
full core result: 3,235 pass, 21 skips and the known #263 fixture failure.
That full run is not green. Both Sphinx builds complete; provider warnings
remain visible. Development editable metadata now exposes the actual new entry
point, observed with a real dialanine view; this is not clean solver or release
artifact qualification. Preserved concurrent provider changes remain explicit
in the receipt's provenance.

The initial provider delivery is published in MolSysMT commit
`fa2f3aa9232372e5fa7db8bbf4ebd9e2ad481056`, tracked by uibcdf/molsysmt#421.
Its routine Viewer source pin is `7449675aa8407e94136357f11da1256188e46183`;
that formatting-only follow-up has the same Python AST as the tested host logic.
Provider developer-guide validation passes on a clean checkout of the delivery.
Both issues remain partial: scientific edits, synchronization and task panels
still require implementation and qualification. No package publication follows
from this source delivery.

## Retained structure correspondence

`apply_system_edit` now accepts `structure_index_map`: entry `j` names the old
structure retained at new position `j`. This supports subsets, reordering and
repetition, unlike an injective old-to-new dictionary. Validation uses the last
projected axis even when native science has already mutated the same MolSys.
Invalid correspondence is rejected before adoption/invalidation, including with
`skip_digestion=True`. Original maps remain unverified when an axis changes
without explicit correspondence, preserving the existing default contract.

Live adoption and independent extraction share structure remapping for shapes,
interaction filters, trajectory cards/events and playhead. Source runs retain
all mapped destinations; scientific analyses must already match the result.
The focused guard is `tests/test_structure_edit_correspondence.py`, with actual
MolSys extraction/removal, combined atom/structure maps and session round-trips.
This does not implement managed scientific execution, deferral, failed-rebuild
recovery, unknown/new structure origins or task panels. Those remain open under
this issue and uibcdf/molsysmt#421.

The [structure receiving receipt](../molsysmt_addon_structure_receiving_20261022.json)
retains the focused source checks and the once-run full core result: 3,257 pass,
21 skips and two administrative failures (untracked archive link and stale
digester count). Tracking the new source and regenerating the inventory resolves
both in an 18-case focused run; that is not a replacement green full-suite run.
The separately reported #263 box fixture now passes its complete 44-case file.
Prior hosted core/source-pair failures at `7449675a` instead concern three
warning-strict documentation pages and deprecated native pandas `inplace`
operations, reported to uibcdf/molsysmt#431. Do not hide that receiving gap by
suppressing the warnings or treating the local source environment as the same
installed dependency composition.


## Managed removal source receiving — 2026-10-22

The provider now admits native `basic.remove` with its False default and
independent result; True mutates the actual bound MolSys and retains native
None. The keyword-only `update_view` controls projection only. The shared host
service composes retained atom/structure maps and preserves existing handles;
`get_sync_status` and `sync_view` expose state and projection-only retry.
Provider preparation uses owned selection/index validation and the qualified
native candidate-publication contract. Other writers are not silently admitted.

Pending/failed edits block old-index commands before digestion/history and at
the frontend event authority, including notebook calls with skip_digestion=True.
A state sheet disables canvas/panel input and offers Update view. A newly
requested popup receives a correlated state-only snapshot; closing it does not
cancel science. The source metadata checkpoint excludes molecular domains,
coordinate/analysis arrays and arbitrary extension attributes. On failed rebuild,
it restores scene metadata before applying maps again, preventing double remaps.
Uncertain scientific writes require explicit replacement; ordinary load cannot
silently discard them. Native reads remain available against pending data.

Receiving tests exposed two existing remapping gaps: active atom picks retained
old indices/hierarchy metadata, and region queries supplied as explicit atom
lists were reevaluated as new indices. Rebuild now resolves active metadata and
remaps explicit region lists/provenance; textual region queries retain their
intentional reevaluation behavior. Actual native subset tests protect this
without changing that established textual-query contract.

Provider receiving has 17 remove/control cases, 20 prior read/extract cases and
30 packaging guards passing. The host has six coordinator cases, including
actual coordinate writes, conflict rejection, uncertain recovery and correlated
popup requests. JS units pass 332 cases. The coordinate-edits browser lane uses
real Mol*/Chromium and a persistent Python owner to receive an Update view
command from a later second controller. This is not an independent qualification
of the complete popup bootstrap/relay stack or live Jupyter.

The once-run full core has 3,266 pass, 21 skips and two failures: the generated
capability inventory and a TypeScript playback-action literal. Both are corrected
and their focused guards pass; the full run is retained as failed, not relabelled
or rerun. The managed receiver has its own experimental capability row, rather
than inheriting a stable label from the existing addon navigation group.
See [the source receipt](../molsysmt_addon_remove_receiving_20261022.json).
Other edit families, full namespace coverage, graphical task panels and installed
artifacts remain pending. Neither 1.0 publication is authorized.


### Published source checkpoints and hosted receiving

Viewer code is published at `9da52e5500c9f8637e2f6f76eea0eb81ce783882`;
MolSysMT delivers the addon at `0629fc941f9224e9d6ac54eaeff875f49589cc74`,
with explicit smoke receiving added in `af560ab4ba5810b2dc2bf02ef91db4d2b9dc330d`.
Provider run 39894101759 passes on Linux/Python 3.14 with the exact Viewer pin,
including the reader and removal receiving files; a preflight import prevents
an optional-host skip from substituting for that receiver. Provider dependency,
policy and publication-governance checks pass. A clean checkout of the provider
feature commit passes developer-guide validation.

Viewer run 39893548732 is not green: the observed Linux/Python 3.14 cell reports
3,267 pass, 24 skips and four failures. Three are the existing warning-strict
examples on the public MolSysMT 0.23.0 dependency (uibcdf/molsysmt#431). Provider
main already contains its separate pandas correction in `128a0bbb9`, but that is
not qualification of a corrected public package. The fourth is the capability
inventory's generated Since value: its new anchor became `unreleased` once
committed, whereas the pre-commit generation had said `unknown`. Regeneration
and its specific guard correct that metadata without changing runtime code.
The passing documentation-notebook, Ruff, policy and Conda-governance workflows
retain their own scopes; remaining core/browser jobs require terminal inspection.

Experimental Qt run 39893548672 fails while waiting for bridge readiness in the
software-rendering host. The receptor's D-Bus line alone does not establish its
cause; native logs also show Vulkan/Mesa diagnostics and the readiness assertion.
Keep this with the existing experimental Qt investigation (uibcdf/molsysviewer#35)
and the compact-diagnostic limitation (uibcdf/gh-run-receptor#62), not as a green
core or a demonstrated new molecular-edit regression. No tags, packages or
publications were produced by these source checkpoints.


## Geometry setter receiving — 2026-10-23

The source adds the coordinates/box subset of native `basic.set` with its native
signature/None result plus keyword-only update_view. Native validation remains
owned by MolSysMT; its attribute catalogue is reused by addon ArgDigest before
checking received effects. Other attributes/axis initialization are explicitly
unreceived, not silently forwarded as unknown mutations. Named analyses retain
native invalidation only on edited structures; no detector runs automatically.

The host executor now accepts an explicit rejection_check token reader. A nested
geometry edit can change protected storage and analysis snapshots without a new
MolSys dictionary. Comparing those family-owned tokens distinguishes unchanged
rejection from potentially partial writes, without claiming multi-attribute
atomicity. An older executor rejects the keyword before native execution.
Full-scene synchronization and broader effect-family qualification remain open;
no scoped trajectory-transfer guarantee follows from this delivery.

The [geometry source receipt](../molsysmt_addon_set_receiving_20261023.json)
records 23 setter cases, 37 existing addon read/remove cases, 30 packaging
guards, eight host coordinator cases and the once-run Viewer core result
(3,278 passed, 21 skipped). Real Chromium receives addon coordinates and box
in two controllers. These are source checks; full popup/Jupyter and installed
artifact qualification remain separate. The prior Viewer checkpoint cef99ec6
now has successful core/browser runs 39948407994 and 39948928788; those runs
do not qualify the new setter implementation.


## Independent conversion and portability receiving — 2026-10-23

MolSysMT source `7367e68ae25230bbe981efdf8a8c563126849e8f` adds bound
`basic.copy`, `basic.convert` and `basic.get_conversion_report` with native
signatures/root aliases. They reuse the host serialized reader: no implicit
adoption or scene projection, including while admitted science is pending.
Files address the Python host. Native sharing, reporting/audited scope,
validation, optional converter dependencies and partial multi-file failures are
not redefined. The provider's per-function effects, source hashes and dated
receipt remain owned under uibcdf/molsysmt#421.

Receiving passes the 122-case addon/packaging/route regression, then three
file-route/option cases (one overlapping) and all six provider guide blocks.
These cover the final conversion file's 23 cases, actual H5MSM 0.5 named analyses,
nonconsecutive/repeated structures, destination-byte preservation at preflight,
copy ownership, pending reads, replacement and closed-view output rejection.
Optional file/engine qualification is not inferred. The provider source smoke
now includes the conversion file; new hosted gates are pending.

The previous exact Viewer runtime's browser run 39992310736 passes. Core
39992310828 and source-pair 39992310747 expose three strict documentation failures
from public MolSysMT/pandas deprecations (uibcdf/molsysmt#431) and one new fixture
portability error: its token assumed replacement of coordinate storage, while
0.23.0 updates in place. The generic receiver itself trusts only the provider's
reviewed token; changing the fixture to read a bounded edited value removes
that unjustified storage assumption. Eight coordinator guards now pass both
with current provider source and cached public 0.23.0 build-0 runtime. This
cached-byte check uses the selected development interpreter and PYTHONPATH;
it is not a clean solver installation or broad package qualification.

The once-run local Viewer core passes 3,278 tests with 21 skips (139.60 s).
The pandas finding remains open rather than being muted in documentation tests.
Experimental Qt 39992310795 separately fails bridge readiness/WebGL setup; native
logs name both no exported WebGL canvas and loading readiness timeouts, alongside
Vulkan/D-Bus diagnostics. D-Bus alone does not identify the cause. Keep the
existing uibcdf/molsysviewer#35 and uibcdf/gh-run-receptor#62 tracking; this is not
green core evidence. No tag, release, package or 1.0 publication is produced.


## Composition and explicit-reference comparison — 2026-10-23

MolSysMT `5911dace61c667138e0596ff631dc628d9b85ac1` adds native bound
`contains`, `is_composed_of` and `compare(redefine_indices=False)`, including
root aliases and exact signatures minus the primary system. The second system
and its separate atom/structure selectors remain explicit. These calls reuse
the serialized reader, including for pending scientific data, without scene
projection or attached results. Auxiliary systems remain caller-owned; this
is not a two-view transaction or automatic cross-view lock.

The native `redefine_indices=True` branch rebuilds topology in both inputs and
stays unreceived, rejected before writes even for trusted calls. The provider
re-scopes its existing ArgDigest alias table before forwarding defaults;
`attributes_type` works without converting a wrapper default into an explicit
user argument, while an actual alias/canonical collision still fails, including
canonical None. There is no independent scientific comparator or alias registry.

The provider receipt under uibcdf/molsysmt#421 records 33 focused cases, 157
addon/packaging/route regression cases, all seven guide blocks and unchanged
course Module 14 code/outputs. Source/wheel/sdist metadata guards include the
new normalization source (13 addon Python files). Clean-checkout devguide
validation passes. Hosted predicate receiving is newly activated; installed
compatibility and wider scientific/GUI coverage remain pending. No host runtime,
frontend, message schema, public package or release changes in this block.

The previous exact host `4b5a0888` has successful policy 39997487212 and browser
39997486583 gates. Source pair 39997486648 reports only the three known strict
documentation failures from public MolSysMT/pandas (uibcdf/molsysmt#431); its
storage-variant guard no longer fails. Experimental Qt 39997486452 still reports
no WebGL canvas / loading readiness failures under its separate #35 scope.
Do not describe either failed campaign as globally green or infer D-Bus as the
cause from the receptor's bounded summary alone.


## Identification utilities and native warning report — 2026-10-23

At the maintainer's explicit request, the native quantity-downcast warning is
now reported as uibcdf/molsysmt#435, with a reproduction that needs no Viewer.
Structural self-comparison emits six UnitStrippedWarning entries with an always
filter while all dictionary results remain True; coordinates-only comparison
does not warn in that exercise. This is distinct from positional-index units
in closed uibcdf/molsysmt#433. The report does not claim a wrong scientific result
or include the separate pending compression-option finding.

Provider `c17869f5ae57b87d1302b7a7fa408e1ecfec2ebd` receives bound get_form,
is_a_molecular_system and where_is_attribute, plus the explicitly supplied
are_multiple_molecular_systems utility. The first three resolve the current
loaded target through serialized reads. The collection utility requires no
loaded primary, never inserts the current MolSys, and leaves caller-owned inputs
stable/unlocked. It does not choose a loading/composition policy or adopt data.
Its owning view must remain open. Native input inspection is preserved.

The three native identification/classification helpers deliberately lack
skip_digestion. Their addon wrappers add the keyword-only boundary control but
never pass it or add native decorators. where_is_attribute retains its ordinary
native skip argument and its live owner/form result. Cached calls, pending reads,
empty/closed views, input collections and native validation all have receiving.

Provider evidence under uibcdf/molsysmt#421 records 28 focused cases, 239 applicable
addon/packaging/dependency/devguide cases and eight executable guide blocks.
Course Module 04 gains narrative only; code cells and outputs remain unchanged.
The working-source checks preserve concurrent native namespace/documentation
changes and do not claim an exact clean full-provider or installed artifact pair.
There is no host runtime change; its public API and browser protocol remain intact.
New source gates, broader namespaces/effects and GUI panels remain pending.

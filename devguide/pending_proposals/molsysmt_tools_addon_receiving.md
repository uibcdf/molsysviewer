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
copy/conversion/preflight, composition/comparison/identity readers, all eleven
current topology readers, eighteen structure calculations, native translation/rotation/reflection/fitting/centering/displacement and synchronization now
have source receiving; other namespaces/edit families, task panels and installed
qualification remain pending. Native repairs under uibcdf/molsysmt#439,
uibcdf/molsysmt#440, uibcdf/molsysmt#441 and uibcdf/molsysmt#442 are now received.
Minimum-weight/neighbor-source repairs under uibcdf/molsysmt#444 and
uibcdf/molsysmt#445 now have authorized local working-tree receiving, including
the requested native pytest matrix. Owner commit/CI and issue closure remain
separate; no published-file compatibility is inferred.

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


## First topology readers and inventory refresh — 2026-10-23

Provider `3e799c0fc7e8c9c52480cfec0489181990087e76` receives four explicit native
`topology` wrappers: bond graphs, covalent blocks/paths and dihedral quartets.
They share the existing serialized reader with `basic`, bind the current primary
and return native scientific values without edits, preparation, adoption or
scene projection. Hypothetical graph cuts do not remove bonds. No topology root
aliases are invented; the two native helpers without declared skip_digestion
receive an addon-only keyword that is not forwarded into scientific kwargs.

The provider receipt under uibcdf/molsysmt#421 records 32 focused cases, one
271-case applicable regression (176 addon, 30 packaging, 11 dependency-route,
54 devguide), nine executable guide blocks and clean-checkout devguide validation.
Source/wheel/sdist guards include all 14 addon Python files. Course Module 13
adds narrative only; executable cells and outputs remain unchanged. These are
working-source checks, not clean solver-installed artifact qualification.

The original 267-export AST ledger remains a dated snapshot. A name-only refresh
at provider `2d5fbb7d5` finds 271 exported paths across the same 21 scopes, with
no removals. New basic/root compose_atom_maps and build project_atom_names /
merge_nonpolar_hydrogens paths remain pending adaptation: their map/collection
inputs, preparation effects and lineage need individual review. This is not a
new qualification of all signatures or scientific behavior. Seven other topology
exports and broader namespaces/effects/GUI remain pending; #264 and #421 stay
partial. Native unspecified path/quartet patterns retain current native error
behavior rather than being silently guessed by the addon.

The prior exact host `26141464` browser 40008519291, policy 40008520013 and
publication-governance 40008519951 gates pass. New provider CI smoke 40012474771
is active for this topology delivery; its result remains pending. Provider Ruff,
dependency, policy, publication-governance and devguide gates pass on that exact
commit. Viewer reporting/link/index guards pass 276 cases; generated queue
indexes are current. Existing
public-backend pandas documentation failures (uibcdf/molsysmt#431) and Qt #35
retain their separate scope. No host runtime change, candidate freeze, package,
tag or release is part of this delivery.


## Topology namespace mirror completed in source — 2026-10-23

Provider `5dab4fa005ac54621db668e47cfd6ef112c8cc2c` receives the seven remaining
baseline topology exports: rings, rigid fragments, rotatable bonds, SMARTS,
atom correspondences, sequence alignment and sequence identity. All eleven
functions now have explicit native signatures and current-primary binding.
The host serialized reader is reused without new public API or frontend logic.

The provider's completion receipt under uibcdf/molsysmt#421 records 39 focused
cases and a single 310-case applicable regression (215 addon, 30 packaging,
11 dependency-route, 54 devguide). All eleven guide examples and 37 docstring
examples pass, as do Ruff and clean-checkout devguide validation. The 14-file
addon packaging inventory remains unchanged. Module 13 gains availability and
limit prose only; executable cells and outputs are preserved. Concurrent
provider stereo/documentation changes were preserved and excluded from this
commit; the working-source checks do not qualify a frozen full-provider or
solver-installed artifact pair.

Native self-comparison of capped pentalanine reports 71.428571 percent and
shifted group indices although alignment returns identical five-letter strings.
The maintainer authorized its native report, now uibcdf/molsysmt#439. This is
independent of Viewer. The wrapper preserves native output and documents the
explicit amino-acid selection route; the defect remains open without a local
scientific workaround. Native quantity-warning issue #435 has since been fixed
in source by provider `3c43a9554`; this does not qualify a corrected public package.

The earlier topology smoke 40012474771 was cancelled on main advancement, not
passed. New exact-provider smoke 40014485194 is active; hosted receiving remains
pending. Viewer `4b58da6b` policy 40012719594 and governance 40012719690 pass;
its browser run 40012719491 was still active at the last inspection. Other
namespaces/effects, general edits, lazy utilities, GUI and installed compatibility
remain pending. #264/#421 stay partial; no freeze, tag or release is introduced.
The host documentation update passes 276 reporting/link guards and the generated
queue-index check; unrelated local notebook and #259 work remains preserved.


## Six structure readers and native heavy defects — 2026-10-23

Provider `8ebb1b4d5bec058e3be837a35e29ef649f0a5333` adds six explicit structure
wrappers: distances, vectors, centers, radius of gyration, angles and dihedrals.
The current view.molsys is implicit; secondary systems/scopes remain explicit.
They reuse the existing serialized reader and return native scientific values
without edits, preparation, result attachment, measurements or scene projection.
Physical quantities, index metadata, PBC and CPU/configuration choices stay native.
The dihedral skip flag is addon-only and never enters scientific named flags.

The provider receipt under uibcdf/molsysmt#421 records 54 focused cases and a
single 364-case applicable regression, fourteen executed guide blocks and sixteen
native-docstring examples. Independent coordinate references check supported
nonperiodic distances/vectors and weighted centers/radii; broader native parity
has its own stated scope. Ruff and clean-checkout devguide validation pass.
Wheel/sdist/source guards now require fifteen addon Python files. Course Module
16 adds narrative only, preserving existing executable cells/outputs and all
protected transformation/RMSD topics.

Two native scientific defects were reproduced without Viewer and filed with
explicit maintainer authorization: uibcdf/molsysmt#440 (forced radius relabels nm
values as alternate standard units) and uibcdf/molsysmt#441 (forced same-system distances
ignore the second atom population). These affected-route parity results are
not scientific validation. The addon retains native options without silently
rerouting calculations or replacing units/formulas. Native fixes remain pending.
Owning AST discovery accounts for 28 structure exports: six received, 22 pending.
No full-provider, clean solver-installed artifact pair, optional GPU/engine or
universal RAM bound is claimed; concurrent native PDBQT work was preserved.

The prior provider c4b71b206 topology smoke 40014551589 now passes, including
all eleven topology wrappers. That scope does not qualify the new structure
commit. Its new hosted receiving is pending. Viewer 9fdd8010 policy/governance
pass; browser 40014718166 remained active at the last inspection.
uibcdf/molsysviewer#264 and uibcdf/molsysmt#421 stay partial; other
namespaces/edits, task panels, installed compatibility,
freeze and publication remain pending.

The structure commit's provider smoke 40016357086 is active. Its Ruff,
dependency-contract, policy, publication-governance and devguide gates pass.
The host documentation update passes 276 reporting/link guards and the generated
queue-index check. These checks do not replace the pending scientific smoke.


## Independent comparison readers while waiting for MolSysMT — 2026-10-23

The maintainer explicitly requires waiting for the MolSysMT development team
on uibcdf/molsysmt#441. This task neither fixes that scientific implementation
nor provides a hidden routing/formula alternative. Min/max distances, contacts
and neighbors remain pending. Reviewed direct RMSD, minimum RMSD, principal axes
and least-squares plane routes avoid the defective matrix in the exercised
numeric/property-selection scenarios; rich selectors and optional engines keep
their native dependencies.

Provider `b236c6e1206f791cfdedd2d44b9587d02bc79405` receives those four explicit
wrappers. They bind the current primary and reuse the same host reader, without
changing either coordinate domain, attaching analyses, creating shapes or
projecting a scene update. References remain caller-owned/stable. Minimum RMSD
is a scientific value, not an in-place coordinate fit. Native missing RMSD skip
control receives an addon-only keyword that is not forwarded. Axes/moments keep
native arrays and conventions; plane results keep source memberships, typed
empty scopes, physical quantity fields and normal-sign semantics.

The provider receipt under uibcdf/molsysmt#421 records 36 focused cases and one
400-case applicable regression (305 addon, 30 packaging, 11 dependency-route,
54 devguide). All seventeen guide examples and twenty-six native-docstring
examples pass, with Ruff and clean-checkout devguide validation. NumPy norms,
SVD/Kabsch, weighted covariance and plane residuals protect actual numbers in
addition to native parity. Source inventory remains fifteen addon Python files.
Module 16 receives availability/limitation prose only; its code/output and
protected native transformation topics remain unchanged. Concurrent PDBQT work,
including its shared manifest change, is preserved outside this commit.

A separate native RMSF forced-unit discrepancy was reproduced without Viewer,
filed with explicit authorization as uibcdf/molsysmt#442 and left to the scientific
team. RMSF remains unreceived. The structure inventory now accounts for ten
received and eighteen pending exports; no optional-GPU, arbitrary selector,
universal RAM or clean installed-artifact qualification is claimed.

Previous structure smoke 40016357086 passes on provider 8ebb1b4d5, covering the
first six readers. It does not qualify this new four-reader commit; exact-head
hosted receiving remains pending. Viewer 3b908582 policy/governance pass;
browser 40016645007 was still active at the last inspection. Overall receiving
under uibcdf/molsysviewer#264 and uibcdf/molsysmt#421 stays partial. Other
namespaces/edits, panels, installed compatibility, freeze and publication remain
outside this delivered scope.

Exact-provider smoke 40018415983 is active; Ruff and dependency-contract gates
pass, while other hosted gates remain pending. The host documentation update
passes 276 reporting/link guards and the generated queue-index check. These
results do not replace the pending source smoke or qualify an installed package.


## Native corrections received; relation readers extended — 2026-10-24

Provider `41388ce99d02eefaab92b1dc290545f002d3a8c6` receives the scientific
repairs from bae6d0101 and 1123eeb7d through bc2142831, plus three new explicit
structure wrappers: maxima, contacts and RMSF. The native sequence flag is now
declared keyword-only and forwarded; actual contributing source-group mapping,
heavy distance populations and radius/RMSF length attribution are received.
No addon formula, argument substitution or hidden routing correction is added.

The new receipt under uibcdf/molsysmt#421 records 47 focused tests and a single
535-case applicable regression including the three owning native repair guards,
all addon/packaging/dependency/devguide checks. Eighteen guide blocks and 74
native-context docstring examples pass. Ruff and clean-checkout devguide
validation pass. Independent norms, weighted centroid/variance, thresholds and
argmax/index calculations protect actual scientific values in nm/angstrom/pm
and repeated structure scopes. Input science, reference ownership, saved analyses
and scene state remain separate from returned results. The source inventory
remains fifteen addon Python files. Course Modules 13/16 gain only current
receiving prose; executable cells/outputs stay unchanged. Historical source
receipts remain immutable.

Two additional forwarding defects were independently reproduced without Viewer:
minimum distances reuse first-population weights for the second center
(uibcdf/molsysmt#444), and neighbors ignore an explicit second system in fallback
(uibcdf/molsysmt#445). The maintainer authorized both reports and explicitly
requested a native pytest contract matrix for all four distance/neighbor/extrema
functions in both issues. That request covers source populations, independent
weights, structure correspondence, PBC/units, execution modes, output/index
metadata, errors and preservation, with numeric/index references independent of
shared implementations. No scientific fixes are implemented here; the two new
wrappers remain pending. The current structure inventory is thirteen received
and fifteen pending exports, not a complete or fully scientifically certified
module. Overall uibcdf/molsysviewer#264 / uibcdf/molsysmt#421 remain partial.

Provider smoke 40123084475 passes on bc2142831 for the repaired previous readers;
its 833-case owner qualification has its own scope. It does not qualify these
three newly added wrappers. Exact new-head smoke 40125052535 remains active;
dependency, guide, publication governance, Ruff and suite-policy gates pass.
The host reconciliation passes 276 reporting/link guards and its generated
queue-index check. This is source receiving, not clean solver-installed
artifacts, optional-GPU qualification,
universal RAM bounds, version freeze, tag, Release or package publication.


## Local minimum and neighbor receiving — 2026-10-24

The maintainer authorizes receiving the provider working tree before its owner
commit. Explicit get_minimum_distances and get_neighbors wrappers preserve the
native signatures after primary binding, including native skip_digestion. The
neighbor wrapper re-scopes the native criterion-admission contract before
forwarding defaults; absent criteria stay absent and explicit incompatible calls
still fail. No scientific formula, weight substitution or fallback is added.

The local receiving record under uibcdf/molsysmt#421 retains provider base
3502232d802ee2927f6b6f5d19f0ae045777ecb5, host base f9a87cb55f9041cffab415fa3b3ddaded54c647a,
file/extension SHA-256 values and original JUnit digests. The source is unchanged
during the 1001-case applicable regression: all pass without errors or skips.
It includes 424 cases from the native family matrix and the 89-case bound
relation file. Nineteen guide blocks and 74 native-context docstring examples
pass, as do Ruff and the sixteen-file packaging inventory. The addon receiving
paragraph in Course Module 16 changes narrative only; the scientific team owns
its independent course changes.

Independent physical-value/index references cover separate endpoint weights,
translated auxiliary systems, repeated structures, units and supported sparse
outputs. View state, analyses, pending-edit status, lifetime and replacement
binding remain guarded. Structure now has fifteen received and thirteen pending
exports; other namespaces, task panels and installed qualification remain partial.
Provider commit/CI and the owner's closure of uibcdf/molsysmt#444 and
uibcdf/molsysmt#445 remain separate. No tag, package, dependency-floor change,
release candidate freeze or public publication is implied.

Host reconciliation passes 276 reporting/link guards and the generated-index
check. Provider developer-guide validation also passes on the local tree.


After this stable regression, the scientific team updated the five native public
function files while extending their documentation. Those later file hashes are
recorded separately; the earlier 1001-case result is not automatically transferred
to changed bytes. The updated documentation passes 19 guide blocks and 90
native-context docstring examples. Final owner-commit/CI reconciliation remains
pending. Host reporting/link guards pass 276 cases and both guide/index checks
pass.


## Structural-analysis source receiving — 2026-10-24

The provider working tree adds get_symmetry_corrected_rmsd,
get_secondary_structure and principal_component_analysis through the existing
serialized primary reader. Native signatures, explicit references, chemical
states, map/constraint scope and execution choices remain intact. The native
secondary-structure helper has no skip flag; its addon-only keyword is not
forwarded. The other native flags retain their ordinary semantics. No host
runtime, wire protocol, coordinate edit or result attachment is introduced.

The provider receipt under uibcdf/molsysmt#421 records 1099 passing
applicable regression cases and 44 focused real-view cases, zero failures/errors/
skips, plus 22 guide blocks and 103 native-context docstring examples. Original
JUnit digests, exact source hashes and source copies are retained. The watched
scientific and addon sources stay unchanged during this regression. Only the
generated version module changed when the owner committed those scientific
corrections; result version strings retain their initial-import provenance. Native/packaging/lifecycle
checks and Ruff pass; this does not qualify clean solver-installed artifacts.

Independent weighted covariance reconstruction and pose geometry over explicitly
declared maps protect values and units; MDTraj codes and actual group/structure
correspondence protect the DSSP integration. Tests retain saved analyses, scene
state, pending updates and cached reader binding after replacement. Discovery
does not import the optional engines. Numerical degeneracy, dense PCA memory,
engine prerequisites and experimental symmetry scope stay explicit.

Native PCA's documented list weights reproduce a Rust type failure independently
of Viewer. The authorized owner report is uibcdf/molsysmt#448. The received CPU
routes use default or float64 ndarray weights, with no addon normalization or
scientific workaround. Eighteen structure readers/calculations are now received;
ten coordinate-changing exports remain pending. The course addon paragraph gains
only current receiving prose; other provider course changes are separately owned.
Overall uibcdf/molsysviewer#264 / uibcdf/molsysmt#421 remain partial, and local
source receiving does not authorize publication or imply completed exact-head CI.


The native scientific owner subsequently committed 5710cc0cff1f3f468823699104e51e6fe029c3b2 and closed
uibcdf/molsysmt#444 and uibcdf/molsysmt#445. This reconciles the earlier local
receiving without rewriting its original hash-scoped evidence. The pending PCA
weight-container defect stays under uibcdf/molsysmt#448. Addon-head CI remains
separate from the native commit and the local applicable regression.

The five newly received readers (minimum distances, neighbors and the three
structural analyses) are integrated in provider main at
`5f1411ac319d10f510c2ba305fb80aeed9825ef4`, over the native scientific fixes and
synchronized integration guides. This head includes the new analysis file in
hosted smoke. Host reconciliation passes 276 reporting/link guards and the
generated-index check; provider guide validation passes. Exact new-head hosted
CI is pending at integration, without a duplicate dispatch or package rebuild.

## Exact provider-head CI completed — 2026-10-24

Provider `5f1411ac319d10f510c2ba305fb80aeed9825ef4` passes all six applicable
hosted checks. [Smoke 40133538822](https://github.com/uibcdf/molsysmt/actions/runs/40133538822)
passes the native bounded tier (499 cases) and the bound-addon tier (439 cases),
with no failures, errors or skips in either summary. Its command includes
`test_structure_analysis_tools.py`; the installed test environment provisions
MDTraj and RDKit. Import, API stability, docstrings, forms and Rust-runtime checks
also pass. Dependency contract 40133538774, Ruff 40133538846, guide integrity
40133538992, publication governance 40133539039 and suite policy 40133539191 pass.

The first final gh-run-receptor request did not execute because automatic
permission review timed out. Native read-only GitHub inspection and the original
job log independently confirm success; this is not a receptor or test failure.
The log is retained locally at `/tmp/msm-addon-5f1411-smoke.log`, SHA-256
`fa7aa78dd7c9b5b4ec930373d460e13c8613df41a24d4a97c51c319889f4b747`. No rerun,
publication dispatch, package reconstruction, version freeze or promotion was
performed. The new PCA weight-container report uibcdf/molsysmt#448 remains
separate; the qualified default/float64-array CPU routes are unchanged.


## Translation and PCA weight repair received — 2026-10-24

The explicit structure.translate wrapper preserves native defaults and returns,
including independent in_place=False output. In-place calls add only keyword-only
update_view=True over the existing coordinator. Family preflight resolves retained
target/selection/structure scope and active-edit exclusion; native science owns
displacement, broadcasting and publication. Independent results are not adopted.
No host runtime, protocol, alternate scientific calculation or full scientific
recovery snapshot is added.

Targeted receiving passes 35 translation cases and 79 structural-analysis cases.
The one applicable 1274-case regression records 1268 passes and six failures from
the obsolete assertion that translate must be absent. The expected public
inventory was updated; all 89 cases in the two affected files pass, including
all six original failures. The full local suite was not repeated. Original
JUnit digests and source snapshots distinguish the initial run and focused
correction; they are not mislabeled as a single green full-suite run. Runtime
scientific/addon files remain fixed during that initial run; only the generated
version module changes. Ruff and 23 guide blocks/105 native-context docstring
examples pass. Exact-head hosted CI remains a separate gate.

Independent displacement and weighted covariance references guard physical
values/units, source ownership, repeated/nonconsecutive axes and repaired PCA
containers/dtypes from 306e91dda (uibcdf/molsysmt#448). Native setter invalidation
preserves unaffected named-analysis coverage. Tests retain scene handles, source
records and navigation, compose pending geometry/removal, and exercise real
transport failure after science with synchronization-only retry. Possible partial
publication becomes uncertain rather than implying rollback or repeat execution.

The authorized native report uibcdf/molsysmt#451 records center's partial-reference
target and in-place return inconsistency without Viewer. Center remains absent;
its scientific owner decides the supported population contract. Source now
provides eighteen structural readers/calculations plus one native coordinate
editor; nine coordinate-changing exports and the broader addon remain partial
under uibcdf/molsysmt#421 / uibcdf/molsysviewer#264. No package, public floor,
version freeze or release is implied.

Native translation and the extended PCA receiving are integrated in provider
`dcc2ca4e1e7a06f1abaed51dd8dd61933ba16933`. The clean exact-commit checkout passes
developer-guide validation and canonical queue-index checks independently of
concurrent file-copy work under uibcdf/molsysmt#450. The committed CI/manifest
hunks and issue index include only this receiving. Host reconciliation passes
276 reporting/link guards. Exact new-head CI remains pending at integration.


## Translation receiving CI completed on descendant head — 2026-10-24

Smoke 40142340045 on `dcc2ca4e1e7a06f1abaed51dd8dd61933ba16933` was cancelled
during the native test tier. GitHub and gh-run-receptor preserve cancellation
with unknown termination cause; it is not a passing result. The workflow uses
`cancel-in-progress: true`, and the subsequent provider push created the existing
replacement run. No cancellation, duplicate dispatch or rerun was requested here.

Descendant `04be76b63fa09cc9713ff20c7c78c46f855df817` retains the translation/PCA
addon sources and tests unchanged, adds the native file-copy repair, and extends
the native bounded CI tier with its guards.
[Smoke 40142480213](https://github.com/uibcdf/molsysmt/actions/runs/40142480213)
passes 655 native cases and 509 bound-addon cases, with no failures, errors or
skips in either summary. The original command includes both
`test_structure_analysis_tools.py` and `test_structure_transform_tools.py`.
Dependency contract 40142480167, Ruff 40142480155, guide integrity 40142480154,
publication governance 40142480426 and suite policy 40142480388 also pass. This
qualifies that descendant source head, not a completed smoke run on its parent.

The original job 121016921506 log is retained at
`/tmp/msm-addon-04be76-smoke.log`, SHA-256
`bb0d3f2490265bc782cf3b60a68e00a801f58211da28eb172c097cc494f83ee1`.
Native GitHub metadata and log summaries agree with gh-run-receptor's successful
offline replay. Its initial inspect found an already-existing cache bundle;
replay used that bundle without overwriting it. No package qualification, public
publication or change to the pending center report uibcdf/molsysmt#451 is implied.


## Rotation and reflection received — 2026-10-24

Explicit structure.rotate and structure.flip wrappers mirror native scientific
parameters, independent in_place=False outputs and in-place None returns. The
existing retained-axis coordinator owns synchronization; no Viewer runtime,
protocol or scientific normalization is added. Flip's keyword-only
skip_digestion controls addon validation only, because the native callable has
no declared flag. Native public validation remains active.

Independent Cartesian quarter-turn/plane references and inverse/involution and
distance invariants receive proper rotations and explicit-unit-normal reflections.
Matrix lists, strided/read-only per-structure stacks, per-atom stacks and actual
SciPy Rotation objects retain native behavior. nm/angstrom/pm contexts, repeated
and nonconsecutive atom/structure axes, untouched boxes and exact edited-structure
interaction invalidation are exercised with real bundled views. Deferred mixed
rotation/translation/removal/reflection retains scene handles, selections, source
accounting and navigation. A real transport interruption after completed science
is recovered by synchronization without executing the transformation twice.

The focused transform file passes 93 cases. The single applicable regression
passes all 733 cases, with zero failures/errors/skips. Scientific/addon source
hashes remain fixed during the regression; only the generated version module
changes. Ruff check/format and 24 guide blocks/110 native-context docstring
examples pass. Original JUnit digests, scope and before/after source snapshots
are retained in the provider's rotation receiving record. Host reporting/link
checks pass 280 cases. Exact committed-head CI remains a separate pending gate.

Native flip independently rejects vector=None before its implementation fallback;
nonunit vectors are not normalized and change distances, while a zero vector is
accepted as a no-op. This receiving certifies only explicit unit normals and
retains the defects visibly in runtime help and owning documentation. The addon
supplies no hidden alternate formula. Center stays absent pending
uibcdf/molsysmt#451. Twenty-one structure tools are now available in source:
eighteen calculations and three coordinate editors; seven reviewed edits and
the broader API/panels remain partial under uibcdf/molsysmt#421 and
uibcdf/molsysviewer#264. This does not qualify installed artifacts or authorize
any tag, release or public promotion.


Provider integration is committed at
`fd2b28a1d4f299466964fd0bf69f5358973b7af4`. Its clean exact-commit checkout
passes developer-guide and canonical index validation, excluding the concurrent
native center report/test edits. The host requires no runtime changes. Hosted
CI on this source head remains pending at integration.


## Exact rotation/reflection provider-head CI completed — 2026-10-24

All five applicable hosted checks pass for
`fd2b28a1d4f299466964fd0bf69f5358973b7af4`.
[Smoke 40143949434](https://github.com/uibcdf/molsysmt/actions/runs/40143949434)
passes 655 native bounded-tier cases and 567 bound-addon cases, with no failures,
errors or skips in either summary. The command includes the extended
`test_structure_transform_tools.py`. Ruff 40143949368, guide integrity
40143949534, suite policy 40143949630 and publication governance 40143949637
also pass. This is the applicable source-head campaign; no extra matrix or
installed-artifact qualification was dispatched.

gh-run-receptor's successful terminal report agrees with native GitHub metadata
and the original job 121021255617 log. The log is retained at
`/tmp/msm-addon-fd2b28-smoke.log`, SHA-256
`c41479e63d7515a4ad5d77832eb7990159274f7a68c5716e1858656940bf4f9c`.
These passing qualified-input tests do not clear the native default/nonunit/zero
normal reflection findings above. Their owning issue draft is prepared, and the
explicit offer to open it awaits the maintainer's answer. No native scientific
fix, package publication or completion of the broader addon is inferred.


## Native rigid fitting and sequence alignment received — 2026-10-24

Explicit structure.least_rmsd_fit and structure.least_rmsd_align preserve native
scientific signatures, independent defaults/results and in-place None returns.
Only keyword-only update_view is added over the existing geometry coordinator.
Fit anchors and moved populations remain distinct; sequence-derived alignment
moves whole selected components. Caller-owned references remain stable inputs,
without locking or synchronizing another view. Independent outputs and conversion
stay in Python; native setters own exact edited-structure analysis invalidation.
No alternate correspondence, fitting, periodic reimaging or host runtime is added.

Independent Cartesian poses protect physical values, partial and whole-component
movement, reference indices and mixed-unit native reference forms. Repeated and
nonconsecutive structures, native CPU precision, cached facade/replacement,
source/scene identities, pending mixed edits and actual transport failure are
received. Synchronization-only retry preserves coordinate storage; an exception
after a real scientific publication enters uncertain state instead of rollback
or repeated science.

The final focused file passes 49 cases. The single 956-case applicable regression
records 952 passes and four failures from a historical assertion that
least_rmsd_fit must still be absent. Only that inventory expectation was corrected;
all 85 cases in the two affected files then pass, explicitly including all four
original failing nodes. The full local suite was not repeated or relabeled green.
Initial fixture corrections and the native numeric-selection reproduction retain
separate original JUnits in the provider's fitting receiving record.

Concurrent native center/get_center and related scientific/documentation work was
present in the local tree. Watched hashes record center.py and generated version
changes during regression; bound-addon/fitting-test sources remain fixed. The
run is scoped working-tree evidence, not one clean immutable native head. Other
native edits and shared-page hunks are excluded from this integration. Exact
committed-head hosted CI remains a separate gate. Ruff and 25 guide blocks/114
native-context docstring examples pass; host reporting/link checks pass 280 cases.

The authorized native reports uibcdf/molsysmt#452 and uibcdf/molsysmt#453 record
None-reference failure and numeric atom/group-index confusion in least_rmsd_align.
Its received route uses explicit references and MolSysMT expression selections;
no silent reference replacement or index-to-expression rewrite is introduced.
Native least_rmsd_fit's implicit self-reference is received separately. Optional
GPU forwarding is not GPU qualification. Earlier reflection limits and the
unreceived center under uibcdf/molsysmt#451 remain separate. The source facade now
exposes twenty-three structure tools: eighteen calculations and five coordinate
editors, with five other reviewed edits and broader coverage/panels pending under
uibcdf/molsysmt#421 / uibcdf/molsysviewer#264. No installed package qualification,
public floor, tag, release, version freeze or promotion is implied.


This receiving is integrated in provider
`5afb557eb6f9304ab48e2df2b6c2d1a0be000b77`. A clean exact-commit checkout passes
developer-guide and canonical queue-index validation. Only the fitting-related
course paragraph, manifest description, workflow addition and generated #452/#453
index delta were staged from shared files; unrelated native-center hunks remain
local to their owner. Exact hosted CI is pending at integration.


## Fitting receiving CI completed on descendant head — 2026-10-24

Smoke 40147023405 on `5afb557eb6f9304ab48e2df2b6c2d1a0be000b77` was cancelled
during toolchain provisioning. GitHub and gh-run-receptor retain unknown
termination cause; the workflow declares cancel-in-progress, and a subsequent
native-owner push created the replacement campaign. The cancellation is not a
passing result; no manual cancellation or duplicate dispatch was requested here.

Descendant `5814dc534cecf179df8bf8f8009c8e21f1593c6e` preserves all bound-addon
sources and tests from the fitting commit unchanged. It separately integrates
the owner's center/get_center contract and related callers/docs, and adds native
center/documentation guards to the bounded CI tier. Native uibcdf/molsysmt#451
is closed; receiving its redesigned center wrapper remains a separate addon task.

[Smoke 40147106374](https://github.com/uibcdf/molsysmt/actions/runs/40147106374)
passes 853 native cases and 616 bound-addon cases, with no failures, errors or
skips in either summary. Its command includes `test_structure_fitting_tools.py`.
Dependency contract 40147106336, Ruff 40147106353, guide integrity 40147106351,
suite policy 40147106563 and publication governance 40147106623 also pass. This
qualifies that descendant source head; it does not relabel the cancelled parent
smoke or the original locally failed inventory assertion as successful.

gh-run-receptor's successful terminal report agrees with native GitHub metadata
and original job 121030682024. The original log is retained at
`/tmp/msm-addon-5814dc-fitting-smoke.log`, SHA-256
`526d3774e0575a995db02ce9a07ac9df2563cfc0eefd4081de9fcc8be0ee4390`.
Native alignment limitations under uibcdf/molsysmt#452 / uibcdf/molsysmt#453 remain
open and explicit. No installed qualification, package reconstruction, version
freeze or public publication is implied.


## Explicit native centering received — 2026-10-24

The bound structure.center mirrors the new native moving/source/initial-target
contract, with source containment, source-only weights, physical destination
units, repeated-scope rules and retired-name rejection. Keyword-only update_view
is the only addition. Native computation, independent default/output ownership,
in-place None returns and edited-structure interaction invalidation remain in
MolSysMT. The existing coordinator retains scene identities and composes pending
edits; no centroid calculation, periodic preparation, molecular snapshot or host
runtime is introduced.

Sixty-eight focused cases pass on real bundled views. The single applicable
regression runs in an isolated checkout based on
99cb83107, applying only the centering reception: **1007 passed**, no failures,
errors or skips, and no watched source changes during execution. Import-origin
assertions confirm isolated Python sources; the existing in-environment native
Rust extension is reused and its path/digest recorded. This is source evidence,
not a new solver installation or compiled-artifact qualification.

Independent weighted/geometric means, coordinate displacements and rigid pair
vectors cover units, defaults, mass weights, repeated atoms and structures,
point/per-structure destinations and overlapping/disjoint/contained initial
targets. Tests distinguish an initial destination snapshot from a final-center
constraint, retain untouched coordinates/box and native named-analysis scope,
exercise real transport interruption, and reject invalid populations/targets
without publication. Deferred center/removal/translation retains scene/source
identities and navigation; synchronization never repeats the science. A real
native publication followed by a pipeline exception becomes uncertain.

Ruff check/format passes six Python files. Twenty-six guide blocks and 120
native-context docstring examples pass. Host reporting/link checks pass 280
cases. Original JUnits, import origins and source snapshots are retained in the
provider's centering receiving record. The native owner separately integrates
alignment repairs in a38c00d19; their scientific/admission/docs changes are
preserved when applying this reception. Exact integrated-head CI remains a
separate gate, and the full local regression is not repeated.

At the maintainer's explicit request uibcdf/molsysmt#451 was reopened with the
missing closure-traceability appreciation; its scientific fix in 5814dc534 and
archived evidence remain accepted. Reopening does not block this addon work or
reopen its numerical diagnosis. Native uibcdf/molsysmt#454 documents the separate
executed course-preparation correction. The facade now has twenty-four structure
tools: eighteen calculations and six coordinate editors, with four reviewed
geometry editors and broader namespaces/task panels still pending under
uibcdf/molsysmt#421 / uibcdf/molsysviewer#264. No public floor, version freeze,
release, package reconstruction or promotion is implied.


The bound centering reception is integrated in provider
`fc2936bf9efd198f02f1d195107e5a5e6f62d13b`, preserving parent a38c00d19's
separate native alignment repairs. A clean exact-commit checkout passes
developer-guide and canonical index validation. No host runtime changed.
Hosted qualification of this integrated head remains pending at integration.


## Exact integrated centering-head CI completed — 2026-10-24

All six applicable hosted controls pass for
`fc2936bf9efd198f02f1d195107e5a5e6f62d13b`.
[Smoke 40150164745](https://github.com/uibcdf/molsysmt/actions/runs/40150164745)
passes 1018 native bounded-tier cases and 696 bound-addon cases, with no failures,
errors or skips in either summary. The command includes
`test_structure_center_tools.py`. Dependency contract 40150164749, guide integrity
40150164737, publication governance 40150165026, Ruff 40150164740 and suite policy
40150164976 also pass. The initial scheduling delay had runner_id=0; no manual
cancellation, rerun or duplicate dispatch was performed.

gh-run-receptor's successful terminal report agrees with native GitHub metadata
and original job 121039854054. The original log is retained at
`/tmp/msm-addon-fc2936-center-smoke.log`, SHA-256
`3f198d372b2520eae7ed99b02fa27334e04c1c44ef7282c9359c684463d10ba8`.
This qualifies the exact integrated source head, including the independently
owned alignment repairs inherited from a38c00d19; it does not substitute for
installed-artifact or full supported-platform qualification.

The maintainer-requested reopening of uibcdf/molsysmt#451 is confirmed at
https://github.com/uibcdf/molsysmt/issues/451#issuecomment-6391625013. It remains
open for its missing closure comment; no scientific regression or revocation
of 5814dc534's archived centering evidence is asserted. The new wrapper is
received under uibcdf/molsysmt#421 / uibcdf/molsysviewer#264, whose broader scope
remains partial. Tags, packages, public floors and promotions are unchanged.


## Single-structure displacement receiving — 2026-10-25

The provider implements structure.move_away through the existing retained-axis
coordinator with native defaults/returns and explicit reference inputs. No host
runtime changes are required. The namespace exposes 25 structure tools:
18 calculations and seven coordinate editors. align_principal_axes and the two
dihedral editors remain pending; broader namespaces/panels and installed
qualification are separate.

The focused guard tests/molsysviewer_molsysmt/test_structure_move_away_tools.py
in the provider passes 38 cases with independent NumPy displacement oracles.
It covers weighted source/reference centers, both modes, non-default unit policies,
copy/in-place ownership, current-primary rebinding, selected-structure analysis
invalidation, scene maps and synchronization retry without repeating science.
The native all-default/degenerate-direction route remains unqualified under
uibcdf/molsysmt#456; multi-structure explicit rejection after partial publication
is tracked under uibcdf/molsysmt#457. Both are reproduced without Viewer and opened
with the maintainer's explicit authorization. No scientific workaround is added.
Broader regression, source identity and CI completion follow separately; no
package or release is implied.


### Completed local displacement qualification — 2026-10-25

The focused guard passes 38 cases. Local regression covers 1061 distinct cases
without a full-suite rerun: the first campaign passed 964, then was interrupted
(exit 2) in a documentary matplotlib Qt plt.show loop inherited from DISPLAY=:0.
The remaining 97 previously unexecuted cases pass with MPLBACKEND=Agg (exit 0).
Both original JUnits are preserved; this is composite evidence, not a single green
run. Scientific/addon source hashes and the compiled backend remain unchanged;
the developer packaging tests regenerate ignored molsysmt/_version.py metadata.
All 27 addon-guide blocks and 125 native-context doctests pass; Viewer
reporting/link guards pass 280 cases. Ruff and provider guide/index validation
pass. MolSysMT's source receipt is
`devtools/data/molsysviewer_tools_move_away_receiving_20261025.json`.
It retains JUnit digests, source/import origins, the native-only reproductions
and actual uncertain-state receiving of #457; sync_view refuses to bless the
partial write. These are not live Qt/window rendering observations.

The independently owned ArgDigest receiving commit 9135cee1fd29f8591d29d802562c34cc27c44353
is preserved as integration parent; its source tests/docs are not bundled as our
changes. Hosted exact-head qualification remains pending at this checkpoint.
No installed compatibility or release is asserted; #456/#457 require the
scientific owner's repair.


### Integrated displacement source — 2026-10-25

Provider a5fb4e2f0eac2c0b7139a8453122335b175d92e3 is pushed to main.
Its actual immediate parent is 9135cee1fd29f8591d29d802562c34cc27c44353,
which adds only three supported-inventory test assertions and preserves the
separate ArgDigest receiving. Clarification: the source receipt's
integration_parent field captured afd906b577d74ad574063efd3177ea16e833a088
at receipt preparation; that field is not the final immediate Git parent. The
concurrent supported-inventory test commit landed before the feature commit.
No scientific/addon source changed between local qualification and integration.
Both independent owner commits and the three unrelated generated-RST edits are
preserved. The exact source CI is now running; no manual heavy dispatch, package
publication or tag change is implied.


## Exact integrated displacement CI completed — 2026-10-25

All six applicable hosted controls pass for
`a5fb4e2f0eac2c0b7139a8453122335b175d92e3`.
[Smoke 40240550036](https://github.com/uibcdf/molsysmt/actions/runs/40240550036)
passes 1018 native bounded-tier cases and 734 bound-addon cases, with no failures,
errors or skips in either summary. The command explicitly includes the new
`test_structure_move_away_tools.py`. Dependency contract 40240549993, guide
integrity 40240549971, publication governance 40240550224, Ruff 40240549961 and
suite policy 40240550251 also pass. No duplicate/manual heavy campaign was launched.

gh-run-receptor's terminal PASS agrees with native GitHub metadata and original
job 121311208884. The original log is retained at
`/tmp/msm-addon-a5fb4e2f-move-away-smoke.log`, SHA-256
`e497c8ec510822b4619febf57c069a99b224fc75c5f3c8cb3280703facd15e86`.
The CLI required explicit escape-sequence permission to save the original log;
only sanitized summary lines were displayed. Native source qualification uses
the workflow's declared Viewer pin deaba4cbea43015859544b1b393ecbe02dd2ee19.
It is separate from local receiving against the current Viewer checkout and
from installed-artifact, full-platform or live-GUI qualification. The prior
receipt's pending-CI state describes preparation; this is its terminal closure.

uibcdf/molsysmt#456 and uibcdf/molsysmt#457 remain open, confirmed after CI.
They retain the two native reproductions and scientific acceptance criteria.
Single-structure nondegenerate displacement is received; the dangerous default/
zero-direction and partial multi-structure routes are not qualified by this
green source CI. Three structure editors and broader addon coverage remain
pending under uibcdf/molsysmt#421 / uibcdf/molsysviewer#264. No tag, package,
public dependency floor, promotion or publication changed.

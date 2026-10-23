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
independent extraction. Retained-axis native removal and synchronization now
have source receiving; other edit families, task panels and installed
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

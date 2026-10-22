# Molecular edits and view reconciliation — revised integration direction

**Status: proposed technical contract under the approved
[core/add-on boundary](core_and_addon_boundary.md) — revised 2026-10-22.**
The earlier requirement for automatic observation of linked MolSys edits is
superseded. The maintainer accepts visual core ownership and additional
molecular tools in an add-on/scientific interface. Explicit reconciliation and
coordinated tool operations are the current design basis. No runtime add-on,
new synchronization API, setter retirement or molecular Undo is implemented.

## Accepted responsibilities and proposed routes

Scientific edits belong to MolSysMT. Core Viewer owns scene reconciliation and
presentation; an integrated molecular tool coordinates the two. Python remains
headless and composable. Its direct MolSysMT calls do not acquire implicit
Viewer notifications or universal tracking of mutable arrays/tables.

| Case | Direction / current limit |
| --- | --- |
| Direct supported MolSysMT edits of `view.molsys` | Caller requests explicit qualified reconciliation after the edit sequence. The exact same-object contract still needs receiving. |
| Edit through the proposed MolSysMT tools add-on | The integrated operation can coordinate scientific editing and scene update; wrapper arguments and batching are not frozen. |
| Independent result from extraction/copy/calculation | Return the result with provider semantics; incorporation into this view is explicit. |
| Raw array/table/alias mutation | No general observation or validity guarantee. Advanced callers retain explicit invalidation/reconciliation responsibilities. |
| Camera, frame or display-only change | Existing scene/navigation contracts; no molecular mutation or scientific rerun. |

The current public extension namespace is `view.addons`. A proposed
`view.addons.molsysmt` tools interface is not currently available: the retired
legacy integration remains refused under uibcdf/molsysviewer#186. The backend
MolSysMT dependency remains required regardless of optional tool presentation.

`view.extract()` remains a view operation returning another view; `load()`
retains explicit add/replace/append intent. `apply_system_edit()` remains the
advanced public adoption/reconciliation boundary. Scientific cell assignment
belongs to MolSysMT and cell-edge display to Viewer. Existing `set_box` and
coordinate APIs remain until any replacement is explicitly designed, qualified
and documented. Planning alone removes no API and raises no dependency floor.

## Provider response and decision rationale

uibcdf/molsysmt#413 proposes editing the linked native object through public
scientific operations, then reconciling explicitly once a group of edits is
complete. Copies would be optional, independent outputs keep their return
semantics, and direct in-place edits do not promise previous-state retention.
The provider asks which information remains missing for geometry versus
axis-changing edits and whether the existing Viewer primitive suffices.

The accepted product boundary removes the requirement for a general native
observer/subscription mechanism. Runtime subscription complexity is not
justified by a concrete current use case. Several tools may still share
private integration services; this does not require observing external calls.
The consumer has now withdrawn the general observer request and told the
provider uibcdf/molsysmt#413 may close without a new deliverable. The
[consumer decision](https://github.com/uibcdf/molsysmt/issues/413#issuecomment-6353744305)
keeps operation-specific receiving separate. No observer API or final wrapper
contract is delivered. Scientific invalidation and visual synchronization
remain distinct.

## What current source actually supplies

Viewer source inspected is `d96b073f23247e25cd42c95af545b6d20e7fa982`, with
the history-boundary follow-up in `b6cc4158c61095421b16d2f37e59f5d657f64f93`.
The original operation inventory retains its separate fixed provider baseline
`b501bfd69ad3e692ceeb865ebcdbd0cd1deed173`; notification-specific source
inspection uses provider `70103677841fba359c7e1ca9b092d04d41e5807e`.

- `apply_system_edit` installs the supplied object before completing scene
  rebuilding. It invalidates interactions by default and clears scene history;
  it is not a complete molecular transaction. Arbitrary failures after mutation
  have no general rollback guarantee.
- `extract` creates a different view and explicitly transfers atom/structure
  correspondence, including repeated structures. Its object-transfer policies
  differ deliberately from live editing, e.g. dropping versus retaining broken
  anchored objects. Reuse mechanisms with explicit policies.
- `load` prepares conversion/composition before mutation. Add/append and
  replace have distinct commit paths. Successful molecular loading clears
  scene-only history; #262 guards replacement, rejection, reset and initial
  shape-only loading. Molecular Undo remains unimplemented.
- `set_box` validates scientific inputs, assigns the live MolSys cell, verifies
  the assignment, reconciles affected analyses and requests rebuilding. Its
  targeted provider-assignment check is not a universal rollback boundary.
- MolSysMT controlled setters already coordinate scientific invalidation within
  the native MolSys. Inspected routes do not supply a general public committed
  edit/subscription boundary for Viewer. Diagnostic signals alone do not imply
  such a contract.

Provider uibcdf/molsysmt#407 separately considers safer raw/uncoordinated native
mutation boundaries after 1.0. Withdrawing uibcdf/molsysmt#413 does not relabel
that work or make arbitrary aliases observable. Provider uibcdf/molsysmt#406
owns remove mutation semantics; uibcdf/molsysmt#369 owns explicit permutations.
Viewer #259 remains separate receiving of copy/edit ownership.

## Contracts still to design and qualify

1. **Same-object versus replacement reconciliation.** Editing the actual bound
   MolSys and adopting an independent result have different ownership and
   before-state availability. Do not treat equal object identity as a no-op.
2. **Correspondence.** Atom/frame/state changes require authoritative maps or an
   explicit unknown-correspondence policy. Preserve known nonconsecutive and
   repeated structure mappings where admitted. Counts and source labels do not
   prove identity.
3. **Deferred update safety.** A proposed `update_view` boolean or batch operation
   must define pending synchronization, accumulated maps, allowed scene actions,
   stale visual selections, completion and failures. It cannot merely suppress
   redraw and silently leave old indices active. Decide the API after review.
4. **Scientific applicability and failure.** Retain provider invalidation and
   distinguish rejection, no-op, committed change and possible partial writes.
   Current `apply_system_edit` conservatively invalidates analyses by default;
   do not use it blindly as a refresh or silently certify preserved analyses.
5. **Recovery and resources.** Managed molecular Undo requires qualified retention
   before destructive writes, explicit history policy and measured residency.
   A later reconciliation call cannot reconstruct data already overwritten.
6. **Shared integration.** Core visual operations and add-on tools use existing
   Python reconciliation/history/transport owners. Keep scientific results
   distinct from their representations and retain producer provenance.
7. **Commit and display.** A disconnected popup does not undo successful science
   or authorize repeating it. Track display synchronization and resynchronize
   canonical state through the existing endpoint owners.

## Receiving order

1. Keep the resolved #262 scene-history boundary distinct from new recovery.
2. Agree a supported operation matrix and receive the public provider contracts
   for copy, in-place edits, outcomes and maps. Viewer #259 remains consumer
   receiving; uibcdf/molsysmt#406 owns removal semantics,
   uibcdf/molsysmt#369 permutations and uibcdf/molsysmt#407 raw mutation
   boundaries. Earlier source observations are not latest-package
   qualification.
3. Qualify same-object coordinate/box/attribute reconciliation and separately
   admit axis-changing edits. Review invalidation, stale handles, errors,
   repeated/nonconsecutive structure maps and pending-update interaction.
4. Design the MolSysMT tools add-on API/panels and wrapper return/update policy.
   Classify each operation under the accepted core/add-on boundary before
   implementation. Reuse scientific tools; no public wrapper per shortcut.
5. Qualify actual widget/popups, headless Python and exact installed artifacts.
   Retire any redundant setter only through its own reviewed migration.

The earlier standalone Studio prototype remains a comparison artifact with toy
edits; it does not qualify current panel placement, molecular reconciliation or
an add-on implementation. Both 1.0 publications remain paused.

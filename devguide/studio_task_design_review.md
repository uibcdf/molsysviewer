# Studio general tools — design review and interactive prototype

**Ownership revision — 2026-10-22:** the approved
[core/add-on boundary](core_and_addon_boundary.md) supersedes the prototype's
native-Studio placement of general molecular tools. Retain its forms, layout
observations and toy recovery only as comparison inputs for add-on/tool design.
The artifact has not been rewritten or requalified for the revised placement;
its hashes and original visual review retain their original scope.

**Status: proposed — 2026-10-22.** Product direction is accepted in the
[integration plan](studio_molsysmt_integration_plan.md); the detailed choices
below and the prototype remain for review. No Python/TypeScript runtime,
scientific execution, compatibility contract, package floor or release changes
are implemented by this document.

The accepted refinement is **general operation + explicit selection/input +
operation-specific parameters**. Water removal is an example of atom removal.
The six scenarios exercise tool composition; they are not six prescribed user
workflows or a plan to add a public Viewer wrapper for every scenario.
The revised [edit/reconciliation direction](linked_molecular_edits_design.md)
uses explicit reconciliation or coordinated integrated operations; general
automatic observation is no longer a requirement. The prototype shows
forms and simulated edits only; it does not implement this provider boundary.

## Reviewable artifact

Open [the standalone HTML prototype](design/studio-task-prototype.html) directly
in a browser. It has no external assets, network requests, scientific engine or
file writer. It is intentionally separate from the product runtime. Repository
websites may display HTML source instead of running it; use the local file or
serve this directory through the existing development/Jupyter file service.
The [static preview](design/studio-task-prototype.png) shows the initial layouts.

The layout selector shows a 420 px notebook card, a 940 px wide window, or both.
These are design-review dimensions, not new fixed product sizes. The narrow
case replaces the panel list with direct panel selection; the wide case keeps
direct access at the left. Headings organize navigation without opening an
intermediate category screen. Horizontal tabs provide the second level.

The example has 12 structures and deliberately fabricated molecule counts and
values; it is **not** a characterization of PDB 1TCD. Both layouts share a toy
session so that review invalidation and Undo/Redo can be explored, while panel
navigation and form drafts remain separate. This is not evidence for actual
widget transport, a proposed scientific model or a new history implementation.

### What can be reviewed

| Task | Route | Prototype behavior / limit |
| --- | --- | --- |
| Remove/retain atoms | System → Edit | The same general operation accepts active/saved selections, sources, chains/groups, molecular categories, current atom indices or Whole. Simulate review/Apply/Undo/Redo for removal and retention. Expressions show the required provider route without being parsed by this offline prototype. |
| Inspect and prepare H | Build → Inspect / Repair | Distinguish coverage from readiness claims and protein pH rules from isolated fixed-state ligand placement. No simulated Apply is offered while the multi-structure/reinsertion prerequisites remain unresolved. |
| Align coordinates | Structure → Align | Separate moving atoms, fitting atoms, reference and target structures; review an ordered correspondence and simulate an edit. No fit is performed. |
| Work with periodic geometry | Structure → PBC | Distinguish assigning a box, wrapping and temporal unwrapping; reject the example's non-temporal `0, 8, 3` order for trajectory unwrapping. Only a toy edit is recorded. |
| Keep an analysis result | Structure → Analyze; Properties → Calculate / Results | Radius of gyration stays in the geometric editor; SASA stays in Properties. Both retain an illustrative indexed table. Selecting `0, 8, 3` preserves that order without inserting zeros for other frames. No plotting or physical values are qualified. |
| Calculate/display interactions | Interactions → Calculate / Results / Display | Show nine existing family names, four participation modes, named analyses and separate visual sets. Non-H-bond method forms remain to be designed; no detector runs. |
| Load and save | System → Load; Save & Export | Review independent/add/replace/append semantics and distinguish molecule/work/figure. No source is fetched, file selected, format converted or output written. |

Topology tabs demonstrate inspection and links to the canonical task editors.
The existing Selections and scene panels, optional add-ons, graph editors,
advanced scientific parameter forms, job execution/progress and checkpoint
management are outside this prototype. Their omission here is not a product
deferral or permission to remove them. Copy Python stays deferred under
uibcdf/molsysviewer#226.

### Suggested review sequence

1. In the notebook card, choose Remove atoms → Molecular categories → Water,
   retain magnesium, review/apply, then Undo and Redo. Repeat with arbitrary
   current atom indices, an active/saved selection, source or group; switch to
   Keep selected atoms using the same selector. Check all-structure scope.
   From Contents, Select waters for removal only prefills the same general form.
   Compare its reviewed effects with the manually entered arguments. Also
   check no-op removal, complete removal and invalid indices.
2. Prepare a review in one layout, then commit a different change in the other.
   The older review must become inapplicable. Check whether the message helps
   without resetting either editor's draft.
3. Visit Build Inspect and both Repair routes. Check that the meaningful
   restrictions are understandable without presenting an unavailable Apply.
4. Review Align and PBC. Check whether atom targets, reference and structure
   scope are evident and whether camera motion could be confused with an edit.
5. Save an illustrative property series for `0, 8, 3`; inspect the indexed table.
   Create a named interaction analysis, then a visual set. Undo/Redo should
   restore outcomes, with no implication that an engine ran again.
6. Edit molecular content after creating results. The prototype conservatively
   marks results historical and removes their toy display; production must use
   actual dependency-specific validity, not invalidate every result blindly.
7. Review Save & Export in Local, Identified remote and Unknown/tunnel scenarios.
   Only the remote case offers two destinations. Molecular export initially
   targets the whole system and all structures independently of calculation
   filters. Check molecule/work/figure distinctions.
8. Navigate tabs with arrows/Home/End and use Tab for controls; repeat at narrow
   width. The prototype is not an accessibility or real-popup certification.

### Prototype receiving

The [presentation receipt](design/studio-task-prototype-review.json) records
the artifact hashes and browser. Headless Chrome exercised fourteen checks:
both layouts; general removal/category target/retained metal/stale review;
toy Undo/Redo; arbitrary indices/retention/invalid inputs/no-op Redo preservation;
active/saved/source/chain targets; shortcut/manual equivalence and unresolved
expressions; complete removal/recovery; sparse result ordering;
ligand route prerequisites, nine families/four modes/visual-set separation,
output scope/destinations, keyboard tabs, 390 px overflow and absence of browser
errors/network requests. The first isolated Chrome launch was blocked by the
filesystem sandbox's socket restrictions; the reviewed launch outside that
sandbox succeeded. A first interaction pass exposed ambiguous field labels;
explicit accessible names fixed that prototype defect before the complete
pass. The later general-tool revision has its own complete presentation pass
and updated artifact hashes. Its explicit atom-ID toy model demonstrates target
composition only; it is not a proposed molecular representation or history
storage design. No production test, scientific method, real widget or popup is qualified.

## Proposed resolutions of technical choices

These proposals refine the alternatives in the
[operation/recovery design](studio_molecular_operations_design.md). They do
not freeze new method names, defaults or provider promises.

| Question | Proposed resolution | Reason / compatibility boundary |
| --- | --- | --- |
| General tool model | General operation plus explicit selection/inputs and scientific parameters, mapped closely to MolSysMT. Optional shortcuts prefill the same editor; composed journeys are acceptance tests. | Do not infer a catalogue of canned workflows from six examples. Preserve free composition and method-specific controls. |
| Python foundation | Public MolSysMT tools plus general public Viewer integration/domain APIs. Private form adapters and private coordination reuse those owners. Additional general view-aware tools need independently useful semantics. | Python stays headless and composable. No compulsory confirmation, method per shortcut, universal tool executor or default changes driven by forms. |
| Linked editing | Review explicit reconciliation/coordinated add-on operations under uibcdf/molsysmt#413. | Independent results are incorporated explicitly; deferred updates need pending-state/map safety. Raw mutations stay outside universal observation; existing setters remain until a qualified migration. |
| Mutation ownership | Prepare an independent candidate and validate it before committing. Receive public copy/extract/edit contracts for the exact route. | An `in_place=False` spelling alone is not ownership evidence. Source `basic.remove` ambiguity is reported as uibcdf/molsysmt#406; do not fork its implementation. |
| History owner | Extend existing Python history with references to retained molecular/result versions and lightweight scene records. | One ordered history, no independent history in each panel or popup. Storage sharing is admitted only after ownership and recovery qualification; no full trajectory copy per scene edit. |
| Long work | Prepare against retained input; serialize accepted changes and check relevant dependencies immediately before commit. | Safe reading/scene work can continue where the engine supports it. Cancellation/discard/termination remain distinct, engine-qualified capabilities. |
| Commit and delivery | Python commits once; each endpoint tracks synchronization separately. | A disconnected window does not turn successful science into a failed calculation. Deduplicate retries, then resynchronize canonical state. |
| Scientific results | Preserve native results and existing owners; add only needed Viewer associations/codecs. | An indexed series needs explicit frame identity, units and provenance. Extend the existing plot owner where applicable; no compulsory universal analysis database or fake zero values. |
| Repair/reinsertion | First qualify composition through public extraction/add/merge with maps, chemistry and all-frame invariants. | Do not infer prepared ligand reinsertion from an unrelated merge test, splice private arrays, or demand a new provider API before testing existing public tools. |
| Persistence | Coherent revision capture; domain-qualified storage, work/checkpoint codecs for supported Viewer results. | H5MSM is recommended for supported molecular domains, not a silent lossless serializer for arbitrary objects or nonempty unsupported mechanics. |
| External output | Browser download ordinarily; identified remote additionally offers Python-host output. Unknown context retains a safe download route and needs explicit connection declaration. | An SSH tunnel cannot be identified by a localhost URL. Python path output remains explicit and independent of Studio. File overwrite/append is not session Undo. |
| Visual simplicity | Stable task location, short forms, conditional scientific fields and an inline effect review for meaningful edits. | Avoid unrelated controls such as ligand pH or H-bond methods in another family. Advanced execution tuning can be disclosed; scientifically essential scope cannot be hidden. |
| Canonical scientific editor | Geometric analyses in Structure Analyze, physical/chemical quantities in Properties; reuse result-display components and contextual links. | Respect the source inventory without requiring users to choose between duplicate calculation editors. Molecular attribute inspection, chemical-state editing and scene measurements retain their own owners. |

### Receiving status, not a new capability floor

The operation inventory remains fixed at provider source
`b501bfd69ad3e692ceeb865ebcdbd0cd1deed173`. Its signatures and 174 source hashes
are not silently refreshed to moving main.

- MolSysMT uibcdf/molsysmt#121 is now closed (observed on 2026-10-22); Viewer
  uibcdf/molsysviewer#259 remains **open for consumer receiving**. Provider
  completion does not qualify independent Viewer revisions, browser restoration
  or installed artifacts. No API migration is performed here.
- uibcdf/molsysmt#406 records the inspected `remove(in_place)` signature/body/
  return contradiction. The explicit extraction proposal avoids relying on
  that flag; extraction independence and remapping still need qualification.
- Existing provider merge fixes such as uibcdf/molsysmt#352 do not by themselves
  prove chemistry/state/all-structure reinsertion for WF02.
- The existing `molsysmt>=0.23.0` floor is unchanged. Source availability,
  scientific execution and public package receiving remain separate evidence.

## Choices still requiring agreement or measurement

1. **General operation and integration contracts.** Reuse the current public
   MolSysMT/Viewer composition first, including extraction and
   `apply_system_edit`. Qualify needed correspondence, return/error, recovery
   and history extensions; consider new general view-aware tools only when
   justified. Current `apply_system_edit` clears history and is not a complete
   transaction. No GUI form or preselected population defines a new API.
   Include the linked-edit boundary, conditional setter migration and the
   separate resolved replacement-history defect #262 and its current-contract guard.
2. **Resource policy.** Measure representative molecule/trajectory/sparse-result
   plus history residency; choose RAM/disk limits, candidate lifetime and
   eviction behavior. No arbitrary universal capacity or performance claim.
3. **Persistence and files.** Qualify codecs per persistent result/domain and
   writer routes/formats/engines with specific losses. Choose host-path/browser
   input presentation, explicit connection declaration and overwrite behavior.
4. **Detailed forms and acceptance.** Review these mockups with Diego/Liliana,
   then finish scientific controls for all admitted inventory workflows,
   asynchronous execution, accessible focus/error recovery, checkpoints and
   chemical-state/correspondence editors. Resolve ambiguities before coding
   those workflows; the six foundations are not the full breadth of 1.0.

## Implementation order after design review

1. Contract general operations and their existing public composition; receive copy/ownership and
   establish recovery/storage/commit foundations with bounded owning issues.
   Preserve unrelated scene behavior and existing public scientific returns.
2. Implement general atom removal/retention and selection integration. Validate
   them through load 1TCD → select atoms → remove/retain → recover → save/reopen.
   Also use non-water/mixed populations, equivalent shortcut/manual targets,
   a retained ion, overlapping source regions, anchored objects, named analyses,
   complete/no-op removal and failure cases. The journey is a composition test.
3. Extend those proven owners to coordinate/box edits and persistent scientific
   results, then chemical preparation/reinsertion and the remaining inventory
   workflows. Any scope deferral needs a concrete reason; engine absence or an
   experimental label alone does not settle the pre-1.0 decision.
4. Integrate forms over the Python contracts; exercise independent drafts,
   embedded/canvas-popup/Studio-popup projection, stale requests and reconnects.
   Qualify scientific methods, scale and persistence separately from UI checks.
5. Run applicable source gates, human scientific dogfooding, public documentation
   and exact installed qualification after an explicitly frozen candidate.
   Both 1.0 publications and candidate freezing remain paused.

Do not open dozens of implementation issues merely to mirror inventory rows.
After the review, divide work by independently reviewable owner/contract changes
and complete vertical workflows; link provider work where actually required.

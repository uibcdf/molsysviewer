# Studio / MolSysMT integration — revised ownership plan

**Status: proposed implementation plan under the approved
[core/add-on boundary](core_and_addon_boundary.md) — revised 2026-10-22;
implementation has not started.** This plan retains the earlier integration
requirements for review under the revised product ownership. Earlier native
Studio expansion and automatic observation choices below are superseded by
that boundary; operation placement, scope and recovery need reassessment.
The plan records the maintainer's direction before
development, including the accepted document-review refinements: browser file
input, edit review, result validity, long operations, recoverable loading,
Python parity, history resource ownership and navigation-preserving Undo.
The maintainer's subsequent clarification makes general molecular operations,
explicit selections and operation-specific parameters the basis of the design;
the example journeys below are acceptance scenarios, not a catalogue of recipes.
Core supports visualization/exploration and qualified calculations for visual
content. General molecular preparation/editing and analysis tools belong to
the scientific library and a redesigned MolSysMT tools add-on. Explicit
reconciliation and coordinated integrated operations are the design basis;
general automatic observation is not required. Scientific setters belong to
MolSysMT; existing Viewer setters retain their current contracts until a
qualified migration is reviewed.
Detailed operation scope, provider receiving and technical designs
remain to be completed. It does not qualify new capabilities or authorize a
candidate freeze, dependency change or publication.

## Purpose and scope

The product ambition is simultaneous ease, power, versatility and a calm
scientific working experience. The
[proposed operation/recovery design](studio_molecular_operations_design.md)
translates that ambition into reviewable quality criteria and technical choices.
Its recommendations remain proposed until reviewed; the approved direction
does not authorize implementation of an unreviewed architecture.

The public Python API is the primary product and architectural foundation.
Studio makes its capabilities accessible without programming; interface design
must not weaken Python's correctness, expressiveness, composability, headless
operation or established contracts. The nonprogramming user journey below is
an acceptance case, not a replacement for scientific Python workflows.

A user who loads TcTIM / 1TCD must be able to remove waters and ions from the
molecular system, prepare and analyze that system, and save the result through
the appropriate tools/add-on interface without writing Python. Native Studio
keeps scene operations and visual scientific conveniences. Hiding components remains a scene operation;
removing them changes the molecular system.

## General operations and composable selections — accepted

Organize capabilities around **operation + explicit input populations + relevant
parameters**. Map scientific semantics closely to the public MolSysMT tools.
For example, the proposed MolSysMT tools interface offers a general operation to remove atoms, with
water as one possible selection. Retaining atoms uses the extraction semantics;
removing structures is a separately explicit change to the structure axis.
Scientific operations may require references, two populations, chemical states
or other domain inputs; the three-part description is not a universal form or
public request schema.

Selections can come from the active mouse selection, saved/query selections,
regions, sources, chains/groups or readable molecular categories, with an
optional expression/index input. Reuse the existing Selections owners and
provider classification. A nonprogramming user must be able to construct and
inspect a target without writing selection syntax. Resolve and capture the
target at review; distinguish the selected atoms from the operation applied to
them. Changing an atom domain affects every structure sharing that domain.

"Remove waters" may be an optional shortcut that opens the general remove
operation with a visible water selection. It has the same scientific arguments,
effect review, validation and recovery as any other selection. It must not hide
ion removal, hydrogen preparation, fitting or other extra scientific steps.
Domain-specific parameters remain explicit: simplicity comes from clear
presentation and reusable selection tools, not from guessing a user's workflow.

Use composed journeys to test that tools work together. Additional guided
workflows need an identified user need and visible constituent operations; they
do not define the base capability catalogue. Panel organization follows the
provider domains and useful operations without mechanically exposing every
export as a control or generating one indiscriminate parameter form.

Take the time needed to expose the useful capabilities already offered by
MolSysMT before Viewer 1.0. Review each operation rather than setting an
arbitrary small initial subset. A deferral needs a concrete scientific,
provider, compatibility or usability reason. Experimental classification alone
does not exclude a capability; its limits must remain visible and qualified.
Export presence in a source checkout does not establish published availability.

MolSysMT remains the required native scientific backend. Other domain libraries
retain their optional addons. Extend reusable operations in their scientific
owner and let the appropriate scene or add-on interface orchestrate them. Existing ownership and scene behavior
remain governed by [architecture](architecture.md),
[scene contracts](scene_contracts.md), the
[Studio contract](studio_interaction_contract.md) and
[addon direction](molsyssuite_addon_direction.md) until their replacements are
implemented and verified. This plan does not make proposed behavior current.

## Navigation and panel responsibilities — placement revised

The following revised ownership replaces the earlier proposal to put all
provider tools in native Studio. Detailed add-on navigation, installation and
function coverage remain to be designed. The accepted boundary does not
restore the retired legacy integration.

Use direct panel access with light navigation headings, not intermediate
category screens. Within a panel, use a title and a short horizontal tab row,
following the existing Elastic Networks addon pattern. Preserve the current
responsive narrow-card route and keyboard/focus behavior. Individual panels
need tabs only where their workflows justify them.

| Navigation grouping | Target panels |
| --- | --- |
| Core visualization/exploration | System inspection/loading, Selections, Whole, Regions, Measures, Annotations, Shapes, Layers, Interactions, Viewport |
| Proposed MolSysMT tools add-on | General composition/editing, Topology, Structure, Build and Properties tools; exact panel/tab organization remains proposed |
| Independent access | Save & Export, Settings |

These are proposed display names and placements within the approved direction;
the complete operation inventory and a narrow/wide mockup must confirm them.
Do not add empty panels merely to announce future functionality. The headings
do not freeze add-on workspace names or make the proposed MolSysMT tools add-on available.

| Panel | Responsibility and tentative internal organization |
| --- | --- |
| System | Core contents/inspection/loading and source identity. General atom removal/composition editing belongs to the proposed MolSysMT tools interface; exact navigation remains proposed. |
| Selections | Active, query and saved populations; reusable selection input for other operations. |
| Topology tools | Proposed add-on connectivity/chemistry/correspondence tools. Specific visual highlights can use existing core scene owners. |
| Structure tools | Proposed add-on coordinate transforms, alignment and general analysis/PBC tools; visual geometry and measurement requests retain scene owners. |
| Build tools | Proposed add-on chemical completeness, repair/preparation and construction tools. |
| Properties tools | Proposed add-on general property analysis; qualified visual conveniences such as property coloring can belong to core scene/style owners. |
| Interactions | Preserve named scientific analyses, calculation/import, queries and visual sets. Internal tabs remain unresolved: avoid obscuring the relationship between analyses and representations. |
| Measures | Preserve distance/angle/dihedral scene objects and their existing structure-series workflows. |
| Other scene panels | Retain their domain ownership and established scene behavior. |
| Save & Export | **Molecular system / Work or Session / Figure or View**; exact labels remain to be finalized. |

System Contents retains current selection, highlighting, focus, context menus,
annotation overlays and the inspector independent of active selection. Group
repetitive waters/ions with counts without losing access to individual groups.
Keep drafts, focused fields and window-local navigation stable across shared
state updates. Opening a tab must not start a scientific computation.

## Python API primacy

Design and verify the Python operations before their Studio controls, following
the [API-first rule](engineering_rules.md#1-the-layering-rule-api-first).
Navigation headings and tabs organize presentation; they do not dictate Python
namespaces or require one public wrapper for each button. Reuse independently
useful scientific tools and compose them through the existing owners.

Python workflows must remain usable in notebooks, scripts, batch jobs and
headless tests without constructing Studio, opening a popup, completing a form
or answering an interactive confirmation. Target review and highlighting are
Studio affordances over explicit public arguments and validation, not mandatory
handshakes for programmatic callers. Errors must remain actionable exceptions
and diagnostics, not only text in a panel.

Preserve the API's supported atom/structure selectors, units, parameters, engine
choices, return values and composition with MolSysMT. A simpler form may expose
a deliberate subset without narrowing the underlying Python operation. Do not
change public defaults, signatures, ownership, performance expectations or
failure behavior merely to suit a form. Any necessary contract change needs
its own justified design review, explicit compatibility assessment and guards.

Transaction and recovery services belong to Python and remain available without
a frontend. Studio adapters can be private compositions of public MolSysMT
tools and public Viewer integration/domain operations. Reconciliation, history
and transport mechanisms stay private within their existing owners; Studio
must not implement an alternative mutation engine.
Python users can freely compose the two libraries. First reuse existing
general boundaries, including `view.extract(...)` and
`view.apply_system_edit(...)`; add a public Viewer tool only where it provides
independently useful view-specific semantics or fills a demonstrated integration
gap. A general view-aware remove tool can be considered on that basis; a new
public method for every selection shortcut or composed journey is not required.
Specify recovery/history policy explicitly for Viewer integration; do not
silently force all existing Python or MolSysMT calls into a GUI-oriented
history, storage budget or confirmation policy. Preserve existing low-level
integration contracts while reviewing any necessary extensions. In particular,
`apply_system_edit` currently reconciles a supplied system, clears scene history
and does not supply the planned complete recovery/transaction guarantee.
Its public role is integration: accept molecular results prepared through
MolSysMT, an addon or another caller and reconcile view-owned objects, using
explicit old-to-new atom maps where needed. It does not itself perform the
scientific edit. Review and extend that boundary on its merits rather than
making it private because Studio's coordination is private.
The local/remote destination chooser affects Studio delivery, not Python's
ability to write an explicitly supplied path.

## Molecular edits and reconciliation — revised direction

Follow [the reconciliation review](linked_molecular_edits_design.md). Direct
Python edits use explicit qualified reconciliation; the proposed MolSysMT tools
add-on can coordinate the operations initiated through it. Independent returned
systems require explicit incorporation. Deferred update/batch semantics,
correspondence, stale visual interactions, failure and recovery still need
contracts. General automatic native observation is not required.

`extract()` and `load()` retain their current view semantics, and
`apply_system_edit()` remains an advanced public boundary with its documented
invalidation/history limits. Scientific cell assignment belongs to MolSysMT;
cell-edge display belongs to Viewer. No setter is removed during planning.

The consumer has withdrawn the general observer request in uibcdf/molsysmt#413
and told the provider that it may close the issue without a new deliverable.
Operation-specific gaps found during receiving will be reported separately.
The [#262 history fix](archive/replacement_load_retains_scene_history.md) is
independent. No new dependency floor, notification API or artifact is qualified.

## Mapping the provider

| Provider domain | Core or proposed tools/add-on consumer |
| --- | --- |
| `basic` | Core loading/selection/extraction/persistence where already supported; additional composition/edit tools in the proposed add-on. No unstructured generic setter grid. |
| `topology` | General graph/chemistry/correspondence tools in the proposed add-on; specific visual highlights may use core scene owners. |
| `structure` | Coordinate transforms/alignment/general analysis in the proposed add-on; qualified measures/axes/plots may be visual core requests. Camera navigation is distinct from coordinate editing. |
| `pbc` | General cell assignment/reimaging tools in the proposed add-on; drawing cell edges remains core. Preserve existing setter contracts pending migration. |
| `build` | Inspection, repair, preparation and construction in the proposed add-on. Water removal remains one target of a general atom-removal tool. |
| `physchem` | General property/chemistry tools in the proposed add-on; qualified property-coloring or feature-display conveniences may use core scene owners. |
| `interactions` | Existing native Interactions domain; retain experimental consumption and scientific validity semantics. |
| Conversion and `h5msm` | System loading, analysis import and Save & Export, using actual public reader/writer capabilities. |
| `molecular_mechanics` | Evaluate operations and engines individually; no panel or stable mechanics contract is promised by this plan. |

Current MolSysMT distinguishes molecular identity, chemical states and structural
observations. Covalent bonds and chemical assignments can belong to a selected
chemical state; `Topology.bonds` is a compatibility facade. Explain the selected
state where relevant without conflating it with the visible structure. An
interaction candidate is not an established covalent bond. PBC operations must
retain explicit box and image conventions.

Preparation actions need specific contracts. Protein/template pH rules and
fixed-state ligand hydrogen placement are different workflows, not a general
environment-dependent pKa prediction. Recorded chemical fields or a readiness
report are not a universal chemical-validity certificate. Unsupported inputs
must remain explicit rather than selecting another scientific method silently.

## Loading and edit review — accepted

System Load must cover remote identifiers such as PDB IDs, file selection on
the browser computer, and paths accessible from Python. Browser-selected files
need an explicit upload/transfer route; their names must not be interpreted as
host paths. Preserve independent-system versus complementary-source semantics,
ordered source/atom/structure correspondence, labels and the existing box and
structure-pairing contracts. Multiple sources may be submitted together or
added progressively. Loading an independent interaction analysis retains the
explicit correspondence declaration required by the
[Interactions consumer contract](interactions_compatibility_contract.md).

Before applying an edit, show a concise review within its form: the explicit
target population, affected component/atom counts, source occurrences,
structures and chemical states where relevant, and consequences for scene
objects and scientific results. Allow optional target highlighting and
population adjustment. Do not turn every action into a separate confirmation
dialog. A water/ion classification is not a recommendation to remove a
biologically relevant metal; components must remain reviewable individually.

Bind the reviewed target and parameters to a molecular revision, not a live
selection that can change underneath the form. Changes from Python or another
window require revalidation and renewed review when scope or effects differ;
never reinterpret stale atom indices against the new system silently. Define
how affected annotations, selections, regions and other anchored objects are
retained, remapped or marked unavailable instead of silently retargeting them.

## Save and delivery — accepted

Offer one ordinary browser-download route for local use. Offer the destination
choice **Download through browser / Save on Python host** only when use is
identified as remote. URL inspection alone cannot classify SSH tunnels;
design detection with an explicit configuration override and specify unknown
classification before implementation. Do not use ambiguous "local computer"
wording or silently switch destinations.

Recommend and default to H5MSM for molecular-system output. Also expose other
formats that the provider can actually write for the chosen content. A reader
adapter is not evidence of a writer. Explain preserved information, losses and
structure/selection restrictions before conversion. Verify each writer route
against a published provider version before claiming it.

Make atom and structure scope explicit: full system or selected atoms; current,
all or explicit structure indices where supported. Canvas visibility must not
implicitly choose file content. Preserve compatible named analyses when the
format and correspondence permit it. Removing atoms affects the shared atom
domain, whereas supported coordinate operations may target selected structures.

Distinguish molecular-system interchange, resumable work/session, and
figure/interactive-view output. Define whether a work file embeds data or needs
external sources. Keep [session reproducibility](session_reproducibility.md)
and conversion loss checks in scope; H5MSM is not a universal codec for every
future result or molecular domain.

Exports, sessions and checkpoints must capture a coherent revision of their
selected molecular data, analyses and scene. If work changes during preparation,
retain the captured version or revalidate/retry before producing the file;
never mix pieces from different revisions. Atomic destination-file replacement
alone does not provide this input-consistency guarantee. Choose and qualify
snapshot/serialization behavior without assuming concurrent writes are safe.

## Scientific results and long operations — accepted

For every operation, classify each existing result as still valid, safely
remappable, retained only as historical evidence, or requiring recalculation.
Preserve scientific data and original provenance where the provider contract
permits it; show applicability to the current system separately. Historical
results must not appear as current measurements or be projected onto unrelated
atoms. No edit, playback, query or panel opening implicitly reruns detectors or
recalculates stored scientific analyses. This does not disable ordinary
frame-dependent visual updates, annotations, measurements or dynamic regions
under their existing contracts; distinguish projection/live geometry from
recalculation of an analysis retained as scientific evidence.
Keep absent, unevaluated, evaluated-empty, unsupported and failed outcomes
distinguishable, including units, method and evaluated scope in result displays.

Long operations need correlated pending/success/failure feedback, duplicate
submission prevention and real progress when the provider supplies it. Offer
cancellation only when execution or safe result rejection actually supports
the stated behavior; hiding a form is not cancellation. Specify computation
ownership when a form, Studio popup or canvas popup closes, and communicate
whether work continues. Closing an editor must not leave an unowned computation.

Bind a calculation to its input revision and parameter/scope snapshot. A late
result cannot attach silently to a different current system, even if atom
counts agree. Recheck applicability at commit, preserve the previous valid
state on failure, and define explicit handling of an obsolete result. Returning
to earlier molecular content through Undo/Redo must not reuse its old execution
generation or reactivate pending requests. Preserve and extend Interactions'
existing stale-calculation checks when designing unified history. Do not
claim asynchronous execution, interruptibility or total-RAM bounds merely from
having a pending indicator.

## Recovery — accepted user experience, technical design pending

Provide one ordered Undo/Redo history covering scene mutations, molecular edits
and persistent scientific-result changes. A meaningful user operation forms one
step, including an explicitly submitted composite workflow. Browsing forms,
inspection and panel navigation do not create scientific history entries.
Preserve the current exclusion of camera/frame/playback navigation from ordinary
Undo snapshots: undoing an annotation or molecular edit must not restore an
unrelated old viewpoint. When a changed structure axis makes the current frame
invalid, define correspondence/fallback explicitly. Explicit session/checkpoint
restoration may restore its saved viewpoint; distinguish that action from
ordinary Undo.

The initial molecular load establishes a baseline without silently discarding
existing shape-only scene work. Subsequent system additions, replacements and
structure appends participate in the unified history. Restoring a session or
checkpoint over existing work must preserve a recoverable prior state within
the agreed budgets. Undo/Redo of these operations cannot rely on the original
input files still existing or on downloading them again. Specify the initial
load/history boundary and complete axis/scene restoration in the technical
design; current load/session history clearing is not the target behavior.

Restore a coherent molecular system, chemical states, structures, attributes,
analyses/coverage, source correspondences and view-owned scene. Redo restores
the retained outcome without rerunning a scientific engine or fetching a source
again. A successful new operation after Undo discards the redo path; a failed
operation preserves it. Both popup types and the embedded canvas share the
authoritative history while keeping their local window layout.

Bound memory and temporary storage, optionally also step count. Retain a
continuous recovery range and expose its oldest available boundary. Reclaim the
oldest steps first. Do not apply an edit silently without recovery when its
required snapshot cannot be retained; explain the limitation and offer explicit
alternatives before mutation. Storage budgets do not establish a process-RSS
ceiling for provider computations.

Use compact scene records referring to recoverable molecular revisions, with
qualified sharing of unchanged data and disk-backed storage where appropriate.
This is an architectural direction, not a selected copy-on-write API, codec or
measured performance guarantee. Deltas may optimize individual operations only
after their reversal is proven. Do not duplicate a trajectory for each color
change. Runtime history storage lives with Python; it is distinct from the
user-facing browser/host choice for exported files.

Assign one owner and lifetime to retained revisions and temporary history files,
following [temporary resource ownership](temporary_resource_lifecycle.md).
Reference-aware eviction and redo-path discard release only data no retained
step or current system still needs. Define cleanup on viewer close and failed
writes, disk exhaustion and kernel interruption. Never delete caller-owned
files or durable checkpoints while cleaning runtime history. Session-scoped
temporary files alone do not establish recovery after a kernel/process crash;
any restart-recovery promise needs its own durable format and receiving.
Closing the viewer releases its owned runtime resources; it does not implicitly
save current work. Protection of the active state during eviction or failure
does not promise that unsaved work survives closing the viewer or kernel.

Add voluntary durable checkpoints for milestones such as "Original", "Without
waters" and "Prepared". They complement session-scoped Undo, survive ordinary
history eviction, and require an explicit persistence format and lifecycle.
Do not save the entire Undo history in ordinary session files implicitly.
Protect current work before replacing it with a checkpoint. Branch management
is not required for this recovery design.

Prepare and validate molecular results independently before commit. Failed
operations must leave the prior system and scene usable; publication/rebuild
failure also needs recovery. `apply_system_edit()` supplies reconciliation,
not the complete transaction guarantee. Preserve source and analysis versions
without recalculating or inventing new provenance during restoration.

## Current gaps and contracts to extend

Current `SceneHistory` snapshots scene state, excludes scientific arrays, and
clears on load/system edit. Ordinary session loading also clears Undo/Redo.
These current mechanisms do not implement the accepted unified history.
Do not revise their documentation to claim new behavior ahead of the code.

The existing architecture avoids generic public molecular editing mutators.
Follow the [API-first layering rule](engineering_rules.md#1-the-layering-rule-api-first):
every scientific Studio workflow must be reproducible through public Python
operations with the same scientific effects, reconciliation, recovery and
diagnostics. Public composition through MolSysMT and general Viewer integration
tools satisfies this requirement; each form or acceptance journey does not need
its own public Viewer method. Assess general view-aware tools individually for
their added value. Keep private adapters and coordination over those public
boundaries without copying provider namespaces or adding unstructured generic
mutators. Preserve
ArgDigest and the public digestion-bypass contract. Keep one reconciliation
and history authority, not parallel Studio-only and Python-only implementations.
Review extensions to the general public integration boundary and revise affected normative
contracts with the implementation and its guards.

Complete-system copy/edit ownership needs scoped receiving through
[uibcdf/molsysviewer#259](pending_proposals/native_copy_contract_receiving.md),
provider uibcdf/molsysmt#121 and coordination uibcdf/molsyssuite#122. Their
current scope is not evidence of cheap, independent molecular revisions.
The new design must qualify the boundary it actually uses; no provider issue
is relabeled resolved or release-blocking by this planning record.

## Work sequence and remaining decisions

1. **Inventory operations — source pass complete.** The
   [169-export / 77-group inventory](studio_molsysmt_operation_inventory.md)
   and its source snapshot account for the reviewed namespaces; the mapping
   remains proposed and general operation contracts need design. Enumerate
   provider operations with their supported inputs and selection/parameter
   contracts; use user tasks to verify their usefulness and composition.
   Record canonical panel/tab, read/calculate/
   edit classification, atom/structure/chemical-state scope, parameters/units,
   target review/impact, public Python route and compatibility, headless use,
   result and display, validity after
   edits, save/checkpoint support, engine/progress/cancellation capabilities,
   published version/stability, evidence and reason for any deferral. Assess
   every useful operation for 1.0; do not equate sequencing with exclusion.
2. **Design and qualify recovery.** Select revision/copy ownership, storage
   formats, budgets/eviction, transactional commit/rebuild recovery, old-handle
   semantics, initial loading and recoverable additions/replacements/restores,
   navigation preservation, resource lifetimes, background-result revision
   checks and handling of edits made outside managed workflows. File bounded
   implementation/provider issues under the reporting protocol before starting
   those changes.
   The [technical proposal](studio_molecular_operations_design.md) separates
   scientific preparation, Python commit, endpoint synchronization and explicit
   programmatic history policy; review its choices and the
   [six composed acceptance scenarios](studio_foundation_workflow_contracts.md)
   first.
   Qualify the [explicit reconciliation boundary](linked_molecular_edits_design.md);
   the general observer request in uibcdf/molsysmt#413 is withdrawn. Recovery
   must start before mutation where promised.
   Current-contract #262 is fixed independently of implementing molecular Undo.
3. **Validate navigation and workflows.** Mock up wide/narrow cards with real
   content; confirm panel/tab labels, Interactions organization, chemical-state
   selection, edit review, result applicability and local/remote/unknown
   destination behavior. Finalize browser/host file input, the writer-format
   inventory and long-operation/closed-editor feedback.
   The [interactive task prototype and design review](studio_task_design_review.md)
   now provide illustrative narrow/wide forms, proposed technical choices and
   the remaining decision groups. Review them; no scientific execution or
   actual widget/popups are qualified by this artifact.
4. **Implement general tools and validate their composition.** Start with atom
   removal/retention over reusable selections and public integration/recovery.
   Validate 1TCD load/select/remove/retain/recover/save plus arbitrary/mixed
   populations, equivalent shortcuts, no-op and empty-system cases.
   Then add topology inspection,
   coordinate/PBC edits, preparation, properties and the remaining inventoried
   analyses. Preserve optional addon, shape-only and popup use throughout.
5. **Verify and document the integrated product.** Real provider systems,
   multi-structure inputs, scientific result validity, failure recovery,
   deterministic Redo, exhausted budgets, persistence and both popup types are
   acceptance cases. Follow focused/local/hosted gate discipline, then human
   scientific dogfooding and broad public documentation. Exact installed
   qualification follows an explicitly frozen candidate.

## Acceptance scenarios to implement and verify

These are required future receiving scenarios, not claims of passing tests.
Use real provider systems, browser transport and the public Python route as
appropriate; provider unit evidence alone cannot qualify Studio behavior.

| Scenario | Required observation |
| --- | --- |
| 1TCD remove/retain/save | Review counts and individual waters/ions, adjust the target, apply a real molecular edit, inspect scene/result consequences, then write and reopen the selected molecular content. |
| Browser/host input | Load real browser-selected files through transfer and host-readable files through their own route; compose independent and complementary sources without confusing file names with server paths. |
| Stale edit review | Change selection/system from Python or a second window after review; no stale target is applied silently. |
| Result applicability | Exercise valid, remappable, historical and invalidated results; retain original scientific provenance and show coverage honestly without rerunning stored analyses implicitly. Ordinary frame-dependent visuals and measurements still update. |
| Long or obsolete calculation | Prevent duplicate submission; report real progress/cancellation limits; close/reopen editors and change the input revision; no orphaned work or result attachment to the wrong system. Exercise pending calculation → edit → Undo → result arrival, with no revival of the old request. |
| Unified history | Interleave molecular edits, scene objects and persistent calculations; Undo/Redo restores coherent states and retained outcomes without rerunning engines. Failed/no-op operations do not consume meaningful steps or destroy Redo. |
| Loading and restoration | Initial loading preserves existing shape-only work; subsequent add/replace/append and session/checkpoint restoration preserve the prior recoverable state, including when original source files become unavailable. |
| Navigation and windows | Ordinary Undo preserves the viewpoint and compatible current frame; changed axes follow the explicit correspondence/fallback rule; both popups mirror shared state while retaining local layout. |
| Budgets and resources | Eviction, redo discard, write failure and exhausted budgets preserve the active state and retained recovery range. Closing releases only owned runtime resources and never deletes caller files or durable checkpoints; it does not implicitly save unsaved work. Kernel interruption behavior is documented and tested to its actual promise. |
| Coherent saving | Change the working system/scene while preparing an export, session or checkpoint; the produced file contains one coherent captured revision or fails/retries explicitly, never a mixture. |
| Python primacy and parity | Compose public MolSysMT tools and general Viewer APIs without a frontend, preserving selectors, units, engine parameters, returns and exceptions. Verify recovery/integration parity and shortcut/manual equivalence. Private adapters add no inaccessible scientific or mutation capability. |
| Formats and delivery | H5MSM and other qualified writers preserve their declared content and report losses. Local Studio export has one destination route; identified remote use offers both. Public Python file output retains explicit path support. |

This is an implementation plan outside the reporting queues, not an issue-state
record. Concrete work items will get owning issues when scoped. The previously
qualified source baseline remains valid for its recorded scope; none of it
qualifies these planned changes. The agreed next version 0.25.0 remains
unfrozen and both 1.0 publications remain paused.

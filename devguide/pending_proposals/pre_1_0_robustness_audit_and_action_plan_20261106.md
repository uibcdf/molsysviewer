---
summary: Track the November robustness audit and pre-1.0 action plan.
issue: uibcdf/molsysviewer#315
status: active
opened: 2026-11-06
closed:
verification: measured
area: [stabilization, api, state, ui, science, packaging]
guard:
normative:
blocked_by: []
supersedes: []
---

# Pre-1.0 robustness audit and action plan — 2026-11-06

**Status: recording approved; proposed action plan; implementation incomplete.** This is the
active audit and execution ledger requested by the principal maintainer. It
records what must improve, why, who owns it, what is already proved and the next
acceptable transition. Writing this document completes the recording task; it
does not resolve the findings or establish release readiness.

The product architecture is sound: a Python-first visualization core, MolSysMT
as scientific authority, and provider-owned additional tools. The main
context menu and Studio have substantial receiving. The immediate priorities
are file/state integrity, rejection without loss of work, resource ownership,
plot authority and scientifically interpretable figures. All previously
approved addon task families and full-session acceptance remain required.

This document owns the current work order. The [product boundary](../core_and_addon_boundary.md),
[scene contracts](../scene_contracts.md), [session requirement](../session_reproducibility.md),
[engineering rules](../engineering_rules.md) and [addon plan](../molsysmt_tools_addon_plan.md)
remain normative. It does not reopen the withdrawn native-Studio expansion.
Qt remains experimental; human review is postponed. Both 1.0 publications and
candidate/tag/package operations remain paused pending separate authorization.

Approval to record this audit does not approve every new API or GUI design in
it or start the corrections. Existing adopted requirements remain adopted.
New design recommendations, especially B4, E3 and F1, need an explicit recorded
scope/contract decision before implementation. Keep that decision and its date
beside the stable ID; do not turn a recommendation into a release gate by
editing a completion percentage.

## How to resume and update this ledger

Start with the dashboard below, then the relevant work-item section. Use the
stable IDs in commits, scoped issue reports and receiving records. Follow
[the reporting protocol](../reporting_protocol.md): check open and closed issues
through a complete paginated inventory, open scoped reports before starting new
implementation themes, and update documents during work. Issue prose changes
at opening and closure, not on every intermediate measurement.

For an active item, retain its owning issue, source identity, actual outcome,
relevant regression and remaining acceptance. A code path existing, an isolated
pass, a green hosted job, an installed artifact and a human observation prove
different things. Do not sum overlapping test scopes or mark an entire family
complete because one mode passes. When an item closes, reduce its dashboard
entry to one outcome/evidence line and move detailed resolution to its owning
archive. Keep rejected attempts and provider limits in their dated receipts.

Sensitive malformed-input reproduction details are retained privately. Public
records contain sanitized conclusions and acceptance criteria; they must not
publish local paths, crafted inputs or unrestricted diagnostic attachments.
Before changing a sensitive finding's disclosure level, review it with the
maintainer. The coordination issue is #315; it does not replace scoped defects.

## Current dashboard

**Next actions:** activate E0's evidence-custody handoff and scope A1–A4,
retaining private handling where appropriate. Safe source investigation and B1's
existing #314 diagnosis can proceed in parallel. E0 prevents premature cleanup
or disclosure; it does not require all unrelated development to stop. No product
correction in this ledger is declared done by this document.

| Block | Current status | Owner and tracking | Exit evidence |
| --- | --- | --- | --- |
| A — integrity, restoration and cleanup | Four reproduced findings await scoped reports/fixes; two further investigations are unconfirmed | Viewer; coordination #315 | Rejection preserves existing work; owned resources close on failure; actual public-API/browser regressions |
| B — plots and DataCards | #314 correction/regression local; broad core failed; precision, provenance and card follow-up pending | Viewer and scientific producer; #314, #264, #315 | Python/render agreement, interpretable retained observations, safe literal titles and complete card lifecycle |
| C — contribution and host integration | Reconciled addon committed locally; remote PR older and reported conflicting; source gates incomplete | Viewer #264/#301/#304/#305/#306; uibcdf/molsysmt#421 and PR #543 | Reviewed delivery, current controlled pair, relevant full/hosted outcomes and explained failures |
| D — scientific prerequisites and approved GUI families | Partial implementation; provider corrections and several task families remain | MolSysMT owns science; addon owns tasks; #264/#315 and uibcdf/molsysmt#421 | Received native fixes plus every required family/effect, without hidden preparation or copied algorithms |
| E — integrated use, scale and human acceptance | Partial headless/Jupyter receiving; complete workflow and prolonged-use checks pending; human review postponed | Viewer/addon; maintainer owns human observations | TcTIM/ensemble save–recover–continue, independent lifetimes and representative measured limits |
| F — public contract and documentation | Digestion/meta checks pass; compatibility snapshot and documentation reconciliation pending | Viewer; #315 | Named stable/experimental contracts, verified references and one usable current handoff |
| G — covering artifact and installed qualification | Pending; candidate/publication actions paused | Viewer #294; coordinated provider/downstream receiving | Authorized exact producer/files, clean installed checks and required distribution evidence |

### Activation card and priorities

The block dashboard is a summary, not a second issue tracker. When an ID or
child ID is activated, keep one short card in its owning report containing:

| Field | Required content |
| --- | --- |
| Identity and scope | Stable ID, parent, finding class and applicable milestone: covering artifact/#294, accepted 1.0 work, investigation, design decision or non-gating polish |
| Ownership | Repository owning implementation and person/team accountable for closure; use a full `uibcdf/<repo>#<number>` reference for provider issues |
| Priority and state | P1 integrity/reliability first; P2 planned accepted work; a decision-dependent recommendation retains that classification. Keep implementation state separate from executed validation |
| Dependency | The condition required, such as an adopted contract, received owner fix plus consumer guard, a reviewed source pair or authorization; an issue number or its closure alone is insufficient |
| Next gate and evidence | One observable next outcome, its applicable guard/receiving, exact source/provider identity and the owning evidence reference; do not duplicate detailed results here |
| Disposition | Open, active, derived, verified resolution or approved disposition, with decision-maker/date and remaining scope; derivation is not resolution |

An assigned repository is not an accepted personal assignment. Record the
responsible developer or owner-team handoff when activating a card. New child
IDs inherit their parent's scope until their own acceptance is recorded; the
parent cannot close while a required child remains unresolved.
The card's operational milestones do not add new allowed front-matter status
values to the reporting protocol.

### Executable queue at the recording checkpoint

| ID | Priority / milestone | Closure owner and record | Dependency and next observable gate |
| --- | --- | --- | --- |
| E0 | P1 evidence handling; before cleanup/disclosure | Principal maintainer's custody decision; Viewer team verifies the transfer; #315 | Approve/reuse a private retention destination, identify custodian, verify content and restore; current temporary custody is not durable acceptance |
| A1–A3 | P1 integrity; affected covering artifact and 1.0 | Viewer; scoped reports to be registered under #315 | Sanitized/private triage as appropriate, then real rejection/literal-text guards on the failing paths |
| A4 | P2 lifecycle; affected covering artifact and 1.0 | Viewer; scoped report to be registered under #315 | Own-versus-caller View distinction, original error retained and resources released after repeated failures |
| A5–A6 | P2 investigation; gate depends on established effect | Viewer; scoped record when activated | Reproduce or record a bounded, evidenced disposition; do not delay unrelated fixes waiting for a hypothetical defect |
| B1–B2 | P1 scientific reading/navigation; affected covering artifact and 1.0 | Viewer; #314 and a scoped precision report | Correlated Python/render acceptance and numerical-label truth; retain original failed runs |
| B3.1–B3.5 | P2 robustness; applicable candidate/1.0 scope | Viewer; split by mechanism under #315 | Reproduce each inspected path, then receive its window/title/layout/keyboard/cleanup outcome |
| B3.6, B4, E3, F1 | Scope/design decision; not an automatic release gate | Principal maintainer decides scope; relevant owner implements | Record accept/reject/defer and contract before implementation; accepted work gains its explicit milestone and guard |
| C1–C3, C5 | P1 integration of selected source pair | Viewer host and MolSysMT owner; #264 and uibcdf/molsysmt#421 / PR #543 | B1 for the new host pin; publish reviewed sources, receive relevant full/hosted results and owner acceptance |
| C4 | P1 qualification disposition | Viewer; #305 | Explain the original failure or a bounded evidenced disposition; a later isolated pass is not closure |
| D1–D5 | P1 for claimed scientific modes; owner handoffs now | MolSysMT owns fixes/definitions; Viewer receives them through uibcdf/molsysmt#421 | Supported owner correction/contract followed by exact consumer evidence; unavailable modes remain explicitly unqualified |
| D6.1–D6.10 | P2 previously accepted 1.0 families | Owning addon through uibcdf/molsysmt#421; Viewer #264 | Applicable native prerequisites and operation/effect matrix below; source exposure alone is insufficient |
| E1–E2 | P2 integrated/scale qualification | Viewer/addon receiving; #315 | Required operations ready, agreed test protocol and comparable identified sources |
| E4 | Human acceptance postponed | Principal maintainer chooses resumption | Relevant automated preparation plus actual human observation when resumed; postponement is not a pass |
| F2–F3 | P2 documentation and current handoff | Viewer; #315 | Selected functionality settled; verified references and one current ledger |
| G1–G2 | Covering artifact and final release have separate gates | Viewer #294 and coordinated provider/downstream owners | Candidate-specific source/docs/installed evidence and separate authorization; full D6 is not automatically a dependency of a scoped core artifact |

## Frozen audit baseline and evidence boundaries

The audit was recorded at **2026-11-06 21:53 UTC**. These are historical inputs,
not moving instructions or a claim about every later main commit.

| Surface | Audited identity and state |
| --- | --- |
| Viewer | Main checkpoint `1bff5884265f90339f4dbf856523427969ff56db`; last pushed executable-source revision `239c8dd74815a660159a95970e9136d7beebfdd2`; local uncommitted #314 correction, regression and reporting profile; no new public package is implied |
| Addon contribution | Local `e119953435a25c72e9a65b7428f74b1c2430b4f1`; feature `b358847cd0203b674ffa62ba90a15ed1a7c6f524`; qualified owner merge `8a0583fbecddd54a2b22a2621b9fff5be33483d3` includes native `4a80c22941090257d8ef78df09c944831413ee31` |
| Remote owner PR | uibcdf/molsysmt PR #543, head `8ab2f5474b2e04c68d31ef2854a238984b645fc8`, open and reported `mergeable=false`; local reconciliation is not delivered owner integration |
| Provider execution | Named Python 3.14.7 source environment; explicit PyUnitWizard `02d0015fa7d3149d92c0e632b8e584f6a47c37dc`; unchanged qualified native binary; installed metadata is not imported-source identity |
| Viewer board | Four complete pages, 313 records including PRs, 285 issues, 37 open, 23 with post-1.0 milestone, zero open Viewer PRs; counts precede coordination #315 |
| MolSysMT board | Seven complete pages, 614 records including PRs; one open PR, #543; provider issue ownership is preserved |

Applicable observations are deliberately separate:

- The audit's API/digestion/docs/capability selection passes **235 cases** in
  13.65 s, with seven legacy-H5MSM warnings. Dependency-route checks and queue
  indexes pass. Those checks do not cover all the reproduced failure paths.
- The complete current local core-browser attempt exits **1** in 1,334.985 s
  at **43/44, trajectory-plot**. Python reports index 1 after a popup click
  intended for 2. The final movie entry has not run in that attempt. All 1,233
  selected inputs, recorded heads and worktree statuses remain unchanged.
- The isolated plot guard and actual Jupyter R4/R5 workflows pass. R5 receives
  all **17 steps** on the merged addon source with all **4,770** selected inputs,
  heads and statuses unchanged. These passes do not erase the broad failure.
- Addon directed receiving passes **133 Analysis cases**, **36 preflight cases**
  on its earlier basis, and **245 combined native/Analysis/preflight cases** on
  the owner merge. These scopes overlap. Ten original course code cells execute
  on both bases; executable content, outputs, IDs and metadata are preserved.
- The complete af8eabcd8 addon attempt retains **4,966 passes/eight failures**;
  8ab2f5474's strict namespace correction passes its 63 affected cases and 36
  preflight controls. This is not one green complete new-addon run; see the
  [recovery receipt](../molsysmt_reference_full_recovery_20261106.json).
- Published code 239c8dd7 has successful hosted core browser, notebooks,
  experimental Qt and Python 3.14 source-pair runs. Its general CI
  **42262783166** still has four macOS cells queued in the audit observation;
  four Linux cells pass. Remote addon smoke **42291734623** passes; full
  **42291734556** remains pending. Neither qualifies the newer working pair.

Shared-environment findings remain tracked under uibcdf/molsyssuite#82. Source
overlays, the prior public package pair and a clean solver installation must not
be described interchangeably. The earlier
[measurement receipt](../measurement_geometry_receiving_20261106.json) and
[reference receipt](../molsysmt_reference_receiving_20261106.json) keep their
original producers and scopes.

## A — integrity, state rejection and resource ownership

| ID / status | What was observed and why it matters | Required correction and acceptance |
| --- | --- | --- |
| **A1 — reproduced, open** | Session loading can consume a benign external H5MSM instead of the legitimate embedded bytes. The extraction and subsequent reader do not use the same normalized member path. This violates isolation, integrity and portability. Source: [session loader](../../molsysviewer/session.py), `load_session`. | Review privately, validate member containment and read only the intended extracted file. Test malformed names and platform path conventions, embedded-byte identity, normal sessions, named analyses and unchanged destination/resources on rejection. Exact crafted inputs remain private. |
| **A2 — reproduced, open** | A rejected `import_state` clears an existing region before discovering an invalid section normal; molecular coordinates remain intact, but the scene changes after failure. Source: [state owner](../../molsysviewer/viewer/state.py), `import_state` / `_restore_sections`. | Complete validation before publishing, or provide a qualified restoration transaction. Test direct import and `load_state`, clear/merge/conflict modes, invalid later objects, history and handle validity. Preserve the semantic scene and relevant resources while retaining monotonic UID/tag/order high-water marks; rejection must not make identities reusable. Closed #127 protects `load_session`'s candidate route, not this direct-state path. |
| **A3 — reproduced, open** | A real DataCard popup parses an inert title marker as markup, while the original card shows literal text. Source: [DataCard](../../molsysviewer/js/src/ui/floating-data-card.ts), `openPopoutWindow`. Executable injection scope was not tested. | Use literal title/header handling consistently; review disclosure privately. Guard initial/restored/updated titles, special characters, ordinary popup input and original/popup parity without executable test payloads. |
| **A4 — reproduced, open** | `new_view` with a failing selection leaves one unreturned open View and two registered widgets. Source: [factory](../../molsysviewer/new_view.py). Repeated ordinary errors can retain resources. | Close the factory-owned View on initialization failure, preserving the original error. Never close a caller-supplied View. Guard invalid selection, conversion/load rejection, repeated failures and restored widget/resource ownership with real demos. |
| **A5 — inspected, investigate** | `save_state` asks for a fresh camera; `save_session` delegates to cached state. Immediate save after camera movement may differ within the debounce interval. This is an inspected asymmetry, not a reproduced camera-loss finding. | Reproduce from notebook and popup with actual camera movement and saved/recovered vantage points. Agree one capture policy and preserve the appropriate headless behavior. Share the qualified mechanism where applicable. |
| **A6 — inspected, investigate** | `close` marks the View closed before all callbacks/widgets are released; an intermediate exception may prevent the remaining cleanup and make retry return early. No universal leak is claimed. | Exercise legitimate addon/transport cleanup failures, retain diagnostics and independently release owned resources. Define idempotent repeated-close behavior. Do not replace real lifecycle tests with a successful-message assertion. |

Register scoped reports after duplicate review, including related closed #127
and #210 where useful. The private receipts support A1–A4; the coordination
issue is not a declaration that any of them is fixed.

## B — plot authority, numerical reading and DataCards

| ID / status | Required work and rationale | Acceptance |
| --- | --- | --- |
| **B1 — active, #314** | Finish plot-origin navigation through the existing authority route. The broad guard calls a queue drain before a popup's asynchronous `postMessage` is necessarily received; this is a plausible guard race, not a proven exclusive explanation of the failure. | One actual click must have correlated Python acceptance, one appropriate public callback and correct coordinates in both renderers. Exercise repeated selection, reverse Python navigation, retained plots, independent exported HTML and a single playback clock. Preserve the original causal red and broad failure; diagnose before rerunning. |
| **B2 — inspected, open** | [Plot formatting](../../molsysviewer/js/src/ui/trajectory-plot-overlay.ts) uses two fixed decimals; a small nonzero observation can read as zero and distinct axis limits can look equal. | Use suitable significant digits/scientific notation with units. Test tiny/large/signed values, narrow spans and cross-unit equivalents in actual labels. Preserve full stored values and numerical axis geometry. |
| **B3 — mixed inspection/reproduction, open** | Complete the DataCard lifecycle around A3: visible errors/retry for blocked or failed windows, current titles after update, usable bounds on small/resized hosts, keyboard/value access, and disposal during drag/resize. Global listener cleanup is incomplete in source; a universal retained-memory leak has not been measured. | Exercise ordinary popup gestures, failure acknowledgement, resize/fullscreen, rename/restore, active-gesture disposal and source independence. Apply the same semantics across hosts. Evaluate blur/opacity consistency as polish, not as a violation of Studio's specific accepted settings. |
| **B4 — inspected, new recommendation; scope/design decision pending** | Retained conformational plots store values/title/axes but not the exact calculation recipe from the private mounted report. After Clear, different references/populations can become indistinguishable. | Proposed direction: producer-supplied, versioned observation metadata that core preserves without interpreting science. If adopted, persist method/software, parameters, exact ordered populations/reference, weights and mass source, native/display units, structure coverage and source/revision linkage. Keep historical observations distinct from current applicability and never recalculate implicitly. |

B4 needs a reusable figure-level contract, with detached metadata and explicit
size/copy/remapping rules. A compact UI summary can accompany the complete
preserved recipe. Test two equal-title/different-recipe observations after
Clear, unmount, save/load and the defined copy/extract cases; test source edits
and stale applicability. This does not establish a universal scientific result
store or authenticate source identity from labels.

B3 is split so that an inspected cleanup path cannot inherit the status of a
reproduced title defect. A3 remains the owner of literal-text safety.

| Child / current class | Required outcome and next guard |
| --- | --- |
| **B3.1 — inspected** | Blocked/failed window creation has an observable error and qualified retry/close behavior, preserving the source View; reproduce the distinct blocked and bootstrap-failure paths |
| **B3.2 — inspected** | Updating a plot's title preserves the current literal title in its card, popup and restoration; qualify rename-before-popout and reuse |
| **B3.3 — inspected** | Cards remain reachable and usable at small host sizes and after resize/fullscreen; define host bounds and receive actual layouts |
| **B3.4 — inspected** | Values and sample navigation have keyboard/accessible equivalents with correct labels; qualify focus, selection and actual current-sample reading |
| **B3.5 — inspected** | Disposing during drag/resize detaches active global listeners and owned windows/observers; qualify repeated gestures/disposal without claiming a universal leak from inspection |
| **B3.6 — optional recommendation, decision pending** | Evaluate visual consistency with the accepted workbench design. Studio's opacity decision alone creates no DataCard styling requirement |

## C — deliver and receive the actual integration

**C1 — partial:** deliver the reconciled addon through uibcdf/molsysmt PR #543;
the owning team reviews/integrates it. Local e11995343 includes the owner's
adapter diagnostics and deposited-model-label corrections, resolving the index
conflict through the official generator. Remote 8ab2f5474 does not contain those
local commits or the conformational GUI. Never push or merge MolSysMT main from
this Viewer session.

**C2 — partial:** after B1's corrected Viewer source is reviewed and pushed, update
all five controlled owner routes and the dependency inventory to that exact
host. Run the complete new-addon collection and applicable hosted/source-pair
checks on the combined input. Keep native binary/tree, imported providers,
source hashes, original failures, skips and platform identity. Review incoming
owner changes at meaningful checkpoints; scoped passes do not qualify a later
native basis automatically.

**C3 — partial:** finish the remaining acceptance for #264 and the implemented
host services #301, #304 and #306. Preserve independent-result presentation,
declared pending readers and atomic reviewed replacement; do not reimplement
them merely because the issue remains open. Use their
[owning](independent_result_view_presentation.md)
[records](read_only_addon_panel_actions.md) and
[receiving criteria](conditional_result_replacement.md).

**C4 — open:** #305's hosted context-menu timeout still needs an explained
disposition. Later non-reproduction is useful evidence, not a causal repair.
Capture the hit target, layout, pointer routing and menu state if it recurs;
preserve assertions and the original failed run. See
[the report](../pending_bugs/hosted_popup_context_menu_receiving.md).

**C5 — reconciliation pending:** uibcdf/molsysmt#587, uibcdf/molsysmt#590,
uibcdf/molsysmt#591, uibcdf/molsysmt#603, uibcdf/molsysmt#609,
uibcdf/molsysmt#611 and uibcdf/molsysmt#614 retain their
board/history/tool/GUI/CI receiving scopes. Several
corrections are already in the contribution; an open owner issue is not proof
that its source implementation is missing. Record the contributed guard and
remaining acceptance, and let the owning team review, integrate and close it.
Owner stabilization/policy/benchmark records uibcdf/molsysmt#334,
uibcdf/molsysmt#524 and uibcdf/molsysmt#567 retain their own
contracts; they do not add unreviewed Viewer scientific features.

## D — scientific prerequisites and the complete approved task ledger

The addon mirrors native methods and scientific results. Its 246/248 reviewed
paths, with two unconditional native MD stubs omitted, establish exposure only.
The provider owns algorithms, physical definitions, validation and units. Keep
expert Python headless/composable and the GUI task-oriented; do not narrow expert
signatures to the fields needed by one form.

| ID / current disposition | Scientific owner requirement and consumer acceptance |
| --- | --- |
| **D1 — waiting on owner** | uibcdf/molsysmt#602: public axis/angle construction for Rotate. Receive handedness, units, degeneracies and selection/structure effects against independent geometry and actual rendered coordinates. Do not copy a private rotation formula into the addon. |
| **D2 — partial periodic family** | uibcdf/molsysmt#605, uibcdf/molsysmt#606, uibcdf/molsysmt#607 and uibcdf/molsysmt#608 cover invalid cells, changing-cell unwrap, oriented wrapping and unit-dependent origins. Retain the declared temporary admission profile and its review/removal condition. Receive independent lattice truth and in-place atomicity before declaring general periodic/cell tasks complete. |
| **D3 — waiting on owner** | uibcdf/molsysmt#613: overlapping global configuration contexts can leak/restore the wrong execution policy. Per-View locks do not isolate separate Views. Receive simultaneous/nested/exception cases through the supported native solution; this is not proof of wrong GPU numerics. |
| **D4 — waiting on owner** | uibcdf/molsysmt#616: compatible structure append fails after canonical H5MSM string restoration. Receive save/recover/continue with preserved scientific alignment. Do not rewrite chemistry tables or weaken identity checks downstream. |
| **D5 — dispositions still required** | Keep D5.1–D5.6 separate, with the qualified provider references below. Preserve scientific limitations or receive the owning definition before presenting provisional properties as verified physical areas/charges; interpretation questions are not demonstrated numerical errors. Test/CI/tool follow-ups retain their own issues. |

**D6 — partial, all previously approved families remain required:** use the
owner GUI task-family ledger under uibcdf/molsysmt#421 as the detailed scientific
acceptance specification. Continue Geometry rotation, principal-axis orientation,
sequence/reference correspondence and general cell work; Chemistry qualified
repairs, typing/charge assignments, construction/assemblies, solvent/ions and
coordinate refinement; Analysis further geometric observables, angles/torsions,
PCA, properties, sequence/connectivity, interactions and mechanical quantities.
Adopt compatible results through core scene/plot/color owners explicitly.

The scope baseline is the
[accepted 2026-11-06 product milestone](../molsysmt_tools_addon_plan.md#accepted-product-milestone--2026-11-06)
as recorded at Viewer `628664dc68c2f625c2beb622b80df45988b03d0d`, together with
the owner task-family ledger received under uibcdf/molsysmt#421 at contribution
`e119953435a25c72e9a65b7428f74b1c2430b4f1`. Incoming native exports do not
automatically expand that GUI milestone. Record explicit later scope decisions;
do not silently omit an existing accepted family.

| D5 child / owner record | Current class and next receiving condition |
| --- | --- |
| **D5.1 — uibcdf/molsysmt#549** | Native naming disposition; receive supported label semantics and consumer consequences |
| **D5.2 — uibcdf/molsysmt#582** | Native effective-mechanics contract; receive declared recipes/unsupported controls without inventing parameterization |
| **D5.3 — uibcdf/molsysmt#612** | Alternate-location/stable-ID admission; distinguish intentional whole-request rejection from a data-fidelity defect |
| **D5.4 — uibcdf/molsysmt#615** | Unexplained initialization observation; receive a causal diagnosis or bounded evidenced disposition, retaining the original timeout |
| **D5.5 — uibcdf/molsysmt#473** | Provisional ISA units/normalization; receive the owner's scientific definition or preserve its explicit limitation |
| **D5.6 — uibcdf/molsysmt#475** | ECI dimensional/charge/aggregation interpretation; receive the owner's scientific definition or preserve its explicit limitation |

| D6 child / accepted family | Current scope and next receiving condition |
| --- | --- |
| **D6.1 — rotation** | Pending graphical rotation; D1's supported constructor plus selection/reference/structure effect and rendered-coordinate guards |
| **D6.2 — orientation and references** | Pending principal-axis orientation and remaining sequence/reference correspondence workflows; native matching/degeneracy semantics and explicit correspondence |
| **D6.3 — periodic coordinates and cells** | Bounded tools exist; D2's received science and the qualified edit/cell effect are needed for general-family acceptance |
| **D6.4 — chemical repair and assignments** | Inspection and heavy/H preparation have source receiving; remaining supported repairs, typing and charge assignments need explicit methods/states, maps or independent ownership |
| **D6.5 — construction and solvent** | Pending accepted construction/assembly, solvent and ion tasks; explicit native inputs/model/seed/charge/cell requirements and result adoption |
| **D6.6 — coordinate refinement** | Pending graphical refinement over the received native minimization; explicit model/engine, supported structure scope and current/independent effect |
| **D6.7 — structural observables** | Distances/neighborhoods and local conformation slices exist; remaining angles/torsions/PCA and accepted structural result modes need numerical/axis/ownership receiving |
| **D6.8 — properties and molecular reports** | Pending accepted property, sequence and connectivity tasks; source maps, scientific definitions, evaluated scope and D5's relevant dispositions |
| **D6.9 — interactions and mechanics** | Expert routes exist; complete the accepted additional task/result integration with native prerequisites, units and separate scientific/visual ownership |
| **D6.10 — qualified visual adoption** | Current Measures/plots are slices; complete compatible accepted scene/color/plot mappings. New renderer or metadata contracts, including B4, require their recorded decisions first |

Implementation and evidence are tracked independently per child in its owning
record. A received native function does not establish GUI availability, and a
missing approved GUI cannot be marked not applicable. Each child retains the
activation-card ownership, dependency, next-gate and evidence fields.

Existing System, transforms/fitting, bounded periodic tasks, Chemistry inspection
and heavy/H preparation, distance/neighborhood analysis and local conformation
tables are receiving slices. They do not complete D6. Do not register placeholder
buttons, silently prepare chemistry, invent correspondences or promote native
experimental science to unconditional stability. This plan adds no detector.

### Operation and effect receiving matrix

For each activated family, identify the public method, actual native/expert/GUI
inputs and supported effect. Reuse its owning tests and acceptance specification;
do not invent a Cartesian product of every argument and platform. The same
resolved inputs and physical quantities must be comparable across surfaces.

| Dimension | Representative acceptance to record |
| --- | --- |
| Effect | Independent result, immediate managed edit, deferred projection, sync failure with synchronization-only retry, rejection and genuine no-op where supported |
| Source axes | Whole/subset populations, local/source maps, ordered/nonconsecutive/repeated atoms and structures, empty or invalid requests according to the native contract |
| Science | Explicit reference/state/engine/weights, nondefault physical units, admitted PBC and cell/coverage effects, finite and degenerate inputs; independent oracle/reference where a numerical claim is made |
| Ownership | Original versus returned data, unselected data, source/result close and replacement, stale reports, identity/history and resource retirement |
| Surfaces | Headless expert route and applicable GUI/Jupyter/popups; actual rendered geometry/values for visual claims; Qt/installed/human observations separately classified |
| Persistence | Supported scientific data and scene round-trip, explicit invalidation/applicability and continued work after recovery |

Each cell is **verified**, **failed**, **pending** or **not applicable with a
contractual reason**. Keep the evidence source and the condition that would make
an N/A cell applicable. Examples: read-only queries have no in-place projection;
an unadopted independent result has no sync retry; categorical results have no
physical-unit conversion; a method without PBC does not gain a PBC mode; an
explicit scene-reset replacement does not infer an atom map. Those exclusions
still require source/result independence and the applicable rejection guards.
Unsupported arguments are tested as rejection, not hidden under N/A. A visual
action on a retained result checks its bindings without rerunning the detector.
Scene Undo must not be mistaken for molecular Undo.

## E — full-session, scale and human acceptance

**E0 — durable evidence handoff pending:** principal-maintainer custody and
destination approval must be recorded, or an existing approved private retention
route reused. The Viewer team prepares and verifies the handoff; the actual
custodian or approved delegate acknowledges it. At this checkpoint the audit
receipts identify temporary artifacts only. No durable copy has been certified.

| E0 stage | Evidence required before marking the stage complete |
| --- | --- |
| Locate and protect temporary custody | Timestamped inventory of originals, scripts/commands, benign fixtures or deterministic fixture generators, full outcomes, source/provider identities and environment manifests; compare recorded hashes and prohibit premature cleanup |
| Record approved custody | Named custodian/delegate, approved private destination and access/retention rules; public ledger uses an opaque recoverable reference, while paths/access details remain private |
| Transfer and verify | Copy the required evidence, compare hashes against the originals and perform a read/restore check through the private reference; reconstructed evidence must be labelled reconstructed |
| Accept retention | Custodian acknowledgement, verification date and manifest digest; only then review temporary cleanup under the resource-ownership policy |

E0 blocks destructive cleanup, uncontrolled disclosure and evidentiary closure
of the affected findings. It does not block safe non-sensitive triage or
unrelated source work while the temporary originals remain protected. Hashes
alone do not preserve content. Keep its private access information out of the
public issue and document.

**E1 — partial:** receive one continuous molecular working session through the
expert API and the implemented GUI, rather than assembling completion from
unrelated successful examples:

1. Load TcTIM/1TCD and compose several sources in one View, both in a batch and
   progressively. Distinguish independent systems from complementary
   topology/coordinate/trajectory input; receive supported Add/Replace/Append
   and explicit structure pairing. Record source occurrences, maps, regions,
   inventory and the first/destination box/time policy, including absence.
   Preserve these bindings through the round-trip. Test PDB-ID acquisition
   separately from deterministic bundled input where networking applies. Reuse
   the [existing Load contract](../studio_interaction_contract.md#card-and-navigation)
   and composition guards; this adds no new loading mode. Preserve the declared
   rejection of unsupported incoming-analysis composition rather than inferring
   an analysis-embedding policy.
2. Inspect/select categories and arbitrary atoms; review removal, extract an
   ordered subset and create an independent copy. Verify exact maps and ownership.
3. Inspect readiness, choose a qualified explicit preparation/state/method,
   inspect the result and adopt its destination deliberately.
4. Transform coordinates and perform a reference-based comparison/alignment.
   Supplement the protein with genuine pentalanine conformations [0,8,3] and
   nonconsecutive local structure order [2,0]; preserve unselected data and cells.
5. Calculate representative geometry, properties and interactions; preserve
   method/units/evidence/coverage. Add compatible visual content explicitly,
   distinguishing zero, evaluated-empty, unevaluated and missing prerequisites.
   For domains with separate scientific analyses and visual references, notably
   named Interactions, hide/show/delete the representation while proving the
   analysis is retained and not recalculated. Receive edit-driven coverage
   invalidation through its scientific owner, separate explicit scientific
   deletion, and declared index correspondence for an independently imported
   analysis. Measures, Shapes and mounted reports retain their own lifecycle
   contracts; this check creates no additional scientific store for them.
6. Save supported molecular data/analyses through the native format owner
   (H5MSM recommended) and scene through Viewer. Close, recover and continue;
   compare inventory, coordinates, structures, scientific parameters, coverage
   and separate analysis/representation bindings. B4's proposed additional
   figure provenance remains conditional on its scope decision.
7. Exercise error/retry, source/result lifetime and relevant operations through
   Jupyter, canvas popup and detached Studio. Keep independent native Qt evidence
   and installed results in their own scopes.

**E2 — protocol proposed; execution and acceptance decisions pending:** measure
the following bounded workloads with existing entrypoints. CLI definitions have
been inspected; this document does not assert that a new campaign has run or
that an old script is compatible with an unreceived future source.

| Measurement | Defined starting workload and existing entrypoint |
| --- | --- |
| Atom/structure axes | `devtools/benchmarks/representative_scale_gate.py --case small --structures 100 --repeats 3 --table-row`, plus small/medium/large with one structure: 2,882 / 26,214 / 104,856 atoms |
| Actual browser rendering | From `molsysviewer/js`, use `MOLSYSVIEWER_SCALE_MATRIX=small:1,small:10,small:100,medium:1,large:1` with `npm run bench:representative-scale` and the explicit qualified `PYTHON`; retain first draw, first/revisited navigation, representation and memory samples |
| Combined coordinates/interactions | `devtools/benchmarks/interactions_residency.py --case medium --pattern churn --layout rings --repeats 3`; receive `reuse` and `churn` on the selected small/medium anchors before extending the matrix |
| Actual detector control | `devtools/benchmarks/interactions_detector.py --family hbond`: 62 atoms and 5,000 real structures, with the tool's twenty queries; this family does not take a `--structures` option |
| Scene history ownership | `devtools/benchmarks/scene_history_memory.py --case ordinary --case literal-overlay --repeats 3`, retaining its twenty-five checkpoints per case |

Invoke Python entrypoints with the selected `molsyssuite@uibcdf_3.14`
interpreter, recording its exact path privately and its version/provider
identities in the receipt. Reuse the
[representative baseline](../performance/representative_scale_gate_2026_08.md)
and [Interactions measurements](../interactions_performance.md); qualify the
fixture/entrypoint on the selected source before comparing measurements.

Representative-scale coordinates are constructed molecular supercells and
rigid-drift structures, not an observed MD trajectory. Interactions-residency
cases are 62×5,000, 10,044×1,000 and 100,006×100 with synthetic nonperiodic
occurrences; selected input hashes and generation recipes must identify that
scope. Detector receiving supplies the distinct real-structure control.
Query repetitions within a process are not fresh-process repetitions.

Record three fresh-process samples per selected anchor, with the tool's actual
repetition semantics. `representative_scale_gate` and `scene_history_memory`
already create three workers with `--repeats 3`; do not wrap that in three more
executions unintentionally. `interactions_residency --repeats 3` repeats queries,
so three separate invocations are needed for three process samples. For browser
cold-per-anchor comparison, run one matrix item per CLI invocation three times.
Alternatively repeat the whole matrix three times and label the shared-browser
sequence and warm/cold observations precisely; that is not a fresh Chrome per
item. Fresh processes do not imply cold filesystem or compilation caches.

Report median, median absolute deviation and range, preserving raw samples.
Record input hashes, sources/providers, policies, cold/warm state, OS,
architecture, kernel/page size, Python, Node/Chrome, CPU, renderer/GPU/driver,
RAM and storage. Compare equivalent conditions and separate fixture preparation,
scientific calculation, transport and drawing. The initial RSS/retirement
profile is Linux with a verified 4 KiB page size: several tools rely on `/proc`
and browser RSS currently assumes 4 KiB pages. Verify that profile before the
campaign. Unsupported/unavailable memory metrics are N/A with their reason and
reactivation condition, never zero or portable qualification. Non-Linux peak
fallback observations remain diagnostic unless separately qualified.
SwiftShader RSS is not hardware VRAM; an incomparable baseline cannot establish
a regression or a pass.

**E2 prolonged-use subcase — instrumentation proposal, not yet executed:** use
one kernel/process for three blocks of ten load/edit/query/window/save/recover/
close cycles, targeting a 20–30 minute observation window. Each block records
actual elapsed time and cycle counts. Keep an independent witness View, exercise
both popup types, close only owned resources and sample live resources/memory/
latencies after each block and at completion. Reuse/instrument the existing
actual-Jupyter receiver; it currently has no `--cycles`/`--duration` contract.
Restarting its kernel for every repetition does not test cumulative retention.
Agree the workload/runtime envelope when E2 is activated before executing it;
it is a measurement design, not a promised product response time.
If the completed active cycles do not cover the agreed observation window,
report that actual scope and the remaining long-session check; agree any
extension instead of counting idle waits or restarted kernels as prolonged use.

E2 closes only with exact scientific/ownership invariants, rejection without
lost work, a complete comparable dataset and explained resource retirement.
Peak RSS is monotonic and allocator retention alone does not prove a leak.
Latency/memory regressions outside observed variability require explanation and
triage against the agreed baseline. Any admission thresholds or tolerances
without an agreed basis remain explicit decisions, not invented universal
RAM/FPS limits. Document admitted limits; do not introduce lazy residency or
prewarming under this measurement task.

**E3 — new recommendation; scope/design decision pending:** evaluate useful
preflight size/cost information before disproportionate scientific jobs. Review
progress/interruption with the native owner before promising cancellation; this
recommendation does not add an approved cancellation API. Bounded browser pages do
not bound query construction, coordinates, disk use or all native calculations.
Keep errors actionable and avoid silently changing the requested science.

**E4 — postponed by maintainer:** retain the agreed human System/results/
Geometry/Jupyter/visible-Qt observations. Automation cannot mark them done.
Resume only when the maintainer chooses. Qt remains an experimental host with
its own qualification; this plan adds no universal desktop-platform release gate.

## F — stable public contract and usable documentation

**F1 — proposed compatibility hardening; scope decision pending:** supplement
the digestion inventory with a reviewed snapshot
of public routes, signatures, defaults and stable/experimental classification
for the intended 1.0 contract. The existing inventory intentionally checks
digestion/totals, not every compatible API change. Preserve its guard and add
the distinct compatibility boundary without freezing private implementation.

**F2 — pending:** reconcile API reference, examples, installation and capability
claims after the functionality is settled. A concrete residue is the abbreviated
`convert(...)` entry in the [public API reference](../../docs/content/developer/public_api.md)
despite removal of `view.convert`; use verifiable qualified names. Check canonical
control modes, source-versus-published addon availability, experimental limits
and provider documentation links. Viewer owns addon management/creation/catalogue;
each component owns its addon use and scientific documentation.

**F3 — initial audit recorded; reconciliation pending:** keep this dashboard as the current
answer, with short links from README/checkpoints/release plan. Preserve dated
receipts without duplicating competing current-status narratives. Correct a
closed item's owning record when closing it and archive/index the resolution;
do not leave historical counts as current instructions. This document itself
does not supersede the normative contracts or erase previous accepted decisions.

## G — covering artifact and exact installed qualification

**G1 — pending, actions paused:** #294 requires a public artifact covering the
delivered scene-handle/player contracts and a disposition for the downstream
initialization case. The intended Viewer successor remains **0.25.0, unfrozen**.
After the required code/docs gates and maintainer decision, fix a clean producer,
source counterpart, build coordinates and original file hashes. Preserve all
existing public tags/packages/DOIs. Addon completeness and the covering-artifact
milestone have separate acceptance; neither automatically authorizes publication.

**G2 — pending:** verify the declared capability floors and the actual installed
pair outside both source trees, including addon discovery/API/GUI where shipped.
Run the required four-platform/Python 3.11–3.14 installed matrix and Windows
launcher checks for exact files. Keep minimum/current provider evidence distinct
from source overlays; do not raise every global dependency floor just to expose
one optional addon capability. Coordinate downstream receiving through #294.

Follow [release evidence](../release_gate_evidence.md) and
[citation/publication policy](../release_and_citation.md) for authorized staging,
public label/index verification, npm/CDN where applicable and preserved releases.
A tag, staging-only success, solver declaration or API path count does not close
the publication lifecycle. Both 1.0 releases remain paused.

## Already deferred or separate work

Retain the accepted post-1.0 placement of Mol* upgrade #115, remote certification
#100, alternate desktop shells #276, lazy materialization/performance architecture
#54/#55, split-screen #49, generated mixin typing #57, and copying Python from
Studio #226. Existing #48/#56 own advanced Interactions growth, not an absent
basic domain/panel. Demos/recents #277 and future standalone certification #113
retain their decisions. #299's design-candidate study is exploratory, not an
extra required scientific task introduced by this audit.

Qt migration #109 and local D-Bus disposition #278 retain their experimental/
provider-specific scopes. #42 is a non-gating upstream source-form improvement;
#41 and #80 are advisory/tooling work. An issue lacking a milestone is not
automatically a core 1.0 blocker. Do not close any of these solely from this list;
use its actual owning acceptance and evidence.

## Execution order and completion audit

### Parallel lanes and dependency conditions

The block letters group work; they are not a mandatory serial schedule.

| Lane | Can advance now | Condition for the next receiving milestone |
| --- | --- | --- |
| Evidence and integrity | Protect E0 originals; scope A1–A4 and prepare their targeted cases | Approved private handling where needed, relevant fixes and actual invariants on rejected/failed operations; E0 acceptance before cleanup/disclosure/evidentiary closure |
| Plot correctness | B1 diagnosis and B2/B3 reproductions can proceed beside A | Correlated authority and observed rendering; receive every applicable safety/contract correction in the selected Viewer source |
| Provider work | D1–D5 handoffs, contract decisions and native review do not wait for all Viewer/UI work | Supported owner revision/contract plus the relevant consumer guard; a provider issue closing is not consumer acceptance |
| Integration and accepted tasks | Review current contributed slices, prepare C1/C5 and unblocked D6 children | C2's new host pin follows B1; each task receives only its actual prerequisites and operation/effect cells |
| Sessions and evidence | Prepare E1 inputs/matrix and E2 protocol; receive implemented slices without declaring the entire session complete | Required operations, scientific prerequisites and identified combined sources for the claimed workflow |
| Decisions and documentation | Resolve B3.6/B4/E3/F1 scope and prepare F1 when adopted; maintain scoped API/help with every change | Broad final documentation follows the agreed functionality; relevant minimal artifact documentation is required before its publication |

A5/A6 can close through reproduction and correction or a documented, tested
disposition. Unconfirmed investigations must not indefinitely serialize unrelated
work. Keep their conclusions distinct from the confirmed defects. Freeze inputs
during a gate, using isolated worktrees for independent work rather than silently
qualifying a moving source. Start with affected cases and broaden when the changed
boundary warrants it; retain still-applicable results.

### Two distinct delivery milestones

| Milestone | Required scope and evidence | What does not follow from it |
| --- | --- | --- |
| **M0 — covering pre-1.0 artifact, #294** | Reviewed selected core source with applicable integrity/navigation/figure defects resolved or validly disposed; capability/compatibility and scoped documentation received; exact candidate/files, provider counterpart and required installed/downstream checks under G | Completion of every D6 GUI task is not automatically a prerequisite for a scoped core artifact. Excluded/unshipped addon capabilities must remain explicit; this milestone neither waives accepted 1.0 work nor authorizes release/tag/package actions |
| **M1 — complete accepted 1.0 scope** | M0-style evidence for the exact intended release candidate plus all adopted D6 families, E1's complete session, applicable E2/E4 acceptance, accepted design decisions and F's final contract/documentation; strict release gates and separate authorization | Historical M0/source/installed passes do not qualify different bytes, versions or later inputs. Qt remains experimental and postponed human acceptance is not a passing observation |

The planned pre-1.0 Viewer version remains 0.25.0, unfrozen. M0 can be planned
without completing all addon growth first; its actual selected scope and provider
capabilities need the maintainer's decision. Both milestones retain the existing
publication pause. Additional artifact work must not produce duplicate workflow
dispatches, rebuild already qualified bytes or move published tags.

### What counts as closing an ID or #315

| Tracking outcome | Meaning for completion |
| --- | --- |
| Audit recorded | Finding, provenance and intended acceptance preserved; implementation is still pending |
| Derived to an owning issue | Scope/ownership established; the parent ID remains open until its acceptance is received |
| Implemented or locally verified | Only the named effect and source are received; required integration/hosted/installed/human checks remain separate |
| Verified resolution | Owning change and relevant executed guard satisfy the ID's applicable acceptance; source and evidence are addressable |
| Scope accepted | Maintainer approves a proposal's scope/contract; only the decision is complete. Its implementation and receiving stay open, with an explicit milestone and owning tasks |
| Approved disposition | Maintainer records rejection/deferral of a new recommendation or an evidenced bounded non-defect/limitation, with date, rationale, scope and review condition where applicable. This does not certify an unimplemented accepted proposal |

B3.6, B4, E3 and F1 first need their explicit scope decisions. A rejected or
deferred new recommendation can receive that recorded disposition without
becoming a new publication gate. Previously accepted families cannot be dropped
through a progress update: any proposed change needs an explicit maintained
scope decision. No disposition silently overrides a normative guarantee or
unmet mandatory release evidence.

Before closing #315, inspect every stable ID and required child against current
source, its owning report, applicable guard and accepted disposition. Derivation
alone is insufficient. Required unresolved families, unexplained failures and
missing evidence remain visible; human postponement does not satisfy acceptance.
Record the appropriate final guard/normative reference, synchronize owning
closures and archive/index the ledger under the reporting protocol. Completion
of this coordination issue and authorization to publish 1.0 are separate facts.

## Evidence retention

The sanitized audit receipt is `msv-repository-audit-20261106.json` in the
maintainer's private temporary evidence collection. It records source states,
complete board acquisition, test selections and artifact digests. **E0 owns
durable preservation; accepted custody/destination/reference and verification
are still pending.** Preserve the scripts/fixtures, environment and outcomes,
not only this digest table. The following identify private records, not publicly
downloadable artifacts or proof that a durable copy already exists.

| Evidence | SHA-256 / identity |
| --- | --- |
| Session member reproduction receipt, benign inputs | `6b195a009b937ea07b3639cc938717c6e3011987cc04e1817f061aeeff7d95ea` |
| State rejection and failed-factory lifecycle receipt | `8718e8b0bb283ac483471757845e39360a5c61169eaf70c7956cc4db549de23a` |
| Literal-title actual-browser result | `4c1a965886319e9b17d350fc8eba5ea6482b563db0bb0ff6660a96e5ae6f6fe8` |
| Literal-title source/provider receipt | `663ca708e40fc45c762fdbf736529428fcea7942473daedf8b6fd7f73b88cbe4` |
| 235-case audit meta-check log | `40ceed2b37b10cd33fff2cfbf36d81059e5c49521f5dd27066e7ff9a6646690b` |
| Failed broad core immutable-input receipt | `9e71071f3a41192f510db88ea3b4469673b0ef4063d264469318cf980fa25915` |

For future transitions, record **ID, source, guard/command, actual outcome,
receiving location and remaining scope** in the owning record, then update the
dashboard. Do not append a second chronological work log here or rewrite the
frozen audit baseline to describe a newer result.

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

**Next action:** scope and register A1–A4, retaining private handling where
appropriate, then repair and qualify those integrity/lifecycle boundaries.
Continue B1's existing #314 diagnosis without treating its broad failure as
passing. No product correction in this ledger is declared done by this document.

| Block | Current status | Owner and tracking | Exit evidence |
| --- | --- | --- | --- |
| A — integrity, restoration and cleanup | Four reproduced findings await scoped reports/fixes; two further investigations are unconfirmed | Viewer; coordination #315 | Rejection preserves existing work; owned resources close on failure; actual public-API/browser regressions |
| B — plots and DataCards | #314 correction/regression local; broad core failed; precision, provenance and card follow-up pending | Viewer and scientific producer; #314, #264, #315 | Python/render agreement, interpretable retained observations, safe literal titles and complete card lifecycle |
| C — contribution and host integration | Reconciled addon committed locally; remote PR older and reported conflicting; source gates incomplete | Viewer #264/#301/#304/#305/#306; uibcdf/molsysmt#421 and PR #543 | Reviewed delivery, current controlled pair, relevant full/hosted outcomes and explained failures |
| D — scientific prerequisites and approved GUI families | Partial implementation; provider corrections and several task families remain | MolSysMT owns science; addon owns tasks; #264/#315 and uibcdf/molsysmt#421 | Received native fixes plus every required family/effect, without hidden preparation or copied algorithms |
| E — integrated use, scale and human acceptance | Partial headless/Jupyter receiving; complete workflow and prolonged-use checks pending; human review postponed | Viewer/addon; maintainer owns human observations | TcTIM/ensemble save–recover–continue, independent lifetimes and representative measured limits |
| F — public contract and documentation | Digestion/meta checks pass; compatibility snapshot and documentation reconciliation pending | Viewer; #315 | Named stable/experimental contracts, verified references and one usable current handoff |
| G — covering artifact and installed qualification | Pending; candidate/publication actions paused | Viewer #294; coordinated provider/downstream receiving | Authorized exact producer/files, clean installed checks and required distribution evidence |

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

**C5 — reconciliation pending:** uibcdf/molsysmt#587, #590/#591, #603,
#609/#611/#614 retain their board/history/tool/GUI/CI receiving scopes. Several
corrections are already in the contribution; an open owner issue is not proof
that its source implementation is missing. Record the contributed guard and
remaining acceptance, and let the owning team review, integrate and close it.
Owner stabilization/policy/benchmark records #334/#524/#567 retain their own
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
| **D2 — partial periodic family** | uibcdf/molsysmt#605–#608: invalid cells, changing-cell unwrap, oriented wrapping and unit-dependent origins. Retain the declared temporary admission profile and its review/removal condition. Receive independent lattice truth and in-place atomicity before declaring general periodic/cell tasks complete. |
| **D3 — waiting on owner** | uibcdf/molsysmt#613: overlapping global configuration contexts can leak/restore the wrong execution policy. Per-View locks do not isolate separate Views. Receive simultaneous/nested/exception cases through the supported native solution; this is not proof of wrong GPU numerics. |
| **D4 — waiting on owner** | uibcdf/molsysmt#616: compatible structure append fails after canonical H5MSM string restoration. Receive save/recover/continue with preserved scientific alignment. Do not rewrite chemistry tables or weaken identity checks downstream. |
| **D5 — dispositions still required** | Keep uibcdf/molsysmt#549, #582, #612 and #615 distinct: legacy naming, effective mechanics recipes, alternate-location/stable-ID admission, and unexplained initial-canvas timeout. uibcdf/molsysmt#473 covers provisional ISA units/normalization; #475 covers ECI dimensional/charge and aggregation semantics. Preserve the native limitations or receive the owning definition before presenting those properties as verified physical areas/charges; these are not demonstrated numerical errors. Test/CI/tool follow-ups retain their own issues. |

**D6 — partial, all previously approved families remain required:** use the
owner GUI task-family ledger under uibcdf/molsysmt#421 as the detailed scientific
acceptance specification. Continue Geometry rotation, principal-axis orientation,
sequence/reference correspondence and general cell work; Chemistry qualified
repairs, typing/charge assignments, construction/assemblies, solvent/ions and
coordinate refinement; Analysis further geometric observables, angles/torsions,
PCA, properties, sequence/connectivity, interactions and mechanical quantities.
Adopt compatible results through core scene/plot/color owners explicitly.

Existing System, transforms/fitting, bounded periodic tasks, Chemistry inspection
and heavy/H preparation, distance/neighborhood analysis and local conformation
tables are receiving slices. They do not complete D6. Do not register placeholder
buttons, silently prepare chemistry, invent correspondences or promote native
experimental science to unconditional stability. This plan adds no detector.

## E — full-session, scale and human acceptance

**E1 — partial:** receive one continuous molecular working session through the
expert API and the implemented GUI, rather than assembling completion from
unrelated successful examples:

1. Load TcTIM/1TCD, recording source, inventory and initial scene. Test PDB-ID
   acquisition separately from deterministic bundled input where networking applies.
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
6. Save supported molecular data/analyses through the native format owner
   (H5MSM recommended) and scene through Viewer. Close, recover and continue;
   compare inventory, coordinates, structures, scientific parameters and objects.
7. Exercise error/retry, source/result lifetime and relevant operations through
   Jupyter, canvas popup and detached Studio. Keep independent native Qt evidence
   and installed results in their own scopes.

**E2 — pending:** measure prolonged sessions, repeated load/close/failure,
several Views and both popup types. Vary atom and structure counts independently:
a small system with many structures and a larger one with fewer structures.
Include combined coordinates/interactions/scene residency, first/revisited
navigation, startup, save/recovery, Python/browser memory and cleanup. Existing
benchmarks are dated evidence, not a current hardware-GPU or universal-RAM claim.
Do not introduce lazy residency or prewarming without its separate evidence.

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

The proposed order is **A → B → C → D → E → F → G**, allowing independent owner
handoffs and received source checks in parallel. A5/A6 are investigations; their
result may be a correction or a documented, tested disposition. F1 can be
prepared during implementation, while broad public documentation remains after
the agreed functionality. Start each fix with its affected failing case, then
broaden when the changed boundary warrants it. Retain still-applicable results.

Before closing #315, inspect each stable ID against its actual current source,
owning report, executed guard and acceptance. Required unfinished task families,
unexplained product/qualification failures, missing installed evidence and
postponed required human acceptance must remain explicit. Deferred items need
their existing decision, not an invented passing result. Close the coordination
issue only after its required work has an evidenced disposition; publishing 1.0
still requires its separate decision and complete release gates.

## Evidence retention

The sanitized audit receipt is `msv-repository-audit-20261106.json` in the
maintainer's private temporary evidence collection. It records source states,
complete board acquisition, test selections and artifact digests. Preserve the
evidence in an approved durable location before temporary cleanup; the following
digests identify private records, not publicly downloadable test artifacts.

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

# Library architecture and scientific review — 2026-11-04

**Status: review completed; recommendations are not implemented by this audit.**
Requested by Diego during the development pause. This document preserves the
assessment reported in the conversation on 2026-11-04. It is dated evidence,
not a normative contract, a new implementation queue or a release approval.

## Scope and evidence limits

The inspected Viewer checkout was
`139fa422c9bd5f0c07006d7ac99b7d1333ab845f`. The review sampled current contracts,
Python and TypeScript implementation, scientific tests and recorded validation.
It covered molecular ownership, scene state, edits, interactions, persistence,
units, scalability, maintainability and opportunities for scientific growth.

No product files were changed and no new scientific tests, full regression, CI,
installed-package qualification or visual smoke were executed for this review.
Existing tests were inspected, not rerun. Previously recorded results retain
their original source, dependency and platform scope. The review does not
certify every line, detector, input format or molecular system. Unpublished
addon work in a separate MolSysMT worktree is not qualified by this document.
Writing and checking this report is documentation work only.

### Review coverage

“Inspected” means source or document reading, not execution. “Recorded” means
an earlier receiving record was consulted, not independently rerun today.

| Area | Evidence used in this review | Coverage boundary |
| --- | --- | --- |
| Scientific ownership and scene lifecycle | Inspected product/scene contracts, interaction manager, edit coordinator and scene history. | Sampled critical paths; no exhaustive public-API or concurrent-operation audit. |
| Scientific result fidelity | Inspected independent geometry reconstruction and tests for queries, coverage, periodic images and scalar units. | Selected examples; no universal detector or chemical-domain validation. |
| Persistence | Inspected session writer, session contracts and interaction persistence assertions. | No fresh archive round trip, compatibility matrix or hostile-file audit. |
| Python/frontend agreement | Inspected serializers, interaction rendering and documented runtime architecture. | No fresh browser, popup, Jupyter or Qt execution; not every action was traced. |
| Scale | Inspected materialization policy, coordinate warning implementation and recorded performance analysis. | No new timing/RSS/GPU measurement or general capacity guarantee. |
| Integration and distribution | Consulted existing qualification/checkpoint records. | No fresh dependency solve, import-origin check, board/CI status audit or candidate qualification. |
| Maintainability | Inspected selected modules and measured two source-file line counts. | No dependency graph, change-coupling metric or full static analysis. |
| Security, accessibility and complete format/platform coverage | Not specifically evaluated. | No positive or negative conclusion about these areas follows from this review. |

Relative source/document links below are navigation aids. Observations refer to
the inspected commit above; recover those paths at that commit when comparing
later changes. Existing issue references identify related ownership, not a
fresh verification of their live board status.

## Overall assessment

MolSysViewer has a sound architectural foundation and a coherent scientific
identity. The review found no evidence that justifies a wholesale rewrite.
The inspected ownership boundaries provide a plausible foundation for further
growth, subject to the contracts and measurements that each expansion needs.
Its principal risks are accumulated coordination
complexity, data scale and the gap between implemented capabilities and fully
qualified capabilities.

The core's maturity should be judged by the reliability and clarity of its
declared promises, rather than the number of MolSysMT functions exposed through
an addon. This review does not declare the current checkout ready for 1.0.

## Strengths supported by the inspected implementation

### Scientific data and visual representations remain separate

Molecular data, named scientific results and visual objects have distinct
ownership. Hiding an interaction set does not delete its analysis, and styling
does not change its measured values. This enables exploration without silently
altering scientific evidence. See the
[product boundary](../core_and_addon_boundary.md) and
[Interactions contract](../interactions_compatibility_contract.md).

### Scientific authority and coordination are explicit

MolSysMT owns molecular semantics and calculations; Viewer owns scene
integration and presentation. Python remains the composable foundation for
graphical actions. The
[edit coordinator](../../molsysviewer/system_edits.py) distinguishes pending
edits, uncertain partial writes and synchronization failures. A display failure
does not justify automatically repeating completed science.

### Identity and validity are treated as scientific requirements

Atom and structure correspondence, analysis revisions and evaluated coverage
are explicit. The
[interaction manager](../../molsysviewer/interactions.py) checks system identity
and revision before publishing a calculation. The
[renderer](../../molsysviewer/js/src/managers/handlers/interaction-handlers.ts)
rejects stale frame/revision replies and hides preceding-frame links when the
frame changes.

### Persistence and units have meaningful safeguards

[Session writing](../../molsysviewer/session.py) stores molecular data and scene
state and replaces the destination through a temporary file. Scientific units
are explicit at relevant transport boundaries; graphical precision is distinct
from the native scientific arrays. These safeguards are stronger than merely
saving a screenshot or replaying past commands.

**Restoring a session and reproducing its calculations are different claims.**
Restoration recovers the stored system, supported results and scene. Recomputing
those results additionally requires sufficient inputs, preparation history,
methods, parameters, software/backend versions and any relevant stochastic
settings. Named analyses preserve supported provenance, but this review did
not audit whether every scientific route records everything needed to rerun
it. A saved session alone is not a universal computational-reproducibility
certificate; see finding A6 below.

### Scientific checks go beyond successful function calls

The inspected [qualification code](../../devtools/qualify_interactions.py)
independently reconstructs observed participant positions and distances from
coordinates, periodic images and box vectors. Tests also cover nonconsecutive
frames, evaluated-empty versus unevaluated coverage, persistence and
[scalar colors under equivalent unit systems](../../tests/test_scalar_color_units.py).
This is relevant evidence of boundary fidelity, not universal validation of
the scientific methods themselves.

## Limitations and improvement opportunities

The identifiers A1–A6 are stable references within this audit, not issue
numbers or assigned bug severities. Observations and recommendations are
separate: a limit or a review question is not automatically a defect.

| ID / area | Observation at the inspected source | Assessment and recommended direction |
| --- | --- | --- |
| A1 — Maintainability | `molsysviewer/viewer/core.py` has 3,820 lines and `molsysviewer/js/src/managers/viewer-controller.ts` has 4,663. | These are candidates for a responsibility/coupling review. Size alone does not prove excessive coupling or justify refactoring. Extract cohesive responsibilities only when review identifies a concrete maintenance benefit. |
| A2 — Scale | All selected structures remain materialized. Coordinate warnings and bounded visual/query replies do not bound total process or browser memory. | State the measured operating scope. Treat topology projection, model/geometry construction and renderer residency as separate costs. |
| A3 — Chemical states | The molecular serializer reads bonds from the reference chemical state. | This is a defined projection contract, not general visual exploration of multiple chemical states or frame-dependent connectivity. Any expansion requires explicit state/structure semantics. |
| A4 — Scientific maturity | Interactions, provider result/page contracts and detection families retain experimental classifications. | Correct integration is distinct from validation of every detector and interpretation. Preserve those labels and prerequisites. |
| A5 — Developer guidance | Current architecture passages describe provider qualification under #114 as open and the redesigned addon as proposed. | Reconcile the current narrative with the accepted boundary and receiving records; precise passages are identified below. Preserve genuinely dated evidence. |
| A6 — Reproducibility claims | Sessions restore stored science and scene; inspected analysis metadata retain supported provenance. | Document restoration separately from recomputation. Completeness of provenance across every route was not evaluated, so no missing-field defect is asserted here. |

The line counts above were measured directly from source during this review.
No complexity metric, performance benchmark or new runtime defect was inferred
from them. The reference-state observation comes from
[the shared molecular serializer](../../molsysviewer/loaders/array_native_molsys.py).

The existing [performance proposal](../pending_proposals/post_1.0/representative_scale_followups.md)
already distinguishes transport, geometry construction and browser memory.
Its historical measurements remain tied to their original conditions. Smaller
wire data alone cannot establish a larger rendering capacity. Related work
already has owners in #54 and #55; this audit does not reopen their release scope.

### A5: specific passages requiring reconciliation

At the inspected commit, [architecture.md](../architecture.md) contains:

- **Python Runtime Layers / InteractionsManager**, line 51:
  “Provider-release qualification remains open under `uibcdf/molsysviewer#114`.”
  The [current public qualification section](../interactions_qualification.md#current-public-qualification--2026-10-07)
  records completion for the public 0.24.0 / 0.23.0 pair and closure of
  #114/#140. A new candidate still needs its own qualification; the current
  sentence does not distinguish those two scopes.
- **Live Edit and Rebuild**, lines 223–231: retirement of the separate addon
  is followed by “A redesigned MolSysMT tools add-on is now proposed”. Legacy
  retirement under #186 is valid history. The
  [accepted boundary](../core_and_addon_boundary.md#python-studio-and-add-on-integration)
  distinguishes that retired entry point from the approved redesign and its
  partially implemented provider-owned source facade. Current architecture
  prose should express that distinction without implying published availability.

These are observations about maintained guidance, not requests to rewrite the
dated staging and public-release observations in qualification records.

### Decision and follow-up criteria

Owners below identify responsibility, not a new assignment or authorization.
No new implementation issue is created by this table.

| ID | Benefit / responsible boundary | Related tracking | Evidence needed to decide or accept follow-up |
| --- | --- | --- | --- |
| A1 | Lower change/review cost; Viewer maintainers. | No dedicated issue verified by this audit. | Identify concrete coupled responsibilities or recurring change failures first. Any extraction must retain affected API, scene, lifecycle and endpoint behavior under applicable tests; file length reduction is not acceptance evidence. |
| A2 | Honest capacity expectations and responsive exploration; Viewer rendering/transport with MolSysMT source access. | Viewer #54 / #55. | Preserve documented current limits. Future optimization needs atom/frame/representation-specific cold/warm timings, peak/retained memory and scientific fidelity checks, including popup cost where claimed. |
| A3 | Unambiguous chemical-state exploration; MolSysMT semantics and Viewer projection/UI. | No dedicated state-visualization issue verified; #46 concerns related chemical metadata, not the whole proposal. | Agree state selection and structure/analysis correspondence first; then verify explicit selection, ambiguous/absent-state behavior, frame changes and persistence. |
| A4 | Prevent overinterpretation; detector owners and Viewer scientific presentation. | Existing Interactions contracts; completed #114/#140 are historical qualification, not reopened issues. | For each advertised method, identify its scientific authority, prerequisites and validated scope. Add independent consumer geometry/identity cases where a specific gap is demonstrated; retain experimental labels. |
| A5 | One understandable current architecture; Viewer documentation owners. | Viewer #264 / MolSysMT #421 supply addon receiving context; no dedicated documentation issue verified here. | Reconcile the cited passages with accepted contracts and distinguish legacy, current source and published package support. Check links and relevant documentation guards. |
| A6 | Accurate reproducibility promises; Viewer persistence plus each scientific result owner. | Existing session and Interactions contracts; no dedicated provenance-completeness issue verified. | Clarify the user-facing claim. Any stronger recomputation promise needs a representative saved-result workflow rerun from its declared inputs/environment and comparison under an explicit tolerance or identity criterion. |

## Scientific correctness: three separate questions

1. **Is the scientific method appropriate and validated?** This primarily belongs
   to MolSysMT or the scientific addon owner, including method assumptions,
   prerequisites, parameters and reference data.
2. **Does Viewer preserve the result?** Selection, correspondence, units,
   coverage and observed geometry belong to the consumer boundary. The
   inspected implementation and tests provide concrete evidence here.
3. **Does the visualization communicate the result accurately?** This remains
   an important development criterion as scientific capabilities grow.

A participant-centroid segment is a graphical guide, a geometric disulfide
candidate is not a confirmed covalent bond, and an unevaluated frame is not a
negative result. Existing distinctions of this kind must remain visible in
Python, Studio, inspection and exported views. A compelling image must not
promote a hypothesis into an established scientific property.

The conclusion is therefore bounded: Viewer is designed to preserve scientific
correctness within declared contracts; it does not independently certify every
scientific result it can display.

### What the inspected scientific examples establish

| Level | Inspected example | What must not be generalized from it |
| --- | --- | --- |
| Method validity | Qualification includes real hydrogen-bond workloads and an independent enumeration of cysteine sulfur-distance candidates. | Agreement with a geometric criterion does not establish that every detected contact has the same physical significance or that a candidate is a covalent bond. No comprehensive literature/method-validation review was performed. |
| Result preservation | `qualify_periodic` / `observed_geometry` reconstruct participant-image geometry; query/persistence tests retain occurrence identity and evaluated coverage. | These cases do not establish correctness for every periodic cell, compound participant, split ring, detector or format. The existing contract explicitly excludes inferring internal unwrapping of a split participant. |
| Quantitative visual mapping | `test_scalar_color_units.py` checks equivalent quantities/ranges and scene restoration; the renderer declares nm and converts to angstroms. | Unit fidelity does not certify palette accessibility, perceptual comparability or interpretation of every property. |
| Visual interpretation | Renderer labels identify centroid guides; contracts distinguish candidates, observations and unevaluated frames. | Source labels and contracts do not replace user comprehension studies or fresh browser inspection. No such study was performed in this review. |

This table describes the sample inspected, not the entire repository's test
coverage. A case not inspected here may already be tested elsewhere; search
existing guards before proposing additional work.

## Scientific growth directions

These are recommendations for discussion, not newly accepted features or 1.0
requirements. Concrete implementation work needs the normal owning-issue route.

1. **Temporal and ensemble interpretation.** User question: “Which contacts
   persist or change between these states?” Interaction occupancy,
   persistence, distributions and comparisons between states, with explicit
   evaluated-frame denominators. Distinguish a conformation collection from a
   time trajectory; temporal interpretation needs the corresponding data.
2. **Quantitative properties on the scene.** User question: “Where does this
   property differ, and are the displayed values comparable?” Property/contribution coloring
   with units, legends, missing-value semantics and comparable scales across
   frames or systems. Build on the existing unit-aware color boundary.
3. **Explicit chemical-state visualization.** User question: “Which chemical
   state am I seeing, and which analyses apply to it?” Let a qualified future interface
   identify the represented chemical state and its relationship to structures
   and analyses. Coordinate this with MolSysMT; do not infer it silently from
   coordinates.
4. **Scientific comparison of systems.** User question: “What actually changes
   between these systems after accounting for correspondence and orientation?”
   Linked selections, comparative views
   and structural differences with declared correspondences and alignments.
   Separate real differences from orientation, numbering or visual-scale
   differences. Existing multi-view work is tracked separately in #49.
5. **Specialized representations through addons.** User question: “How does
   this domain-specific result relate to the molecular structure?” Cavities, channels,
   pharmacophores and elastic networks can reuse core geometry and scene
   primitives. Keep models and scientific interpretation in their owning
   components. The existing representation proposal #59 is a design input,
   not qualification of those scientific interpretations.

Calculations and domain models remain with their scientific owners; Viewer
owns generic presentation and qualified visual conveniences under the product
boundary. Before accepting any direction, identify a representative workflow,
the existing capability it extends, the scientific contract and an independent
acceptance example. Useful evidence includes a hand-checkable occupancy
denominator, equivalent-unit colors under a shared scale, explicit state
switching, known coordinate/correspondence transformations or a domain result
whose rendered geometry can be reconstructed independently. Reuse existing
issues where their scope matches; otherwise propose an owning issue before
implementation. None of these suggestions proves that the capability is absent
from every existing addon.

## Priority groups and stabilization decisions

### 1. Consolidate existing promises before stabilization

Finish the declared scope, reconcile documentation with actual availability,
complete applicable validation of pending code and qualify the exact installed
candidate. Add independent scientific cases where a concrete gap is identified;
do not indiscriminately repeat still-applicable tests or treat test counts as
scientific coverage.

For this audit, A5 and the claim-clarification parts of A2/A4/A6 belong in that
consolidation. This does not require bounded-memory trajectories, universal
method certification or automatic recomputation before 1.0. Candidate acceptance
continues to follow the existing release plan and its exact-source/artifact gates.

### 2. Maintainability work conditional on demonstrated benefit

A1 warrants investigation during related development, not a mandatory large
refactoring. Use concrete responsibility/coupling findings to choose a bounded
change. Preserve public behavior and avoid disrupting qualified paths merely
to reduce file size. No new pre-1.0 blocker is established by the line counts.

### 3. Scientific and scale growth for a separate decision

A3, expanded residency/performance architecture and the five growth directions
above require their own product/scientific decisions. They are not added to
1.0 acceptance by this audit. Existing post-1.0 scope remains unchanged unless
the maintainer explicitly revises it.

The addon remains separate receiving work under Viewer #264 / MolSysMT #421.
This audit does not complete that work, authorize its publication or resume the
paused implementation. Experimental standalone and deferred remote/scale work
retain their existing boundaries.

The assessment favors focused consolidation over a broad architectural rewrite
or an obligation to expose all possible scientific capabilities before 1.0.
No issues were opened or closed by this review. New recommendations remain
unapproved discussion items until they are dispositioned through the owning
reporting process; existing contracts and queues retain precedence.

## Follow-up — 2026-11-04

During the authorized return to development, the maintained architecture
passages cited by A5 were reconciled: public-pair qualification is distinguished
from future candidate qualification, and legacy addon retirement from the
approved, partially implemented provider-owned tools facade. The observations
above remain tied to the original inspected commit. This documentation change
adds no runtime, scientific-validation or publication claim.
